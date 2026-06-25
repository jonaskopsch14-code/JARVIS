"""
JARVIS V6 — Mailbox hygiene integration.

Implements the INTEGRATION POINT for MailboxHygieneTask:

  * SpamClassifier  — a transparent, dependency-free heuristic that scores a
                      message as 'spam', 'lead' (qualified business enquiry) or
                      'keep'. Pure logic, fully unit-testable offline.
  * run_hygiene()   — connects to the IMAP account (via imap-tools), classifies
                      the inbox, persists qualified leads to a dashboard file,
                      and — ONLY when dry_run is False — moves spam to the Trash
                      folder. It never hard-deletes by default: spam is *moved*,
                      so a misfire is always recoverable.

Safety posture: in dry_run nothing on the server is touched. Even live, the
default action is "move to Trash", not permanent deletion.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Heuristic signal lists (German + English; Fashion Aura is a German store with
# international suppliers). Tunable — these are starting points, not gospel.
# ---------------------------------------------------------------------------
SPAM_PHRASES = [
    "viagra", "cialis", "lottery", "you have won", "sie haben gewonnen",
    "gewinnspiel", "verify your account", "konto bestätigen", "account suspended",
    "konto gesperrt", "click here", "hier klicken", "free money", "kostenlos geld",
    "bitcoin", "crypto investment", "krypto investment", "nigerian prince",
    "wire transfer", "western union", "act now", "jetzt handeln", "limited offer",
    "risk free", "risikofrei", "weight loss", "abnehmen garantiert",
    "dear customer", "sehr geehrter kunde,", "unsubscribe to stop",
    "increase your", "seo backlinks", "rank #1", "guaranteed traffic",
]
SPAM_SENDER_HINTS = [".ru", ".top", ".xyz", "no-reply@", "noreply@", "info@mailer"]

LEAD_PHRASES = [
    "anfrage", "angebot", "kooperation", "zusammenarbeit", "partnership",
    "collaboration", "großhandel", "wholesale", "bulk order", "bestellung",
    "großbestellung", "invoice", "rechnung", "kaufen", "purchase order",
    "interessiert an", "interested in", "distribution", "vertrieb",
    "kondition", "quotation", "request for quote", "rfq", "muster", "sample",
]


def _norm(text: Optional[str]) -> str:
    return (text or "").lower()


@dataclass
class MailMessage:
    """Minimal, server-agnostic view of an email — keeps the classifier
    testable without any IMAP connection."""

    uid: str
    subject: str
    from_: str
    text: str
    date: str = ""


@dataclass
class Classification:
    label: str            # 'spam' | 'lead' | 'keep'
    spam_score: int
    lead_score: int
    reasons: List[str] = field(default_factory=list)


class SpamClassifier:
    """Transparent heuristic classifier. Conservative by design: a message is
    only 'spam' when it clearly out-scores its lead signal, so a genuine (if
    salesy) business enquiry is never silently trashed."""

    def __init__(self, spam_threshold: int = 2, lead_threshold: int = 1):
        self.spam_threshold = spam_threshold
        self.lead_threshold = lead_threshold

    def classify(self, msg: MailMessage) -> Classification:
        subject = _norm(msg.subject)
        body = _norm(msg.text)
        sender = _norm(msg.from_)
        haystack = f"{subject}\n{body}"
        reasons: List[str] = []

        spam = 0
        for phrase in SPAM_PHRASES:
            if phrase in haystack:
                spam += 1
                reasons.append(f"spam-phrase:{phrase}")
        for hint in SPAM_SENDER_HINTS:
            if hint in sender:
                spam += 1
                reasons.append(f"sender:{hint}")
        # Shouty subject / excessive punctuation are weak spam signals.
        if re.search(r"[A-Z]{6,}", msg.subject or ""):
            spam += 1
            reasons.append("subject:allcaps")
        if (msg.subject or "").count("!") >= 3:
            spam += 1
            reasons.append("subject:exclaim")

        lead = 0
        for phrase in LEAD_PHRASES:
            if phrase in haystack:
                lead += 1
                reasons.append(f"lead-phrase:{phrase}")

        if spam >= self.spam_threshold and spam > lead:
            label = "spam"
        elif lead >= self.lead_threshold:
            label = "lead"
        else:
            label = "keep"
        return Classification(label=label, spam_score=spam, lead_score=lead, reasons=reasons)


@dataclass
class HygieneReport:
    spam: int = 0
    leads: int = 0
    kept: int = 0
    scanned: int = 0
    dry_run: bool = True
    lead_items: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    def as_metrics(self) -> Dict[str, int]:
        return {"spam": self.spam, "leads": self.leads,
                "kept": self.kept, "scanned": self.scanned}


def classify_messages(messages: List[MailMessage],
                      classifier: Optional[SpamClassifier] = None) -> HygieneReport:
    """Classify an in-memory batch — the network-free core, used by tests and
    by run_hygiene() once messages are fetched."""
    classifier = classifier or SpamClassifier()
    report = HygieneReport()
    for msg in messages:
        report.scanned += 1
        result = classifier.classify(msg)
        if result.label == "spam":
            report.spam += 1
        elif result.label == "lead":
            report.leads += 1
            report.lead_items.append({
                "uid": msg.uid, "from": msg.from_, "subject": msg.subject,
                "date": msg.date, "lead_score": result.lead_score,
            })
        else:
            report.kept += 1
    return report


def _persist_leads(leads: List[dict], leads_file: Path) -> None:
    """Write qualified leads to the dashboard file so they 'warten im Dashboard
    auf deine Freigabe'."""
    try:
        leads_file.parent.mkdir(parents=True, exist_ok=True)
        leads_file.write_text(json.dumps(leads, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    except OSError:
        pass  # best-effort; classification result still returned


def run_hygiene(
    *,
    host: str,
    user: str,
    password: str,
    port: int = 993,
    inbox: str = "INBOX",
    trash_folder: str = "Trash",
    leads_file: Optional[Path] = None,
    dry_run: bool = True,
    limit: Optional[int] = None,
    classifier: Optional[SpamClassifier] = None,
    cancel=None,
) -> HygieneReport:
    """Connect over IMAP, classify the inbox, persist leads, and (only when
    not dry_run) move spam to Trash.

    Requires the optional 'mail' extra: pip install -e ".[mail]"
    """
    try:
        from imap_tools import AND, MailBox  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return HygieneReport(dry_run=dry_run,
                             error=f"imap-tools nicht installiert ({exc}); pip install -e '.[mail]'")

    classifier = classifier or SpamClassifier()
    report = HygieneReport(dry_run=dry_run)
    spam_uids: List[str] = []
    try:
        with MailBox(host, port=port).login(user, password, initial_folder=inbox) as mb:
            fetched = 0
            for letter in mb.fetch(AND(all=True), reverse=True, mark_seen=False):
                if cancel is not None and cancel.is_set():
                    break
                if limit is not None and fetched >= limit:
                    break
                fetched += 1
                msg = MailMessage(
                    uid=str(letter.uid), subject=letter.subject or "",
                    from_=letter.from_ or "", text=letter.text or letter.html or "",
                    date=str(getattr(letter, "date", "")),
                )
                report.scanned += 1
                result = classifier.classify(msg)
                if result.label == "spam":
                    report.spam += 1
                    spam_uids.append(msg.uid)
                elif result.label == "lead":
                    report.leads += 1
                    report.lead_items.append({
                        "uid": msg.uid, "from": msg.from_, "subject": msg.subject,
                        "date": msg.date, "lead_score": result.lead_score,
                    })
                else:
                    report.kept += 1

            # Apply actions only in live mode. Move (not delete) → recoverable.
            if not dry_run and spam_uids:
                mb.move(spam_uids, trash_folder)
    except Exception as exc:  # noqa: BLE001
        report.error = str(exc)
        return report

    if leads_file is not None and report.lead_items:
        _persist_leads(report.lead_items, Path(leads_file))
    return report
