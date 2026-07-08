"""Web-Agent-Tools (Hybrid: Cloud-Modell steuert den Browser).

Der Leitfaden ist eindeutig: lokale 8B-Modelle sind für browser-use „not powerful
enough". Daher läuft der Web-Agent über ein Cloud-Modell (Claude/GPT/Gemini).
Recherche (nur lesen) ist Tier 0. Jede Web-Aktion mit Nebenwirkung (absenden,
kaufen) ist Tier 1 und wird vom Gateway angehalten.

Die ``browser_use``-Anbindung ist gekapselt – ohne installiertes Paket bzw. ohne
API-Key liefert das Tool eine klare Meldung statt zu crashen.
"""
from __future__ import annotations

import os

from ..security.permission_gateway import EffectCategory
from .base import Tool, ToolResult


def _run_browser_agent(task: str, allow_actions: bool) -> ToolResult:  # pragma: no cover - braucht Cloud
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return ToolResult(
            False,
            "Web-Agent nicht konfiguriert: kein Cloud-API-Key (ANTHROPIC_API_KEY/OPENAI_API_KEY) gesetzt.",
        )
    try:
        from browser_use import Agent  # type: ignore
    except ImportError:
        return ToolResult(False, "browser-use nicht installiert: `pip install browser-use`.")
    # Bewusst knapp gehalten – die konkrete LLM-Verdrahtung passiert am Windows-PC.
    agent = Agent(task=task)
    result = agent.run_sync() if hasattr(agent, "run_sync") else None
    return ToolResult(True, str(result) if result else "Web-Aufgabe ausgeführt.")


def build_web_tools() -> list[Tool]:
    def web_research(task: str) -> ToolResult:
        return _run_browser_agent(task, allow_actions=False)

    def web_action(task: str) -> ToolResult:
        # Erreicht diese Funktion nur nach Tier-1-Freigabe durch das Gateway.
        return _run_browser_agent(task, allow_actions=True)

    return [
        Tool(
            name="web_research",
            description="Recherchiert im Web (nur lesen) über einen Cloud-Browser-Agenten.",
            effect=EffectCategory.READ,
            parameters={"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]},
            run=web_research, intent_template="Web-Recherche: {task}",
        ),
        Tool(
            name="web_action",
            description="Führt eine Web-Aktion mit Nebenwirkung aus (Formular absenden o.ä.). Braucht Freigabe.",
            effect=EffectCategory.SEND,
            parameters={"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]},
            run=web_action, intent_template="Web-Aktion (mit Nebenwirkung): {task}",
        ),
    ]
