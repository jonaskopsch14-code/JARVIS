"""Beispiel-Skill (Phase 7): Produkt-/Marktrecherche (Stufe 1, nur lesen).

Nutzt die vorhandene Websuche und bereitet die Treffer als kurze Recherche auf.
"""

from __future__ import annotations

from . import skill
from ..security import Risk


@skill(
    name="research_product",
    description="Recherchiert kurz zu einem Produkt oder Trend im Web und fasst zusammen.",
    parameters={"type": "object", "properties": {
        "query": {"type": "string"}}, "required": ["query"]},
    risk=Risk.AUTO,
)
def research_product(query: str) -> str:
    from .web_search import web_search
    findings = web_search(f"{query} Trend kaufen Bewertung")
    return f"Kurzrecherche zu '{query}': {findings}"
