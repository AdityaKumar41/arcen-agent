from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "business"
    / "ecommerce-optimizer"
    / "scripts"
    / "ecommerce_optimizer.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("ecommerce_optimizer_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _store(**overrides):
    m = {"monthly_visitors": 50000, "monthly_carts": 5200, "monthly_orders": 2700,
         "monthly_revenue": 86400, "products": 400, "skus": 780,
         "avg_inventory_value": 60000, "slow_skus": 220, "fast_skus": 130,
         "gross_margin": 0.42, "repeat_purchase_rate_pct": 24, "return_rate_pct": 9,
         "price_elasticity": 1.2}
    m.update(overrides)
    return m


def test_diagnose_computes_funnel():
    mod = load_module()
    d = mod.diagnose(_store())
    assert round(d["conversion_rate_pct"], 2) == 5.4
    assert round(d["add_to_cart_rate_pct"], 2) == 10.4
    assert round(d["cart_to_order_pct"], 2) == 51.92
    assert round(d["aov"], 2) == 32.0


def test_diagnose_low_conversion_flags_issue():
    mod = load_module()
    d = mod.diagnose(_store(monthly_orders=500))
    assert any("Conversion rate is low" in i for i in d["issues"])
    assert d["severity"] in {"critical", "watch"}


def test_inventory_turnover_computed():
    mod = load_module()
    d = mod.diagnose(_store())
    # COGS = 86400*(1-0.42)=50112 ; turnover = 50112/60000 = 0.835..
    assert d["inventory_turnover_x"] is not None
    assert round(d["inventory_turnover_x"], 2) == 0.84


def test_price_recommendations_include_threshold():
    mod = load_module()
    d = mod.diagnose(_store())
    recs = mod.price_recommendations(_store(), d)
    assert any("threshold free shipping" in r["action"] for r in recs)


def test_cro_plan_healthy_fallback():
    mod = load_module()
    d = mod.diagnose(_store())
    plan = mod.cro_plan(d)
    assert plan and isinstance(plan[0], str)


def test_scaling_plan_gates_on_conversion():
    mod = load_module()
    d = mod.diagnose(_store(monthly_orders=500))
    plan = mod.scaling_plan(_store(monthly_orders=500), d)
    assert any("Fix conversion first" in p for p in plan)