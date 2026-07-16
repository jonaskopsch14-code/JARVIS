#!/usr/bin/env python3
"""ChillGo automated product sourcing (Section 4).

Runs the full flow: authenticate against the CJ API, search the fan keywords,
merge + dedupe by product id, pull warehouse stock for the top candidates,
score/rank them, auto-select the winner, and write a decision record the
operator can glance at later (Section 4.4). This is a report, not a request
for approval — no confirmation gate on the selection itself.

Usage:
    export CJ_EMAIL=...          # your CJ account email
    export CJ_API_KEY=...        # generated in CJ > API / Developer
    python source_product.py                 # live run
    python source_product.py --dry-run FILE  # score a saved JSON fixture offline

Outputs:
    decision_record.md   — human-readable pick + score breakdown
    selected_product.json — machine-readable spec sheet feeding Sections 5/9/12
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import scoring

KEYWORDS = ["handheld fan", "portable fan", "turbo fan", "rechargeable fan"]
HERE = Path(__file__).parent
DECISION_MD = HERE / "decision_record.md"
SELECTED_JSON = HERE / "selected_product.json"
# How many top-by-title candidates to enrich with a (rate-limited) stock lookup.
ENRICH_TOP_N = 15


def gather_live() -> list[dict]:
    from cj_client import CJClient, normalise_product

    client = CJClient()
    client.authenticate()

    merged: dict[str, dict] = {}
    for kw in KEYWORDS:
        for raw in client.search(kw):
            pid = raw.get("pid") or raw.get("productId")
            if pid and pid not in merged:
                merged[pid] = raw
    print(f"[sourcing] {len(merged)} unique candidates across {len(KEYWORDS)} keywords")

    # Cheap pre-rank on title/keywords only, so we spend the rate-limited
    # detail/stock calls on the most promising handful.
    prelim = scoring.rank([normalise_product(r) for r in merged.values()])
    top_ids = [r.product_id for r in prelim if not r.rejected][:ENRICH_TOP_N]

    enriched: list[dict] = []
    for pid in top_ids:
        raw = merged[pid]
        try:
            detail = client.product_detail(pid)
            vid = ((detail.get("variants") or [{}])[0]).get("vid")
            warehouses = None
            if vid:
                inv = client.inventory(vid)
                warehouses = [str(i.get("areaEn") or i.get("area") or "") for i in inv if i.get("totalInventoryNum", 0)]
            enriched.append(normalise_product(raw, detail, warehouses))
        except Exception as exc:  # keep going; one bad detail call shouldn't abort
            print(f"[sourcing] warn: enrich failed for {pid}: {exc}", file=sys.stderr)
            enriched.append(normalise_product(raw))
    return enriched


def gather_fixture(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text())
    return data if isinstance(data, list) else data.get("products", [])


def write_records(ranked: list[scoring.ScoreResult], candidates: dict[str, dict]) -> scoring.ScoreResult:
    winners = [r for r in ranked if not r.rejected]
    if not winners:
        raise SystemExit("[sourcing] no candidate passed the hard filters — widen keywords or relax rules")
    winner = winners[0]
    spec = candidates.get(winner.product_id, {})

    retail = scoring.RETAIL_MIN
    cost = spec.get("supplier_cost")
    if cost:
        # Land in-band, rounded to a .99 charm price with a comfortable margin.
        target = min(scoring.RETAIL_MAX, max(scoring.RETAIL_MIN, round(cost * 3) - 0.01))
        retail = round(target, 2)

    SELECTED_JSON.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "product_id": winner.product_id,
        "title": spec.get("title"),
        "cj_url": spec.get("cj_url"),
        "image": spec.get("image"),
        "supplier_cost": cost,
        "chosen_retail_price": retail,
        "warehouses": spec.get("warehouses"),
        "spec_source_description": spec.get("description"),
        "score": round(winner.total, 2),
        "score_breakdown": {k: round(v, 2) for k, v in winner.breakdown.items()},
    }, indent=2))

    lines = [
        "# ChillGo — Product Sourcing Decision Record",
        "",
        f"_Generated {date.today().isoformat()} by `source_product.py` (Section 4.4). "
        "This is a report, not a request for approval._",
        "",
        "## Selected hero product",
        f"- **Title:** {spec.get('title', 'n/a')}",
        f"- **CJ product ID:** `{winner.product_id}`",
        f"- **CJ link:** {spec.get('cj_url', 'n/a')}",
        f"- **Warehouse(s):** {', '.join(spec.get('warehouses') or []) or 'unknown'}",
        f"- **Supplier cost:** ${cost if cost is not None else 'n/a'}",
        f"- **Chosen retail price:** ${retail}",
        f"- **Total score:** {round(winner.total, 2)}",
        "",
        "### Why it won",
        "| Criterion | Points |",
        "|---|---|",
    ]
    for k, v in winner.breakdown.items():
        lines.append(f"| {k.replace('_', ' ')} | {round(v, 2)} |")
    if winner.notes:
        lines += ["", "### Notes", *[f"- **{k}:** {v}" for k, v in winner.notes.items()]]

    lines += ["", f"### Runners-up ({min(4, len(winners) - 1)})"]
    for r in winners[1:5]:
        s = candidates.get(r.product_id, {})
        lines.append(f"- {s.get('title', r.product_id)} — score {round(r.total, 2)}, "
                     f"warehouse {', '.join(s.get('warehouses') or []) or '?'}")

    rejected = [r for r in ranked if r.rejected]
    if rejected:
        lines += ["", f"### Rejected ({len(rejected)})",
                  "First few, with reasons:"]
        for r in rejected[:5]:
            lines.append(f"- {r.title or r.product_id}: {'; '.join(r.reject_reasons)}")

    lines += ["", "---",
              "Next steps (automated): this product ID feeds Section 5 (import), "
              "Section 9 (copy from the real spec sheet in `selected_product.json`), "
              "and the sample-unit order in Section 12."]
    DECISION_MD.write_text("\n".join(lines) + "\n")
    return winner


def main() -> None:
    ap = argparse.ArgumentParser(description="ChillGo automated product sourcing")
    ap.add_argument("--dry-run", metavar="FIXTURE",
                    help="score a saved JSON list of normalised candidates offline (no API calls)")
    args = ap.parse_args()

    if args.dry_run:
        candidates_list = gather_fixture(args.dry_run)
    else:
        candidates_list = gather_live()

    candidates = {str(c.get("product_id")): c for c in candidates_list}
    ranked = scoring.rank(candidates_list)
    winner = write_records(ranked, candidates)
    print(f"[sourcing] selected {winner.product_id} (score {round(winner.total, 2)})")
    print(f"[sourcing] wrote {DECISION_MD.name} and {SELECTED_JSON.name}")


if __name__ == "__main__":
    main()
