"""Offline tests for the tier permission system and the browser toolset.

No browser and no network: the browser session is a tiny fake, so we verify the
tier classification and the permission gate — the safety-critical behaviour that
the spec's acceptance criteria hinge on (cart = automatic, checkout = confirm).
Standard library only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.permissions import (  # noqa: E402
    AUTO_TIERS, CONFIRM_TIERS, Decision, PermissionDenied, PermissionManager, Tier,
)
from integrations.browser import (  # noqa: E402
    BrowserTools, ToolResult, classify_click_tier,
)


# ---------------------------------------------------------------------------
# Permission manager.
# ---------------------------------------------------------------------------
def test_auto_tiers_run_without_confirmation():
    pm = PermissionManager()  # no confirm_fn wired
    for tier in AUTO_TIERS:
        d = pm.check(tier, "irgendeine Leseaktion")
        assert d.allowed and not d.needed_confirmation


def test_confirm_tiers_refused_without_confirm_fn():
    pm = PermissionManager()  # nothing wired => safe default is refuse
    for tier in CONFIRM_TIERS:
        d = pm.check(tier, "gefährliche Aktion")
        assert not d.allowed and d.needed_confirmation


def test_confirm_fn_can_allow_and_deny():
    calls = []
    yes = PermissionManager(confirm_fn=lambda t, a: calls.append((t, a)) or True)
    assert yes.check(Tier.SPEND, "Jetzt kaufen").allowed
    assert calls and calls[0][0] == Tier.SPEND

    no = PermissionManager(confirm_fn=lambda t, a: False)
    assert not no.check(Tier.SPEND, "Jetzt kaufen").allowed


def test_auto_approve_bypasses_prompt():
    pm = PermissionManager(auto_approve=True)
    assert pm.check(Tier.PUBLISH, "veröffentlichen").allowed


def test_require_raises_on_refusal():
    pm = PermissionManager()
    try:
        pm.require(Tier.DELETE, "alles löschen")
    except PermissionDenied as exc:
        assert isinstance(exc.decision, Decision)
    else:
        assert False, "PermissionDenied wurde nicht ausgelöst"


def test_confirm_fn_exception_is_treated_as_refusal():
    def boom(t, a):
        raise RuntimeError("prompt kaputt")
    pm = PermissionManager(confirm_fn=boom)
    assert not pm.check(Tier.SEND, "senden").allowed


# ---------------------------------------------------------------------------
# Click classification — the crux of the spend gate.
# ---------------------------------------------------------------------------
def test_cart_and_search_are_suggest_tier():
    for desc in ["In den Warenkorb", "Add to cart", "Suchen", "Ergebnis öffnen",
                 "Auf die Wunschliste", "Menge erhöhen"]:
        assert classify_click_tier(desc) == Tier.SUGGEST


def test_checkout_and_payment_are_spend_tier():
    for desc in ["Jetzt kaufen", "Zur Kasse", "Checkout", "Bezahlen",
                 "Zahlungspflichtig bestellen", "Buy now", "Place order",
                 "Kauf abschließen"]:
        assert classify_click_tier(desc) == Tier.SPEND


# ---------------------------------------------------------------------------
# Browser tools with a fake session (no real browser).
# ---------------------------------------------------------------------------
class FakeSession:
    def __init__(self):
        self.events = []

    def open(self, url):
        self.events.append(("open", url)); return f"Titel von {url}"

    def click(self, description):
        self.events.append(("click", description)); return f"geklickt: {description}"

    def type(self, description, text):
        self.events.append(("type", description, text)); return "ok"

    def read(self, description=None):
        self.events.append(("read", description)); return "Seiteninhalt"

    def screenshot(self, path=None):
        self.events.append(("screenshot", path)); return path or "shot.png"

    def close(self):
        self.events.append(("close",))


def _tools(confirm=None, auto_approve=False):
    fake = FakeSession()
    pm = PermissionManager(confirm_fn=confirm, auto_approve=auto_approve)
    return BrowserTools(pm, session=fake), fake


def test_cart_click_runs_automatically():
    # Acceptance criterion 1: add-to-cart needs no confirmation.
    tools, fake = _tools()  # nothing wired => confirm tiers would be refused
    res = tools.browser_click("In den Warenkorb")
    assert isinstance(res, ToolResult)
    assert res.ok and not res.blocked and res.tier == Tier.SUGGEST.value
    assert ("click", "In den Warenkorb") in fake.events


def test_checkout_click_blocked_without_confirmation():
    # Acceptance criterion 2: a checkout step must stop and ask.
    tools, fake = _tools()  # no confirm_fn => refuse
    res = tools.browser_click("Jetzt kaufen")
    assert not res.ok and res.blocked and res.needs_confirmation
    assert res.tier == Tier.SPEND.value
    # The click must NOT have reached the browser.
    assert all(ev[0] != "click" for ev in fake.events)


def test_checkout_click_runs_when_confirmed():
    tools, fake = _tools(confirm=lambda t, a: True)
    res = tools.browser_click("Zur Kasse")
    assert res.ok and not res.blocked and res.tier == Tier.SPEND.value
    assert ("click", "Zur Kasse") in fake.events


def test_open_read_type_are_automatic():
    tools, fake = _tools()
    assert tools.browser_open("example.com").ok
    assert tools.browser_type("Suchfeld", "Weider Protein").ok
    assert tools.browser_read().ok
    assert tools.browser_screenshot().ok
    kinds = [ev[0] for ev in fake.events]
    assert kinds == ["open", "type", "read", "screenshot"]


def test_session_error_is_surfaced_not_raised():
    class Boom(FakeSession):
        def open(self, url):
            raise RuntimeError("navigation failed")
    pm = PermissionManager()
    tools = BrowserTools(pm, session=Boom())
    res = tools.browser_open("example.com")
    assert not res.ok and "Fehler" in res.detail and not res.blocked


def test_as_tools_exposes_five_callables():
    tools, _ = _tools()
    reg = tools.as_tools()
    assert set(reg) == {"browser_open", "browser_click", "browser_type",
                        "browser_read", "browser_screenshot"}
    assert all(callable(fn) for fn in reg.values())


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
