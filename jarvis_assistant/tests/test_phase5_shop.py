"""Phase 5: Shop-Wächter-Analyse (reine Logik, offline mit Mock-Daten)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarvis import skills                       # noqa: E402
from jarvis.security import Risk                 # noqa: E402
from jarvis.skills.shop_watch import (          # noqa: E402
    compose_alerts, detect_abandoned, detect_low_stock, detect_revenue_anomaly,
    detect_slow_movers, proactive_check,
)


def test_low_stock_flags_bestsellers_only():
    products = [
        {"title": "Cargo Jeans", "inventory": 2, "sales_7d": 12},   # Bestseller, knapp
        {"title": "Basic Shirt", "inventory": 1, "sales_7d": 0},    # knapp, aber kein Seller
        {"title": "Pullover", "inventory": 50, "sales_7d": 20},     # genug Bestand
    ]
    low = detect_low_stock(products)
    assert any("Cargo Jeans" in x for x in low)
    assert not any("Basic Shirt" in x for x in low)
    assert not any("Pullover" in x for x in low)


def test_revenue_anomaly_detects_drop_and_spike():
    assert detect_revenue_anomaly([100, 100, 100, 40]) is not None      # Einbruch
    assert "gestiegen" in (detect_revenue_anomaly([100, 100, 100, 200]) or "")
    assert detect_revenue_anomaly([100, 100, 100, 105]) is None         # normal
    assert detect_revenue_anomaly([100]) is None                        # zu wenig Daten


def test_abandoned_checkouts_threshold():
    assert detect_abandoned(2, 8) is not None       # 80 % abgebrochen
    assert detect_abandoned(9, 1) is None           # 10 %
    assert detect_abandoned(1, 1) is None           # zu wenig Daten


def test_slow_movers():
    products = [
        {"title": "Altbestand", "inventory": 10, "sales_30d": 0},
        {"title": "Renner", "inventory": 5, "sales_30d": 30},
        {"title": "Ausverkauft", "inventory": 0, "sales_30d": 0},
    ]
    slow = detect_slow_movers(products)
    assert any("Altbestand" in x for x in slow)
    assert not any("Renner" in x for x in slow)
    assert not any("Ausverkauft" in x for x in slow)


def test_compose_alerts_is_concise_suggestions():
    data = {
        "products": [{"title": "Cargo Jeans", "inventory": 1, "sales_7d": 15, "sales_30d": 60},
                     {"title": "Altware", "inventory": 8, "sales_7d": 0, "sales_30d": 0}],
        "daily_revenues": [200, 220, 210, 60],
        "checkouts_completed": 3, "checkouts_abandoned": 12,
    }
    alerts = compose_alerts(data)
    assert len(alerts) >= 3                      # Bestand, Umsatz, Abbrüche, Ladenhüter
    joined = " ".join(alerts)
    assert "Cargo Jeans" in joined and "Umsatz" in joined and "abgebrochene" in joined


def test_shop_skills_registered_read_only():
    assert skills.get("shop_summary").risk == Risk.AUTO
    assert skills.get("shop_alerts").risk == Risk.AUTO


def test_proactive_check_none_without_config():
    class Cfg:  # nicht konfiguriert
        shopify_domain = ""
        shopify_token = ""
    assert proactive_check(Cfg()) is None


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn(); print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1; print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
