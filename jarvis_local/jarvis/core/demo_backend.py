"""Regelbasiertes Demo-Backend (kein LLM/keine GPU nötig).

Bildet nur so viel „Intelligenz" nach, dass der Agent-Loop end-to-end läuft und
die Werkzeuge + das Freigabe-Gateway sichtbar arbeiten. In Produktion ersetzt
das :class:`~jarvis.core.llm.OllamaBackend` dieses Backend 1:1.
"""
from __future__ import annotations

import re

from .llm import Message, final, tool_call


def demo_responder(messages: list[Message], tools: list[dict] | None = None) -> Message:
    # Letzte Nutzer- oder Tool-Nachricht betrachten.
    last = messages[-1]
    if last.get("role") == "tool":
        # Tool-Ergebnis liegt vor → knapp zusammenfassen und abschließen.
        return final(last.get("content", "Erledigt."))

    text = (last.get("content") or "").lower()

    # Kauf / Geld ausgeben → Tier-1-Tool (Freigabe erforderlich).
    m = re.search(r"(kauf|bestell|besorg)\w*\s+(.+?)(?:\s+für\s+([\d.,]+)\s*(?:eur|euro|€))", text)
    if m:
        item = m.group(2).strip()
        price = float(m.group(3).replace(",", ".")) if m.group(3) else 0.0
        return tool_call("shop_purchase", item=item, price_eur=price)

    # Notiz speichern.
    if any(w in text for w in ("merke", "notier", "speicher", "schreib dir auf", "erinnere mich")):
        content = last.get("content", "")
        cleaned = re.sub(r"^(bitte\s+)?(merke dir|notiere|speichere|schreib dir auf)[:,]?\s*", "", content, flags=re.I)
        return tool_call("memory_write", text=cleaned or content)

    # Gedächtnis durchsuchen.
    if any(w in text for w in ("was weißt du", "erinnerst du", "suche", "finde", "wonach")):
        return tool_call("memory_search", query=re.sub(r"[?.!]", "", last.get("content", "")))

    # Ungelesene Mails.
    if "mail" in text or "e-mail" in text or "postfach" in text:
        return tool_call("gmail_list", max_results=10)

    # Sonst: einfache Antwort.
    return final(
        "Alles klar. (Demo-Modus ohne echtes LLM – probier z. B. »merke dir …«, "
        "»was weißt du über …«, »zeig ungelesene Mails« oder »kaufe X für 20 Euro«.)"
    )
