"""Offline tests for the supplier / trends / store integrations and an
end-to-end dry-run through the supervisor. No network or paid APIs needed."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.suppliers import extract_links, filter_suppliers  # noqa: E402
from integrations.trends import (  # noqa: E402
    analyse_trends, pick_winning_products, score_record,
)
from integrations.store import build_campaign, build_seo, optimize_store  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# --- suppliers --------------------------------------------------------------
def test_extract_and_filter_supplier_links():
    html = """
    <html><body>
      <a href="/wholesale/fashion">Großhandel Mode</a>
      <a href="https://example.com/about">Über uns</a>
      <a href="https://supplier.example/b2b">B2B Supplier</a>
    </body></html>
    """
    links = extract_links(html, base_url="https://shop.example")
    assert any(l.url == "https://shop.example/wholesale/fashion" for l in links)
    suppliers = filter_suppliers(links)
    urls = {l.url for l in suppliers}
    assert "https://shop.example/wholesale/fashion" in urls
    assert "https://supplier.example/b2b" in urls
    assert "https://example.com/about" not in urls  # no supplier hint


def test_filter_dedupes():
    from integrations.suppliers import SupplierLink
    links = [SupplierLink("Wholesale", "https://a.de/wholesale"),
             SupplierLink("Wholesale", "https://a.de/wholesale/")]
    assert len(filter_suppliers(links)) == 1


# --- trends -----------------------------------------------------------------
def test_high_demand_growth_scores_higher_than_saturated():
    winner = score_record({"search_volume": 12000, "growth": 120, "competition": 0.3, "margin": 0.6})
    loser = score_record({"search_volume": 400, "growth": -20, "competition": 0.9, "margin": 0.2})
    assert winner > loser
    assert 0.0 <= loser <= 100.0 and 0.0 <= winner <= 100.0


def test_pick_winning_products_respects_top_n_and_threshold():
    records = json.loads((FIXTURES / "trends_feed.json").read_text(encoding="utf-8"))
    winners = pick_winning_products(records, top_n=2, min_score=60.0)
    assert len(winners) == 2
    titles = [w["title"] for w in winners]
    assert "Basic Baumwoll-Shirt" not in titles  # below threshold
    # Sorted best-first.
    assert winners[0]["score"] >= winners[1]["score"]


# --- store ------------------------------------------------------------------
def test_build_seo_lengths_and_slug():
    product = {"title": "Oversized Strickpullover", "type": "Pullover",
               "color": "Beige", "material": "Bio-Baumwolle", "audience": "Damen",
               "keywords": ["strickpullover", "oversized"]}
    seo = build_seo(product)
    assert len(seo["seo_title"]) <= 60
    assert len(seo["meta_description"]) <= 160
    assert seo["handle"] == "oversized-strickpullover"
    assert "Pullover" in seo["tags"]


def test_build_campaign_budget_scales_with_score():
    p = {"title": "Cargo Jeans", "type": "Jeans", "keywords": ["cargo"]}
    low = build_campaign(p, trend_score=0)["suggested_daily_budget_eur"]
    high = build_campaign(p, trend_score=100)["suggested_daily_budget_eur"]
    assert high > low
    assert build_campaign(p)["status"] == "DRAFT"


def test_optimize_store_dryrun_publishes_nothing():
    products = json.loads((FIXTURES / "products.json").read_text(encoding="utf-8"))
    rep = optimize_store(products, dry_run=True)
    assert rep.products_seo == 2 and rep.campaigns == 2 and rep.published == 0
    assert rep.error is None


# --- end-to-end through the supervisor (dry-run) ----------------------------
def test_end_to_end_dryrun_writes_dashboard():
    from main import NightShiftConfig, NightShiftSupervisor
    with tempfile.TemporaryDirectory() as tmp:
        dash = Path(tmp) / "dash"
        cfg = NightShiftConfig()
        cfg.dry_run = True
        cfg.trends_feed = str(FIXTURES / "trends_feed.json")
        cfg.store_products_file = str(FIXTURES / "products.json")
        cfg.dashboard_dir = dash
        sup = NightShiftSupervisor(cfg)
        results = sup.run_tasks()
        by = {r.name: r for r in results}
        assert by["market_trends"].metrics["winning_products"] == 2
        assert by["store_optimizer"].metrics["products_seo"] == 2
        assert all(r.ok for r in results)
        # Dashboard artefacts were written.
        assert (dash / "winning_products.json").exists()
        assert (dash / "store_drafts.json").exists()


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
