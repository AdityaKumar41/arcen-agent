from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "marketing"
    / "marketing-automation-hub"
    / "scripts"
    / "marketing_hub.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("marketing_hub_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_plan_calendar_respects_weekdays_and_channels():
    mod = load_module()
    camp = {"name": "Q3", "channels": ["social", "newsletter"], "cadence": "weekdays"}
    items = mod.plan_calendar(camp, "2026-01-05", 14)  # 2 weeks
    dates = {i["date"] for i in items}
    # Jan 10/11 are Sat/Sun -> must not appear
    assert "2026-01-10" not in dates
    assert "2026-01-11" not in dates
    for it in items:
        assert it["status"] == "draft"
        assert it["channel"] in {"social", "newsletter"}


def test_plan_calendar_biweekly_is_sparse():
    mod = load_module()
    camp = {"name": "Q3", "channels": ["blog"], "cadence": "biweekly"}
    items = mod.plan_calendar(camp, "2026-01-01", 30)
    assert len(items) <= 4


def test_upsert_metric_merges_same_period():
    mod = load_module()
    d = {"campaigns": {}, "content": [], "metrics": [], "sequences": []}
    mod.upsert_metric(d, "social", "2026-01", 100, 10, 1)
    mod.upsert_metric(d, "social", "2026-01", 200, 20, 2)
    mod.upsert_metric(d, "email", "2026-01", 500, 50, 5)
    assert len(d["metrics"]) == 2
    social = next(m for m in d["metrics"] if m["channel"] == "social")
    assert social["impressions"] == 200


def test_ctr_calculation():
    mod = load_module()
    assert mod._ctr({"impressions": 0, "clicks": 10}) == 0.0
    assert mod._ctr({"impressions": 1000, "clicks": 50}) == 5.0


def test_performance_report_ranks_channels_and_insights():
    mod = load_module()
    d = {"campaigns": {}, "content": [], "metrics": [], "sequences": []}
    mod.upsert_metric(d, "social", "2026-01", 500000, 20000, 500, 2000, 15000)
    mod.upsert_metric(d, "email", "2026-01", 50000, 500, 50, 1000, 2000)
    rep = mod.performance_report(d)
    # social has higher ROAS (7.5 vs 2) -> best channel social
    assert rep["best_channel"] == "social"
    assert rep["totals"]["ctr_pct"] > 0
    assert rep["insights"]


def test_default_type_mapping():
    mod = load_module()
    assert mod._default_type("newsletter") == "email"
    assert mod._default_type("blog") == "article"
    assert mod._default_type("social") == "post"