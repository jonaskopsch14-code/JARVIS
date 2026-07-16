"""ChillGo product scoring.

Implements Section 4.3 of the masterprompt as an actual rank function, not an
eyeball check. Each candidate is a normalised dict (see cj_client.normalise_product)
and gets a numeric score plus a human-readable breakdown so the decision record
in Section 4.4 explains *why* the winner won.

The weights favour the single biggest conversion lever for a €50 organic launch:
US/EU warehouse stock (fast delivery -> better reviews -> higher CR). Everything
else is secondary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Hard rules (a candidate that fails any of these is rejected outright) -----

MIN_RATING = 4.3            # reject below
MAX_PACKAGE_WEIGHT_G = 300  # dimensional-shipping risk on a €50 budget
RETAIL_MIN = 24.99          # target retail band the supplier cost must support
RETAIL_MAX = 39.99
# A rough max supplier cost that still leaves a healthy margin inside the band.
# (retail_low / ~2.6 landed-cost multiple, incl. shipping + payment fees).
MAX_SUPPLIER_COST = 9.60

# Warehouses we treat as "fast" for a global-but-Western audience.
FAST_WAREHOUSE_HINTS = (
    "us", "united states", "usa",
    "eu", "germany", "de", "france", "fr", "czech", "cz",
    "poland", "pl", "spain", "es", "uk", "united kingdom", "gb",
)
CN_WAREHOUSE_HINTS = ("cn", "china", "guangdong", "yiwu", "shenzhen")

USBC_PATTERNS = (r"usb[\s\-]?c", r"type[\s\-]?c")
MAH_PATTERN = r"\b(\d{3,5})\s?mah\b"
SPEED_PATTERNS = (r"\b([2-9])[\s\-]?speed", r"\b([2-9])\s?gear", r"adjustable")
BONUS_PATTERNS = {
    "battery display": r"(battery\s?(display|indicator)|digital\s?display|led\s?display)",
    "cooling plate": r"(cooling\s?(plate|pad)|semiconductor|ice\s?feel)",
    "power bank": r"(power\s?bank|powerbank|charge\s?(phone|device))",
}
BATTERY_SAFETY_PATTERNS = (
    r"\bce\b", r"\bfcc\b", r"\brohs\b", r"\bun\s?38\.3\b", r"\bmsds\b",
    r"battery\s?(safety|certification|report)",
)


@dataclass
class ScoreResult:
    product_id: str
    title: str
    total: float
    rejected: bool
    reject_reasons: list[str] = field(default_factory=list)
    breakdown: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def as_record(self) -> dict:
        return {
            "product_id": self.product_id,
            "title": self.title,
            "score": round(self.total, 2),
            "rejected": self.rejected,
            "reject_reasons": self.reject_reasons,
            "breakdown": {k: round(v, 2) for k, v in self.breakdown.items()},
            "notes": self.notes,
        }


def _text(product: dict) -> str:
    parts = [
        product.get("title", ""),
        product.get("description", ""),
        " ".join(product.get("keywords", []) or []),
    ]
    return " ".join(parts).lower()


def _matches_any(text: str, patterns) -> bool:
    return any(re.search(p, text) for p in patterns)


def _warehouse_score(warehouses: list[str]) -> tuple[float, str]:
    """Heavily weight US/EU stock. Returns (points, note)."""
    whs = [w.lower() for w in (warehouses or [])]
    if any(any(h in w for h in FAST_WAREHOUSE_HINTS) for w in whs):
        fast = [w for w in whs if any(h in w for h in FAST_WAREHOUSE_HINTS)]
        return 40.0, f"fast warehouse(s): {', '.join(sorted(set(fast)))}"
    if any(any(h in w for h in CN_WAREHOUSE_HINTS) for w in whs):
        return 5.0, "CN-only stock (slow shipping — big conversion drag)"
    return 0.0, "no warehouse data"


def score_product(product: dict) -> ScoreResult:
    """Score one normalised candidate. See module docstring for the schema."""
    text = _text(product)
    res = ScoreResult(
        product_id=str(product.get("product_id", "")),
        title=product.get("title", ""),
        total=0.0,
        rejected=False,
    )

    rating = product.get("rating")
    orders = product.get("orders") or 0
    weight_g = product.get("package_weight_g")
    supplier_cost = product.get("supplier_cost")

    # --- Hard rejects ---------------------------------------------------------
    if rating is not None and rating < MIN_RATING:
        res.reject_reasons.append(f"rating {rating} < {MIN_RATING}")
    if weight_g is not None and weight_g > MAX_PACKAGE_WEIGHT_G:
        res.reject_reasons.append(f"package weight {weight_g}g > {MAX_PACKAGE_WEIGHT_G}g")
    if supplier_cost is not None and supplier_cost > MAX_SUPPLIER_COST:
        res.reject_reasons.append(
            f"supplier cost ${supplier_cost} can't support ${RETAIL_MIN}-${RETAIL_MAX} at healthy margin"
        )
    if not _matches_any(text, BATTERY_SAFETY_PATTERNS):
        res.reject_reasons.append("no battery-safety documentation keywords found")

    if res.reject_reasons:
        res.rejected = True
        return res

    # --- Weighted scoring -----------------------------------------------------
    # Rating (0-15): linear from the 4.3 floor to a perfect 5.0.
    if rating is not None:
        res.breakdown["rating"] = min(15.0, max(0.0, (rating - MIN_RATING) / (5.0 - MIN_RATING) * 15.0))

    # Warehouse (0-40): the dominant lever.
    wh_pts, wh_note = _warehouse_score(product.get("warehouses", []))
    res.breakdown["warehouse"] = wh_pts
    res.notes["warehouse"] = wh_note

    # Order volume (0-10): tie-breaker, not a hard cutoff. Saturates around 500.
    res.breakdown["orders"] = min(10.0, orders / 50.0)

    # USB-C + mAh present (0-10).
    usbc = _matches_any(text, USBC_PATTERNS)
    mah_match = re.search(MAH_PATTERN, text)
    batt_pts = (6.0 if usbc else 0.0) + (4.0 if mah_match else 0.0)
    res.breakdown["battery_usbc"] = batt_pts
    if mah_match:
        res.notes["mah"] = f"{mah_match.group(1)} mAh"

    # Speed settings (0-8).
    res.breakdown["speed_settings"] = 8.0 if _matches_any(text, SPEED_PATTERNS) else 0.0

    # Bonus features (0-12, +4 each).
    bonuses = [name for name, pat in BONUS_PATTERNS.items() if re.search(pat, text)]
    res.breakdown["bonus_features"] = min(12.0, len(bonuses) * 4.0)
    if bonuses:
        res.notes["bonus_features"] = ", ".join(bonuses)

    # Price fit (0-5): reward a supplier cost that leaves the fattest margin.
    if supplier_cost is not None and supplier_cost > 0:
        margin_headroom = (RETAIL_MIN - supplier_cost) / RETAIL_MIN
        res.breakdown["price_fit"] = max(0.0, min(5.0, margin_headroom * 6.0))

    res.total = sum(res.breakdown.values())
    return res


def rank(products: list[dict]) -> list[ScoreResult]:
    """Score and sort candidates best-first; rejected ones sink to the bottom."""
    scored = [score_product(p) for p in products]
    scored.sort(key=lambda r: (not r.rejected, r.total), reverse=True)
    return scored
