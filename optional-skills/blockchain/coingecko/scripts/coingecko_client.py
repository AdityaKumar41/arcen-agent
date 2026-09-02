#!/usr/bin/env python3
"""coingecko_client.py - Crypto market data CLI for the Arcen Agent project.
Read-only CoinGecko data. Zero external dependencies (stdlib only:
urllib, json, argparse, time, os, sys, typing).  Free public API, no key.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")

# Known id <-> symbol map for friendly lookups.  CoinGecko accepts ids (but not
# bare symbols) on the public api, so we resolve common names here and fall
# back to /search for anything unknown.
COMMON_IDS: Dict[str, str] = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "usdt": "tether",
    "usdc": "usd-coin",
    "bnb": "binancecoin",
    "sol": "solana",
    "solana": "solana",
    "xrp": "ripple",
    "ripple": "ripple",
    "ada": "cardano",
    "cardano": "cardano",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    "avax": "avalanche-2",
    "avalanche": "avalanche-2",
    "trx": "tron",
    "tron": "tron",
    "dot": "polkadot",
    "polkadot": "polkadot",
    "matic": "matic-network",
    "polygon": "matic-network",
    "link": "chainlink",
    "chainlink": "chainlink",
    "uni": "uniswap",
    "uniswap": "uniswap",
    "ltc": "litecoin",
    "litecoin": "litecoin",
    "atom": "cosmos",
    "cosmos": "cosmos",
    "apt": "aptos",
    "aptos": "aptos",
    "arb": "arbitrum",
    "arbitrum": "arbitrum",
    "op": "optimism",
    "optimism": "optimism",
    "ton": "the-open-network",
    "near": "near",
    "near-protocol": "near",
    "hbar": "hedera-hashgraph",
    "hedera": "hedera-hashgraph",
    "fida": "bonfida",
    "shib": "shiba-inu",
    "shiba-inu": "shiba-inu",
    "pepe": "pepe",
    "wbtc": "wrapped-bitcoin",
    "weth": "weth",
    "dai": "dai",
    "aave": "aave",
    "sui": "sui",
    "pyth": "pyth-network",
    "jup": "jupiter-exchange-solana",
    "bonk": "bonk",
    "wif": "dogwifcoin",
    "fartcoin": "fartcoin",
    "xlm": "stellar",
    "stellar": "stellar",
    "vet": "vechain",
    "vechain": "vechain",
    "algo": "algorand",
    "algorand": "algorand",
    "ftm": "fantom",
    "fantom": "fantom",
    "icp": "internet-computer",
    "internet-computer": "internet-computer",
    "gala": "gala",
    "gala-games": "gala",
    "sand": "the-sandbox",
    "the-sandbox": "the-sandbox",
    "mana": "decentraland",
    "decentraland": "decentraland",
    "axs": "axie-infinity",
    "axie-infinity": "axie-infinity",
    "mkr": "maker",
    "maker": "maker",
    "comp": "compound-governance-token",
    "compound": "compound-governance-token",
    "snx": "havven",
    "synthetix": "havven",
}

# Symbols we resolve without a /search round trip.  CoinGecko symbols are not
# unique, so we only trust this curated set of well-known tickers.
TRUSTED_SYMBOLS = {
    "BTC", "ETH", "USDT", "USDC", "BNB", "SOL", "XRP", "ADA", "DOGE",
    "AVAX", "TRX", "DOT", "MATIC", "LINK", "UNI", "LTC", "ATOM", "APT",
    "ARB", "OP", "TON", "NEAR", "HBAR", "SHIB", "PEPE", "WBTC", "DAI",
    "AAVE", "SUI", "PYTH", "JUP", "BONK", "WIF", "XLM", "VET", "ALGO",
    "FTM", "ICP", "GALA", "SAND", "MANA", "AXS", "MKR", "COMP", "SNX",
}

DEFAULT_TOP = 10
DEFAULT_VS = "usd"


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def _http_get_json(url: str, timeout: int = 20, retries: int = 3) -> Any:
    """GET a JSON endpoint with a small retry/backoff on 429s."""
    delay = 1.0
    last_err: Exception = RuntimeError("no attempts made")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (compatible; coingecko_client/1.0)",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                if not body:
                    return {}
                return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            last_err = e
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"CoinGecko request failed after {retries} attempts: {last_err}")


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _usd(val: Optional[float], convert: str = "usd") -> str:
    if val is None:
        return "N/A"
    convert = (convert or "usd").lower()
    symbol = {"usd": "$", "eur": "EUR ", "gbp": "GBP ", "jpy": "JPY ",
              "btc": "BTC ", "eth": "ETH "}.get(convert, f"{convert.upper()} ")
    if convert in ("btc", "eth"):
        return f"{symbol}{val:,.6f}"
    return f"{symbol}{val:,.2f}"


def _pct(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    return f"{val:+.2f}%"


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Normalization helpers (kept testable)
# ---------------------------------------------------------------------------

def _normalize_market_row(row: Dict[str, Any], vs: str = DEFAULT_VS) -> Dict[str, Any]:
    """Normalize one /coins/markets row into a flat, stable dict."""
    return {
        "rank": row.get("market_cap_rank"),
        "id": row.get("id"),
        "symbol": (row.get("symbol") or "").upper(),
        "name": row.get("name"),
        "price": row.get("current_price"),
        "market_cap": row.get("market_cap"),
        "volume_24h": row.get("total_volume"),
        "change_24h_pct": row.get("price_change_percentage_24h"),
        "circulating": row.get("circulating_supply"),
        "total_supply": row.get("total_supply"),
        "ath": row.get("ath"),
        "vs_currency": vs.lower(),
    }


def _normalize_trending(items: List[Any]) -> List[Dict[str, Any]]:
    """Normalize /search/trending coins into a stable list."""
    out: List[Dict[str, Any]] = []
    for item in items:
        coin = item.get("item") or {}
        out.append({
            "rank": coin.get("market_cap_rank"),
            "id": coin.get("id"),
            "name": coin.get("name"),
            "symbol": (coin.get("symbol") or "").upper(),
            "score": coin.get("score"),
        })
    return out


def _normalize_categories(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize /coins/categories rows into a stable list."""
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "market_cap": row.get("market_cap"),
            "volume_24h": row.get("volume_24h"),
            "change_24h_pct": row.get("market_cap_change_24h"),
        })
    return out


def _render_market_overview(data: Any, convert: str = "usd") -> Dict[str, Any]:
    """Render /global payload (already parsed) into a stable dict."""
    gd = data.get("data") or {}
    total = gd.get("total_market_cap") or {}
    volumes = gd.get("total_volume") or {}
    caps_pct = gd.get("market_cap_percentage") or {}
    return {
        "active_cryptocurrencies": gd.get("active_cryptocurrencies"),
        "total_market_cap": total.get(convert.lower()),
        "total_volume_24h": volumes.get(convert.lower()),
        "btc_dominance_pct": caps_pct.get("btc"),
        "eth_dominance_pct": caps_pct.get("eth"),
        "market_cap_change_24h_pct": gd.get("market_cap_change_percentage_24h_usd"),
    }


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_market(args: argparse.Namespace) -> None:
    convert = (args.convert or DEFAULT_VS).lower()
    url = f"{API_BASE}/global?vs_currency={urllib.parse.quote(convert)}"
    data = _http_get_json(url)
    overview = _render_market_overview(data, convert)
    if args.json:
        print_json(overview)
        return
    print(f"Active cryptocurrencies : {overview['active_cryptocurrencies']}")
    print(f"Total market cap       : {_usd(overview['total_market_cap'], convert)}")
    print(f"24h volume             : {_usd(overview['total_volume_24h'], convert)}")
    print(f"24h market cap change  : {_pct(overview['market_cap_change_24h_pct'])}")
    print(f"BTC dominance          : {_pct(overview['btc_dominance_pct'])}")
    print(f"ETH dominance          : {_pct(overview['eth_dominance_pct'])}")


def _fetch_markets(vs: str, per_page: int = 100, order: str = "market_cap_desc") -> List[Dict[str, Any]]:
    url = (
        f"{API_BASE}/coins/markets?vs_currency={urllib.parse.quote(vs.lower())}"
        f"&order={order}&per_page={per_page}&page=1&sparkline=false&price_change_percentage=24h"
    )
    rows_raw = _http_get_json(url)
    return [_normalize_market_row(r, vs.lower()) for r in rows_raw]


def cmd_top(args: argparse.Namespace) -> None:
    vs = (args.vs or DEFAULT_VS).lower()
    limit = max(1, min(args.limit or DEFAULT_TOP, 250))
    rows = _fetch_markets(vs, per_page=limit, order=args.order)
    if args.json:
        print_json({"count": len(rows), "coins": rows})
        return
    for i, row in enumerate(rows, start=1):
        print(f"{i:>3}. {row['rank'] or '?':>3}  {row['symbol']:<9} {row['name']:<24} "
              f"{_usd(row['price'], vs):>16}  {_pct(row['change_24h_pct']):>9}  "
              f"mcap {_usd(row['market_cap'], vs)}")


def cmd_trending(args: argparse.Namespace) -> None:
    url = f"{API_BASE}/search/trending"
    data = _http_get_json(url)
    coins = _normalize_trending(data.get("coins") or [])
    if args.json:
        print_json({"count": len(coins), "coins": coins})
        return
    for row in coins:
        print(f"#{row['rank'] or '?':>3}  {row['symbol']:<9} {row['name']}")


def _fetch_movers(vs: str, limit: int, descending: bool) -> List[Dict[str, Any]]:
    """Top 100 coins by market cap, sorted by 24h % change locally."""
    rows = _fetch_markets(vs, per_page=100)
    priced = [r for r in rows if r.get("change_24h_pct") is not None]
    priced.sort(key=lambda r: r["change_24h_pct"], reverse=descending)
    return priced[: max(1, min(limit, 100))]


def _print_movers(args: argparse.Namespace, descending: bool) -> None:
    vs = (args.vs or DEFAULT_VS).lower()
    limit = max(1, min(args.limit or DEFAULT_TOP, 100))
    rows = _fetch_movers(vs, limit, descending)
    if args.json:
        print_json({"count": len(rows), "coins": rows})
        return
    for i, row in enumerate(rows, start=1):
        print(f"{i:>3}. {row['symbol']:<9} {row['name']:<24} "
              f"{_pct(row['change_24h_pct']):>9}  {_usd(row['price'], vs)}")


def cmd_gainers(args: argparse.Namespace) -> None:
    _print_movers(args, descending=True)


def cmd_losers(args: argparse.Namespace) -> None:
    _print_movers(args, descending=False)


def cmd_categories(args: argparse.Namespace) -> None:
    vs = (args.vs or DEFAULT_VS).lower()
    limit = max(1, min(args.limit or DEFAULT_TOP, 250))
    url = f"{API_BASE}/coins/categories?order=market_cap_desc"
    rows_raw = _http_get_json(url)
    rows = [_normalize_categories(r) for r in rows_raw][:limit]
    if args.json:
        print_json({"count": len(rows), "categories": rows})
        return
    for row in rows:
        print(f"{row['name']:<28} mcap {_usd(row['market_cap'], vs):>18}  "
              f"vol {_usd(row['volume_24h'], vs):>18}  {_pct(row['change_24h_pct'])}")


def _resolve_ids(symbols: List[str]) -> Tuple[List[str], List[str]]:
    """Map each requested symbol to a CoinGecko id via COMMON_IDS/TRUSTED_SYMBOLS.
    Returns (resolved_ids, unresolved_symbols)."""
    ids: List[str] = []
    unresolved: List[str] = []
    for sym in symbols:
        lower = sym.lower()
        if lower in COMMON_IDS:
            ids.append(COMMON_IDS[lower])
        elif sym.upper() in TRUSTED_SYMBOLS and lower in COMMON_IDS:
            ids.append(COMMON_IDS[lower])
        else:
            unresolved.append(sym)
    return ids, unresolved


def cmd_price(args: argparse.Namespace) -> None:
    vs = (args.vs or DEFAULT_VS).lower()
    symbols = [s.strip() for s in args.coins.split(",") if s.strip()]
    ids, unresolved = _resolve_ids(symbols)

    rows: List[Dict[str, Any]] = []
    if ids:
        rows.extend(_fetch_price_ids(ids, vs))
    for sym in unresolved:
        rows.extend(_fetch_price_search(sym, vs))

    if args.json:
        print_json({"count": len(rows), "prices": rows})
        return
    for row in rows:
        label = f" ({row['label']})" if row.get("label") else ""
        print(f"{row['id']}{label}: {_usd(row['price'], vs)} {_pct(row['change_24h_pct'])}")


def _fetch_price_ids(ids: List[str], vs: str) -> List[Dict[str, Any]]:
    joined = ",".join(dict.fromkeys(ids))
    url = (
        f"{API_BASE}/simple/price?ids={urllib.parse.quote(joined)}"
        f"&vs_currencies={urllib.parse.quote(vs)}&include_24hr_change=true"
    )
    data = _http_get_json(url)
    out: List[Dict[str, Any]] = []
    for cg_id in dict.fromkeys(ids):
        v = data.get(cg_id) or {}
        out.append({
            "id": cg_id,
            "symbol": cg_id,
            "price": v.get(vs),
            "change_24h_pct": v.get(f"{vs}_24h_change"),
            "label": "",
        })
    return out


def _fetch_price_search(symbol: str, vs: str) -> List[Dict[str, Any]]:
    url = f"{API_BASE}/search?query={urllib.parse.quote(symbol)}"
    data = _http_get_json(url)
    coins = data.get("coins") or []
    if not coins:
        return [{"id": symbol, "symbol": symbol, "price": None,
                 "change_24h_pct": None, "label": "no match found"}]
    best = coins[0]
    cg_id = best.get("id")
    url2 = (
        f"{API_BASE}/simple/price?ids={urllib.parse.quote(cg_id)}"
        f"&vs_currencies={urllib.parse.quote(vs)}&include_24hr_change=true"
    )
    data2 = _http_get_json(url2)
    v = data2.get(cg_id) or {}
    return [{"id": cg_id,
             "symbol": (best.get("symbol") or "").upper(),
             "price": v.get(vs),
             "change_24h_pct": v.get(f"{vs}_24h_change"),
             "label": f"searched '{symbol}'"}]


# ---------------------------------------------------------------------------
# Parser + dispatch
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coingecko_client",
        description="Crypto market data CLI via CoinGecko - stdlib only, no API key.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p_market = sub.add_parser("market", help="Global crypto market overview")
    p_market.add_argument("--convert", default=DEFAULT_VS, help="Currency (default: usd)")
    p_market.add_argument("--json", action="store_true", help="Print JSON")

    p_top = sub.add_parser("top", help="Top coins by market cap")
    p_top.add_argument("--limit", type=int, default=DEFAULT_TOP, metavar="N",
                       help="Number of coins (default: 10, max 250)")
    p_top.add_argument("--vs", default=DEFAULT_VS, help="Currency (default: usd)")
    p_top.add_argument("--order", default="market_cap_desc",
                       choices=["market_cap_desc", "market_cap_asc", "volume_desc",
                                "gecko_desc", "gecko_asc", "id_asc", "id_desc"])
    p_top.add_argument("--json", action="store_true", help="Print JSON")

    p_trending = sub.add_parser("trending", help="Trending searched coins")
    p_trending.add_argument("--json", action="store_true", help="Print JSON")

    for name, desc in (("gainers", "Biggest 24h gainers"),
                       ("losers", "Biggest 24h losers")):
        p_m = sub.add_parser(name, help=desc)
        p_m.add_argument("--limit", type=int, default=DEFAULT_TOP, metavar="N",
                         help="Number of coins (default: 10)")
        p_m.add_argument("--vs", default=DEFAULT_VS, help="Currency (default: usd)")
        p_m.add_argument("--json", action="store_true", help="Print JSON")

    p_cat = sub.add_parser("categories", help="Crypto categories by market cap")
    p_cat.add_argument("--limit", type=int, default=DEFAULT_TOP, metavar="N",
                       help="Number of categories (default: 10, max 250)")
    p_cat.add_argument("--vs", default=DEFAULT_VS, help="Currency (default: usd)")
    p_cat.add_argument("--json", action="store_true", help="Print JSON")

    p_price = sub.add_parser("price", help="Price for symbols or ids (comma-separated)")
    p_price.add_argument("coins", help="Comma-separated symbols or CoinGecko ids (e.g. BTC,ETH or bitcoin,ethereum)")
    p_price.add_argument("--vs", default=DEFAULT_VS, help="Currency (default: usd)")
    p_price.add_argument("--json", action="store_true", help="Print JSON")

    return parser


DISPATCH = {
    "market": cmd_market,
    "top": cmd_top,
    "trending": cmd_trending,
    "gainers": cmd_gainers,
    "losers": cmd_losers,
    "categories": cmd_categories,
    "price": cmd_price,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cmd_fn = DISPATCH.get(args.command)
    if cmd_fn is None:
        print_json({"error": f"Unknown command '{args.command}'"})
        return 1

    try:
        cmd_fn(args)
    except KeyboardInterrupt:
        print_json({"error": "Interrupted by user"})
        return 130
    except Exception as e:
        print_json({"error": str(e)})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())