"""Beispiel-Skill (Phase 7): Marketing-Text vorbereiten.

Muster „vorschlagen/vorbereiten, ausführen erst mit Bestätigung": Das Erstellen
eines Entwurfs ist harmlos (Stufe 1). Das tatsächliche Veröffentlichen wäre ein
separater Stufe-3-Skill.
"""

from __future__ import annotations

from . import skill
from ..security import Risk

_TONE = {
    "freundlich": ("Entdecke", "Sichere dir jetzt deins."),
    "hochwertig": ("Erlebe", "Zeitlose Qualität, die bleibt."),
    "verknappt": ("Nur kurz verfügbar:", "Schnell sein lohnt sich."),
}


@skill(
    name="draft_marketing_text",
    description="Erstellt einen Entwurf für einen Werbetext zu einem Produkt (veröffentlicht nichts).",
    parameters={
        "type": "object",
        "properties": {
            "product": {"type": "string", "description": "Produktname"},
            "benefit": {"type": "string", "description": "wichtigster Vorteil (optional)"},
            "tone": {"type": "string", "description": "freundlich | hochwertig | verknappt"},
        },
        "required": ["product"],
    },
    risk=Risk.AUTO,
)
def draft_marketing_text(product: str, benefit: str = "", tone: str = "freundlich") -> str:
    opener, closer = _TONE.get(tone, _TONE["freundlich"])
    headline = f"{opener} {product}"
    body = f"{product} von Fashion Aura"
    if benefit:
        body += f" – {benefit}"
    body += ". " + closer
    tag = "".join(w.capitalize() for w in product.split())
    return (f"Entwurf (nicht veröffentlicht):\n"
            f"Überschrift: {headline}\n"
            f"Text: {body}\n"
            f"Hashtags: #FashionAura #{tag} #Mode")
