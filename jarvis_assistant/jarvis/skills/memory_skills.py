"""Skills, mit denen Jarvis sich Dinge merkt/vergisst (Phase 2).

Der aktive Speicher wird von main gesetzt (MEMORY). Ohne Speicher antworten die
Skills freundlich statt zu scheitern.
"""

from __future__ import annotations

from . import skill
from ..security import Risk

MEMORY = None  # von main gesetzt: eine Memory-Instanz


@skill(
    name="remember_fact",
    description="Merkt sich dauerhaft eine Vorliebe oder einen Fakt über den Nutzer.",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "kurzes Stichwort, z. B. 'lieblingsfarbe'"},
            "value": {"type": "string", "description": "der zu merkende Wert"},
        },
        "required": ["key", "value"],
    },
    risk=Risk.AUTO,
)
def remember_fact(key: str, value: str) -> str:
    if MEMORY is None:
        return "Kein Gedächtnis aktiv."
    MEMORY.remember(key, value)
    return f"Gemerkt: {key} = {value}."


@skill(
    name="recall_facts",
    description="Gibt zurück, was Jarvis sich über den Nutzer gemerkt hat.",
    parameters={"type": "object", "properties": {
        "key": {"type": "string", "description": "optional: bestimmtes Stichwort"}}},
    risk=Risk.AUTO,
)
def recall_facts(key: str = "") -> str:
    if MEMORY is None:
        return "Kein Gedächtnis aktiv."
    if key:
        val = MEMORY.recall(key)
        return f"{key} = {val}." if val else f"Zu '{key}' habe ich nichts gespeichert."
    facts = MEMORY.facts()
    if not facts:
        return "Ich habe mir bisher nichts Bestimmtes gemerkt."
    return "; ".join(f"{k} = {v}" for k, v in facts.items())


@skill(
    name="forget_fact",
    description="Löscht einen gemerkten Fakt.",
    parameters={"type": "object", "properties": {
        "key": {"type": "string"}}, "required": ["key"]},
    risk=Risk.CONFIRM,
    confirm_prompt="Soll ich diesen gemerkten Eintrag wirklich löschen?",
)
def forget_fact(key: str) -> str:
    if MEMORY is None:
        return "Kein Gedächtnis aktiv."
    return f"'{key}' vergessen." if MEMORY.forget(key) else f"'{key}' war nicht gespeichert."
