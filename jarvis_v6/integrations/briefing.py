"""
JARVIS V6 — Briefing skill.

The on-demand ("Jarvis, gib mir ein Briefing") and schedulable spoken briefing
that made the video click: JARVIS gathers a batch of items and *tells* you about
them in his own voice, not as a dry list.

    briefing_compile(sources, max_items=10, ...) -> str

Two sources, **both first-class from the start, equal weight** (Jonas' rule —
neither is bolted on later):

  * ``news``  — web/news search for configurable topics (economy, tech, the
    Wittenberg region, …). The topic list lives in config, not in code.
  * ``inbox`` — your own mail. Reuses the IMAP access JARVIS already has
    (``JARVIS_IMAP_*``); a Gmail app-password works here too.

This is a pure **read** action, so it never needs a confirmation.

Testability: the network parts (news fetch, inbox fetch) are injected callables.
The composition — merging both sources with equal weight, capping at
``max_items`` and phrasing it in the Jarvis tone — is a pure function tested
fully offline. The default fetchers use only the standard library (news via the
Google-News RSS endpoint) or the already-declared ``mail`` extra (inbox).
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

LOG = logging.getLogger("jarvis_v6.briefing")


# ---------------------------------------------------------------------------
# Item + config.
# ---------------------------------------------------------------------------
@dataclass
class BriefItem:
    """One thing worth mentioning in the briefing."""

    source: str                 # "news" | "inbox"
    title: str
    detail: str = ""            # source (news outlet) or sender (inbox)
    when: str = ""              # optional human date/time

    def spoken(self) -> str:
        """Render this item as one natural spoken clause."""
        who = self.detail.strip()
        quoted = "„" + self.title.strip() + "“"  # „…" German quotes
        if self.source == "inbox":
            return f"eine Mail von {who}: {quoted}" if who else f"eine Mail: {quoted}"
        # news
        return f"{quoted} ({who})" if who else quoted


@dataclass
class BriefingConfig:
    """Where the briefing gets its topics and how big it is."""

    topics: List[str] = field(default_factory=list)
    max_items: int = 10
    user: str = "Jonas"

    @classmethod
    def load(cls, *, env: Optional[dict] = None) -> "BriefingConfig":
        """Build config from a JSON file (``JARVIS_BRIEFING_CONFIG``) and/or
        env (``JARVIS_BRIEFING_TOPICS`` — comma-separated). Env topics win when
        both are present. Falls back to a sensible default topic set."""
        env = env if env is not None else os.environ
        topics: List[str] = []
        max_items = 10

        cfg_path = env.get("JARVIS_BRIEFING_CONFIG", "")
        if cfg_path:
            try:
                data = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
                topics = [str(t) for t in data.get("topics", []) if str(t).strip()]
                max_items = int(data.get("max_items", max_items))
            except (OSError, ValueError, TypeError):
                LOG.warning("Briefing-Config %s nicht lesbar — nutze Defaults.", cfg_path)

        env_topics = env.get("JARVIS_BRIEFING_TOPICS", "")
        if env_topics.strip():
            topics = [t.strip() for t in env_topics.split(",") if t.strip()]

        if not topics:
            topics = ["Wirtschaft", "Technologie", "Wittenberg"]
        return cls(topics=topics, max_items=max_items,
                   user=env.get("JARVIS_USER", "Jonas"))


# Fetcher signatures: news gets (topics, limit); inbox gets (limit).
NewsFetcher = Callable[[List[str], int], List[BriefItem]]
InboxFetcher = Callable[[int], List[BriefItem]]


# ---------------------------------------------------------------------------
# Composition — the pure, offline-tested core.
# ---------------------------------------------------------------------------
def _interleave(news: List[BriefItem], inbox: List[BriefItem],
                max_items: int) -> List[BriefItem]:
    """Merge both sources with equal weight: alternate one from each so neither
    dominates, then cap at ``max_items``."""
    merged: List[BriefItem] = []
    i = 0
    while (news[i:] or inbox[i:]) and len(merged) < max_items:
        if i < len(news):
            merged.append(news[i])
        if len(merged) < max_items and i < len(inbox):
            merged.append(inbox[i])
        i += 1
    return merged


def _greeting(now: _dt.datetime, user: str) -> str:
    h = now.hour
    if h < 11:
        return f"Guten Morgen, {user}."
    if h < 18:
        return f"Guten Tag, {user}."
    return f"Guten Abend, {user}."


def compose_briefing(news: List[BriefItem], inbox: List[BriefItem], *,
                     max_items: int = 10, user: str = "Jonas",
                     now: Optional[_dt.datetime] = None) -> str:
    """Turn gathered items into a spoken-style German briefing in Jarvis' tone.

    Pure function — no network, no clock unless you pass one. Addresses Jonas
    (never "Master"), leads with a short line, then narrates the items grouped
    by source in flowing sentences, and closes with a light note."""
    now = now or _dt.datetime.now()
    items = _interleave(news, inbox, max_items)

    if not items:
        return (f"{_greeting(now, user)} Ich habe nichts Neues für Sie — weder in "
                f"den Nachrichten noch im Postfach ist etwas hängen geblieben. "
                f"Geben Sie mir gern eine Aufgabe.")

    news_items = [it for it in items if it.source == "news"]
    inbox_items = [it for it in items if it.source == "inbox"]

    parts: List[str] = [f"{_greeting(now, user)} Hier Ihr Briefing."]

    if news_items:
        if len(news_items) == 1:
            parts.append(f"Aus den Nachrichten: {news_items[0].spoken()}.")
        else:
            head = "; ".join(it.spoken() for it in news_items[:-1])
            parts.append(f"Aus den Nachrichten: {head}; und {news_items[-1].spoken()}.")

    if inbox_items:
        n = len(inbox_items)
        lead = "Im Postfach liegt" if n == 1 else f"Im Postfach liegen {n} Meldungen, darunter"
        listing = "; ".join(it.spoken() for it in inbox_items)
        parts.append(f"{lead} {listing}.")

    parts.append("Sagen Sie Bescheid, wenn ich etwas davon übernehmen soll.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Default fetchers — standard-library news, IMAP inbox.
# ---------------------------------------------------------------------------
def default_news_fetcher(topics: List[str], limit: int) -> List[BriefItem]:
    """Fetch recent headlines per topic via the Google-News RSS endpoint.

    Standard library only (urllib + xml). INTEGRATION POINT: swap this for a
    paid news API by passing your own ``news_fetcher`` to ``briefing_compile``.
    Returns [] on any network/parse error — the briefing degrades gracefully.
    """
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    items: List[BriefItem] = []
    per_topic = max(1, limit // max(1, len(topics)))
    for topic in topics:
        if len(items) >= limit:
            break
        q = urllib.parse.quote(topic)
        url = (f"https://news.google.com/rss/search?q={q}"
               f"&hl=de&gl=DE&ceid=DE:de")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-V6/6.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                root = ET.fromstring(resp.read())
        except Exception as exc:  # noqa: BLE001 - offline / blocked / bad XML
            LOG.info("news fetch für '%s' fehlgeschlagen: %s", topic, exc)
            continue
        count = 0
        for item in root.iter("item"):
            if count >= per_topic or len(items) >= limit:
                break
            title = (item.findtext("title") or "").strip()
            if not title:
                continue
            source = ""
            src_el = item.find("source")
            if src_el is not None and (src_el.text or "").strip():
                source = src_el.text.strip()
            items.append(BriefItem(source="news", title=title, detail=source,
                                   when=(item.findtext("pubDate") or "").strip()))
            count += 1
    return items[:limit]


def default_inbox_fetcher(limit: int, *, host: str = "", user: str = "",
                          password: str = "", port: int = 993,
                          inbox: str = "INBOX") -> List[BriefItem]:
    """Fetch the most recent inbox headers via IMAP (reuses JARVIS_IMAP_*).

    Requires the ``mail`` extra (imap-tools). Read-only: it only reads headers,
    it never marks, moves or deletes anything. Returns [] when unconfigured or
    on error, so the briefing still runs from the news source alone.
    """
    if not host:
        return []
    try:
        from imap_tools import AND, MailBox  # type: ignore
    except Exception as exc:  # noqa: BLE001
        LOG.info("inbox fetch übersprungen: imap-tools fehlt (%s)", exc)
        return []
    items: List[BriefItem] = []
    try:
        with MailBox(host, port=port).login(user, password, initial_folder=inbox) as mb:
            for letter in mb.fetch(AND(all=True), reverse=True, mark_seen=False,
                                   headers_only=True, bulk=True):
                if len(items) >= limit:
                    break
                items.append(BriefItem(
                    source="inbox",
                    title=(letter.subject or "(kein Betreff)").strip(),
                    detail=(letter.from_ or "").strip(),
                    when=str(getattr(letter, "date", "")),
                ))
    except Exception as exc:  # noqa: BLE001 - IMAP down / bad creds
        LOG.warning("inbox fetch fehlgeschlagen: %s", exc)
        return []
    return items


# ---------------------------------------------------------------------------
# The public tool.
# ---------------------------------------------------------------------------
def briefing_compile(sources: Optional[List[str]] = None, max_items: int = 10, *,
                     config: Optional[BriefingConfig] = None,
                     news_fetcher: Optional[NewsFetcher] = None,
                     inbox_fetcher: Optional[InboxFetcher] = None,
                     now: Optional[_dt.datetime] = None) -> str:
    """Gather from ``sources`` and return a spoken-style German briefing.

    Parameters
    ----------
    sources:
        Which sources to include, e.g. ``["news", "inbox"]`` (the default —
        both, equal weight).
    max_items:
        Hard cap on how many items are spoken.
    config:
        A :class:`BriefingConfig`; loaded from env/file when omitted.
    news_fetcher / inbox_fetcher:
        Injected for tests or to plug in a different provider. Default fetchers
        use Google-News RSS (stdlib) and IMAP (``JARVIS_IMAP_*``).
    """
    sources = sources or ["news", "inbox"]
    config = config or BriefingConfig.load()
    cap = max_items or config.max_items

    news_items: List[BriefItem] = []
    inbox_items: List[BriefItem] = []

    if "news" in sources:
        fetch = news_fetcher or default_news_fetcher
        try:
            news_items = list(fetch(config.topics, cap))
        except Exception as exc:  # noqa: BLE001
            LOG.warning("news source fehlgeschlagen: %s", exc)

    if "inbox" in sources:
        if inbox_fetcher is not None:
            fetch_inbox = inbox_fetcher
        else:
            def fetch_inbox(limit: int) -> List[BriefItem]:
                return default_inbox_fetcher(
                    limit,
                    host=os.getenv("JARVIS_IMAP_HOST", ""),
                    user=os.getenv("JARVIS_IMAP_USER", ""),
                    password=os.getenv("JARVIS_IMAP_PASSWORD", ""),
                    port=int(os.getenv("JARVIS_IMAP_PORT", "993")),
                    inbox=os.getenv("JARVIS_IMAP_INBOX", "INBOX"),
                )
        try:
            inbox_items = list(fetch_inbox(cap))
        except Exception as exc:  # noqa: BLE001
            LOG.warning("inbox source fehlgeschlagen: %s", exc)

    return compose_briefing(news_items, inbox_items, max_items=cap,
                            user=config.user, now=now)
