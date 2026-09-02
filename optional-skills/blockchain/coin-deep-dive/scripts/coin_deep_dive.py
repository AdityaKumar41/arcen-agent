#!/usr/bin/env python3
"""coin_deep_dive.py - Granular coin deep-analysis engine.

Audits a cryptocurrency across tokenomics, utility, on-chain metrics, team,
and technical architecture.  Pulls live facts from CoinGecko's public API
and combines them with research the agent supplies into a weighted rubric
score and a structured deep-dive report.

Stdlib only.  Read-only.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

CG_BASE = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
UA = "Mozilla/5.0 (compatible; arcen-coin-deep-dive/1.0)"

# Weighted rubric: dimensions map to fields in the research payload.
RUBRIC = {
    "tokenomics": {"weight": 0.25, "cues": ["supply_cap", "emission", "allocations", "staking"]},
    "utility": {"weight": 0.25, "cues": ["use_cases", "revenue_flywheel", "demand"]},
    "onchain": {"weight": 0.20, "cues": ["active_users", "fees", "tv_locked", "holders"]},
    "team": {"weight": 0.15, "cues": ["founders", "experience", "transparency", "known_identity"]},
    "architecture": {"weight": 0.15, "cues": ["consensus", "centricity", "throughput", "upgradeability"]},
}

CATEGORY_BONUS = {"defi", "layer-1", "layer-2", "ecosystem", "scaling",
                  "governance", "real-world-assets", "stablecoins"}
CATEGORY_PENALTY = {"meme", "fan-token", "nft-collection"}


def _get(url: str, timeout: int = 20, retries: int = 2) -> Any:
    delay = 1.0
    last: Exception = RuntimeError("no attempts")
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last = e
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"CoinGecko fetch failed: {last}")


def fetch_coingecko(coin: str) -> Dict[str, Any]:
    url = f"{CG_BASE}/coins/{urllib.parse.quote(coin)}?localization=false&tickers=false&community_data=false&developer_data=true"
    data = _get(url)
    if not data or data.get("error"):
        raise RuntimeError(data.get("error") if isinstance(data, dict) else "no data")
    links = data.get("links") or {}
    market = data.get("market_data") or {}
    return {
        "name": data.get("name"),
        "symbol": (data.get("symbol") or "").upper(),
        "categories": data.get("categories") or [],
        "genesis_date": data.get("genesis_date"),
        "description": (data.get("description") or {}).get("en") or "",
        "links": {
            "homepage": (links.get("homepage") or [None])[0],
            "whitepaper": (links.get("whitepaper") or ""),
            "github": (links.get("repos_url") or {}).get("github") or [],
            "twitter": links.get("twitter_screen_name"),
            "blockchain_site": (links.get("blockchain_site") or [None])[0],
        },
        "market": {
            "current_price_usd": market.get("current_price", {}).get("usd"),
            "market_cap_rank": market.get("market_cap_rank"),
            "market_cap_usd": market.get("market_cap", {}).get("usd"),
            "total_volume_usd": market.get("total_volume", {}).get("usd"),
            "circulating_supply": market.get("circulating_supply"),
            "total_supply": market.get("total_supply"),
            "max_supply": market.get("max_supply"),
            "ath_usd": market.get("ath", {}).get("usd"),
            "price_change_24h_pct": market.get("price_change_percentage_24h"),
            "fdv_usd": market.get("fully_diluted_valuation", {}).get("usd"),
        },
        "github_stats": {
            "stars": data.get("developer_data", {}).get("stars"),
            "forks": data.get("developer_data", {}).get("forks"),
            "subscribers": data.get("developer_data", {}).get("subscribers"),
            "open_issues": data.get("developer_data", {}).get("open_issues"),
        },
    }


def score_research(research: Dict[str, Any]) -> Dict[str, Any]:
    """Score each rubric dimension from a research payload the agent supplies.

    research: {
      "tokenomics": {...sub-field values...},
      "utility": {...}, "onchain": {...}, "team": {...}, "architecture": {...}
    }
    Missing dimensions score 0 and are flagged rather than guessed.
    """
    dimension_scores: Dict[str, Any] = {}
    missing: List[str] = []
    for dim, meta in RUBRIC.items():
        raw = research.get(dim)
        if not isinstance(raw, dict):
            missing.append(dim)
            dimension_scores[dim] = {"score": 0.0, "basis": "missing research"}
            continue
        # Score = avg of provided numeric 0-10 fields, weighted 0 if none.
        values = [v for v in raw.values() if isinstance(v, (int, float))]
        if not values:
            missing.append(dim)
            dimension_scores[dim] = {"score": 0.0, "basis": raw}
            continue
        dimension_scores[dim] = {
            "score": round(sum(values) / len(values), 2),
            "basis": raw,
        }
    total = sum(ds["score"] * RUBRIC[d]["weight"] for d, ds in dimension_scores.items())
    category_adj = _category_adjustment(research.get("categories") or [])
    adjusted = max(0.0, min(10.0, total + category_adj))
    grade = _grade(adjusted)
    return {
        "dimensions": dimension_scores,
        "missing_dimensions": missing,
        "raw_total": round(total, 2),
        "category_adjustment": category_adj,
        "final_score": round(adjusted, 2),
        "grade": grade,
    }


def _category_adjustment(categories: List[str]) -> float:
    cats = set(c.lower() for c in categories)
    adj = 0.0
    if cats & CATEGORY_PENALTY:
        adj -= 1.0
    if cats & CATEGORY_BONUS:
        adj += 0.5
    return adj


def _grade(score: float) -> str:
    if score >= 8:
        return "A"
    if score >= 6.5:
        return "B"
    if score >= 5:
        return "C"
    if score >= 3.5:
        return "D"
    return "F"


def rubric_template() -> Dict[str, Any]:
    """Printable research template the agent fills via web/search tools."""
    return {
        "coin": "",
        "categories": [],
        "tokenomics": {
            "supply_cap_score": 0,
            "emission_sustainability_score": 0,
            "allocation_fairness_score": 0,
            "staking/utility_of_token_score": 0,
        },
        "utility": {
            "real_use_cases_score": 0,
            "revenue_flywheel_score": 0,
            "demand_generation_score": 0,
        },
        "onchain": {
            "active_users_score": 0,
            "fees_generated_score": 0,
            "tvl/liquidity_score": 0,
            "holder_distribution_score": 0,
        },
        "team": {
            "founder_credibility_score": 0,
            "track_record_score": 0,
            "transparency_score": 0,
            "identity_known_score": 0,
        },
        "architecture": {
            "consensus_soundness_score": 0,
            "decentralization_score": 0,
            "throughput_scalability_score": 0,
            "upgrade_path_score": 0,
        },
    }


def compose_report(coin: Optional[Dict[str, Any]], research: Dict[str, Any]) -> Dict[str, Any]:
    scored = score_research(research)
    out: Dict[str, Any] = {
        "coin": (coin or {}).get("name") or research.get("coin"),
        "symbol": (coin or {}).get("symbol"),
        "coingecko_facts": coin,
        "research_scores": scored,
    }
    if coin:
        m = coin.get("market") or {}
        max_supply = m.get("max_supply")
        circ = m.get("circulating_supply")
        dilution = 0.0
        if max_supply and circ and max_supply > 0:
            dilution = round((1 - circ / max_supply) * 100, 1)
        out["tokenomics_highlights"] = {
            "circulating_supply": circ,
            "max_supply": max_supply,
            "fdv_usd": m.get("fdv_usd"),
            "unreleased_supply_pct": dilution,
            "ath_usd": m.get("ath_usd"),
            "price_change_24h_pct": m.get("price_change_24h_pct"),
        }
        out["flags"] = _flags(coin, scored)
    return out


def _flags(coin: Dict[str, Any], scored: Dict[str, Any]) -> List[str]:
    m = coin.get("market") or {}
    flags: List[str] = []
    max_s = m.get("max_supply")
    circ = m.get("circulating_supply")
    if max_s and circ and circ / max_s < 0.3:
        flags.append("LOW float relative to max supply — heavy unlock overhang")
    if not max_s and circ:
        flags.append("No max supply — potentially unlimited inflation")
    links = coin.get("links") or {}
    if not (links.get("github")):
        flags.append("No public GitHub — code transparency weak")
    if scored.get("missing_dimensions"):
        flags.append(f"Missing research dims: {', '.join(scored['missing_dimensions'])} — score penalized")
    return flags


def cmd_analyze(args: argparse.Namespace) -> None:
    research = {}
    if args.research_file:
        with open(args.research_file, encoding="utf-8") as fh:
            research = json.load(fh)
    elif args.categories:
        research["categories"] = args.categories.split(",")
    else:
        research["categories"] = []
    coin = None
    try:
        coin = fetch_coingecko(args.coin)
        if args.categories:
            coin["categories"] = args.categories.split(",")
        elif not research.get("categories"):
            research["categories"] = coin["categories"]
    except Exception as e:  # noqa: BLE001
        if args.fail_fast:
            print(json.dumps({"error": f"CoinGecko: {e}"}))
            sys.exit(1)
        # offline mode: score against research file only
        research.setdefault("categories", args.categories.split(",") if args.categories else [])
    report = compose_report(coin, research)
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"[{report['coin']} ({report.get('symbol')})] Grade: {report['research_scores']['grade']} "
          f"({report['research_scores']['final_score']}/10)")
    for dim, ds in report["research_scores"]["dimensions"].items():
        print(f"  {dim:<14} {ds['score']:>5.2f}  {str(ds.get('basis'))[:60]}")
    if report.get("flags"):
        print("Flags:")
        for f in report["flags"]:
            print(f"  ! {f}")


def cmd_template(_args: argparse.Namespace) -> None:
    out = _args.out or "research.example.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rubric_template(), fh, indent=2)
    print(f"Research template written to {out}. Fill each 0-10 score via web/search tools, "
          f"then run analyze --research-file {out}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coin_deep_dive",
        description="Granular coin deep-analysis engine (tokenomics/utility/on-chain/team/architecture)")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p = sub.add_parser("analyze", help="deep-dive a coin")
    p.add_argument("coin", help="CoinGecko coin id, e.g. bitcoin, solana, pepe")
    p.add_argument("--research-file", default=None, help="rubric JSON with 0-10 scores")
    p.add_argument("--categories", default="", help="comma list (used when offline)")
    p.add_argument("--fail-fast", action="store_true", help="error out if CoinGecko unreachable")
    p.add_argument("--json", action="store_true")

    t = sub.add_parser("template", help="write the scoring rubric template")
    t.add_argument("--out", default=None)
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


DISPATCH = {"analyze": cmd_analyze, "template": cmd_template}


if __name__ == "__main__":
    sys.exit(main())