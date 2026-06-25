"""
JARVIS V6 — Supplier crawl integration.

Implements the INTEGRATION POINT for SupplierCrawlTask.

  * extract_links()  / filter_suppliers()  — pure HTML parsing built on the
    standard library (html.parser), so the core is testable with zero
    third-party deps.
  * crawl()          — fetches the configured source URLs (httpx, optional
    'crawl' extra), extracts supplier candidates, deduplicates against a
    persisted "seen" set, and writes new finds to the dashboard.

Crawling is read-only, so there is no destructive action here. It is still
polite: short timeout, explicit User-Agent, bounded per-source link count, and
cooperative cancellation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

USER_AGENT = "JARVIS-V6-SupplierBot/1.0 (+fashion-aura; respectful crawler)"

#: Words that suggest a link points at a supplier/wholesaler/manufacturer.
SUPPLIER_HINTS = [
    "supplier", "lieferant", "wholesale", "großhandel", "grosshandel",
    "manufacturer", "hersteller", "vendor", "distributor", "vertrieb",
    "b2b", "bulk", "factory", "fabrik",
]


@dataclass
class SupplierLink:
    text: str
    url: str

    def key(self) -> str:
        return self.url.split("#", 1)[0].rstrip("/").lower()


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: Optional[str] = None
        self._buf: List[str] = []
        self.links: List[SupplierLink] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href = href
                self._buf = []

    def handle_data(self, data):
        if self._href is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            text = " ".join("".join(self._buf).split())
            self.links.append(SupplierLink(text=text, url=self._href))
            self._href = None
            self._buf = []


def extract_links(html: str, base_url: str = "") -> List[SupplierLink]:
    """Extract all anchors as (text, absolute-url). Pure, dependency-free."""
    parser = _LinkExtractor()
    parser.feed(html or "")
    out: List[SupplierLink] = []
    for link in parser.links:
        url = urljoin(base_url, link.url) if base_url else link.url
        if urlparse(url).scheme in ("http", "https"):
            out.append(SupplierLink(text=link.text, url=url))
    return out


def filter_suppliers(links: List[SupplierLink],
                     hints: Optional[List[str]] = None) -> List[SupplierLink]:
    """Keep only links whose text or URL hints at a supplier. Deduplicated."""
    hints = hints or SUPPLIER_HINTS
    seen: Set[str] = set()
    result: List[SupplierLink] = []
    for link in links:
        hay = f"{link.text} {link.url}".lower()
        if any(h in hay for h in hints):
            k = link.key()
            if k not in seen:
                seen.add(k)
                result.append(link)
    return result


def _load_seen(seen_file: Path) -> Set[str]:
    try:
        return set(json.loads(seen_file.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def _save(path: Path, data) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


@dataclass
class CrawlReport:
    found: int = 0
    new: int = 0
    sources_ok: int = 0
    sources_failed: int = 0
    items: List[dict] = field(default_factory=list)
    error: Optional[str] = None

    def as_metrics(self) -> Dict[str, int]:
        return {"suppliers_found": self.found, "suppliers_new": self.new,
                "sources_ok": self.sources_ok, "sources_failed": self.sources_failed}


def crawl(
    sources: List[str],
    *,
    seen_file: Optional[Path] = None,
    out_file: Optional[Path] = None,
    timeout: float = 10.0,
    max_links_per_source: int = 50,
    cancel=None,
) -> CrawlReport:
    """Fetch each source, extract + filter supplier links, dedupe, persist."""
    report = CrawlReport()
    if not sources:
        return report
    try:
        import httpx  # type: ignore
    except Exception as exc:  # noqa: BLE001
        report.error = f"httpx nicht installiert ({exc}); pip install -e '.[crawl]'"
        return report

    seen = _load_seen(seen_file) if seen_file else set()
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
        for src in sources:
            if cancel is not None and cancel.is_set():
                break
            try:
                resp = client.get(src)
                resp.raise_for_status()
            except Exception:  # noqa: BLE001 - one bad source must not abort the crawl
                report.sources_failed += 1
                continue
            report.sources_ok += 1
            links = filter_suppliers(extract_links(resp.text, base_url=src))
            for link in links[:max_links_per_source]:
                report.found += 1
                k = link.key()
                if k in seen:
                    continue
                seen.add(k)
                report.new += 1
                report.items.append({"name": link.text or link.url, "url": link.url, "source": src})

    if seen_file:
        _save(Path(seen_file), sorted(seen))
    if out_file and report.items:
        _save(Path(out_file), report.items)
    return report
