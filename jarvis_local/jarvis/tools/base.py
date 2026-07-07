"""Tool-Abstraktion + Registry.

Jedes Tool deklariert seine Wirkungs-Kategorie (``effect``). Daraus leitet das
Permission-Gateway das Risiko-Tier ab – die Klassifikation liegt also NICHT im
Agent-Code, sondern folgt aus einer Daten-Deklaration am Tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..security.permission_gateway import EffectCategory


@dataclass
class ToolResult:
    ok: bool
    content: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    name: str
    description: str
    effect: EffectCategory
    parameters: dict[str, Any]                 # JSON-Schema der Argumente
    run: Callable[..., ToolResult]
    intent_template: str = ""                   # z.B. "E-Mail-Entwurf an {to}"

    def describe_intent(self, args: dict[str, Any]) -> str:
        if self.intent_template:
            try:
                return self.intent_template.format(**args)
            except Exception:
                pass
        return f"{self.name}({', '.join(f'{k}={v!r}' for k, v in args.items())})"

    def to_ollama_schema(self) -> dict[str, Any]:
        """Format für den nativen Ollama-/OpenAI-``tools``-Parameter."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {"type": "object", "properties": {}},
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' bereits registriert.")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def ollama_schemas(self) -> list[dict[str, Any]]:
        return [t.to_ollama_schema() for t in self._tools.values()]

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
