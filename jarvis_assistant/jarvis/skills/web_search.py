"""Skill: Websuche (Stufe 1). Best-effort über DuckDuckGo, ohne API-Key."""

from __future__ import annotations

import html
import re
from urllib.parse import quote_plus

from . import skill
from ..security import Risk


@skill(
    name="web_search",
    description="Sucht im Web und gibt die wichtigsten Treffer als kurzen Text zurück.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Suchbegriff"}},
        "required": ["query"],
    },
    risk=Risk.AUTO,
)
def web_search(query: str) -> str:
    q = (query or "").strip()
    if not q:
        return "Kein Suchbegriff angegeben."
    try:
        import httpx  # lazy
    except Exception as exc:  # noqa: BLE001
        return f"Websuche nicht verfügbar (httpx fehlt: {exc})."
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(q)
    try:
        r = httpx.get(url, timeout=10.0,
                      headers={"User-Agent": "Mozilla/5.0 JarvisBot"})
        r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return f"Websuche fehlgeschlagen: {exc}"
    # Ergebnis-Titel + Snippets grob extrahieren.
    titles = re.findall(r'result__a[^>]*>(.*?)</a>', r.text, re.S)
    snippets = re.findall(r'result__snippet[^>]*>(.*?)</a>', r.text, re.S)

    def clean(s: str) -> str:
        return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

    out = []
    for i in range(min(3, len(titles))):
        t = clean(titles[i])
        s = clean(snippets[i]) if i < len(snippets) else ""
        if t:
            out.append(f"{t}: {s}" if s else t)
    if not out:
        return f"Keine klaren Treffer für '{q}' gefunden."
    return " | ".join(out)
