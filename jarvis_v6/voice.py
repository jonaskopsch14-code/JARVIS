"""
JARVIS V6 — Voice / conversation module ("Telefon-Modus").

A dependency-free German dialogue engine so you can *talk* to JARVIS like a
phone call: you speak, JARVIS understands the intent, answers from live system
state, and the browser speaks the answer back. The speech-to-text and
text-to-speech happen in the browser via the Web Speech API (see the
"Telefon-Modus" block in ``webapp.py``); this module is the brain in the
middle — it turns a recognised utterance into a spoken reply.

Design goals (same ethos as the rest of JARVIS V6):
  * **Standard library only.** No cloud, no API key — it always boots.
  * **Live answers.** It reads the real supervisor state and dashboard counts
    through small injected callables, so it never invents numbers.
  * **Fully testable offline.** ``VoiceBrain.reply()`` is a pure function of
    (utterance, injected providers); no network, no globals.

If you later wire in an LLM for free-form chat, pass an ``llm_fn`` and it is
used only as the fallback when no built-in intent matches — the deterministic,
no-key path stays the default.
"""

from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Text normalisation — make matching robust to umlauts, case and punctuation.
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    """Lowercase, fold umlauts (ä→ae, ß→ss …) and strip punctuation.

    Speech-recognition output is messy; matching on a folded form means
    "Lieferanten?", "lieferanten" and "LIEFERANTEN" all hit the same intent.
    """
    text = (text or "").strip().lower()
    replacements = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # Drop any remaining accents, then keep word characters + spaces.
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _has(text: str, *keywords: str) -> bool:
    """True if any keyword (already normalised) appears as a substring."""
    return any(k in text for k in keywords)


# German number words for small counts, so spoken replies sound natural.
_NUM_DE = ["null", "ein", "zwei", "drei", "vier", "fuenf", "sechs", "sieben",
           "acht", "neun", "zehn", "elf", "zwoelf"]


def _say_count(n: int, singular: str, plural: str) -> str:
    word = _NUM_DE[n] if 0 <= n < len(_NUM_DE) else str(n)
    if n == 1:
        return f"ein {singular}"
    return f"{word} {plural}"


# Human-readable German names for the supervisor states.
_STATE_DE = {
    "booting": "Ich initialisiere gerade.",
    "night_shift": "Die Nachtschicht läuft, ich arbeite die Aufgaben-Queue ab.",
    "sleeping": "Die Arbeit ist erledigt, ich warte auf die Weckzeit.",
    "waking": "Ich bin in der Weck-Sequenz.",
    "briefing": "Ich halte gerade das Executive-Briefing.",
    "idle": "Ich bin im Leerlauf und bereit für deine Anweisungen.",
    "stopped": "Das Protokoll ist gestoppt.",
}


# ---------------------------------------------------------------------------
# Reply container.
# ---------------------------------------------------------------------------
@dataclass
class VoiceReply:
    """One turn of the conversation."""

    text: str                       # what JARVIS says back (spoken by the browser)
    intent: str = "unknown"         # which intent fired (handy for tests/logs)
    end: bool = False               # True => caller should hang up (Telefon-Modus off)
    action: Optional[str] = None    # side-effect hint for the UI, e.g. "started"

    def as_dict(self) -> Dict[str, object]:
        return {"reply": self.text, "intent": self.intent,
                "end": self.end, "action": self.action}


# ---------------------------------------------------------------------------
# The dialogue engine.
# ---------------------------------------------------------------------------
@dataclass
class VoiceBrain:
    """Turn a recognised German utterance into a spoken reply.

    Providers are injected so the brain stays testable and decoupled from the
    web layer:

      status_fn    () -> dict   live status (state, running, briefing, counts,
                                wake_hour, wake_minute, dry_run)
      start_fn     () -> bool   start the night shift, returns True if it began
      preflight_fn () -> dict   {"rows": [{capability,status,detail}, ...]}
      llm_fn       (str) -> str optional free-form fallback (no key by default)
    """

    status_fn: Callable[[], dict]
    start_fn: Optional[Callable[[], bool]] = None
    preflight_fn: Optional[Callable[[], dict]] = None
    llm_fn: Optional[Callable[[str], str]] = None
    name: str = "JARVIS"
    user: str = "Jonas"
    _now: Callable[[], _dt.datetime] = field(default=_dt.datetime.now, repr=False)

    # -- public API ---------------------------------------------------------
    def greeting(self) -> str:
        """Opening line when the user picks up the phone."""
        return (f"Guten Tag, {self.user}. Hier ist {self.name}. "
                f"Ich höre — wie kann ich helfen?")

    def reply(self, utterance: str) -> VoiceReply:
        """Map an utterance to a reply. Order matters: the most specific and
        the 'hang up' intents are checked before the broad ones."""
        text = normalize(utterance)
        if not text:
            return VoiceReply("Ich habe nichts verstanden. Sag es bitte noch einmal.",
                              intent="empty")

        # Hang up first — must win over everything else.
        if _has(text, "auflegen", "aufgelegt", "tschuess", "wiederhoeren",
                "auf wiedersehen", "beenden", "ende", "gespraech beenden",
                "leg auf", "stopp telefon", "schluss"):
            return VoiceReply(f"Auf Wiederhören, {self.user}.",
                              intent="goodbye", end=True)

        # Start the night shift (an explicit command verb + the subject).
        if (_has(text, "starte", "start", "leg los", "loslegen", "beginne", "fang an")
                and _has(text, "nachtschicht", "protokoll", "schicht", "los")):
            return self._do_start()
        if _has(text, "nachtschicht starten", "protokoll starten",
                "starte das protokoll", "starte die nachtschicht"):
            return self._do_start()

        if _has(text, "preflight", "systemcheck", "system check", "selbsttest",
                "bist du bereit", "alles bereit", "check mal"):
            return self._do_preflight()

        if _has(text, "briefing", "zusammenfassung", "bericht", "fasse zusammen",
                "was ist passiert", "ergebnis"):
            return self._do_briefing()

        if _has(text, "dry run", "dryrun", "sicherheitsmodus", "sicher", "live modus",
                "echt scharf", "scharf"):
            return self._do_safety()

        if _has(text, "weckzeit", "weck", "wann weckst", "wann ist 16",
                "aufwachen", "wake"):
            return self._do_wake()

        # Dashboard numbers — accept either the umbrella word or a section.
        if _has(text, "dashboard", "zahlen", "wie viele", "wieviele", "leads",
                "lead", "winner", "winning", "gewinner", "lieferant", "lieferanten",
                "entwuerfe", "entwurf", "drafts"):
            return self._do_counts(text)

        if _has(text, "wie spaet", "uhrzeit", "wie viel uhr", "wieviel uhr",
                "welche zeit", "datum", "welcher tag"):
            return self._do_clock()

        if _has(text, "status", "wie geht", "was machst du", "laeuft", "zustand",
                "alles ok", "alles in ordnung", "wie steht"):
            return self._do_status()

        if _has(text, "was kannst du", "hilfe", "kommandos", "befehle",
                "moeglichkeiten", "optionen", "was geht"):
            return self._do_help()

        if _has(text, "danke", "vielen dank", "super", "perfekt", "klasse"):
            return VoiceReply("Gern geschehen. Sonst noch etwas?", intent="thanks")

        if _has(text, "hallo", "hi", "hey", "guten tag", "guten morgen",
                "guten abend", "moin", "jarvis"):
            return VoiceReply(f"Hallo {self.user}. Ich bin bereit. Frag mich nach "
                              f"Status, Briefing oder den Zahlen, oder sag "
                              f"'starte die Nachtschicht'.", intent="greeting")

        # No built-in intent matched.
        if self.llm_fn is not None:
            try:
                answer = self.llm_fn(utterance)
                if answer:
                    return VoiceReply(answer, intent="llm")
            except Exception:  # noqa: BLE001 - fallback must never crash the call
                pass
        return VoiceReply(
            "Das habe ich nicht ganz verstanden. Du kannst mich nach dem Status, "
            "dem Briefing, der Weckzeit oder den Zahlen fragen — oder sagen "
            "'starte die Nachtschicht'.",
            intent="fallback")

    # -- intent handlers ----------------------------------------------------
    def _status(self) -> dict:
        try:
            return self.status_fn() or {}
        except Exception:  # noqa: BLE001 - never let a provider crash the reply
            return {}

    def _do_status(self) -> VoiceReply:
        s = self._status()
        state = s.get("state", "idle")
        line = _STATE_DE.get(state, f"Aktueller Zustand: {state}.")
        mode = ("im Sicherheitsmodus, also Dry-Run"
                if s.get("dry_run", True) else "im Live-Modus")
        return VoiceReply(f"{line} Das System ist {mode}.", intent="status")

    def _do_counts(self, text: str) -> VoiceReply:
        c = (self._status().get("counts") or {})
        leads = int(c.get("leads", 0))
        winners = int(c.get("winners", 0))
        suppliers = int(c.get("suppliers", 0))
        drafts = int(c.get("drafts", 0))

        # If a single section was asked for, answer just that — feels natural.
        if _has(text, "lead") and not _has(text, "dashboard", "zahlen"):
            return VoiceReply(f"Es liegen {_say_count(leads, 'Lead', 'Leads')} vor.",
                              intent="counts_leads")
        if _has(text, "winner", "winning", "gewinner"):
            return VoiceReply(
                f"Ich habe {_say_count(winners, 'Winning Product', 'Winning Products')} "
                f"identifiziert.", intent="counts_winners")
        if _has(text, "lieferant"):
            return VoiceReply(
                f"Es sind {_say_count(suppliers, 'Lieferant', 'Lieferanten')} erfasst.",
                intent="counts_suppliers")
        if _has(text, "entwurf", "entwuerfe", "draft"):
            return VoiceReply(
                f"Es gibt {_say_count(drafts, 'Store-Entwurf', 'Store-Entwürfe')}.",
                intent="counts_drafts")

        return VoiceReply(
            f"Aktueller Stand: {_say_count(leads, 'Lead', 'Leads')}, "
            f"{_say_count(winners, 'Winning Product', 'Winning Products')}, "
            f"{_say_count(suppliers, 'Lieferant', 'Lieferanten')} und "
            f"{_say_count(drafts, 'Store-Entwurf', 'Store-Entwürfe')}.",
            intent="counts")

    def _do_briefing(self) -> VoiceReply:
        briefing = (self._status().get("briefing") or "").strip()
        if briefing:
            return VoiceReply(briefing, intent="briefing")
        return VoiceReply(
            "Es liegt noch kein Briefing vor. Sobald die Nachtschicht durch ist "
            "und die Weckzeit erreicht wurde, fasse ich alles für dich zusammen.",
            intent="briefing_empty")

    def _do_start(self) -> VoiceReply:
        if self.start_fn is None:
            return VoiceReply(
                "Ich kann die Nachtschicht von hier aus nicht starten — diese "
                "Sitzung hat keinen Supervisor angebunden.", intent="start_unavailable")
        try:
            started = bool(self.start_fn())
        except Exception:  # noqa: BLE001
            return VoiceReply("Der Start ist fehlgeschlagen. Bitte prüfe das System.",
                              intent="start_error")
        if started:
            return VoiceReply(
                "Verstanden. Ich starte das Nachtschicht-Protokoll und arbeite die "
                "Aufgaben jetzt ab.", intent="start", action="started")
        return VoiceReply("Das Protokoll läuft bereits.", intent="start_already")

    def _do_preflight(self) -> VoiceReply:
        if self.preflight_fn is None:
            return VoiceReply("Ein Preflight ist hier nicht verfügbar.",
                              intent="preflight_unavailable")
        try:
            rows = (self.preflight_fn() or {}).get("rows", [])
        except Exception:  # noqa: BLE001
            rows = []
        if not rows:
            return VoiceReply("Ich konnte den Preflight nicht ausführen.",
                              intent="preflight_empty")
        fails = [r for r in rows if str(r.get("status")).upper() == "FAIL"]
        ready = [r for r in rows if str(r.get("status")).upper() in ("READY", "OK", "LIVE")]
        if not fails:
            return VoiceReply(
                f"Preflight bestanden. {_say_count(len(ready), 'Fähigkeit ist', 'Fähigkeiten sind')} "
                f"einsatzbereit, keine Fehler.", intent="preflight_ok")
        names = ", ".join(str(r.get("capability", "?")) for r in fails[:4])
        return VoiceReply(
            f"Achtung: {_say_count(len(fails), 'Fähigkeit meldet', 'Fähigkeiten melden')} "
            f"ein Problem — {names}. Den Rest habe ich startklar.",
            intent="preflight_fail")

    def _do_safety(self) -> VoiceReply:
        dry = self._status().get("dry_run", True)
        if dry:
            return VoiceReply(
                "Ich bin im Sicherheitsmodus, also Dry-Run. Kein Task verändert "
                "echte Systeme — alles wird nur als Entwurf gespeichert.",
                intent="safety")
        return VoiceReply(
            "Achtung: der Live-Modus ist aktiv. Tasks dürfen echte Systeme "
            "verändern.", intent="safety_live")

    def _do_wake(self) -> VoiceReply:
        s = self._status()
        h = int(s.get("wake_hour", 16))
        m = int(s.get("wake_minute", 0))
        return VoiceReply(
            f"Die Weckzeit ist auf {h:02d}:{m:02d} Uhr gesetzt. Dann hellt der "
            f"Reaktor auf und ich liefere das Briefing.", intent="wake")

    def _do_clock(self) -> VoiceReply:
        now = self._now()
        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag",
                "Samstag", "Sonntag"]
        return VoiceReply(
            f"Es ist {now.hour:02d}:{now.minute:02d} Uhr, "
            f"{days[now.weekday()]}, der {now.day}.{now.month}.{now.year}.",
            intent="clock")

    def _do_help(self) -> VoiceReply:
        return VoiceReply(
            "Du kannst mich zum Beispiel fragen: Wie ist der Status? "
            "Gib mir das Briefing. Wie viele Leads gibt es? Wann ist die Weckzeit? "
            "Sind wir im Sicherheitsmodus? Mach einen Preflight. "
            "Oder sag: starte die Nachtschicht. Zum Auflegen sag einfach Tschüss.",
            intent="help")


# ---------------------------------------------------------------------------
# Convenience: build a brain wired to a running WebApp.
# ---------------------------------------------------------------------------
def brain_for_app(app, **kwargs) -> VoiceBrain:
    """Wire a VoiceBrain to a webapp.WebApp instance (duck-typed).

    Kept here (not in webapp.py) so the brain can be unit-tested with fakes and
    the web layer simply hands it the live providers.
    """
    return VoiceBrain(
        status_fn=app.status,
        start_fn=app.start,
        preflight_fn=app.preflight,
        **kwargs,
    )
