#!/usr/bin/env python3
"""influencer_analyzer.py - AI influencer & campaign marketing analyzer.

Ingests a JSON/CSV payload of discovered creators (name, platform, niche,
followers, engagement, CTR, sample post text), ranks them against a product
brief, extracts the top marketing hooks per creator, and produces a ranked
shortlist + campaign plan.

Discovery is done by the agent (e.g. via the agent-reach skill / web tools);
this script is the analytics + planning engine.  Stdlib only, fully offline.
"""

import argparse
import csv
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "..", "analysis.json")


# Common hook openers used to score "hook intensity" in post text.
HOOK_PATTERNS = [
    r"^[^.]*\?",          # question opener
    r"\b(how|why|what|when|who)\b",  # interrogative framing
    r"\b(never|always|stop|start|don't|do not|you won't|wait)\b",
    r"\b(before|after) (you|they|the)\b",
    r"\b(x|times|reasons|ways|mistakes|secrets|hacks|steps|tips)\b",
    r"\{\{|\}\}",         # curiosity-gap empty phrase
    r"\b(new|now|finally|just revealed|shocking)\b",
    r"\b(mistake|fail|error|trap|scam)\b",
    r"\d+\s+(things|ways|reasons|signs|steps)",
]


def _score_hooks(text: str) -> int:
    t = (text or "").lower()
    return sum(1 for p in HOOK_PATTERNS if re.search(p, t))


def _extract_hook(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return sentences[0] if sentences else text[:120]


def _engagement_rate(c: Dict[str, Any]) -> float:
    followers = float(c.get("followers") or 0)
    eng = float(c.get("avg_engagement") or 0)
    if followers <= 0:
        return 0.0
    return round((eng / followers) * 100, 3)


def analyze_creators(creators: List[Dict[str, Any]], product: str,
                     niche: str = "", budget: float = 0.0) -> Dict[str, Any]:
    scored = []
    for c in creators:
        followers = float(c.get("followers") or 0)
        eng_rate = _engagement_rate(c)
        ctr = float(c.get("ctr") or 0.0)
        est_reach = followers * (eng_rate / 100.0)
        # hook signal from sample posts
        posts = c.get("sample_posts") or []
        if isinstance(posts, str):
            posts = [posts]
        if not posts and c.get("best_content"):
            posts = [c["best_content"]]
        hook_scores = [_score_hooks(p) for p in posts]
        hook_score = sum(hook_scores)
        top_hook = _extract_hook(posts[0]) if posts else ""

        niche_hit = 0.0
        if niche:
            n = (c.get("topics") or c.get("niche") or "").lower()
            if n and niche.lower() in n:
                niche_hit = 1.0
            elif n and any(k in niche.lower() for k in _tokenize(n)):
                niche_hit = 0.5

        # Composite score: engagement, reach, CTR, hook writing, niche fit
        score = (eng_rate * 60) + (ctr * 8) + (hook_score * 3) + (niche_hit * 10)
        score = round(score, 2)

        est_cost = float(c.get("est_cost") or 0.0)
        roi = None
        if budget and est_cost:
            roi = round(est_reach / budget * 100, 2)  # normalized default reach
        scored.append({
            "name": c.get("name") or "unknown",
            "platform": c.get("platform") or "unknown",
            "handle": c.get("handle") or "",
            "followers": followers,
            "engagement_rate_pct": eng_rate,
            "ctr_pct": ctr,
            "est_reach": round(est_reach, 0),
            "hook_score": hook_score,
            "niche_fit_pct": round(niche_hit * 100, 0),
            "top_hook": top_hook,
            "all_hooks": [_extract_hook(p) for p in posts[:3]],
            "weighed_score": score,
            "est_cost": est_cost,
            "notes": c.get("notes") or "",
        })

    scored.sort(key=lambda x: x["weighed_score"], reverse=True)

    top = scored[:3]
    campaign = []
    for i, c in enumerate(top, start=1):
        campaign.append({
            "tier": i,
            "creator": c["name"],
            "role": "primary anchor" if i == 1 else ("co-signal" if i == 2 else "amplifier"),
            "angle": _suggest_angle(c, product),
            "deliverables": ["3-story/native posts", "2 feed posts", "1 long-form (YT/Substack)"],
            "measure": ["engagement rate", "CTR", "promo-code redemptions"],
        })

    return {
        "product": product,
        "niche": niche,
        "creators_analyzed": len(scored),
        "ranked_shortlist": scored,
        "campaign_plan": campaign,
        "recommendation": _recommendation(scored),
    }


def _tokenize(text: str) -> List[str]:
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if len(w) > 2]


def _suggest_angle(c: Dict[str, Any], product: str) -> str:
    eng = c.get("engagement_rate_pct", 0)
    if eng >= 5:
        return f"Authentic-tryout angle: let them use {product} in their natural workflow and react live."
    if c.get("niche_fit_pct", 0) >= 50:
        return f"Authority angle: position {product} as the {c.get('platform')}-friendly answer to their audience's pain."
    return f"Contrast angle: show {product} versus {c.get('handle') or 'their usual pick'} side by side."


def _recommendation(scored: List[Dict[str, Any]]) -> str:
    if not scored:
        return "No creators provided. Gather data first (agent-reach / web search), then re-run."
    top = scored[0]
    if top.get("niche_fit_pct", 0) >= 50 and top.get("engagement_rate_pct", 0) >= 3:
        return (f"Lead with {top['name']} ({top['platform']}) — strong fit + healthy engagement. "
                f"Negotiate bundles with #{' and #'.join([x['name'] for x in scored[1:3]])}.")
    if top.get("hook_score", 0) >= 2:
        return (f"{top['name']} writes strong hooks; brief content but plan a paid amplification "
                f"boost to multiply reach.")
    return ("Spread a small test across 2-3 mid-tier creators before committing budget. "
            "Measure CTR + engagement, then double down on the winner.")


def _load_creators(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        if path.endswith(".csv"):
            return list(csv.DictReader(fh))
        data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("creators") or data.get("rows") or []
        return data


def cmd_analyze(args: argparse.Namespace) -> None:
    creators = _load_creators(args.creators)
    if not creators:
        print(json.dumps({"error": "No creators found in input file"},
                         indent=2))
        sys.exit(1)
    result = analyze_creators(creators, args.product, args.niche, args.budget)
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"[Product] {result['product']}   [Niche] {result['niche'] or '-'}")
    print(f"{'':-<72}")
    print(f"{'Name':<24}{'PF':<10}{'Eng%':>7}{'CTR%':>7}{'Reach':>12}{'Score':>9}  Hook")
    for c in result["ranked_shortlist"][:8]:
        print(f"{c['name'][:24]:<24}{c['platform'][:9]:<10}{c['engagement_rate_pct']:>7.2f}"
              f"{c['ctr_pct']:>7.2f}{c['est_reach']:>12,.0f}{c['weighed_score']:>9.2f}  {c['top_hook'][:40]}")
    print(f"\n[Campaign] ")
    for step in result["campaign_plan"]:
        print(f"  T{step['tier']} {step['creator']} ({step['role']}) — {step['angle']}")
    print(f"\n[Recommendation] {result['recommendation']}")


def cmd_template(_args: argparse.Namespace) -> None:
    tpl = {
        "product": "example product",
        "niche": "skincare",
        "budget": 5000,
        "creators": [{
            "name": "Jane Creator",
            "platform": "tiktok",
            "handle": "@janecreates",
            "followers": 250000,
            "avg_engagement": 17500,
            "ctr": 3.2,
            "topics": "skincare, beauty, routines",
            "est_cost": 900,
            "sample_posts": [
                "3 skincare mistakes that age you faster",
                "Why I stopped using chemical sunscreen",
            ],
        }],
    }
    out = args.out or "creators.example.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(tpl, fh, indent=2)
    print(f"Template written to {out}. Fill it, then run analyze.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="influencer_analyzer",
        description="AI influencer & campaign marketing analyzer",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p = sub.add_parser("analyze", help="Analyze a creators file against a product")
    p.add_argument("creators", help="path to creators.json or .csv")
    p.add_argument("--product", required=True, help="product / offer under analysis")
    p.add_argument("--niche", default="", help="target niche keyword")
    p.add_argument("--budget", type=float, default=0.0)
    p.add_argument("--json", action="store_true")

    t = sub.add_parser("template", help="Generate an editable creators input template")
    t.add_argument("--out", default=None)
    return parser


DISPATCH = {"analyze": cmd_analyze, "template": cmd_template}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    fn = DISPATCH.get(args.command)
    if fn is None:
        print(json.dumps({"error": f"Unknown command '{args.command}'"}))
        return 1
    try:
        fn(args)
    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted by user"}))
        return 130
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())