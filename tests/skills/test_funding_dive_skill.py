from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "blockchain"
    / "funding-dive"
    / "scripts"
    / "funding_dive.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("funding_dive_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_vesting_schedule_tge_cliff_linear():
    mod = load_module()
    s = mod.vesting_schedule(1_000_000_000, 10, 6, 24, 12)
    assert s[0]["delta_tokens"] == 1e8  # 10% TGE
    assert s[5]["delta_tokens"] == 0.0  # within 6-mo cliff
    assert s[6]["delta_tokens"] > 0.0   # first linear unlock
    # by month 12: 10% + (90/24)*6 = 32.5%
    assert round(s[11]["cumulative_released_tokens"] / 1e9 * 100, 1) == 32.5


def test_vesting_never_exceeds_amount():
    mod = load_module()
    s = mod.vesting_schedule(100_000, 15, 6, 24, 48)
    assert all(x["cumulative_released_tokens"] <= 100_000 + 0.005 for x in s)


def test_schedule_for_model_defaults():
    mod = load_module()
    assert mod.schedule_for("SEED")["cliff"] == 6
    assert mod.schedule_for("unknown") == mod.STANDARD_VESTING["private"]


def test_analyze_project_concentration():
    mod = load_module()
    rounds = [
        {"project": "Acme", "date": "2024-01-01", "round": "seed",
         "amount_usd": 5_000_000, "investors": ["a16z", "Pantera"]},
        {"project": "Acme", "date": "2024-09-01", "round": "private",
         "amount_usd": 20_000_000, "investors": ["a16z", "Polychain"]},
    ]
    a = mod.analyze_project(rounds, "acme")
    assert a["total_raised_usd"] == 25_000_000
    assert a["round_count"] == 2
    assert a["top_investor"] == "a16z"
    assert a["latest_round"] == "private"


def test_analyze_project_missing():
    mod = load_module()
    try:
        mod.analyze_project([], "nope")
    except LookupError as e:
        assert "No funding rounds tracked" in str(e)
    else:
        raise AssertionError("expected LookupError")


def test_inflows_by_sector_aggregates():
    mod = load_module()
    rounds = [
        {"project": "A", "sector": "defi", "amount_usd": 3_000_000},
        {"project": "B", "sector": "defi", "amount_usd": 9_000_000},
        {"project": "C", "sector": "infra", "amount_usd": 2_000_000},
    ]
    out = mod.inflows_by_sector(rounds)
    assert out["total_raised_usd"] == 14_000_000
    assert out["trending_sector"] == "defi"