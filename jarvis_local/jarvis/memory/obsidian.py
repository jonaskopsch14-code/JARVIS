"""Obsidian-Vault als Langzeitgedächtnis (Markdown = Wahrheit).

Muster aus dem Leitfaden (Abschnitt G): strukturierte Markdown-Notizen mit
Frontmatter und ``[[wikilinks]]``. Ordner-Semantik::

    00-inbox/  – schnelle Captures
    10-raw/    – immutable Quellen (Transkripte, E-Mail-Auszüge)
    20-wiki/   – synthetisierte Entity-/Konzept-Seiten
    90-system/ – Regeln, Index

Der Frontmatter-Parser ist ein bewusst kleiner YAML-Teil (Skalare + Inline-Listen),
damit keine externe Bibliothek nötig ist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

INBOX = "00-inbox"
RAW = "10-raw"
WIKI = "20-wiki"
SYSTEM = "90-system"
FOLDERS = (INBOX, RAW, WIKI, SYSTEM)

_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass
class Note:
    path: Path
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ""

    @property
    def title(self) -> str:
        return self.frontmatter.get("title") or self.path.stem

    def wikilinks(self) -> list[str]:
        return [m.strip() for m in _WIKILINK.findall(self.body)]


class ObsidianVault:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        for folder in FOLDERS:
            (self.root / folder).mkdir(parents=True, exist_ok=True)

    # ---- Schreiben ----
    def write_note(
        self,
        title: str,
        body: str,
        *,
        folder: str = INBOX,
        topics: list[str] | None = None,
        entities: list[str] | None = None,
        importance: int = 1,
        extra: dict[str, Any] | None = None,
    ) -> Note:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        fm: dict[str, Any] = {
            "title": title,
            "timestamp": now,
            "importance": int(importance),
            "topics": topics or [],
            "entities": entities or [],
        }
        if extra:
            fm.update(extra)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = self.root / folder / f"{stamp}-{_slug(title)}.md"
        path.write_text(_serialize(fm, body), encoding="utf-8")
        return Note(path=path, frontmatter=fm, body=body)

    def append_inbox(self, text: str) -> Note:
        return self.write_note(_first_line(text), text, folder=INBOX)

    # ---- Lesen ----
    def read_note(self, path: str | Path) -> Note:
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        fm, body = _parse(p.read_text(encoding="utf-8"))
        return Note(path=p, frontmatter=fm, body=body)

    def list_notes(self, folder: str | None = None) -> list[Note]:
        base = self.root / folder if folder else self.root
        notes: list[Note] = []
        for p in sorted(base.rglob("*.md")):
            try:
                fm, body = _parse(p.read_text(encoding="utf-8"))
                notes.append(Note(path=p, frontmatter=fm, body=body))
            except OSError:
                continue
        return notes

    # ---- Suche (Recency + einfache Relevanz) ----
    def search(self, query: str, *, limit: int = 5, folder: str | None = None) -> list[Note]:
        terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
        scored: list[tuple[float, Note]] = []
        for note in self.list_notes(folder):
            hay = (note.title + "\n" + note.body + "\n" + " ".join(_flatten(note.frontmatter))).lower()
            score = sum(hay.count(t) for t in terms)
            if score:
                score += float(note.frontmatter.get("importance", 1))
                scored.append((score, note))
        scored.sort(key=lambda s: (s[0], s[1].frontmatter.get("timestamp", "")), reverse=True)
        return [n for _, n in scored[:limit]]

    def resolve_link(self, name: str) -> Note | None:
        target = _slug(name)
        for note in self.list_notes():
            if _slug(note.title) == target or note.path.stem.endswith(target):
                return note
        return None


# ---------- Frontmatter (kleiner YAML-Teil) ----------
def _serialize(fm: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key, value in fm.items():
        lines.append(f"{key}: {_dump_value(value)}")
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip() + "\n")
    return "\n".join(lines)


def _dump_value(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


def _parse(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n")
    if parts[0].strip() != "---":
        return {}, text
    fm: dict[str, Any] = {}
    i = 1
    while i < len(parts) and parts[i].strip() != "---":
        line = parts[i]
        if ":" in line:
            key, _, raw = line.partition(":")
            fm[key.strip()] = _load_value(raw.strip())
        i += 1
    body = "\n".join(parts[i + 1:]).lstrip("\n") if i < len(parts) else ""
    return fm, body


def _load_value(raw: str) -> Any:
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [x.strip() for x in inner.split(",") if x.strip()] if inner else []
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw.strip('"').strip("'")


def _flatten(fm: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for v in fm.values():
        if isinstance(v, list):
            out.extend(str(x) for x in v)
        else:
            out.append(str(v))
    return out


def _slug(text: str) -> str:
    text = text.lower().strip()
    text = (text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60] or "notiz"


def _first_line(text: str) -> str:
    return text.strip().splitlines()[0][:80] if text.strip() else "Notiz"
