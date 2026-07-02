"""Bildschirm sehen (Phase 3).

  screenshot     Stufe 1 (Screenshot speichern)
  read_screen    Stufe 1 (Screenshot + lokale Bildbeschreibung via Vision-Modell)

Die Bildbeschreibung nutzt ein lokales Vision-Modell über Ollama (z. B. 'llava').
Fehlt es, gibt read_screen wenigstens den gespeicherten Pfad zurück.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from . import skill
from ..security import Risk

# von main aus Config gesetzt (Ollama-URL + optionales Vision-Modell)
OLLAMA_URL = "http://127.0.0.1:11434"
VISION_MODEL = "llava"


def _capture() -> Path:
    import mss  # lazy
    out = Path(tempfile.gettempdir()) / "jarvis_screen.png"
    with mss.mss() as sct:
        sct.shot(mon=-1, output=str(out))
    return out


@skill(
    name="screenshot",
    description="Macht einen Screenshot des Bildschirms und speichert ihn.",
    parameters={"type": "object", "properties": {}},
    risk=Risk.AUTO,
)
def screenshot() -> str:
    try:
        path = _capture()
        return f"Screenshot gespeichert: {path}"
    except Exception as exc:  # noqa: BLE001
        return f"Screenshot fehlgeschlagen: {exc}"


@skill(
    name="read_screen",
    description="Beschreibt, was gerade auf dem Bildschirm zu sehen ist.",
    parameters={"type": "object", "properties": {
        "question": {"type": "string", "description": "optional: konkrete Frage zum Bild"}}},
    risk=Risk.AUTO,
)
def read_screen(question: str = "") -> str:
    try:
        path = _capture()
    except Exception as exc:  # noqa: BLE001
        return f"Screenshot fehlgeschlagen: {exc}"
    try:
        import httpx  # lazy
        img_b64 = base64.b64encode(Path(path).read_bytes()).decode()
        prompt = question or "Beschreibe knapp, was auf dem Bildschirm zu sehen ist."
        r = httpx.post(f"{OLLAMA_URL}/api/generate", timeout=120.0, json={
            "model": VISION_MODEL, "prompt": prompt,
            "images": [img_b64], "stream": False})
        r.raise_for_status()
        return r.json().get("response", "").strip() or f"(Keine Beschreibung; Bild: {path})"
    except Exception as exc:  # noqa: BLE001
        return (f"Bild gespeichert unter {path}, aber Bildbeschreibung nicht möglich "
                f"({exc}). Tipp: 'ollama pull {VISION_MODEL}'.")
