"""
JARVIS V6 — Fashion Aura store-optimizer integration.

Implements the INTEGRATION POINT for StoreOptimizerTask.

  * build_seo()        — deterministic, dependency-free SEO copy (title, meta
                         description, slug, tags) from a product dict.
  * build_campaign()   — an ad-campaign draft (headlines, primary text,
                         interests, suggested daily budget) from a product +
                         its trend score.
  * optimize_store()   — generates SEO + campaign DRAFTS for the catalogue and
                         writes them to the dashboard. It PUBLISHES nothing
                         unless dry_run is False AND Shopify credentials/the
                         'store' extra are present; the publish call itself is
                         the remaining marked integration point.

Everything that could change the live store is gated behind dry_run. The copy
generation is fully testable offline.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

BRAND = "Fashion Aura"
SEO_TITLE_MAX = 60
META_DESC_MAX = 160


def _slugify(text: str) -> str:
    text = (text or "").lower()
    repl = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    for a, b in repl.items():
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return re.sub(r"-{2,}", "-", text)


def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;") or text[:limit]


def build_seo(product: dict) -> dict:
    """Generate SEO metadata for one product. Deterministic & dependency-free.

    Recognised fields: title, type, color, material, brand, price, currency,
    audience, keywords (list).
    """
    title = (product.get("title") or "").strip()
    ptype = (product.get("type") or "").strip()
    color = (product.get("color") or "").strip()
    material = (product.get("material") or "").strip()
    audience = (product.get("audience") or "").strip()
    keywords = [str(k).strip() for k in product.get("keywords", []) if str(k).strip()]

    descriptors = " ".join(p for p in [material, color, ptype] if p)
    seo_title = _truncate(f"{title} – {descriptors} | {BRAND}" if descriptors
                          else f"{title} | {BRAND}", SEO_TITLE_MAX)

    parts = [f"{title} bei {BRAND}."]
    if descriptors:
        parts.append(f"{descriptors.capitalize()}.")
    if audience:
        parts.append(f"Perfekt für {audience}.")
    parts.append("Jetzt entdecken – schneller Versand.")
    meta_description = _truncate(" ".join(parts), META_DESC_MAX)

    tag_seed = keywords + [ptype, color, material, audience, BRAND]
    tags = []
    for t in tag_seed:
        t = (t or "").strip()
        if t and t.lower() not in [x.lower() for x in tags]:
            tags.append(t)

    return {
        "handle": _slugify(title),
        "seo_title": seo_title,
        "meta_description": meta_description,
        "tags": tags,
    }


def build_campaign(product: dict, *, trend_score: float = 0.0) -> dict:
    """Build an ad-campaign draft. Budget scales with the trend score."""
    title = (product.get("title") or "").strip()
    audience = (product.get("audience") or "Mode-Interessierte").strip()
    keywords = [str(k).strip() for k in product.get("keywords", []) if str(k).strip()]
    ptype = (product.get("type") or "").strip()

    # Budget heuristic: €8 base, up to +€22 for a top-scoring winner.
    daily_budget = round(8.0 + (max(0.0, min(100.0, trend_score)) / 100.0) * 22.0, 2)

    headlines = [
        _truncate(f"Neu: {title}", 40),
        _truncate(f"{title} – nur bei {BRAND}", 40),
        _truncate(f"{ptype or title} im Trend", 40),
    ]
    primary_text = _truncate(
        f"Entdecke {title} bei {BRAND}. Limitierte Verfügbarkeit – sichere dir deins, "
        f"bevor es ausverkauft ist. Schneller Versand, einfache Rückgabe.", 220)

    return {
        "platform": "meta",
        "objective": "conversions",
        "product": title,
        "headlines": headlines,
        "primary_text": primary_text,
        "interests": (keywords + [ptype, audience, "Fashion", "Online Shopping"])[:8],
        "suggested_daily_budget_eur": daily_budget,
        "status": "DRAFT",
    }


@dataclass
class StoreReport:
    products_seo: int = 0
    campaigns: int = 0
    published: int = 0
    dry_run: bool = True
    drafts: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    def as_metrics(self) -> Dict[str, int]:
        return {"products_seo": self.products_seo, "campaigns": self.campaigns,
                "published": self.published}


def load_products(products_file: Optional[Path]) -> List[dict]:
    """Load the catalogue from a local JSON file. INTEGRATION POINT: replace
    with a Shopify Admin API fetch when credentials are available."""
    if not products_file:
        return []
    try:
        data = json.loads(Path(products_file).read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def build_shopify_product_payload(product: dict, seo: dict) -> dict:
    """Build the JSON body for a Shopify Admin API product update.

    SEO title/description map to Shopify's global metafields
    (`global.title_tag` / `global.description_tag`); tags update the product
    tag list. Pure & offline-testable.
    """
    payload = {
        "product": {
            "id": product.get("id"),
            "tags": ", ".join(seo.get("tags", [])),
            "metafields": [
                {"namespace": "global", "key": "title_tag",
                 "type": "single_line_text_field", "value": seo.get("seo_title", "")},
                {"namespace": "global", "key": "description_tag",
                 "type": "multi_line_text_field", "value": seo.get("meta_description", "")},
            ],
        }
    }
    return payload


def _publish_to_shopify(
    drafts: List[dict],
    *,
    shop_domain: str,
    access_token: str,
    api_version: str = "2024-01",
    timeout: float = 15.0,
) -> int:
    """Publish SEO fields for each draft that carries a product id, via the
    Shopify Admin REST API. Only ever reached in confirmed live mode.

    Returns the number of products successfully updated. Campaign drafts are
    NOT published here — launching paid ads stays a manual decision.
    """
    try:
        import httpx  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"httpx nicht installiert ({exc}); pip install -e '.[crawl]'")

    base = f"https://{shop_domain}/admin/api/{api_version}"
    headers = {"X-Shopify-Access-Token": access_token,
               "Content-Type": "application/json"}
    published = 0
    with httpx.Client(timeout=timeout, headers=headers) as client:
        for draft in drafts:
            pid = draft.get("product_id")
            if not pid:
                continue
            body = build_shopify_product_payload({"id": pid}, draft.get("seo", {}))
            resp = client.put(f"{base}/products/{pid}.json", json=body)
            if resp.status_code < 300:
                published += 1
    return published


def optimize_store(
    products: List[dict],
    *,
    winners: Optional[List[dict]] = None,
    out_file: Optional[Path] = None,
    dry_run: bool = True,
    shopify_api_key: str = "",
    shop_domain: str = "",
    confirm_live: bool = False,
) -> StoreReport:
    """Generate SEO + campaign drafts for the catalogue; publish only if live.

    Live publishing requires ALL of: dry_run=False, a Shopify access token, a
    shop domain, AND confirm_live=True (the deliberate second gate). Campaign
    drafts are never auto-launched.
    """
    report = StoreReport(dry_run=dry_run)
    if not products:
        return report

    # Map product title -> trend score so campaign budgets reflect demand.
    score_by_title = {(w.get("title") or "").lower(): float(w.get("score", 0) or 0)
                      for w in (winners or [])}

    for product in products:
        seo = build_seo(product)
        score = score_by_title.get((product.get("title") or "").lower(), 0.0)
        campaign = build_campaign(product, trend_score=score)
        report.products_seo += 1
        report.campaigns += 1
        report.drafts.append({
            "product": product.get("title"),
            "product_id": product.get("id"),
            "seo": seo,
            "campaign": campaign,
        })

    if out_file and report.drafts:
        try:
            Path(out_file).parent.mkdir(parents=True, exist_ok=True)
            Path(out_file).write_text(json.dumps(report.drafts, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        except OSError:
            pass

    if not dry_run:
        if not (shopify_api_key and shop_domain):
            report.error = "Live-Modus, aber Shopify-Domain/-Token fehlt — nichts veröffentlicht."
        elif not confirm_live:
            report.error = ("Live-Modus nicht bestätigt — setze JARVIS_STORE_CONFIRM_LIVE=1, "
                            "um Produkttexte tatsächlich zu veröffentlichen.")
        else:
            try:
                report.published = _publish_to_shopify(
                    report.drafts, shop_domain=shop_domain, access_token=shopify_api_key)
            except Exception as exc:  # noqa: BLE001
                report.error = f"Shopify-Publish fehlgeschlagen: {exc}"
    return report
