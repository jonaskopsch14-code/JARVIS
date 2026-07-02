"""
JARVIS V6 — Validator / QA-Agent.

The quality gate from the multi-agent design (ARCHITECTURE.md §3.7). It reviews
each agent's output against explicit rules and returns a structured verdict:

    OK      — output passes
    REFINE  — fixable problems; send back to the producing agent with critique
    FAIL    — the task did not succeed at all

The content validators (validate_seo, validate_campaign) are pure and fully
unit-testable offline. `Validator.review()` turns a TaskResult (plus any
artifacts the task attached) into a Verdict the orchestrator's refine loop uses.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List, Optional

# Verdict statuses.
OK, REFINE, FAIL = "OK", "REFINE", "FAIL"

# Below this score a result with fixable issues is sent back to refine.
REFINE_THRESHOLD = 80


@dataclass
class Issue:
    field: str
    problem: str
    suggestion: str
    severity: str = "error"  # "error" (blocks) | "warn" (note only)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verdict:
    status: str
    score: int
    issues: List[Issue] = field(default_factory=list)

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    def as_dict(self) -> dict:
        return {"status": self.status, "score": self.score,
                "issues": [i.as_dict() for i in self.issues]}


# ---------------------------------------------------------------------------
# Pure content validators.
# ---------------------------------------------------------------------------
def validate_seo(seo: dict) -> List[Issue]:
    issues: List[Issue] = []
    title = seo.get("seo_title", "") or ""
    meta = seo.get("meta_description", "") or ""
    handle = seo.get("handle", "") or ""
    tags = seo.get("tags", []) or []

    if not title:
        issues.append(Issue("seo_title", "Leerer SEO-Titel", "Titel generieren", "error"))
    elif len(title) > 60:
        issues.append(Issue("seo_title", f"Titel zu lang ({len(title)}>60)",
                            "Auf 60 Zeichen kürzen", "error"))
    if not meta:
        issues.append(Issue("meta_description", "Leere Meta-Beschreibung",
                            "Beschreibung generieren", "error"))
    elif len(meta) > 160:
        issues.append(Issue("meta_description", f"Meta zu lang ({len(meta)}>160)",
                            "Auf 160 Zeichen kürzen", "error"))
    elif len(meta) < 50:
        issues.append(Issue("meta_description", f"Meta sehr kurz ({len(meta)}<50)",
                            "Mehr Nutzen/CTA ergänzen", "warn"))
    if not handle or any(c for c in handle if not (c.isalnum() or c == "-") or c.isupper()):
        issues.append(Issue("handle", "Ungültiger Slug",
                            "Nur Kleinbuchstaben, Ziffern, Bindestriche", "error"))
    if not tags:
        issues.append(Issue("tags", "Keine Tags", "Mind. 1 relevantes Tag", "warn"))
    return issues


def validate_campaign(campaign: dict) -> List[Issue]:
    issues: List[Issue] = []
    headlines = campaign.get("headlines", []) or []
    primary = campaign.get("primary_text", "") or ""
    budget = campaign.get("suggested_daily_budget_eur", 0) or 0
    status = campaign.get("status", "")

    if not headlines:
        issues.append(Issue("headlines", "Keine Headlines", "Mind. 1 Headline", "error"))
    for i, h in enumerate(headlines):
        if not h:
            issues.append(Issue(f"headlines[{i}]", "Leere Headline", "Text ergänzen", "error"))
        elif len(h) > 40:
            issues.append(Issue(f"headlines[{i}]", f"Headline zu lang ({len(h)}>40)",
                                "Auf 40 Zeichen kürzen", "error"))
    if not primary:
        issues.append(Issue("primary_text", "Leerer Anzeigentext", "Text ergänzen", "error"))
    if float(budget) <= 0:
        issues.append(Issue("suggested_daily_budget_eur", "Budget ≤ 0",
                            "Positives Tagesbudget setzen", "error"))
    if status != "DRAFT":
        issues.append(Issue("status", f"Status ist '{status}', nicht DRAFT",
                            "Kampagnen nie automatisch schalten — DRAFT erzwingen", "error"))
    return issues


# ---------------------------------------------------------------------------
# The QA-Agent.
# ---------------------------------------------------------------------------
class Validator:
    """Reviews a TaskResult (and its attached artifacts) into a Verdict."""

    def __init__(self, refine_threshold: int = REFINE_THRESHOLD):
        self.refine_threshold = refine_threshold

    def review(self, result) -> Verdict:
        # A task that outright failed cannot be refined into success here.
        if not getattr(result, "ok", False):
            return Verdict(FAIL, 0, [Issue("task", result.summary or "fehlgeschlagen",
                                           "Fehler beheben / erneut versuchen", "error")])

        issues: List[Issue] = []
        artifacts = getattr(result, "artifacts", {}) or {}

        # Store drafts: validate every SEO block + campaign.
        for draft in artifacts.get("drafts", []):
            issues += validate_seo(draft.get("seo", {}) or {})
            issues += validate_campaign(draft.get("campaign", {}) or {})

        # Plausibility: a configured task that scanned/produced nothing is a warn.
        metrics = getattr(result, "metrics", {}) or {}
        if result.name == "mailbox_hygiene" and "scanned" in metrics and metrics["scanned"] == 0 \
                and "übersprungen" not in (result.summary or ""):
            issues.append(Issue("scanned", "0 Mails trotz Konto",
                                "IMAP-Ordner/Filter prüfen", "warn"))

        # Score: each error -10, each warn -3 (floored at 0).
        penalty = 10 * sum(1 for i in issues if i.severity == "error") \
            + 3 * sum(1 for i in issues if i.severity == "warn")
        score = max(0, 100 - penalty)

        # Any blocking (error-severity) issue is fixable → send back to refine.
        # Warnings alone do not block; they ride along on an OK verdict.
        if any(i.severity == "error" for i in issues):
            return Verdict(REFINE, score, issues)
        return Verdict(OK, score, issues)
