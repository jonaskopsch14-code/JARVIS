"""Browser-Automatisierung via Playwright (Phase 3).

  browse_page   Stufe 1 (Seite öffnen und Text auslesen)

Weitere Aktionen (Formular ausfüllen, klicken) kommen später und laufen dann
als Stufe 2/3 — je nachdem, ob sie etwas verändern.
"""

from __future__ import annotations

from . import skill
from ..security import Risk


@skill(
    name="browse_page",
    description="Öffnet eine Webseite im Hintergrund-Browser und gibt den sichtbaren Text zurück.",
    parameters={"type": "object", "properties": {
        "url": {"type": "string"}}, "required": ["url"]},
    risk=Risk.AUTO,
)
def browse_page(url: str) -> str:
    if not (url or "").startswith(("http://", "https://")):
        url = "https://" + (url or "")
    try:
        from playwright.sync_api import sync_playwright  # lazy
    except Exception as exc:  # noqa: BLE001
        return (f"Browser-Automatisierung nicht verfügbar (Playwright fehlt: {exc}). "
                f"Einrichten: pip install playwright && playwright install chromium")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            text = page.inner_text("body")
            browser.close()
        text = " ".join(text.split())
        return text[:4000] + ("…" if len(text) > 4000 else "")
    except Exception as exc:  # noqa: BLE001
        return f"Konnte Seite nicht laden: {exc}"
