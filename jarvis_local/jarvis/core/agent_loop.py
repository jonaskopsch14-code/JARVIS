"""ReAct-Agent-Loop: Observe → Think → Act → Repeat.

Der Loop ist bewusst schlank und vollständig verstehbar. Vor JEDER Tool-Ausführung
mit Nebenwirkung fragt er das :class:`PermissionGateway`. Tier-1-Aktionen werden
angehalten, bis ein ``approver`` zustimmt – der Agent kann diese Schranke nicht
umgehen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..security.permission_gateway import (
    Action, ApprovalStatus, PermissionGateway,
)
from ..tools.base import ToolRegistry, ToolResult
from .llm import LLMBackend, Message

DEFAULT_SYSTEM_PROMPT = (
    "Du bist Jarvis, ein deutschsprachiger persönlicher Assistent für Jonas. "
    "Antworte knapp und natürlich auf Deutsch. Nutze Werkzeuge (Tools) nur, wenn "
    "sie wirklich gebraucht werden. Aktionen mit Nebenwirkung (senden, bezahlen, "
    "löschen, veröffentlichen) müssen von Jonas freigegeben werden – kündige sie "
    "klar an, statt sie stillschweigend auszuführen."
)

# Rückfrage an den Menschen: bekommt die Aktion, gibt True (freigeben) / False.
Approver = Callable[[Action], bool]


@dataclass
class AgentResult:
    reply: str
    steps: int
    pending_approvals: list[str] = field(default_factory=list)
    transcript: list[Message] = field(default_factory=list)


class AgentLoop:
    def __init__(
        self,
        backend: LLMBackend,
        registry: ToolRegistry,
        gateway: PermissionGateway,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_steps: int = 8,
    ) -> None:
        self.backend = backend
        self.registry = registry
        self.gateway = gateway
        self.system_prompt = system_prompt
        self.max_steps = max_steps

    def run(self, user_input: str, approver: Approver | None = None) -> AgentResult:
        messages: list[Message] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        schemas = self.registry.ollama_schemas()
        pending: list[str] = []

        for step in range(1, self.max_steps + 1):
            assistant = self.backend.chat(messages, schemas)
            messages.append(assistant)
            tool_calls = assistant.get("tool_calls") or []

            if not tool_calls:
                return AgentResult(
                    reply=(assistant.get("content") or "").strip(),
                    steps=step, pending_approvals=pending, transcript=messages,
                )

            for call in tool_calls:
                fn = call["function"]
                name = fn["name"]
                args = fn.get("arguments") or {}
                result_msg = self._dispatch(name, args, approver, pending)
                messages.append(result_msg)

        # max_steps erreicht → letzte Antwort erzwingen
        final = self.backend.chat(messages, schemas)
        return AgentResult(
            reply=(final.get("content") or "Ich konnte die Aufgabe nicht abschließen.").strip(),
            steps=self.max_steps, pending_approvals=pending, transcript=messages,
        )

    def _dispatch(
        self, name: str, args: dict[str, Any], approver: Approver | None, pending: list[str]
    ) -> Message:
        tool = self.registry.get(name)
        if tool is None:
            self.gateway.audit.record("tool_unknown", tool=name, status="error")
            return {"role": "tool", "name": name, "content": f"Unbekanntes Tool: {name}"}

        action = Action(
            tool=tool.name,
            effect=tool.effect,
            intent=tool.describe_intent(args),
            args=args,
            expected_result=tool.description,
        )
        self.gateway.audit.record(
            "tool_call", tool=tool.name, tier=f"TIER{int(self.gateway.classify(tool.effect))}",
            intent=action.intent,
        )

        decision = self.gateway.authorize(action, approver)

        if decision.status is ApprovalStatus.PENDING:
            pending.append(decision.approval_id)
            return {
                "role": "tool", "name": name,
                "content": (
                    f"⏸ Aktion angehalten und wartet auf Jonas' Freigabe "
                    f"(Freigabe-ID {decision.approval_id}). Nicht ausgeführt."
                ),
            }
        if decision.status is ApprovalStatus.DENIED:
            return {"role": "tool", "name": name, "content": "Aktion von Jonas abgelehnt. Nicht ausgeführt."}

        # freigegeben (Tier 0 automatisch oder Tier 1 bestätigt) → ausführen
        try:
            result: ToolResult = tool.run(**args)
        except Exception as exc:  # Tool-Fehler nicht den Loop crashen lassen
            self.gateway.audit.record("tool_error", tool=tool.name, status="error", error=str(exc))
            return {"role": "tool", "name": name, "content": f"Fehler im Tool: {exc}"}

        self.gateway.audit.record(
            "executed", tool=tool.name, status="ok" if result.ok else "failed",
        )
        return {"role": "tool", "name": name, "content": result.content}
