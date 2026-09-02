from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "marketing"
    / "b2b-lead-generation"
    / "scripts"
    / "b2b_lead_gen.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("b2b_lead_gen_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_email_ok():
    mod = load_module()
    v = mod.validate_email("jane.doe@acme.io")
    assert v["syntax_ok"] is True
    assert v["verdict"] == "ok"
    assert v["disposable"] is False
    assert v["role_account"] is False


def test_validate_email_disposable():
    mod = load_module()
    assert mod.validate_email("x@mailinator.com")["verdict"] == "block_disposable"


def test_validate_email_role_and_invalid():
    mod = load_module()
    assert mod.validate_email("info@acme.io")["verdict"] == "flag_role"
    assert mod.validate_email("nope")["verdict"] == "invalid"


def test_lead_score_hot_and_cold():
    mod = load_module()
    hot = mod.lead_score({"employees": 800, "funding_usd": 15000000,
                          "intent": "requested demo", "email_verified": "ok"})
    assert hot["bucket"] in {"hot", "warm"}
    cold = mod.lead_score({"employees": 2, "funding_usd": 0, "intent": "",
                           "email_verified": "invalid"})
    assert cold["bucket"] == "cold"


def test_lead_score_bad_contact_penalizes():
    mod = load_module()
    s = mod.lead_score({"employees": 800, "email_verified": "invalid"})
    assert any("bad contact" in r for r in s["reasons"])


def test_build_sequence_cadence_and_personalization():
    mod = load_module()
    seq = mod.build_sequence({"name": "Jane Roe", "company": "Acme",
                              "role": "CTO", "pain_point": "slow procurement"}, touches=5)
    assert len(seq) == 5
    assert seq[0]["day_offset"] == 0
    assert seq[1]["day_offset"] > seq[0]["day_offset"]
    assert any("Acme" in h for h in seq[0]["personalization_hooks"])
    assert "Quick idea for Acme" == seq[0]["subject_template"]


def test_first_name_extraction():
    mod = load_module()
    assert mod._first_name("Jane Roe") == "Jane"
    assert mod._first_name("") == "there"