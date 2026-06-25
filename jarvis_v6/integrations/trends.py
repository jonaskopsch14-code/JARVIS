"""
JARVIS V6 — Market-trend analysis integration.

Implements the INTEGRATION POINT for MarketTrendTask.

  * score_record() / analyse_trends() / pick_winning_products()
        Pure, dependency-free scoring of product/keyword records. Each record
        is a dict with optional numeric signals:
            search_volume : int    monthly searches
            growth        : float  % change vs. previous period (can be negative)
            competition   : float  0..1, higher = harder
            margin        : float  0..1, contribution margin
        The score rewards demand + growth + margin and penalises competition.
        Fully testable offline.
  * load_feed()   reads a local JSON feed (JARVIS_TRENDS_FEED) so the task is
        runnable without any paid trends API. INTEGRATION POINT: swap load_feed
        for a Google Trends / ads-API client when you have one.

No external mutation happens here — it only reads and ranks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Scoring weights — tunable. Demand and growth drive winners; competition hurts.
WEIGHTS = {"demand": 0.35, "growth": 0.30, "margin": 0.25, "competition": -0.20}


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_record(record: dict) -> float:
    """Return a 0..100 trend score for one product/keyword record."""
    volume = float(record.get("search_volume", 0) or 0)
    growth = float(record.get("growth", 0) or 0)
    competition = _clamp01(float(record.get("competition", 0.5) or 0.5))
    margin = _clamp01(float(record.get("margin", 0.5) or 0.5))

    # Normalise demand on a log-ish scale so 10k+ searches saturate near 1.0.
    demand = _clamp01(volume / 10000.0)
    # Map growth (%) into 0..1, with +100% growth saturating at 1.0.
    growth_n = _clamp01((growth + 100.0) / 200.0)

    raw = (WEIGHTS["demand"] * demand
           + WEIGHTS["growth"] * growth_n
           + WEIGHTS["margin"] * margin
           + WEIGHTS["competition"] * competition)
    # WEIGHTS sum to 0.70 positive max, -0.20 min → normalise to 0..100.
    score = (raw + 0.20) / 0.90 * 100.0
    return round(_clamp01(score / 100.0) * 100.0, 1)


@dataclass
class TrendReport:
    analysed: int = 0
    winners: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    def as_metrics(self) -> Dict[str, int]:
        return {"trends_logged": self.analysed, "winning_products": len(self.winners)}


def analyse_trends(records: List[dict]) -> List[dict]:
    """Attach a 'score' to each record and return them sorted best-first."""
    scored = []
    for r in records:
        item = dict(r)
        item["score"] = score_record(r)
        scored.append(item)
    return sorted(scored, key=lambda x: x["score"], reverse=True)


def pick_winning_products(records: List[dict], *, top_n: int = 2,
                          min_score: float = 60.0) -> List[dict]:
    """Pick up to top_n products that clear the winning threshold."""
    scored = analyse_trends(records)
    return [r for r in scored if r["score"] >= min_score][:top_n]


def load_feed(feed_file: Optional[Path]) -> List[dict]:
    """Load trend records from a local JSON feed. INTEGRATION POINT: replace
    with a live trends/ads API client. Returns [] if no feed is present."""
    if not feed_file:
        return []
    try:
        data = json.loads(Path(feed_file).read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def run_analysis(
    *,
    feed_file: Optional[Path] = None,
    out_file: Optional[Path] = None,
    top_n: int = 2,
    min_score: float = 60.0,
) -> TrendReport:
    records = load_feed(feed_file)
    report = TrendReport(analysed=len(records))
    if not records:
        return report
    winners = pick_winning_products(records, top_n=top_n, min_score=min_score)
    report.winners = winners
    if out_file and winners:
        try:
            Path(out_file).parent.mkdir(parents=True, exist_ok=True)
            Path(out_file).write_text(json.dumps(winners, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        except OSError:
            pass
    return report
