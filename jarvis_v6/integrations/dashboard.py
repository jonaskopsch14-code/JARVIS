"""
JARVIS V6 — Dashboard data loader.

Reads the artefacts the night-shift tasks write (leads, winning products,
suppliers, store drafts) so the GUI — or any consumer — can surface them. Pure
file I/O, no Tk dependency, fully testable offline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

# filename -> dashboard section key
SECTIONS = {
    "leads.json": "leads",
    "winning_products.json": "winners",
    "suppliers.json": "suppliers",
    "store_drafts.json": "drafts",
}


@dataclass
class DashboardData:
    leads: List[dict] = field(default_factory=list)
    winners: List[dict] = field(default_factory=list)
    suppliers: List[dict] = field(default_factory=list)
    drafts: List[dict] = field(default_factory=list)

    @property
    def counts(self) -> Dict[str, int]:
        return {"leads": len(self.leads), "winners": len(self.winners),
                "suppliers": len(self.suppliers), "drafts": len(self.drafts)}


def _read_list(path: Path) -> List[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def load_dashboard(dashboard_dir) -> DashboardData:
    """Load every known artefact from dashboard_dir into a DashboardData."""
    d = Path(dashboard_dir)
    data = DashboardData()
    for filename, key in SECTIONS.items():
        setattr(data, key, _read_list(d / filename))
    return data


def format_summary(data: DashboardData) -> str:
    """Compact human-readable summary used in the GUI panel."""
    c = data.counts
    lines = [
        f"Leads: {c['leads']}   Winning Products: {c['winners']}   "
        f"Lieferanten: {c['suppliers']}   Store-Entwürfe: {c['drafts']}",
    ]
    for lead in data.leads[:3]:
        lines.append(f"  • Lead: {lead.get('from', '?')} — {lead.get('subject', '')}")
    for win in data.winners[:3]:
        score = win.get("score")
        score_s = f" (Score {score})" if score is not None else ""
        lines.append(f"  • Winner: {win.get('title', '?')}{score_s}")
    for sup in data.suppliers[:3]:
        lines.append(f"  • Lieferant: {sup.get('name', sup.get('url', '?'))}")
    return "\n".join(lines)
