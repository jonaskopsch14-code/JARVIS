"""Offline tests for the Validator/QA-Agent and the supervisor refine loop."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.validator import (  # noqa: E402
    FAIL, OK, REFINE, Validator, validate_campaign, validate_seo,
)


def _good_seo():
    return {"seo_title": "Cargo Jeans – Denim Khaki | Fashion Aura",
            "meta_description": "Cargo Wide-Leg Jeans bei Fashion Aura. Khaki Denim. "
                                "Perfekt für Damen. Jetzt entdecken – schneller Versand.",
            "handle": "cargo-jeans", "tags": ["cargo", "jeans"]}


def _good_campaign():
    return {"headlines": ["Neu: Cargo Jeans", "Cargo Jeans bei Fashion Aura"],
            "primary_text": "Entdecke die Cargo Jeans.", "suggested_daily_budget_eur": 20.0,
            "status": "DRAFT"}


# --- content validators -----------------------------------------------------
def test_good_seo_has_no_errors():
    assert not [i for i in validate_seo(_good_seo()) if i.severity == "error"]


def test_seo_flags_overlong_title_and_meta():
    seo = _good_seo()
    seo["seo_title"] = "x" * 70
    seo["meta_description"] = "y" * 200
    fields = {i.field for i in validate_seo(seo) if i.severity == "error"}
    assert "seo_title" in fields and "meta_description" in fields


def test_seo_flags_bad_slug():
    seo = _good_seo(); seo["handle"] = "Cargo Jeans!"
    assert any(i.field == "handle" for i in validate_seo(seo))


def test_campaign_must_be_draft():
    camp = _good_campaign(); camp["status"] = "ACTIVE"
    assert any(i.field == "status" for i in validate_campaign(camp))


def test_campaign_flags_overlong_headline_and_budget():
    camp = _good_campaign()
    camp["headlines"] = ["x" * 50]
    camp["suggested_daily_budget_eur"] = 0
    fields = {i.field for i in validate_campaign(camp)}
    assert "headlines[0]" in fields and "suggested_daily_budget_eur" in fields


# --- Validator.review over a TaskResult -------------------------------------
class _Result:
    def __init__(self, name="store_optimizer", ok=True, drafts=None, metrics=None, summary=""):
        self.name = name; self.ok = ok; self.summary = summary
        self.metrics = metrics or {}
        self.artifacts = {"drafts": drafts} if drafts is not None else {}


def test_review_ok_for_clean_drafts():
    r = _Result(drafts=[{"seo": _good_seo(), "campaign": _good_campaign()}])
    v = Validator().review(r)
    assert v.status == OK and v.score == 100


def test_review_refine_for_bad_drafts():
    bad = {"seo": {**_good_seo(), "seo_title": "x" * 80},
           "campaign": {**_good_campaign(), "status": "ACTIVE"}}
    v = Validator().review(_Result(drafts=[bad]))
    assert v.status == REFINE and v.score < 100 and v.errors


def test_review_fail_when_task_not_ok():
    v = Validator().review(_Result(ok=False, summary="kaputt"))
    assert v.status == FAIL


# --- supervisor refine loop terminates and records verdict ------------------
def test_supervisor_qa_loop_terminates_and_annotates():
    import threading
    from main import NightShiftConfig, NightShiftSupervisor, NightShiftTask, TaskResult

    class BadStoreTask(NightShiftTask):
        name = "store_optimizer"
        runs = 0

        def run(self):
            BadStoreTask.runs += 1
            return TaskResult(
                name=self.name, ok=True, summary="x",
                artifacts={"drafts": [{"seo": {**_good_seo(), "seo_title": "x" * 90},
                                       "campaign": _good_campaign()}]})

    cfg = NightShiftConfig()
    cfg.max_refine = 2
    sup = NightShiftSupervisor(cfg, task_classes=[BadStoreTask])
    results = sup.run_tasks()
    assert len(results) == 1
    assert results[0].qa_status == REFINE
    # 1 initial run + up to max_refine retries → bounded (terminates).
    assert BadStoreTask.runs == 3


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
