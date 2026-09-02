from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "marketing"
    / "influencer-analyzer"
    / "scripts"
    / "influencer_analyzer.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("influencer_analyzer_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _creators():
    return [
        {"name": "A", "platform": "tiktok", "followers": 250000,
         "avg_engagement": 17500, "ctr": 3.2, "topics": "skincare",
         "est_cost": 900, "sample_posts": ["3 skincare mistakes that age you faster",
                                           "Why I stopped using chemical sunscreen"]},
        {"name": "B", "platform": "instagram", "followers": 80000,
         "avg_engagement": 2000, "ctr": 1.1, "topics": "tech",
         "est_cost": 300, "sample_posts": ["check out my setup"]},
        {"name": "C", "platform": "youtube", "followers": 5000,
         "avg_engagement": 2500, "ctr": 5.0, "topics": "skincare",
         "est_cost": 100, "sample_posts": ["Never make this face-mask mistake",
                                           "5 reasons your serum is failing"]},
    ]


def test_engagement_rate_computation():
    mod = load_module()
    assert mod._engagement_rate({"followers": 1000, "avg_engagement": 50}) == 5.0
    assert mod._engagement_rate({"followers": 0, "avg_engagement": 10}) == 0.0


def test_hook_scoring_counts_openers():
    mod = load_module()
    assert mod._score_hooks("3 skincare mistakes that age you faster") >= 1
    assert mod._score_hooks("check out my setup") == 0
    assert mod._score_hooks("Why I stopped using chemical sunscreen") >= 1


def test_extract_hook_takes_first_sentence():
    mod = load_module()
    assert mod._extract_hook("How to fix this. Then we talk price.") == "How to fix this."
    assert mod._extract_hook("") == ""
    assert mod._extract_hook("No punctuation here") == "No punctuation here"


def test_analyze_ranks_by_fit_and_engagement():
    mod = load_module()
    r = mod.analyze_creators(_creators(), "Hydra Face Serum", "skincare", 5000)
    assert r["creators_analyzed"] == 3
    ranked = r["ranked_shortlist"]
    # skincare creators with hooks outrank tech with no hooks
    assert ranked[0]["name"] in {"A", "C"}
    assert ranked[-1]["name"] == "B"
    assert ranked[0]["niche_fit_pct"] >= ranked[1]["niche_fit_pct"]


def test_analyze_builds_tiered_campaign():
    mod = load_module()
    r = mod.analyze_creators(_creators(), "Serum", "skincare", 5000)
    plan = r["campaign_plan"]
    assert len(plan) == 3
    assert plan[0]["role"] == "primary anchor"
    assert plan[1]["role"] == "co-signal"
    assert plan[2]["role"] == "amplifier"
    assert "deliverables" in plan[0]


def test_recommendation_when_no_creators():
    mod = load_module()
    r = mod.analyze_creators([], "Serum", "")
    assert "No creators provided" in r["recommendation"]


def test_main_analyze_json(capsys, tmp_path):
    mod = load_module()
    f = tmp_path / "creators.json"
    f.write_text(json.dumps({"product": "Serum", "creators": _creators()}))
    with patch.object(sys, "argv", ["prog", str(f), "--product", "Serum",
                                    "--niche", "skincare", "--json"]):
        # call the command fn directly via main
        pass
    rc = mod.main(["analyze", str(f), "--product", "Serum", "--niche", "skincare", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["product"] == "Serum"
    assert len(out["ranked_shortlist"]) == 3