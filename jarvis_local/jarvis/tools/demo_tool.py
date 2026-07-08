"""Demo-Tools, um die Freigabe-Logik greifbar zu machen.

``shop_purchase`` hat die Wirkung ``SPEND`` → immer Tier 1 → immer Bestätigung
durch Jonas. Genau die eine Regel: *Wenn Geld ausgegeben wird, braucht es
Bestätigung.* Ohne Freigabe wird nichts gekauft.
"""
from __future__ import annotations

from ..security.permission_gateway import EffectCategory
from .base import Tool, ToolResult


def build_demo_tools() -> list[Tool]:
    purchases: list[dict] = []

    def shop_purchase(item: str, price_eur: float) -> ToolResult:
        # Läuft nur, wenn das Gateway die Tier-1-Freigabe erteilt hat.
        purchases.append({"item": item, "price_eur": float(price_eur)})
        return ToolResult(True, f"Gekauft: {item} für {float(price_eur):.2f} €.", {"purchases": purchases})

    return [
        Tool(
            name="shop_purchase",
            description="Kauft einen Artikel (gibt Geld aus). Erfordert ausdrückliche Freigabe von Jonas.",
            effect=EffectCategory.SPEND,
            parameters={
                "type": "object",
                "properties": {
                    "item": {"type": "string", "description": "Was gekauft werden soll."},
                    "price_eur": {"type": "number", "description": "Preis in Euro."},
                },
                "required": ["item", "price_eur"],
            },
            run=shop_purchase, intent_template="Kauf: {item} für {price_eur} €",
        ),
    ]
