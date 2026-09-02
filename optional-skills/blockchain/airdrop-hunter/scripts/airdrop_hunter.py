#!/usr/bin/env python3
"""airdrop_hunter.py - Automated airdrop hunting & qualification tracker.

Wallet-scanning orchestration: checks a wallet for on-chain interactions with
known airdrop-associated protocols (via public EVM RPC `eth_getLogs`), tracks
multi-chain eligibility locally, and produces a claim-ready checklist.

Stdlib only.  Read-only public RPC.  No keys required.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STORE = os.path.join(SCRIPT_DIR, "..", "airdrops.json")

RPC_ETH = os.getenv("ETH_RPC_URL", "https://ethereum-rpc.publicnode.com")
RPC_BASE = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
RPC_ARB = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")

# Well-known protocols that are airdrop-associated (or historically dropped).
# Each: {"name", "chain", "contract", "note"}  -- contract may be "" to use
# transfer-any heuristic.  This is a seed list; users add their own via `track`.
PROTOCOLS = [
    {"name": "Uniswap V2", "chain": "ethereum", "contract": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
     "note": "historic UNI drop"},
    {"name": "Uniswap V3", "chain": "ethereum", "contract": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
     "note": "historic UNI drop"},
    {"name": "Aave", "chain": "ethereum", "contract": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
     "note": "AAVE holders"},
    {"name": "Lido", "chain": "ethereum", "contract": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
     "note": "stETH interactions"},
    {"name": "1inch", "chain": "ethereum", "contract": "0x111111111117dC0aa78b770fA6A738034120C302",
     "note": "exchange activity"},
    {"name": "SushiSwap", "chain": "ethereum", "contract": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
     "note": "SUSHI drop"},
    {"name": "Arbitrum", "chain": "ethereum", "contract": "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a",
     "note": "contract bridge; historic ARB drop"},
    {"name": "Optimism", "chain": "ethereum", "contract": "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1",
     "note": "OP drop"},
    {"name": "zkSync Era", "chain": "ethereum", "contract": "0x32400084C286CF3E17e7B677ea9583e60a000324",
     "note": "historic ZK drop"},
    {"name": "EigenLayer", "chain": "ethereum", "contract": "0x858646372CC42E1A627fcE94aa7A7033e904b0D5",
     "note": "restaking"},  # placeholder; verify on-chain
    {"name": "Base/Swap (Uniswap Base)", "chain": "base", "contract": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
     "note": "explore Base airdrop exposure"},
]


def _rpc(url: str, method: str, params: List[Any], timeout: int = 25) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    # Public RPC providers 403 the default Python-urllib UA; send a browser-like one.
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (compatible; arcen-airdrop-hunter/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data.get("result")


def block_number(url: str) -> int:
    result = _rpc(url, "eth_blockNumber", [])
    return int(result, 16)


def wallet_balance(url: str, address: str) -> float:
    result = _rpc(url, "eth_getBalance", [address, "latest"])
    return int(result, 16) / 1e18


def count_transfers(url: str, wallet: str, contract: str, from_block: int,
                    to_block: int) -> int:
    """Count ERC-20 Transfer events involving the wallet for a token contract."""
    # topic0 = Transfer event signature
    topic0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    topic_wallet = "0x" + wallet[2:].lower().zfill(64)
    log = _rpc(url, "eth_getLogs", [{
        "address": contract,
        "topics": [topic0, None, topic_wallet],  # wallet as recipient
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
    }])
    log2 = _rpc(url, "eth_getLogs", [{
        "address": contract,
        "topics": [topic0, topic_wallet],  # wallet as sender
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
    }])
    return len(log or []) + len(log2 or [])


def scan_wallet(wallet: str, blocks: int = 50_000, protocols: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Scan known protocols for interactions with the wallet in recent history."""
    wallet = wallet.lower()
    if not wallet.startswith("0x") or len(wallet) != 42:
        raise ValueError("Invalid address")
    protocols = protocols or PROTOCOLS
    results: List[Dict[str, Any]] = []
    by_chain: Dict[str, int] = {}
    for p in protocols:
        url = {"ethereum": RPC_ETH, "base": RPC_BASE, "arbitrum": RPC_ARB}.get(
            p["chain"], RPC_ETH)
        try:
            latest = block_number(url)
            to_block = latest
            from_block = max(0, latest - blocks)
            if p["contract"]:
                count = count_transfers(url, wallet, p["contract"], from_block, to_block)
            else:
                count = 0
            matched = count > 0
            results.append({"protocol": p["name"], "chain": p["chain"],
                            "contract": p["contract"],
                            "matched": matched, "transfer_events": count,
                            "note": p.get("note", ""),
                            "window_blocks": blocks,
                            "scan_from_block": from_block, "scan_to_block": to_block})
            if matched:
                by_chain[p["chain"]] = by_chain.get(p["chain"], 0) + 1
        except Exception as e:  # noqa: BLE001
            results.append({"protocol": p["name"], "chain": p["chain"], "matched": None,
                            "transfer_events": 0, "note": p.get("note", ""),
                            "error": str(e)})
        time.sleep(0.05)  # be gentle on public RPCs
    return {"wallet": wallet, "matches": [r for r in results if r.get("matched")],
            "scanned": results, "matched_protocols": len([r for r in results if r.get("matched")]),
            "chains_active": by_chain, "window_blocks": blocks}


def _store_path(store: str) -> str:
    path = os.path.abspath(store)
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    return path


def _load(store: str) -> List[Dict[str, Any]]:
    fp = _store_path(store)
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as fh:
            return json.load(fh)
    return []


def _save(store: str, data: List[Dict[str, Any]]) -> None:
    with open(_store_path(store), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def cmd_scan(args: argparse.Namespace) -> None:
    result = scan_wallet(args.address, args.blocks)
    # Fold results into the tracking store.
    if args.track:
        store = _load(args.store)
        for m in result["matches"]:
            rec = {"wallet": args.address, "protocol": m["protocol"], "chain": m["chain"],
                   "status": "eligible", "note": m["note"],
                   "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "actions": ["confirm on explorer", "check claim portal/deadline"]}
            # upsert
            store = [s for s in store if not (s.get("wallet") == args.address
                                              and s.get("protocol") == m["protocol"])]
            store.append(rec)
        _save(args.store, store)
        result["tracked"] = len(result["matches"])
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"Wallet: {result['wallet']}")
    print(f"Matched {result['matched_protocols']} protocol(s): {result['chains_active']}")
    for m in result["matches"]:
        print(f"  [+] {m['protocol']} ({m['chain']}) — {m['transfer_events']} transfers — {m['note']}")
    no_match = [r for r in result["scanned"] if r.get("matched") is False]
    if no_match:
        print(f"Checked {len(no_match)} others — no interactions in {result['window_blocks']} blocks:")
        for m in no_match[:6]:
            print(f"      {m['protocol']} ({m['chain']})")


def cmd_track(args: argparse.Namespace) -> None:
    store = _load(args.store)
    p = {"name": args.name, "protocol": args.name, "chain": args.chain, "contract": args.contract,
         "note": args.note, "user_added": True}
    PROTOCOLS.append(p)
    store.append({"wallet": "", "protocol": args.name, "chain": args.chain,
                  "status": "unknown", "note": args.note,
                  "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "user_added": True})
    _save(args.store, store)
    print(json.dumps({"added_protocol": p, "tracked_entries": len(store)}, indent=2))


def cmd_status(args: argparse.Namespace) -> None:
    store = _load(args.store)
    if args.json:
        print(json.dumps({"count": len(store), "tracked": store}, indent=2))
        return
    if not store:
        print("Nothing tracked yet. Run scan --track <wallet> first.")
        return
    for s in store:
        print(f"[{s['status']:>8}] {s['protocol']} ({s['chain']}) — {s.get('note','')}")
        for a in s.get("actions", []):
            print(f"         - {a}")


def cmd_report(args: argparse.Namespace) -> None:
    store = _load(args.store)
    lines = ["# Airdrop claim checklist", ""]
    eligible = [s for s in store if s.get("status") == "eligible"]
    for s in eligible:
        lines.append(f"- [ ] Claim **{s['protocol']}** ({s['chain']})")
        for a in s.get("actions", []):
            lines.append(f"  - [ ] {a}")
    if not eligible:
        lines.append("No eligible protocols tracked yet.")
    text = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="airdrop_hunter",
        description="Automated airdrop hunting & qualification tracker")
    parser.add_argument("--store", default=DEFAULT_STORE)
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p = sub.add_parser("scan", help="scan a wallet against known protocols")
    p.add_argument("address")
    p.add_argument("--blocks", type=int, default=50_000, help="lookback blocks per chain")
    p.add_argument("--track", action="store_true", help="persist matches to the tracker")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("track", help="register a custom airdrop protocol")
    p.add_argument("name")
    p.add_argument("--chain", default="ethereum")
    p.add_argument("--contract", required=True, help="token/bridge contract for Transfer logs")
    p.add_argument("--note", default="")

    p = sub.add_parser("status", help="show tracked eligibility")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("report", help="print a claim checklist")
    p.add_argument("--out", default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        DISPATCH[args.command](args)
    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted by user"}))
        return 130
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


DISPATCH = {"scan": cmd_scan, "track": cmd_track, "status": cmd_status,
            "report": cmd_report}


if __name__ == "__main__":
    sys.exit(main())