"""Intent-Router: entscheidet lokal (Qwen) vs. Cloud (Web-Agent / komplexes Reasoning).

Bewusst einfache Heuristik – der Leitfaden empfiehlt Hybrid: lokales LLM für
Chat/Routing/Gedächtnis, Cloud nur für den Web-Agenten und sehr komplexe
Multi-Step-Aufgaben (8B-Klasse trifft dort ihre Intelligenz-Decke).
"""
from __future__ import annotations

import enum
import re
from dataclasses import dataclass


class Route(str, enum.Enum):
    LOCAL = "local"    # Qwen3-8B via Ollama
    CLOUD = "cloud"    # Cloud-Modell (Web-Agent, komplexes Reasoning)


# Wörter, die auf eine echte Web-/Browser-Aufgabe hindeuten.
_WEB_HINTS = (
    "browser", "webseite", "website", "im internet", "online", "google", "such im netz",
    "recherchiere", "öffne die seite", "buche", "bestelle", "formular", "einloggen", "login bei",
    "warenkorb", "checkout",
)
_COMPLEX_HINTS = ("plane in mehreren schritten", "vergleiche mehrere", "erstelle einen ausführlichen")


@dataclass
class RouteDecision:
    route: Route
    reason: str


def route(user_input: str) -> RouteDecision:
    text = user_input.lower()
    for hint in _WEB_HINTS:
        if hint in text:
            return RouteDecision(Route.CLOUD, f"Web-Aufgabe erkannt ('{hint}') → Cloud-Web-Agent.")
    for hint in _COMPLEX_HINTS:
        if hint in text:
            return RouteDecision(Route.CLOUD, "Komplexe Multi-Step-Aufgabe → Cloud-Reasoning.")
    # Sehr lange Anfragen deuten auf hohen Kontextbedarf → Cloud.
    if len(re.findall(r"\w+", text)) > 220:
        return RouteDecision(Route.CLOUD, "Sehr langer Kontext → Cloud (8B-VRAM-Grenze).")
    return RouteDecision(Route.LOCAL, "Standard-Dialog/Tool-Nutzung → lokales Qwen.")
