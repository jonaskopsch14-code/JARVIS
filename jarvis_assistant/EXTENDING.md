# Jarvis um eigene Fähigkeiten erweitern

Jede Fähigkeit ist ein **Skill**: eine Python-Funktion mit einem `@skill`-Dekorator.
Jarvis (das lokale Modell) sieht automatisch alle registrierten Skills und ruft
sie bei Bedarf auf. Das Sicherheits-Gate erzwingt vor jeder Ausführung die
richtige Risikostufe.

## Ein Skill in 30 Sekunden

Lege eine Datei unter `jarvis/skills/` an, z. B. `mein_skill.py`:

```python
from . import skill
from ..security import Risk

@skill(
    name="wuerfeln",
    description="Würfelt eine Zahl von 1 bis 6.",
    parameters={"type": "object", "properties": {}},   # keine Argumente
    risk=Risk.AUTO,        # Stufe 1: nur informierend
)
def wuerfeln() -> str:
    import random
    return f"Gewürfelt: {random.randint(1, 6)}."
```

Dann in `jarvis/skills/__init__.py` in `_register_builtin()` importieren
(eine Zeile). Fertig — beim nächsten Start kennt Jarvis „würfeln".

## Die Regeln

1. **Rückgabe ist immer ein `str`** — kurz und gut vorlesbar (kein Markdown/Emoji).
2. **Risikostufe wählen** (das ist Pflicht, kein Nice-to-have):
   - `Risk.AUTO` (1): nur lesen/informieren/öffnen → läuft ohne Rückfrage.
   - `Risk.CONFIRM` (2): reversibel ändern → kurze Bestätigung.
   - `Risk.EXPLICIT` (3): löschen, Geld, senden, öffentlich → ausdrückliche Bestätigung.
   Für Stufe 2/3 zusätzlich `confirm_prompt="..."` setzen (die Frage, die Jarvis stellt).
3. **`parameters`** ist ein JSON-Schema. Die Argumentnamen müssen mit den
   Funktionsparametern übereinstimmen.
4. **Fehler abfangen und als Text zurückgeben** — nie eine Exception nach oben
   werfen. Jarvis meldet dem Nutzer dann ehrlich, dass es nicht klappte.
5. **Muster für alles Weitere (Phase 7+):** erst *vorbereiten/vorschlagen*
   (Stufe 1/2), das *Ausführen nach außen* als getrennter Stufe-3-Skill. Siehe
   `marketing.py` (Entwurf = Stufe 1) als Vorlage.

## Beispiel mit Bestätigung (Stufe 2)

```python
@skill(
    name="notiz_speichern",
    description="Speichert eine kurze Notiz in einer Datei.",
    parameters={"type": "object", "properties": {
        "text": {"type": "string"}}, "required": ["text"]},
    risk=Risk.CONFIRM,
    confirm_prompt="Soll ich die Notiz speichern?",
)
def notiz_speichern(text: str) -> str:
    from pathlib import Path
    p = Path.home() / "Jarvis" / "notizen.txt"
    with open(p, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    return "Notiz gespeichert."
```

## Testen (ohne Mikro/Modell)

Nutze das Test-Double `ScriptedLLM`, um einen Werkzeug-Aufruf zu simulieren —
siehe `tests/test_phase1_core.py`. So prüfst du Skill + Sicherheitsstufe rein
in Python, bevor du es per Stimme ausprobierst.
