"""Langzeit-Gedächtnis über Sitzungen hinweg (Phase 2).

Speichert in einer lokalen SQLite-Datei:
  - facts  : ausdrücklich gemerkte Vorlieben/Fakten (Schlüssel→Wert)
  - turns  : Gesprächsverlauf (für Zusammenfassungen)
  - topics : wiederkehrende Themen (grob gezählt)

`context_block()` liefert einen kompakten Text, den der Assistent in seinen
System-Prompt einspeist, damit Jarvis sich „erinnert". Reines stdlib-sqlite3,
vollständig offline testbar.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

_STOP = set("der die das und oder ich du er sie es wir ihr mir mich dir dich den dem "
            "ein eine einen einem eines ist bin bist sind war auf für mit von zu im in "
            "am an ob dass wie was wer wo wann warum bitte danke jarvis mal noch schon "
            "kannst kann soll sollst mach machen tu tun gib zeig".split())


class Memory:
    def __init__(self, db_path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS facts "
                         "(key TEXT PRIMARY KEY, value TEXT, updated TEXT)")
        self._db.execute("CREATE TABLE IF NOT EXISTS turns "
                         "(id INTEGER PRIMARY KEY, ts TEXT, user TEXT, assistant TEXT)")
        self._db.execute("CREATE TABLE IF NOT EXISTS topics "
                         "(topic TEXT PRIMARY KEY, last_seen TEXT, cnt INTEGER)")
        self._db.commit()

    # --- Fakten / Vorlieben ------------------------------------------------
    def remember(self, key: str, value: str) -> None:
        key = (key or "").strip().lower()
        if not key:
            return
        self._db.execute(
            "INSERT INTO facts(key,value,updated) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
            (key, value, datetime.now().isoformat(timespec="seconds")))
        self._db.commit()

    def recall(self, key: str) -> str:
        row = self._db.execute("SELECT value FROM facts WHERE key=?",
                               ((key or "").strip().lower(),)).fetchone()
        return row[0] if row else ""

    def forget(self, key: str) -> bool:
        cur = self._db.execute("DELETE FROM facts WHERE key=?",
                               ((key or "").strip().lower(),))
        self._db.commit()
        return cur.rowcount > 0

    def facts(self) -> Dict[str, str]:
        return {k: v for k, v in self._db.execute(
            "SELECT key,value FROM facts ORDER BY updated DESC").fetchall()}

    # --- Verlauf / Themen --------------------------------------------------
    def observe(self, user_text: str, assistant_text: str) -> None:
        self._db.execute("INSERT INTO turns(ts,user,assistant) VALUES(?,?,?)",
                         (datetime.now().isoformat(timespec="seconds"),
                          user_text, assistant_text))
        for word in self._keywords(user_text):
            self._db.execute(
                "INSERT INTO topics(topic,last_seen,cnt) VALUES(?,?,1) "
                "ON CONFLICT(topic) DO UPDATE SET last_seen=excluded.last_seen, cnt=cnt+1",
                (word, datetime.now().isoformat(timespec="seconds")))
        self._db.commit()

    @staticmethod
    def _keywords(text: str) -> List[str]:
        words = re.findall(r"[A-Za-zÄÖÜäöüß]{4,}", (text or "").lower())
        return [w for w in words if w not in _STOP][:8]

    def top_topics(self, n: int = 5) -> List[str]:
        return [t for (t,) in self._db.execute(
            "SELECT topic FROM topics ORDER BY cnt DESC, last_seen DESC LIMIT ?",
            (n,)).fetchall()]

    def recent_turns(self, n: int = 3) -> List[tuple]:
        rows = self._db.execute(
            "SELECT user,assistant FROM turns ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        return list(reversed(rows))

    # --- Kontext für den System-Prompt -------------------------------------
    def context_block(self) -> str:
        parts = []
        facts = self.facts()
        if facts:
            parts.append("Bekannte Fakten über den Nutzer: "
                         + "; ".join(f"{k} = {v}" for k, v in list(facts.items())[:15]) + ".")
        topics = self.top_topics()
        if topics:
            parts.append("Häufige Themen zuletzt: " + ", ".join(topics) + ".")
        return "\n".join(parts)

    def close(self) -> None:
        try:
            self._db.close()
        except Exception:  # noqa: BLE001
            pass
