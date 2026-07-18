"""
JARVIS V6 — Browser task execution (generic, not site-specific).

A small Playwright-backed toolset the ReAct agent can drive step by step to
carry out real web tasks ("leg mir das Weider Protein bei Amazon in den
Warenkorb"). The agent plans the steps itself — search → open result → add to
cart — so there is **no hard-coded Amazon (or any) script** here.

Five tools, matching the spec:

    browser_open(url)
    browser_click(description)          # find by visible text / role, not CSS
    browser_type(description, text)
    browser_read(description=None)      # return page text / structure
    browser_screenshot()               # fallback when text selectors fall short

Safety (the important part):

  * Reversible, no-money actions — open, read, search, fill a cart, type into a
    search box — run automatically (``read`` / ``suggest`` tier).
  * Any click that completes a purchase or moves money — "Jetzt kaufen", "Zur
    Kasse", "Checkout", "Bezahlen", "Order now" — is classified ``spend`` and
    routed through the :class:`PermissionManager`, so JARVIS asks Jonas first.
    This holds no matter what triggered the task.

Design for testability: the browser itself lives behind a tiny ``Session``
protocol (open/click/type/read/screenshot/close). The real one is
:class:`PlaywrightSession` (lazy-imports Playwright — optional ``browser``
extra); tests inject a fake session and assert the tier gating without a
browser. The tier classification is a pure function, tested directly.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Protocol

from .permissions import PermissionManager, Tier

LOG = logging.getLogger("jarvis_v6.browser")


# ---------------------------------------------------------------------------
# Action classification — pure, dependency-free, unit-tested.
# ---------------------------------------------------------------------------
# Phrases that mean "this click spends money / completes a purchase". Kept
# generic (German + English) so it works across shops without site-specific
# logic. Matched against the normalised element description.
SPEND_PHRASES = [
    "jetzt kaufen", "kaufen", "buy now", "buy", "place order", "order now",
    "bestellung aufgeben", "kostenpflichtig bestellen", "zahlungspflichtig bestellen",
    "zur kasse", "kasse", "checkout", "check out", "proceed to checkout",
    "bezahlen", "jetzt bezahlen", "pay now", "pay", "complete purchase",
    "complete order", "confirm purchase", "confirm and pay", "submit payment",
    "kauf abschliessen", "bestellung abschliessen", "purchase",
]

# Phrases that look money-ish but are explicitly the reversible cart step, which
# the spec wants to stay automatic. Checked first so "in den Warenkorb" never
# trips the "kaufen"-in-substring spend rule.
CART_PHRASES = [
    "in den warenkorb", "zum warenkorb hinzufuegen", "warenkorb",
    "add to cart", "add to basket", "add to bag", "in den einkaufswagen",
    "merken", "auf die wunschliste", "wishlist", "save for later",
]


def _norm(text: Optional[str]) -> str:
    """Lowercase + fold umlauts so matching is robust to messy descriptions."""
    text = (text or "").lower()
    for src, dst in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text).strip()


def classify_click_tier(description: str) -> Tier:
    """Classify a click on ``description`` into a permission tier.

    Returns :attr:`Tier.SPEND` for checkout/payment actions, otherwise
    :attr:`Tier.SUGGEST` (an ordinary, reversible interaction). Cart / wishlist
    actions are deliberately kept as SUGGEST even though they contain "kaufen".
    """
    text = _norm(description)
    if any(p in text for p in CART_PHRASES):
        return Tier.SUGGEST
    if any(p in text for p in SPEND_PHRASES):
        return Tier.SPEND
    return Tier.SUGGEST


# ---------------------------------------------------------------------------
# Session protocol + the real Playwright implementation.
# ---------------------------------------------------------------------------
class Session(Protocol):
    """Minimal browser surface the tools need. Kept tiny so a fake is trivial."""

    def open(self, url: str) -> str: ...
    def click(self, description: str) -> str: ...
    def type(self, description: str, text: str) -> str: ...
    def read(self, description: Optional[str] = None) -> str: ...
    def screenshot(self, path: Optional[str] = None) -> str: ...
    def close(self) -> None: ...


class PlaywrightSession:
    """Real browser session backed by Playwright (sync API).

    Element location prefers *visible text / role* over brittle CSS selectors,
    exactly as the spec asks: we try an exact-then-substring text match, then a
    button/link role with that name, before giving up.

    Requires the optional ``browser`` extra::

        pip install -e ".[browser]"
        playwright install chromium
    """

    def __init__(self, headless: bool = True):
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Playwright ist nicht installiert; pip install -e '.[browser]' "
                "und danach 'playwright install chromium'."
            ) from exc
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        self._page = self._pw_new_page()

    def _pw_new_page(self):
        page = self._browser.new_page()
        page.set_default_timeout(15000)
        return page

    # -- locate-by-text/role -------------------------------------------------
    def _locate(self, description: str):
        page = self._page
        # 1) exact visible text, 2) substring text, 3) button, 4) link.
        candidates = [
            lambda: page.get_by_text(description, exact=True),
            lambda: page.get_by_text(description, exact=False),
            lambda: page.get_by_role("button", name=description),
            lambda: page.get_by_role("link", name=description),
            lambda: page.get_by_placeholder(description),
            lambda: page.get_by_label(description),
        ]
        for make in candidates:
            try:
                loc = make().first
                if loc.count() > 0:
                    return loc
            except Exception:  # noqa: BLE001 - try the next strategy
                continue
        # Fall back to the first strategy's locator so the caller gets a clear
        # Playwright timeout error naming the description.
        return page.get_by_text(description, exact=False).first

    # -- Session protocol ----------------------------------------------------
    def open(self, url: str) -> str:
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
            url = "https://" + url
        self._page.goto(url, wait_until="domcontentloaded")
        return self._page.title() or url

    def click(self, description: str) -> str:
        self._locate(description).click()
        return f"geklickt: {description}"

    def type(self, description: str, text: str) -> str:
        loc = self._locate(description)
        loc.fill(text)
        return f"'{text}' eingegeben in: {description}"

    def read(self, description: Optional[str] = None) -> str:
        if description:
            try:
                return self._locate(description).inner_text()
            except Exception:  # noqa: BLE001 - fall back to whole-page text
                pass
        try:
            return self._page.inner_text("body")
        except Exception:  # noqa: BLE001
            return self._page.content()

    def screenshot(self, path: Optional[str] = None) -> str:
        path = path or "jarvis_browser.png"
        self._page.screenshot(path=path, full_page=True)
        return path

    def close(self) -> None:
        for closer in (getattr(self._browser, "close", None),
                       getattr(self._pw, "stop", None)):
            try:
                if closer:
                    closer()
            except Exception:  # noqa: BLE001 - best effort teardown
                pass


# ---------------------------------------------------------------------------
# Tool result + the toolset the ReAct loop calls.
# ---------------------------------------------------------------------------
@dataclass
class ToolResult:
    ok: bool
    tool: str
    detail: str
    tier: str = Tier.READ.value
    blocked: bool = False            # True => refused by the permission gate
    needs_confirmation: bool = False

    def as_dict(self) -> dict:
        return {
            "ok": self.ok, "tool": self.tool, "detail": self.detail,
            "tier": self.tier, "blocked": self.blocked,
            "needs_confirmation": self.needs_confirmation,
        }


SessionFactory = Callable[[], Session]


class BrowserTools:
    """The five browser tools, wired to a :class:`PermissionManager`.

    The session is created lazily on first use (so importing this module — and
    booting JARVIS — never needs a browser). Pass ``session`` directly (a fake)
    in tests, or a ``session_factory`` to control how the real one is built.
    """

    def __init__(self, permissions: Optional[PermissionManager] = None, *,
                 session: Optional[Session] = None,
                 session_factory: Optional[SessionFactory] = None,
                 headless: bool = True):
        self.permissions = permissions or PermissionManager()
        self._session = session
        self._factory = session_factory or (lambda: PlaywrightSession(headless=headless))

    # -- lifecycle -----------------------------------------------------------
    def _ensure(self) -> Session:
        if self._session is None:
            self._session = self._factory()
        return self._session

    def close(self) -> None:
        if self._session is not None:
            try:
                self._session.close()
            finally:
                self._session = None

    def _guard(self, tool: str, tier: Tier, description: str):
        """Run the permission gate; return a blocking ToolResult if refused."""
        decision = self.permissions.check(tier, f"{tool}: {description}")
        if not decision.allowed:
            LOG.info("browser action blocked: %s", decision.reason)
            return ToolResult(ok=False, tool=tool, detail=decision.reason,
                              tier=tier.value, blocked=True, needs_confirmation=True)
        return None

    def _run(self, tool: str, tier: Tier, description: str, fn) -> ToolResult:
        blocked = self._guard(tool, tier, description)
        if blocked is not None:
            return blocked
        try:
            detail = fn()
        except Exception as exc:  # noqa: BLE001 - surface, never crash the loop
            LOG.warning("browser %s failed: %s", tool, exc)
            return ToolResult(ok=False, tool=tool, detail=f"Fehler: {exc}", tier=tier.value)
        return ToolResult(ok=True, tool=tool, detail=str(detail), tier=tier.value,
                          needs_confirmation=(tier in (Tier.SEND, Tier.SPEND,
                                                       Tier.DELETE, Tier.PUBLISH)))

    # -- the tools -----------------------------------------------------------
    def browser_open(self, url: str) -> ToolResult:
        return self._run("browser_open", Tier.READ, url,
                         lambda: self._ensure().open(url))

    def browser_click(self, description: str) -> ToolResult:
        tier = classify_click_tier(description)
        return self._run("browser_click", tier, description,
                         lambda: self._ensure().click(description))

    def browser_type(self, description: str, text: str) -> ToolResult:
        return self._run("browser_type", Tier.SUGGEST, description,
                         lambda: self._ensure().type(description, text))

    def browser_read(self, description: Optional[str] = None) -> ToolResult:
        label = description or "ganze Seite"
        return self._run("browser_read", Tier.READ, label,
                         lambda: self._ensure().read(description))

    def browser_screenshot(self, path: Optional[str] = None) -> ToolResult:
        return self._run("browser_screenshot", Tier.READ, path or "screenshot",
                         lambda: self._ensure().screenshot(path))

    # -- registry for the ReAct loop ----------------------------------------
    def as_tools(self) -> dict:
        """Return {name: callable} so the agent's tool registry can mount them."""
        return {
            "browser_open": self.browser_open,
            "browser_click": self.browser_click,
            "browser_type": self.browser_type,
            "browser_read": self.browser_read,
            "browser_screenshot": self.browser_screenshot,
        }
