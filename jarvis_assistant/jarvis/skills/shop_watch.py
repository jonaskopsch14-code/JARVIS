"""Shop-Wächter für Fashion Aura (Phase 5, Shopify Admin API).

Lesen/Analysieren ist Stufe 1; alles Verändernde (z. B. Preise) ist Stufe 3.
Die Analyse-Funktionen sind reine Logik und offline mit Mock-Daten testbar;
die Shopify-Aufrufe sind echter Code (lazy), der auf dem PC mit Token läuft.

Grundhaltung aus dem Auftrag: proaktiv **kurze, konkrete Vorschläge**, keine
Datendumps.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from . import skill
from ..security import Risk

DOMAIN = ""     # z. B. "fashion-aura.myshopify.com"
TOKEN = ""      # Shopify Admin API Access-Token
API_VERSION = "2024-01"


def configure(domain: str, token: str) -> None:
    global DOMAIN, TOKEN
    DOMAIN, TOKEN = domain or "", token or ""


def _enabled() -> bool:
    return bool(DOMAIN and TOKEN)


def _api(path: str, params: dict = None) -> dict:
    """GET auf die Shopify Admin REST API. Wirft mit klarer Meldung bei Setup-Fehlern."""
    if not _enabled():
        raise RuntimeError("Shopify nicht konfiguriert (Domain/Token fehlen).")
    import httpx  # lazy
    url = f"https://{DOMAIN}/admin/api/{API_VERSION}/{path.lstrip('/')}"
    r = httpx.get(url, timeout=20.0,
                  headers={"X-Shopify-Access-Token": TOKEN}, params=params or {})
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Reine Analyse (testbar).
# ---------------------------------------------------------------------------
def detect_low_stock(products: List[dict], *, stock_threshold: int = 5,
                     min_sales: int = 3) -> List[str]:
    """Bestseller (viel verkauft), die fast ausverkauft sind."""
    out = []
    for p in products:
        inv = int(p.get("inventory", 0) or 0)
        sales = int(p.get("sales_7d", 0) or 0)
        if sales >= min_sales and inv <= stock_threshold:
            out.append(f"{p.get('title', '?')} (nur noch {inv} Stück, "
                       f"{sales} Verkäufe/Woche)")
    return out


def detect_revenue_anomaly(daily_revenues: List[float], *, deviation: float = 0.4
                           ) -> Optional[str]:
    """Vergleicht den letzten Tag mit dem Mittel der Vortage."""
    if len(daily_revenues) < 3:
        return None
    prev = daily_revenues[:-1]
    latest = daily_revenues[-1]
    avg = sum(prev) / len(prev)
    if avg <= 0:
        return None
    change = (latest - avg) / avg
    if change <= -deviation:
        return (f"Der Umsatz ist gestern auf {round(latest)} Euro gefallen, "
                f"rund {abs(round(change * 100))} Prozent unter dem Schnitt.")
    if change >= deviation:
        return (f"Der Umsatz ist gestern auf {round(latest)} Euro gestiegen, "
                f"rund {round(change * 100)} Prozent über dem Schnitt.")
    return None


def detect_abandoned(completed: int, abandoned: int, *, rate_threshold: float = 0.6
                     ) -> Optional[str]:
    total = completed + abandoned
    if total < 5:
        return None
    rate = abandoned / total
    if rate >= rate_threshold:
        return (f"Auffällig viele abgebrochene Käufe: {abandoned} von {total} "
                f"({round(rate * 100)} Prozent). Vielleicht hakt es an Versand oder Bezahlung.")
    return None


def detect_slow_movers(products: List[dict], *, days: int = 30) -> List[str]:
    """Ware mit Bestand, aber ohne Verkäufe im Zeitraum."""
    return [f"{p.get('title', '?')} ({p.get('inventory', 0)} auf Lager, seit "
            f"{days} Tagen kein Verkauf)"
            for p in products
            if int(p.get("inventory", 0) or 0) > 0 and int(p.get("sales_30d", 0) or 0) == 0]


def compose_alerts(data: Dict) -> List[str]:
    """Aus Rohdaten die konkreten, kurzen Hinweise bauen."""
    alerts: List[str] = []
    low = detect_low_stock(data.get("products", []))
    if low:
        alerts.append("Fast ausverkauft: " + "; ".join(low[:3]) + ".")
    rev = detect_revenue_anomaly(data.get("daily_revenues", []))
    if rev:
        alerts.append(rev)
    ab = detect_abandoned(data.get("checkouts_completed", 0),
                          data.get("checkouts_abandoned", 0))
    if ab:
        alerts.append(ab)
    slow = detect_slow_movers(data.get("products", []))
    if slow:
        alerts.append("Ladenhüter: " + "; ".join(slow[:3])
                      + ". Vielleicht ein Rabatt oder Bundle?")
    return alerts


# ---------------------------------------------------------------------------
# Datenbeschaffung (echter Shopify-Aufruf; best effort).
# ---------------------------------------------------------------------------
def _gather() -> Dict:
    data: Dict = {"products": [], "daily_revenues": [],
                  "checkouts_completed": 0, "checkouts_abandoned": 0}
    # Produkte + Bestand
    prods = _api("products.json", {"limit": 50}).get("products", [])
    for p in prods:
        inv = sum(int(v.get("inventory_quantity", 0) or 0) for v in p.get("variants", []))
        data["products"].append({"title": p.get("title"), "inventory": inv,
                                  "sales_7d": 0, "sales_30d": 0})
    # Bestellungen der letzten Tage (für Umsatz + Verkaufszahlen)
    orders = _api("orders.json", {"status": "any", "limit": 250}).get("orders", [])
    from collections import defaultdict
    rev_by_day: Dict[str, float] = defaultdict(float)
    sold: Dict[str, int] = defaultdict(int)
    for o in orders:
        day = (o.get("created_at") or "")[:10]
        rev_by_day[day] += float(o.get("total_price", 0) or 0)
        for li in o.get("line_items", []):
            sold[li.get("title", "")] += int(li.get("quantity", 0) or 0)
    data["daily_revenues"] = [rev_by_day[d] for d in sorted(rev_by_day)][-7:]
    for p in data["products"]:
        p["sales_7d"] = sold.get(p["title"], 0)
        p["sales_30d"] = sold.get(p["title"], 0)
    # Abgebrochene Checkouts
    ab = _api("checkouts/count.json").get("count", 0)
    data["checkouts_abandoned"] = int(ab or 0)
    data["checkouts_completed"] = len(orders)
    return data


# ---------------------------------------------------------------------------
# Skills.
# ---------------------------------------------------------------------------
@skill(
    name="shop_summary",
    description="Kurzer Überblick über den Fashion-Aura-Shop (Umsatz, Bestseller, Bestand).",
    parameters={"type": "object", "properties": {}},
    risk=Risk.AUTO,
)
def shop_summary() -> str:
    try:
        d = _gather()
    except Exception as exc:  # noqa: BLE001
        return f"Shop-Daten nicht abrufbar: {exc}"
    rev = round(sum(d["daily_revenues"]))
    n = len(d["products"])
    return (f"Fashion Aura: {n} Produkte, Umsatz der letzten Tage rund {rev} Euro, "
            f"{d['checkouts_completed']} Bestellungen.")


@skill(
    name="shop_alerts",
    description="Konkrete Handlungsvorschläge zum Shop (fast ausverkauft, Umsatz, Ladenhüter).",
    parameters={"type": "object", "properties": {}},
    risk=Risk.AUTO,
)
def shop_alerts() -> str:
    try:
        d = _gather()
    except Exception as exc:  # noqa: BLE001
        return f"Shop-Daten nicht abrufbar: {exc}"
    alerts = compose_alerts(d)
    return " ".join(alerts) if alerts else "Beim Shop sieht gerade alles unauffällig aus."


def proactive_check(cfg) -> Optional[Callable[[], Optional[str]]]:
    """Liefert einen Proaktiv-Check (oder None, wenn Shop nicht konfiguriert)."""
    if not (getattr(cfg, "shopify_domain", "") and getattr(cfg, "shopify_token", "")):
        return None

    def check() -> Optional[str]:
        try:
            alerts = compose_alerts(_gather())
        except Exception:  # noqa: BLE001
            return None
        if alerts:
            return "Kurzer Blick auf Fashion Aura, Sir: " + " ".join(alerts[:2])
        return None
    return check
