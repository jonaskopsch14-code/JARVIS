"""Skill: Wetter (Stufe 1) über Open-Meteo — kein API-Key nötig."""

from __future__ import annotations

from . import skill
from ..security import Risk

# Aus der Config gesetzt (main füllt das); Fallback Berlin.
DEFAULT_CITY = "Berlin"

_WMO = {
    0: "klar", 1: "überwiegend klar", 2: "teils bewölkt", 3: "bewölkt",
    45: "Nebel", 48: "Reifnebel", 51: "leichter Niesel", 53: "Niesel",
    55: "starker Niesel", 61: "leichter Regen", 63: "Regen", 65: "starker Regen",
    71: "leichter Schnee", 73: "Schnee", 75: "starker Schnee", 80: "Schauer",
    81: "Schauer", 82: "heftige Schauer", 95: "Gewitter", 96: "Gewitter mit Hagel",
}


def _geocode(client, city: str):
    r = client.get("https://geocoding-api.open-meteo.com/v1/search",
                   params={"name": city, "count": 1, "language": "de"})
    r.raise_for_status()
    res = r.json().get("results") or []
    if not res:
        return None
    return res[0]["latitude"], res[0]["longitude"], res[0].get("name", city)


@skill(
    name="weather",
    description="Aktuelles Wetter und Tagesvorhersage für einen Ort (Standard: konfigurierte Stadt).",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string", "description": "Ort (optional)"}},
    },
    risk=Risk.AUTO,
)
def weather(city: str = "") -> str:
    place = (city or DEFAULT_CITY).strip()
    try:
        import httpx  # lazy
    except Exception as exc:  # noqa: BLE001
        return f"Wetter nicht verfügbar (httpx fehlt: {exc})."
    try:
        with httpx.Client(timeout=10.0) as client:
            geo = _geocode(client, place)
            if not geo:
                return f"Ort '{place}' nicht gefunden."
            lat, lon, name = geo
            r = client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lon, "current_weather": True,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
            })
            r.raise_for_status()
            d = r.json()
    except Exception as exc:  # noqa: BLE001
        return f"Wetterabruf fehlgeschlagen: {exc}"
    cur = d.get("current_weather", {})
    daily = d.get("daily", {})
    cond = _WMO.get(cur.get("weathercode"), "wechselhaft")
    tmax = (daily.get("temperature_2m_max") or [None])[0]
    tmin = (daily.get("temperature_2m_min") or [None])[0]
    rain = (daily.get("precipitation_probability_max") or [None])[0]
    parts = [f"In {name} ist es gerade {cur.get('temperature', '?')} Grad, {cond}"]
    if tmax is not None and tmin is not None:
        parts.append(f"heute {round(tmin)} bis {round(tmax)} Grad")
    if rain is not None:
        parts.append(f"Regenwahrscheinlichkeit {rain} Prozent")
    return ", ".join(parts) + "."
