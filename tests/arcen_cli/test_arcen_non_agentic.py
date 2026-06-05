"""Tests for the Arcen-3/4 non-agentic warning detector.

Prior to this check, the warning fired on any model whose name contained
``"arcen"`` anywhere (case-insensitive). That false-positived on unrelated
local Modelfiles such as ``arcen-brain:qwen3-14b-ctx16k`` — a tool-capable
Qwen3 wrapper that happens to live under the "arcen" tag namespace.

``is_arcen_non_agentic_model`` should only match the actual ArcenPay
Arcen-3 / Arcen-4 chat family.
"""

from __future__ import annotations

import pytest

from arcen_cli.model_switch import (
    _ARCEN_MODEL_WARNING,
    _check_arcen_model_warning,
    is_arcen_non_agentic_model,
)


@pytest.mark.parametrize(
    "model_name",
    [
        "ArcenPay/Arcen-3-Llama-3.1-70B",
        "ArcenPay/Arcen-3-Llama-3.1-405B",
        "arcen-3",
        "Arcen-3",
        "arcen-4",
        "arcen-4-405b",
        "arcen_4_70b",
        "openrouter/arcen3:70b",
        "arcen-4-405b",
        "ArcenPay/Arcen3",
        "arcen-3.1",
    ],
)
def test_matches_real_arcen_chat_models(model_name: str) -> None:
    assert is_arcen_non_agentic_model(model_name), (
        f"expected {model_name!r} to be flagged as Arcen 3/4"
    )
    assert _check_arcen_model_warning(model_name) == _ARCEN_MODEL_WARNING


@pytest.mark.parametrize(
    "model_name",
    [
        # Kyle's local Modelfile — qwen3:14b under a custom tag
        "arcen-brain:qwen3-14b-ctx16k",
        "arcen-brain:qwen3-14b-ctx32k",
        "arcen-honcho:qwen3-8b-ctx8k",
        # Plain unrelated models
        "qwen3:14b",
        "qwen3-coder:30b",
        "qwen2.5:14b",
        "claude-opus-4-6",
        "anthropic/claude-sonnet-4.5",
        "gpt-5",
        "openai/gpt-4o",
        "google/gemini-2.5-flash",
        "deepseek-chat",
        # Non-chat Arcen models we don't warn about
        "arcen-llm-2",
        "arcen2-pro",
        "arcen-2-mistral",
        # Edge cases
        "",
        "arcen",  # bare "arcen" isn't the 3/4 family
        "arcen-brain",
        "brain-arcen-3-impostor",  # "3" not preceded by /: boundary
    ],
)
def test_does_not_match_unrelated_models(model_name: str) -> None:
    assert not is_arcen_non_agentic_model(model_name), (
        f"expected {model_name!r} NOT to be flagged as Arcen 3/4"
    )
    assert _check_arcen_model_warning(model_name) == ""


def test_none_like_inputs_are_safe() -> None:
    assert is_arcen_non_agentic_model("") is False
    # Defensive: the helper shouldn't crash on None-ish falsy input either.
    assert _check_arcen_model_warning("") == ""
