from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "blockchain"
    / "coingecko"
    / "scripts"
    / "coingecko_client.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("coingecko_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _market_row(**overrides):
    row = {
        "market_cap_rank": 1,
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 60000.5,
        "market_cap": 1_200_000_000_000,
        "total_volume": 30_000_000_000,
        "price_change_percentage_24h": 2.5,
        "circulating_supply": 19_000_000,
        "total_supply": 21_000_000,
        "ath": 73500.0,
    }
    row.update(overrides)
    return row


def test_normalize_market_row_fields():
    mod = load_module()
    row = mod._normalize_market_row(_market_row())

    assert row["rank"] == 1
    assert row["id"] == "bitcoin"
    assert row["symbol"] == "BTC"
    assert row["name"] == "Bitcoin"
    assert row["price"] == 60000.5
    assert row["market_cap"] == 1_200_000_000_000
    assert row["volume_24h"] == 30_000_000_000
    assert row["change_24h_pct"] == 2.5
    assert row["vs_currency"] == "usd"


def test_normalize_market_row_missing_price_fields():
    mod = load_module()
    row = mod._normalize_market_row({"id": "burnt-tree", "symbol": "TREE", "name": "Tree"})

    assert row["rank"] is None
    assert row["price"] is None
    assert row["symbol"] == "TREE"


def test_normalize_trending_skips_nested_item_container():
    mod = load_module()
    rows = mod._normalize_trending(
        [
            {"item": {"market_cap_rank": 2, "id": "ethereum", "name": "Ethereum", "symbol": "eth", "score": 3}},
            {"item": {"id": "solana", "name": "Solana", "symbol": "sol", "score": 1}},
        ]
    )

    assert len(rows) == 2
    assert rows[0]["id"] == "ethereum"
    assert rows[0]["symbol"] == "ETH"
    assert rows[0]["rank"] == 2
    assert rows[1]["rank"] is None


def test_normalize_categories_keeps_expected_keys():
    mod = load_module()
    rows = mod._normalize_categories(
        [
            {
                "id": "defi",
                "name": "DeFi",
                "market_cap": 100_000_000_000,
                "volume_24h": 5_000_000_000,
                "market_cap_change_24h": 3.2,
            }
        ]
    )

    assert rows[0]["id"] == "defi"
    assert rows[0]["market_cap"] == 100_000_000_000
    assert rows[0]["change_24h_pct"] == 3.2


def test_render_market_overview_extracts_usd_fields():
    mod = load_module()
    payload = {
        "data": {
            "active_cryptocurrencies": 16123,
            "total_market_cap": {"usd": 2.5e12, "btc": 34000000},
            "total_volume": {"usd": 1.2e11},
            "market_cap_percentage": {"btc": 59.1, "eth": 11.0},
            "market_cap_change_percentage_24h_usd": -1.5,
        }
    }

    out = mod._render_market_overview(payload, "usd")

    assert out["active_cryptocurrencies"] == 16123
    assert out["total_market_cap"] == 2.5e12
    assert out["total_volume_24h"] == 1.2e11
    assert out["btc_dominance_pct"] == 59.1
    assert out["market_cap_change_24h_pct"] == -1.5


def test_resolve_ids_known_and_unresolved():
    mod = load_module()

    ids, unresolved = mod._resolve_ids(["BTC", "ETH", "?weird?"])

    assert ids == ["bitcoin", "ethereum"]
    assert unresolved == ["?weird?"]


def test_resolve_ids_dedupes_lowercase_alias():
    mod = load_module()

    ids, unresolved = mod._resolve_ids(["btc", "BITCOIN", "bitcoin"])

    assert ids == ["bitcoin", "bitcoin", "bitcoin"]
    assert unresolved == []


def test_main_price_json_prints_normalized_payload(capsys):
    mod = load_module()

    def fake_get(url):
        if "/simple/price" in url and "include_24hr_change" in url:
            return {
                "bitcoin": {"usd": 77400, "usd_24h_change": -1.77},
                "ethereum": {"usd": 2411.22, "usd_24h_change": -2.57},
            }
        raise AssertionError(f"Unexpected URL: {url}")

    with patch.object(mod, "_http_get_json", side_effect=fake_get):
        exit_code = mod.main(["price", "BTC,ETH", "--json"])

    stdout = capsys.readouterr().out
    rendered = json.loads(stdout)

    assert exit_code == 0
    assert rendered["count"] == 2
    assert rendered["prices"][0]["id"] == "bitcoin"
    assert rendered["prices"][0]["price"] == 77400
    assert rendered["prices"][0]["change_24h_pct"] == -1.77


def test_main_top_json_respects_limit(capsys):
    mod = load_module()

    def fake_get(url):
        return [_market_row(rank=i, id=f"coin-{i}", symbol=f"C{i}", name=f"Coin {i}")
                for i in range(1, 6)]

    with patch.object(mod, "_http_get_json", side_effect=fake_get):
        exit_code = mod.main(["top", "--limit", "3", "--json"])

    stdout = capsys.readouterr().out
    rendered = json.loads(stdout)

    assert exit_code == 0
    assert rendered["count"] == 5
    assert len(rendered["coins"]) == 5
    assert rendered["coins"][0]["rank"] == 1
    assert rendered["coins"][0]["vs_currency"] == "usd"


def test_main_market_json(capsys):
    mod = load_module()

    payload = {
        "data": {
            "active_cryptocurrencies": 19473,
            "total_market_cap": {"usd": 2.6e12, "btc": 34000000},
            "total_volume": {"usd": 8.4e10},
            "market_cap_percentage": {"btc": 59.1, "eth": 11.0},
            "market_cap_change_percentage_24h_usd": -4.05,
        }
    }

    with patch.object(mod, "_http_get_json", return_value=payload):
        exit_code = mod.main(["market", "--json"])

    stdout = capsys.readouterr().out
    rendered = json.loads(stdout)

    assert exit_code == 0
    assert rendered["active_cryptocurrencies"] == 19473
    assert rendered["total_market_cap"] == 2.6e12
    assert rendered["btc_dominance_pct"] == 59.1


def test_main_gainers_sorts_descending(capsys):
    mod = load_module()

    rows = [
        _market_row(id="a", symbol="A", name="A", price_change_percentage_24h=1.0),
        _market_row(id="b", symbol="B", name="B", price_change_percentage_24h=10.0, market_cap_rank=2),
        _market_row(id="c", symbol="C", name="C", market_cap_rank=3, price_change_percentage_24h=None),  # no change data -> filtered
    ]

    with patch.object(mod, "_http_get_json", return_value=rows):
        exit_code = mod.main(["gainers", "--limit", "5", "--json"])

    stdout = capsys.readouterr().out
    rendered = json.loads(stdout)

    assert exit_code == 0
    assert [c["id"] for c in rendered["coins"]] == ["b", "a"]


def test_main_losers_sorts_ascending(capsys):
    mod = load_module()

    rows = [
        _market_row(id="a", symbol="A", name="A", price_change_percentage_24h=-1.0),
        _market_row(id="b", symbol="B", name="B", price_change_percentage_24h=-10.0, market_cap_rank=2),
    ]

    with patch.object(mod, "_http_get_json", return_value=rows):
        exit_code = mod.main(["losers", "--limit", "5", "--json"])

    stdout = capsys.readouterr().out
    rendered = json.loads(stdout)

    assert exit_code == 0
    assert [c["id"] for c in rendered["coins"]] == ["b", "a"]


def test_main_price_unresolved_falls_back_to_search(capsys):
    mod = load_module()

    calls = {"n_search": 0}

    def fake_get(url):
        if "/search?query=" in url:
            calls["n_search"] += 1
            return {"coins": [{"id": "wonder-coin", "name": "Wonder Coin", "symbol": "WND"}]}
        if "/simple/price" in url:
            return {"wonder-coin": {"usd": 4.44, "usd_24h_change": 0.5}}
        raise AssertionError(f"Unexpected URL: {url}")

    with patch.object(mod, "_http_get_json", side_effect=fake_get):
        exit_code = mod.main(["price", "WonderCoin", "--json"])

    stdout = capsys.readouterr().out
    rendered = json.loads(stdout)

    assert exit_code == 0
    assert calls["n_search"] == 1
    assert rendered["prices"][0]["id"] == "wonder-coin"
    assert rendered["prices"][0]["price"] == 4.44


def test_main_price_no_match_reports_missing(capsys):
    mod = load_module()

    with patch.object(mod, "_http_get_json", return_value={"coins": []}):
        exit_code = mod.main(["price", "NoSuchCoinXyz", "--json"])

    stdout = capsys.readouterr().out
    rendered = json.loads(stdout)

    assert exit_code == 0
    assert rendered["count"] == 1
    assert rendered["prices"][0]["label"] == "no match found"
    assert rendered["prices"][0]["price"] is None