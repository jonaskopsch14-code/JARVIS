"""Skill-Registry: Werkzeuge, die Jarvis (das LLM) aufrufen kann.

Jedes Skill hat: Name, Beschreibung, Parameter-Schema (für Ollama-Tool-Calling),
eine Standard-Risikostufe (Sicherheits-Gate) und die Funktion selbst.

Skills registrieren sich per @skill-Dekorator. `build_tools()` erzeugt die
Tool-Definitionen im OpenAI/Ollama-Format; `get(name)` liefert das Skill zurück.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from ..security import Risk


@dataclass
class Skill:
    name: str
    description: str
    parameters: dict           # JSON-Schema der Argumente
    risk: Risk
    func: Callable[..., str]
    confirm_prompt: str = ""   # Vorlage für die Bestätigungsfrage (Stufe 2/3)


_REGISTRY: Dict[str, Skill] = {}


def skill(name: str, description: str, parameters: dict, risk: Risk = Risk.EXPLICIT,
          confirm_prompt: str = ""):
    """Dekorator zum Registrieren eines Skills. Default-Risiko konservativ (3)."""
    def deco(func: Callable[..., str]) -> Callable[..., str]:
        _REGISTRY[name] = Skill(name, description, parameters, risk, func, confirm_prompt)
        return func
    return deco


def get(name: str) -> Skill | None:
    return _REGISTRY.get(name)


def all_skills() -> List[Skill]:
    return list(_REGISTRY.values())


def build_tools() -> List[dict]:
    """Tool-Definitionen für den Ollama-/OpenAI-Chat mit Tool-Calling."""
    tools = []
    for s in _REGISTRY.values():
        tools.append({
            "type": "function",
            "function": {
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters or {"type": "object", "properties": {}},
            },
        })
    return tools


def _register_builtin() -> None:
    # Import der Skill-Module registriert sie über den Dekorator.
    from . import open_app, web_search, read_file, weather, calendar_local  # noqa: F401
    # Phasen 3/5 (werden importiert, wenn vorhanden — brechen den Kern nie).
    for mod in ("files", "processes", "browser", "screen", "email_gmail",
                "shop_watch"):
        try:
            __import__(f"jarvis.skills.{mod}")
        except Exception:  # noqa: BLE001 - optionale/hardware-abhängige Skills
            pass


_register_builtin()
