from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "blockchain"
    / "coin-deep-dive"
    / "scripts"
    / "coin_deep_dive.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("coin_deep_dive_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _research(**overrides):
    r = {
        "coin": "ex", "categories": ["defi", "layer-1"],
        "tokenomics": {"supply_cap_score": 8, "emission_score": 7, "allocation_score": 8},
        "utility": {"use_cases_score": 8, "revenue_flywheel_score": 6},
        "onchain": {"active_users_score": 7, "fees_score": 8},
        "team": {"founders_score": 8, "transparency_score": 9},
        "architecture": {"consensus_score": 8, "throughput_score": 7},
    }
    r.update(overrides)
    return r


def test_score_research_weights_dimensions():
    mod = load_module()
    s = mod.score_research(_research())
    assert s["raw_total"] > 5
    assert s["final_score"] > 5
    assert s["grade"] in {"A", "B", "C", "D", "F"}
    assert set(s["dimensions"]) == set(mod.RUBRIC)


def test_category_penalty_lowers_score():
    mod = load_module()
    good = mod.score_research(_research())["final_score"]
    meme = mod.score_research(_research(categories=["meme"]))["final_score"]
    assert meme < good


def test_missing_dimensions_flagged_and_penalized():
    mod = load_module()
    s = mod.score_research({"coin": "x", "categories": [], "tokenomics": {"a": 9}})
    assert "utility" in s["missing_dimensions"]
    assert s["final_score"] < 9


def test_grade_bands():
    mod = load_module()
    assert mod._grade(8.5) == "A"
    assert mod._grade(7.0) == "B"
    assert mod._grade(0.5) == "F"


def test_flags_low_float_and_no_github():
    mod = load_module()
    coin = {
        "market": {"max_supply": 1_000_000_000, "circulating_supply": 100_000_000,
                   "fdv_usd": 1e9, "ath_usd": 2},
        "links": {"github": []},
    }
    flags = mod._flags(coin, {"missing_dimensions": []})
    assert any("unlock overhang" in f for f in flags)
    assert any("No public GitHub" in f for f in flags)


def test_max_drawdown_no_flags_when_full_float():
    mod = load_module()
    coin = {"market": {"max_supply": 1e9, "circulating_supply": 1e9},
            "links": {"github": ["https://github.com/x"]}}
    flags = mod._flags(coin, {"missing_dimensions": ["team"]})
    assert not any("unlock overhang" in f for f in flags)
    assert any("Missing research dims" in f for f in flags)