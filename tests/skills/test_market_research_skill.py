from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "research"
    / "market-research-engine"
    / "scripts"
    / "market_research.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("market_research_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_sentiment_positive_negative_mixed():
    mod = load_module()
    assert mod.sentiment("Strong growth, record profits")["label"] == "positive"
    assert mod.sentiment("Layoffs, lawsuit, plunge")["label"] == "negative"
    assert mod.sentiment("meetings happened on tuesday")["label"] == "neutral"


def test_sentiment_counts():
    mod = load_module()
    s = mod.sentiment("Strong growth and strong profits")
    assert s["positive"] == 4  # strong + strong + growth + profits
    assert s["negative"] == 0


def test_fetch_rss_parses_items():
    mod = load_module()
    rss = (
        '<?xml version="1.0"?><rss><channel>'
        "<item><title>Big win for crypto</title><link>https://ex.com/a</link>"
        "<description>Market surge and progress</description>"
        "<pubDate>Mon, 01 Jan 2026</pubDate></item>"
        "</channel></rss>"
    )
    with patch.object(mod, "_get", return_value=rss.encode()):
        items = mod.fetch_rss("https://feed", limit=10)
    assert items[0]["title"] == "Big win for crypto"
    assert items[0]["link"] == "https://ex.com/a"


def test_token_freq_drops_stopwords():
    mod = load_module()
    freq = mod._token_freq(["bitcoin rally and ethereum rally again", "the bitcoin price"])
    terms = {t["term"]: t["count"] for t in freq}
    assert terms["bitcoin"] >= 2
    assert "and" not in terms
    assert "the" not in terms


def test_competitor_matrix_ranks_by_mentions():
    mod = load_module()
    mat = mod.competitor_matrix([
        {"name": "B", "rating": 3.2, "mentions": 30},
        {"name": "A", "rating": 4.8, "mentions": 12},
    ])
    assert mat["top_competitor"] == "B"
    assert mat["competitors"][0]["name"] == "B"
    assert any("Highest-rated" in s and "A" in s for s in mat["suggestions"])


def test_build_brief_has_questions_and_sources():
    mod = load_module()
    b = mod.build_brief("ai chips", "q3")
    assert b["topic"] == "ai chips"
    assert len(b["questions"]) >= 4
    assert "rss command" in " ".join(b["data_sources"])


def test_sentiment_over_concatenation_label_packagable():
    mod = load_module()
    # ensure the lexicon doesn't crash on punctuation only
    assert mod.sentiment("!!! --- 123")["label"] == "neutral"