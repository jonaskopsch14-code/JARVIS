"""Thin client for the CJ Dropshipping Open API (API 2.0).

Section 4.1 of the masterprompt. Endpoints and field names are declared as
constants at the top so they are trivial to correct against the live docs at
https://developers.cjdropshipping.com — CJ changes response fields over time
(e.g. `deliveryTime` was added to the product list), so treat the published
docs as the source of truth, not this file.

Auth: getAccessToken returns a token that CJ rate-limits (1 fresh token / 5 min,
token valid ~15 days). We cache it on disk so repeated runs during development
don't trip the limit.

No credentials are ever hardcoded. Set CJ_EMAIL and CJ_API_KEY in the
environment (see .env.example).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

BASE = os.environ.get("CJ_API_BASE", "https://developers.cjdropshipping.com/api2.0/v1")

# Endpoint paths — verify against live docs before a production run.
EP_AUTH = "/authentication/getAccessToken"
EP_PRODUCT_LIST = "/product/list"
EP_PRODUCT_QUERY = "/product/query"
EP_INVENTORY = "/product/stock/queryByVid"

TOKEN_CACHE = Path(__file__).with_name(".cj_token.json")
REQUEST_TIMEOUT = 30
MAX_RETRIES = 4


class CJError(RuntimeError):
    pass


class CJClient:
    def __init__(self, email: str | None = None, api_key: str | None = None):
        self.email = email or os.environ.get("CJ_EMAIL")
        self.api_key = api_key or os.environ.get("CJ_API_KEY")
        if not self.email or not self.api_key:
            raise CJError(
                "Set CJ_EMAIL and CJ_API_KEY in the environment "
                "(generate the API key in CJ account > API / Developer)."
            )
        self._token: str | None = None
        self._session = requests.Session()

    # --- auth -----------------------------------------------------------------
    def _load_cached_token(self) -> str | None:
        if not TOKEN_CACHE.exists():
            return None
        try:
            data = json.loads(TOKEN_CACHE.read_text())
        except (ValueError, OSError):
            return None
        # Refresh a day before CJ's ~15-day expiry to be safe.
        if data.get("email") == self.email and data.get("expires_at", 0) > time.time() + 86400:
            return data.get("token")
        return None

    def _save_cached_token(self, token: str) -> None:
        try:
            TOKEN_CACHE.write_text(json.dumps({
                "email": self.email,
                "token": token,
                "expires_at": time.time() + 14 * 86400,
            }))
            TOKEN_CACHE.chmod(0o600)
        except OSError:
            pass  # cache is best-effort

    def authenticate(self) -> str:
        cached = self._load_cached_token()
        if cached:
            self._token = cached
            return cached
        resp = self._session.post(
            BASE + EP_AUTH,
            json={"email": self.email, "password": self.api_key},
            timeout=REQUEST_TIMEOUT,
        )
        payload = _json(resp)
        token = (payload.get("data") or {}).get("accessToken")
        if not token:
            raise CJError(f"getAccessToken failed: {payload.get('message', resp.text)}")
        self._token = token
        self._save_cached_token(token)
        return token

    def _headers(self) -> dict:
        if not self._token:
            self.authenticate()
        return {"CJ-Access-Token": self._token, "Content-Type": "application/json"}

    def _get(self, path: str, params: dict) -> dict:
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._session.get(
                    BASE + path, params=params, headers=self._headers(),
                    timeout=REQUEST_TIMEOUT,
                )
                payload = _json(resp)
                # CJ code 1600xxx == rate limit; back off and retry.
                if str(payload.get("code")) in ("1600200", "1600100"):
                    raise CJError(f"rate limited: {payload.get('message')}")
                return payload
            except (requests.RequestException, CJError) as exc:
                last_exc = exc
                time.sleep(2 ** attempt)
        raise CJError(f"GET {path} failed after {MAX_RETRIES} tries: {last_exc}")

    # --- product interfaces ---------------------------------------------------
    def search(self, keyword: str, page_size: int = 40, max_pages: int = 1) -> list[dict]:
        out: list[dict] = []
        for page in range(1, max_pages + 1):
            payload = self._get(EP_PRODUCT_LIST, {
                "pageNum": page, "pageSize": page_size, "productNameEn": keyword,
            })
            rows = ((payload.get("data") or {}).get("list")) or []
            out.extend(rows)
            if len(rows) < page_size:
                break
        return out

    def product_detail(self, pid: str) -> dict:
        payload = self._get(EP_PRODUCT_QUERY, {"pid": pid})
        return payload.get("data") or {}

    def inventory(self, vid: str) -> list[dict]:
        """Storage interface — warehouse location(s) per listing (Section 4.1)."""
        payload = self._get(EP_INVENTORY, {"vid": vid})
        return payload.get("data") or []


def _json(resp: requests.Response) -> dict:
    try:
        return resp.json()
    except ValueError as exc:
        raise CJError(f"non-JSON response ({resp.status_code}): {resp.text[:200]}") from exc


# --- normalisation ------------------------------------------------------------
# Map CJ's raw fields onto the flat schema scoring.py expects. CJ field names
# drift; adjust the .get() keys here rather than touching scoring.py.

def _to_float(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def normalise_product(raw: dict, detail: dict | None = None, warehouses: list[str] | None = None) -> dict:
    detail = detail or {}
    desc = detail.get("description") or raw.get("description") or ""
    sell_price = raw.get("sellPrice") or detail.get("sellPrice")
    # sellPrice can be a "min--max" range string.
    if isinstance(sell_price, str) and "--" in sell_price:
        sell_price = sell_price.split("--")[0]
    weight = raw.get("packWeight") or detail.get("packWeight") or raw.get("productWeight")
    return {
        "product_id": raw.get("pid") or raw.get("productId") or detail.get("pid"),
        "title": raw.get("productNameEn") or raw.get("productName") or detail.get("productNameEn", ""),
        "description": desc,
        "keywords": (raw.get("productKeyEn") or "").split(",") if raw.get("productKeyEn") else [],
        "rating": _to_float(raw.get("productScore") or detail.get("score")),
        "orders": int(_to_float(raw.get("listedNum") or raw.get("saleStatus") or 0) or 0),
        "supplier_cost": _to_float(sell_price),
        "package_weight_g": _to_float(weight),
        "warehouses": warehouses or _extract_warehouses(raw, detail),
        "cj_url": f"https://cjdropshipping.com/product-detail.html?id={raw.get('pid', '')}",
        "image": raw.get("productImage") or detail.get("productImage"),
    }


def _extract_warehouses(raw: dict, detail: dict) -> list[str]:
    whs: list[str] = []
    for src in (detail.get("variants") or []):
        area = src.get("variantWarehouse") or src.get("area")
        if area:
            whs.append(str(area))
    if not whs:
        area = raw.get("warehouse") or detail.get("entryCode")
        if area:
            whs.append(str(area))
    return whs
