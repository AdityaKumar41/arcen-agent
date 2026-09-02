#!/usr/bin/env python3
"""funding_dive.py - Crypto investment & funding rounds deep-dive.

Aggregates venture capital funding rounds, investor backing, token vesting
schedules, and early-stage capital inflows for target crypto assets.

Local tracker (JSON) + optional CoinGecko enrichment.  Stdlib only.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import time
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STORE = os.path.join(SCRIPT_DIR, "..", "funding.json")
CG_BASE = "https://api.coingecko.com/api/v3"
UA = "Mozilla/5.0 (compatible; arcen-funding-dive/1.0)"


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
    raise RuntimeError(f"Fetch failed: {last}")


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


def _save(store: str, rounds: List[Dict[str, Any]]) -> None:
    with open(_store_path(store), "w", encoding="utf-8") as fh:
        json.dump(rounds, fh, indent=2)


STANDARD_VESTING = {"seed": {"tge": 10, "cliff": 6, "duration": 24},
                    "private": {"tge": 15, "cliff": 6, "duration": 24},
                    "public": {"tge": 30, "cliff": 1, "duration": 12},
                    "strategic": {"tge": 10, "cliff": 12, "duration": 36}}


def schedule_for(round_name: str) -> Dict[str, int]:
    return STANDARD_VESTING.get(round_name.lower().strip(), STANDARD_VESTING["private"])


def vesting_schedule(amount_tokens: float, tge_pct: float, cliff_months: int,
                     duration_months: int, months: int = 24) -> List[Dict[str, Any]]:
    """Emulate a linear vesting schedule after a TGE + cliff."""
    out: List[Dict[str, Any]] = []
    released = 0.0
    tge_tokens = amount_tokens * (tge_pct / 100.0)
    for mo in range(1, months + 1):
        if mo == 1:
            released = tge_tokens
        elif mo > cliff_months:
            linear = (amount_tokens * (1 - tge_pct / 100.0)) / duration_months
            released += linear
        out.append({"month": mo, "delta_tokens": round(
            tge_tokens if mo == 1 else (0.0 if mo <= cliff_months else linear), 2),
            "cumulative_released_tokens": round(min(released, amount_tokens), 2)})
        cumulative = out[-1]["cumulative_released_tokens"]
        if mo > cliff_months and cumulative + 0.005 >= amount_tokens:
            break
    return out


def analyze_project(rounds: List[Dict[str, Any]], project: str) -> Dict[str, Any]:
    proj = [r for r in rounds if (r.get("project") or "").lower() == project.lower()]
    if not proj:
        raise LookupError(f"No funding rounds tracked for '{project}'")
    proj.sort(key=lambda r: r.get("date") or "")
    total = sum(float(r.get("amount_usd") or 0) for r in proj)
    # investor concentration = share of total contributed by top investor
    investor_share: Dict[str, float] = {}
    for r in proj:
        amount = float(r.get("amount_usd") or 0)
        for inv in (r.get("investors") or []):
            investor_share[inv] = investor_share.get(inv, 0) + amount
    if not investor_share:
        investor_share["(unknown)"] = 0.0
    top_investor = max(investor_share, key=investor_share.get)
    top_share = investor_share[top_investor] / total if total else 0.0
    rounds_summary = []
    for r in proj:
        sched_param = STANDARD_VESTING.get((r.get("round") or "private").lower(), STANDARD_VESTING["private"])
        token_alloc = float(r.get("token_allocation_pct") or 0)
        est_tokens = token_alloc / 100.0 if token_alloc else 0.0
        sched = vesting_schedule(est_tokens or 1e9, sched_param["tge"], sched_param["cliff"],
                                 sched_param["duration"], 36)
        rounds_summary.append({
            **r,
            "vesting_model": sched_param,
            "percent_released_12mo": round(next(
                (x["cumulative_released_tokens"] for x in sched if x["month"] == 12), 0) / (est_tokens or 1e9) * 100, 1),
        })
    return {
        "project": project,
        "rounds": rounds_summary,
        "total_raised_usd": round(total, 2),
        "round_count": len(proj),
        "top_investor": top_investor,
        "top_investor_share_pct": round(top_share * 100, 1),
        "investor_concentration": _concentration_label(top_share),
        "latest_round": proj[-1].get("round"),
        "latest_valuation_usd": proj[-1].get("valuation_usd"),
    }


def _concentration_label(share: float) -> str:
    if share >= 0.5:
        return "high (single-anchor led)"
    if share >= 0.25:
        return "moderate"
    return "diversified"


def inflows_by_sector(rounds: List[Dict[str, Any]]) -> Dict[str, Any]:
    sectors: Dict[str, Dict[str, float]] = {}
    for r in rounds:
        sector = r.get("sector") or "other"
        entry = sectors.setdefault(sector, {"raised_usd": 0.0, "rounds": 0.0})
        entry["raised_usd"] += float(r.get("amount_usd") or 0)
        entry["rounds"] += 1
    ranked = sorted(sectors.items(), key=lambda kv: kv[1]["raised_usd"], reverse=True)
    return {"sectors": [{"sector": k, "raised_usd": round(v["raised_usd"], 2),
                         "rounds": int(v["rounds"])} for k, v in ranked],
            "total_raised_usd": round(sum(v["raised_usd"] for _, v in sectors.items()), 2),
            "trending_sector": ranked[0][0] if ranked else None}


def cmd_add(args: argparse.Namespace) -> None:
    store = _load(args.store)
    investors = [i.strip() for i in args.investors.split(",") if i.strip()]
    rec = {"project": args.project, "date": args.date, "round": args.round,
           "amount_usd": args.amount, "valuation_usd": args.valuation,
           "investors": investors, "sector": args.sector,
           "token_allocation_pct": args.token_alloc,
           "notes": args.notes, "source": args.source}
    store.append(rec)
    _save(args.store, store)
    print(json.dumps({"added": rec, "total_rounds": len(store)}, indent=2))


def cmd_analyze(args: argparse.Namespace) -> None:
    store = _load(args.store)
    try:
        result = analyze_project(store, args.project)
    except LookupError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    if args.vesting:
        # Print one round's full vesting table
        for r in result["rounds"]:
            if (r.get("round") or "").lower() == args.vesting.lower():
                sched = vesting_schedule(1e9, r["vesting_model"]["tge"],
                                         r["vesting_model"]["cliff"],
                                         r["vesting_model"]["duration"], 36)
                print(json.dumps({"project": args.project, "round": r["round"],
                                  "schedule": sched}, indent=2))
                return
        print(json.dumps({"error": f"round '{args.vesting}' not found"}))
        return
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"[{result['project']}] raised ${result['total_raised_usd']:,.0f} "
          f"across {result['round_count']} rounds")
    print(f"  latest: {result['latest_round']} val ${result['latest_valuation_usd'] or 'n/a'}")
    print(f"  top investor: {result['top_investor']} "
          f"({result['top_investor_share_pct']}% — {result['investor_concentration']})")
    for r in result["rounds"]:
        print(f"  {r['date']} {r['round']:<9} ${float(r['amount_usd'] or 0):>12,.0f}  "
              f"investors: {', '.join(r.get('investors') or [])[:60]}")


def cmd_sectors(_args: argparse.Namespace) -> None:
    store = _load(_args.store)
    out = inflows_by_sector(store)
    if _args.json:
        print(json.dumps(out, indent=2))
        return
    print(f"Total tracked: ${out['total_raised_usd']:,.0f} | trending: {out['trending_sector']}")
    for s in out["sectors"]:
        print(f"  {s['sector']:<22} ${s['raised_usd']:>14,.0f}  ({s['rounds']:.0f} rounds)")


def cmd_gecko(args: argparse.Namespace) -> None:
    """Enrichment helper: pull basic project facts from CoinGecko to seed a round."""
    url = f"{CG_BASE}/coins/{urllib.parse.quote(args.coin)}?localization=false&tickers=false&community_data=false&developer_data=false"
    data = _get(url)
    links = (data.get("links") or {})
    out = {
        "name": data.get("name"),
        "symbol": data.get("symbol"),
        "homepage": (links.get("homepage") or [None])[0],
        "twitter": links.get("twitter_screen_name"),
        "genesis_date": data.get("genesis_date"),
        "categories": data.get("categories") or [],
        "description_en": (data.get("description") or {}).get("en"),
    }
    print(json.dumps(out, indent=2))


def cmd_list(args: argparse.Namespace) -> None:
    store = _load(args.store)
    if args.json:
        print(json.dumps({"count": len(store), "rounds": store}, indent=2))
        return
    for r in sorted(store, key=lambda x: x.get("date") or ""):
        print(f"{r.get('date')} {r.get('project',''):<22} {r.get('round',''):<9} "
              f"${float(r.get('amount_usd') or 0):>12,.0f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="funding_dive",
        description="Crypto investment & funding rounds deep-dive")
    parser.add_argument("--store", default=DEFAULT_STORE)
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p = sub.add_parser("add", help="record a funding round")
    p.add_argument("project")
    p.add_argument("--date", required=True)
    p.add_argument("--round", default="private", choices=["seed", "private", "strategic", "public", "equity"])
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--valuation", type=float, default=None)
    p.add_argument("--investors", default="")
    p.add_argument("--sector", default="")
    p.add_argument("--token-alloc", type=float, default=0.0, help="% of supply allocated in this round")
    p.add_argument("--notes", default="")
    p.add_argument("--source", default="")

    p = sub.add_parser("analyze", help="deep-dive a tracked project")
    p.add_argument("project")
    p.add_argument("--json", action="store_true")
    p.add_argument("--vesting", default="", help="emit full vesting table for a round name")

    p = sub.add_parser("sectors", help="aggregate early-stage inflows by sector")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("list", help="list all tracked rounds")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("gecko", help="seed project facts from CoinGecko")
    p.add_argument("coin")
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


DISPATCH = {"add": cmd_add, "analyze": cmd_analyze, "sectors": cmd_sectors,
            "list": cmd_list, "gecko": cmd_gecko}


if __name__ == "__main__":
    sys.exit(main())