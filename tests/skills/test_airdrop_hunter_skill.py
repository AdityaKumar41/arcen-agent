from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "blockchain"
    / "airdrop-hunter"
    / "scripts"
    / "airdrop_hunter.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("airdrop_hunter_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_address_validation():
    mod = load_module()
    try:
        mod.scan_wallet("zzz", protocols=[])
    except ValueError as e:
        assert "Invalid address" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_scan_wallet_detects_transfers_and_chains():
    mod = load_module()
    W = "0x" + "aa" * 20
    w_topic = "0x" + W[2:].lower().zfill(64)

    def fake_rpc(url, method, params, timeout=25):
        if method == "eth_blockNumber":
            return "0x1300000"
        if method == "eth_getBalance":
            return "0x29a2241af62c0000"
        if method == "eth_getLogs":
            topics = params[0]["topics"]
            # wallet appears as recipient (topic2) or sender (topic1)
            return [{"address": params[0]["address"]}] if (topics[1] == w_topic or topics[2] == w_topic) else []
        raise AssertionError((url, method, params))

    with patch.object(mod, "_rpc", side_effect=fake_rpc):
        res = mod.scan_wallet(W, blocks=10000, protocols=mod.PROTOCOLS[:5])

    assert res["matched_protocols"] == 5
    assert res["chains_active"] == {"ethereum": 5}
    assert res["matches"][0]["transfer_events"] == 2


def test_scan_wallet_counts_recipient_and_sender_once():
    mod = load_module()
    W = "0x" + "bb" * 20
    w_topic = "0x" + W[2:].lower().zfill(64)

    def fake_rpc(url, method, params, timeout=25):
        if method == "eth_blockNumber":
            return "0x1300000"
        if method == "eth_getLogs":
            topics = params[0]["topics"]
            # 3 recipient logs + 2 sender logs = 5
            if topics[1] == w_topic:
                return [{}, {}]
            return [{}, {}, {}]
        raise AssertionError(url)

    with patch.object(mod, "_rpc", side_effect=fake_rpc):
        n = mod.count_transfers("https://rpc", W, "0x12345678901234567890123456789012345678901", 1000, 2000)
    assert n == 5


def test_wallet_balance_decimal():
    mod = load_module()
    with patch.object(mod, "_rpc", return_value=hex(3 * 10**18)):
        assert mod.wallet_balance("https://rpc", "0x" + "aa" * 20) == 3.0


def test_track_adds_protocol_and_store_entry(tmp_path):
    mod = load_module()
    from argparse import Namespace
    store = str(tmp_path / "airdrops.json")
    ns = Namespace(store=store, name="MyDrop", chain="arbitrum",
                   contract="0xabc", note="new")
    mod.cmd_track(ns)
    entries = mod._load(store)
    assert any(e["protocol"] == "MyDrop" for e in entries)
    assert any(p["name"] == "MyDrop" for p in mod.PROTOCOLS)