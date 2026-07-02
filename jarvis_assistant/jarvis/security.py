"""Sicherheitsstufen — echter Prüf-Mechanismus vor jeder Werkzeug-Ausführung.

Stufe 1  automatisch      lesen/informieren/öffnen/abrufen
Stufe 2  kurz bestätigen   reversibel (Datei schreiben, Programm schließen …)
Stufe 3  explizit bestätigen  Geld/endgültig/nach außen (löschen, senden, Preise …)

Unbekanntes wird konservativ als Stufe 3 behandelt (sicher per Default).
Die Bestätigung ist über einen `Confirmer` austauschbar: Konsole (Text-Modus),
Stimme (Sprach-Modus) oder Auto-Verweigern (unbeaufsichtigt).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Optional


class Risk(IntEnum):
    AUTO = 1        # automatisch erlaubt
    CONFIRM = 2     # kurze Bestätigung
    EXPLICIT = 3    # immer explizit bestätigen


@dataclass
class Decision:
    allowed: bool
    risk: Risk
    reason: str = ""


# --- Bestätiger (Confirmer) -------------------------------------------------
Confirmer = Callable[[str, Risk], bool]


def auto_deny(prompt: str, risk: Risk) -> bool:
    """Unbeaufsichtigt: alles jenseits Stufe 1 wird verweigert."""
    return False


def console_confirmer(prompt: str, risk: Risk) -> bool:
    """Text-Modus: y/n auf der Konsole. Stufe 3 verlangt ausdrückliches 'ja'."""
    try:
        ans = input(f"[Bestätigung Stufe {int(risk)}] {prompt}  "
                    f"{'(tippe JA) ' if risk == Risk.EXPLICIT else '(j/n) '}").strip().lower()
    except EOFError:
        return False
    if risk == Risk.EXPLICIT:
        return ans == "ja"
    return ans in ("j", "ja", "y", "yes")


class Guard:
    """Torwächter: bestimmt die Risikostufe und holt ggf. eine Bestätigung."""

    def __init__(self, confirmer: Optional[Confirmer] = None):
        # Default konservativ: ohne expliziten Confirmer wird bestätigt-nötiges verweigert.
        self.confirmer: Confirmer = confirmer or auto_deny

    def assess(self, risk: Risk) -> Risk:
        # Platzhalter für kontextabhängige Verschärfung (z. B. args-basiert).
        return risk

    def check(self, tool_name: str, risk: Risk, prompt: str) -> Decision:
        risk = self.assess(risk)
        if risk == Risk.AUTO:
            return Decision(True, risk, "Stufe 1: automatisch erlaubt")
        allowed = bool(self.confirmer(prompt, risk))
        return Decision(allowed, risk,
                        "bestätigt" if allowed else "abgelehnt/keine Bestätigung")
