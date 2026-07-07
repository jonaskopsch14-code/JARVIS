"""Gedächtnis-Tools: Notizen schreiben, suchen, lesen (Obsidian-Vault)."""
from __future__ import annotations

from ..memory.obsidian import ObsidianVault, INBOX, WIKI
from ..memory.vector_index import VectorIndex
from ..security.permission_gateway import EffectCategory
from .base import Tool, ToolResult


def build_memory_tools(vault: ObsidianVault, index: VectorIndex | None = None) -> list[Tool]:
    def memory_write(text: str, title: str = "", topics: str = "", importance: int = 1) -> ToolResult:
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]
        note = vault.write_note(
            title or _first_line(text), text,
            folder=WIKI if topic_list else INBOX,
            topics=topic_list, importance=int(importance),
        )
        if index is not None:
            index.add(str(note.path), f"{note.title}\n{text}")
        return ToolResult(True, f"Notiz gespeichert: {note.path.name}", {"path": str(note.path)})

    def memory_search(query: str, limit: int = 5) -> ToolResult:
        notes = vault.search(query, limit=int(limit))
        if not notes:
            return ToolResult(True, "Keine passenden Notizen gefunden.")
        lines = [f"- {n.title}: {n.body.strip().splitlines()[0][:120]}" for n in notes if n.body.strip()]
        return ToolResult(True, "Gefundene Notizen:\n" + "\n".join(lines), {"count": len(notes)})

    def memory_read(title: str) -> ToolResult:
        note = vault.resolve_link(title)
        if note is None:
            return ToolResult(False, f"Keine Notiz mit Titel '{title}' gefunden.")
        return ToolResult(True, note.body.strip()[:1500], {"path": str(note.path)})

    return [
        Tool(
            name="memory_write", description="Speichert eine Notiz/Erinnerung im Gedächtnis (Obsidian-Vault).",
            effect=EffectCategory.SUGGEST,
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Inhalt der Notiz."},
                    "title": {"type": "string", "description": "Optionaler Titel."},
                    "topics": {"type": "string", "description": "Kommagetrennte Themen/Tags."},
                    "importance": {"type": "integer", "description": "1 (normal) bis 5 (wichtig)."},
                },
                "required": ["text"],
            },
            run=memory_write, intent_template="Notiz speichern: {text}",
        ),
        Tool(
            name="memory_search", description="Durchsucht das Gedächtnis nach relevanten Notizen.",
            effect=EffectCategory.READ,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Suchbegriff."},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            run=memory_search, intent_template="Gedächtnis durchsuchen: {query}",
        ),
        Tool(
            name="memory_read", description="Liest eine bestimmte Notiz per Titel/Wikilink.",
            effect=EffectCategory.READ,
            parameters={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
            run=memory_read, intent_template="Notiz lesen: {title}",
        ),
    ]


def _first_line(text: str) -> str:
    return text.strip().splitlines()[0][:80] if text.strip() else "Notiz"
