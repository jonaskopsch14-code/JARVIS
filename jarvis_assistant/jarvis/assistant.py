"""Assistent-Kern: verbindet LLM, Werkzeuge und das Sicherheits-Gate.

Hardware-unabhängig und testbar. `handle(text) -> antwort_text` führt die
Tool-Calling-Schleife aus: das LLM darf Werkzeuge aufrufen, jedes wird vom
Guard geprüft, ausgeführt und das Ergebnis zurückgespeist, bis eine finale
Antwort steht.
"""

from __future__ import annotations

import json
from typing import List, Optional

from . import skills
from .audit import audit
from .llm import LLM
from .persona import system_prompt
from .security import Guard, Risk

MAX_TOOL_HOPS = 5  # Schutz gegen Endlosschleifen


def _parse_args(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except ValueError:
            return {}
    return {}


class Assistant:
    def __init__(self, llm: LLM, guard: Optional[Guard] = None,
                 user_name: str = "Jonas", memory=None, extra_context: str = ""):
        self.llm = llm
        self.guard = guard or Guard()
        self.user_name = user_name
        self.memory = memory
        self.history: List[dict] = []
        self._extra_context = extra_context

    def _system(self) -> dict:
        ctx = self._extra_context
        if self.memory is not None:
            ctx = (ctx + "\n" + self.memory.context_block()).strip()
        return {"role": "system", "content": system_prompt(self.user_name, ctx)}

    def handle(self, user_text: str) -> str:
        """Eine Nutzeräußerung verarbeiten und die gesprochene Antwort liefern."""
        tools = skills.build_tools()
        messages: List[dict] = [self._system()] + self.history + \
            [{"role": "user", "content": user_text}]

        final = ""
        for _ in range(MAX_TOOL_HOPS):
            msg = self.llm.chat(messages, tools=tools)
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                final = msg.get("content", "").strip()
                break
            messages.append({"role": "assistant", "content": msg.get("content", ""),
                             "tool_calls": tool_calls})
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                args = _parse_args(fn.get("arguments"))
                result = self._run_tool(name, args)
                messages.append({"role": "tool", "name": name, "content": result})
        else:
            final = "Ich habe zu viele Zwischenschritte gebraucht und breche hier ab, Sir."

        # Dialog-Gedächtnis pflegen.
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": final})
        self.history = self.history[-12:]  # nur jüngsten Verlauf mitschleppen
        if self.memory is not None:
            try:
                self.memory.observe(user_text, final)
            except Exception:  # noqa: BLE001 - Gedächtnis darf den Dialog nie sprengen
                pass
        return final or "Verzeihung, dazu habe ich gerade keine Antwort."

    def _run_tool(self, name: str, args: dict) -> str:
        sk = skills.get(name)
        if sk is None:
            audit("tool.unknown", args={"name": name}, ok=False,
                  error="unbekanntes Werkzeug")
            return f"Unbekanntes Werkzeug: {name}"
        prompt = (sk.confirm_prompt or f"Werkzeug '{name}' mit {args} ausführen?")
        decision = self.guard.check(name, sk.risk, prompt)
        if not decision.allowed:
            audit(f"tool.{name}", args=args, risk=int(sk.risk), allowed=False,
                  ok=False, error="nicht bestätigt")
            return (f"Aktion '{name}' wurde nicht ausgeführt "
                    f"(Sicherheitsstufe {int(sk.risk)}, keine Bestätigung).")
        try:
            result = sk.func(**args) if args else sk.func()
            audit(f"tool.{name}", args=args, risk=int(sk.risk), allowed=True,
                  ok=True, result=str(result))
            return str(result)
        except TypeError as exc:
            audit(f"tool.{name}", args=args, risk=int(sk.risk), allowed=True,
                  ok=False, error=str(exc))
            return f"Falsche Argumente für '{name}': {exc}"
        except Exception as exc:  # noqa: BLE001
            audit(f"tool.{name}", args=args, risk=int(sk.risk), allowed=True,
                  ok=False, error=str(exc))
            return f"Werkzeug '{name}' ist fehlgeschlagen: {exc}"
