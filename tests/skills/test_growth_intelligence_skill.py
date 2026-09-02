from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "business"
    / "growth-intelligence"
    / "scripts"
    / "growth_intelligence.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("growth_intelligence_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _metrics(**overrides):
    m = {"customers": 1200, "new_customers_monthly": 60,
         "churned_customers_monthly": 18, "monthly_revenue": 96000,
         "gross_margin": 0.8, "monthly_marketing_spend": 15000,
         "monthly_sales_spend": 5000, "nrr": 108}
    m.update(overrides)
    return m


def test_compute_unit_economics_healthy():
    mod = load_module()
    e = mod.compute_unit_economics(_metrics())
    assert round(e["arpu"], 2) == 80.0
    assert e["cac"] == 333.33
    assert round(e["ltv_cac_ratio"], 2) == 12.8
    assert round(e["payback_months"], 1) == 5.2


def test_churn_high_gives_critical_retention():
    mod = load_module()
    e = mod.compute_unit_economics(_metrics(churned_customers_monthly=120,
                                            new_customers_monthly=30))
    h = mod.health_report(e)
    assert h["overall"] == "critical"
    retention = next(f for f in h["flags"] if f["domain"] == "retention")
    assert retention["status"] == "critical"


def test_healthy_case_overall_healthy():
    mod = load_module()
    e = mod.compute_unit_economics(_metrics())
    h = mod.health_report(e)
    assert any(f["domain"] == "unit-economics" and f["status"] == "healthy" for f in h["flags"])


def test_recommendations_follow_critical_flags():
    mod = load_module()
    e = mod.compute_unit_economics(_metrics(churned_customers_monthly=120,
                                            new_customers_monthly=30))
    h = mod.health_report(e)
    recs = mod.recommendations(e, h)
    assert any("churn" in r.lower() for r in recs)


def test_no_double_count_cac_warning_when_payback_short():
    mod = load_module()
    e = mod.compute_unit_economics(_metrics())
    h = mod.health_report(e)
    recs = mod.recommendations(e, h)
    assert not any("CAC exceeds 3x" in r for r in recs)


def test_build_plan_has_three_phases():
    mod = load_module()
    plan = mod.build_plan(["fix retention"])
    assert len(plan) == 3
    assert "stabilization" in plan[0]["phase"]


def test_missing_revenue_defaults_to_derived():
    mod = load_module()
    e = mod.compute_unit_economics({**_metrics(), "arr": 1_152_000, "monthly_revenue": 0})
    # ARR/12 = 96000
    assert round(e["arpu"], 2) == 80.0