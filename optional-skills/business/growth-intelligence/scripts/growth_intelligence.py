#!/usr/bin/env python3
"""growth_intelligence.py - All-in-one business growth intelligence engine.

Integrates marketing, financial metrics, and operational data into automated,
actionable insights and growth recommendations.

Input: a metrics JSON file.  Stdlib only.  Computes unit economics (CAC, LTV,
LTV:CAC, churn, payback, NRR, growth rate), scores business health across
domains, and produces prioritized recommendations + a 90-day plan.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional


def _num(d: Dict[str, Any], k: str) -> float:
    try:
        return float(d.get(k) or 0)
    except (TypeError, ValueError):
        return 0.0


def compute_unit_economics(m: Dict[str, Any]) -> Dict[str, Any]:
    monthly_revenue = _num(m, "monthly_revenue") or (_num(m, "arr") / 12)
    customers = _num(m, "customers")
    marketing_spend = _num(m, "monthly_marketing_spend")
    sales_spend = _num(m, "monthly_sales_spend") if "monthly_sales_spend" in m else 0
    acq_spend = marketing_spend + sales_spend

    arpu = monthly_revenue / customers if customers else 0.0
    gross_margin = _num(m, "gross_margin") or 0.8  # default 80% margin
    new_customers = _num(m, "new_customers_monthly")
    churned = _num(m, "churned_customers_monthly")

    cac = acq_spend / new_customers if new_customers else None
    arpc = arpu * gross_margin
    churn_rate = (churned / customers) if customers else None
    ltv = arpc / churn_rate if churn_rate else None
    ltv_cac = (ltv / cac) if (ltv is not None and cac) else None
    payback_months = (cac / arpc) if (cac and arpc) else None
    nrr = _num(m, "nrr") if "nrr" in m else None

    # growth rate (CAGR-like over the given period count)
    growth = None
    if new_customers and customers and new_customers <= customers:
        growth = round(new_customers / max(customers - new_customers, 1) * 100, 2)

    return {
        "monthly_revenue": round(monthly_revenue, 2),
        "arpu": round(arpu, 2),
        "arpa_gross_margin": round(arpc, 2),
        "cac": round(cac, 2) if cac is not None else None,
        "churn_rate_pct": round(churn_rate * 100, 2) if churn_rate is not None else None,
        "ltv": round(ltv, 2) if ltv is not None else None,
        "ltv_cac_ratio": round(ltv_cac, 2) if ltv_cac is not None else None,
        "payback_months": round(payback_months, 1) if payback_months is not None else None,
        "nrr_pct": nrr,
        "customer_growth_rate_pct": growth,
    }


def health_report(e: Dict[str, Any]) -> Dict[str, Any]:
    flags: List[Dict[str, str]] = []
    def _flag(domain: str, status: str, note: str) -> None:
        flags.append({"domain": domain, "status": status, "note": note})

    ltv = e["ltv_cac_ratio"]
    if ltv is None:
        _flag("unit-economics", "watch", "No data to compute LTV:CAC")
    elif ltv >= 3:
        _flag("unit-economics", "healthy", f"LTV:CAC {ltv}:1 is efficient")
    elif ltv >= 1.5:
        _flag("unit-economics", "watch", f"LTV:CAC {ltv}:1 — borderline, improve retention")
    else:
        _flag("unit-economics", "critical", f"LTV:CAC {ltv}:1 is below the 3:1 target")

    payback = e["payback_months"]
    if payback is not None:
        if payback <= 12:
            _flag("payback", "healthy", f"{payback}mo payback is fine for SaaS")
        else:
            _flag("payback", "watch", f"{payback}mo payback is long — cash-hungry")

    churn = e["churn_rate_pct"]
    if churn is not None:
        if churn <= 2:
            _flag("retention", "healthy", f"{churn}% monthly churn is low")
        elif churn <= 5:
            _flag("retention", "watch", f"{churn}% monthly churn — focus on onboarding/expansion")
        else:
            _flag("retention", "critical", f"{churn}% monthly churn is high; retention first")

    nrr = e["nrr_pct"]
    if nrr is not None:
        if nrr >= 110:
            _flag("expansion", "healthy", f"NRR {nrr}% — expansion engine working")
        elif nrr < 100:
            _flag("expansion", "critical", f"NRR {nrr}% below 100 — shrinking without new logos")

    growth = e["customer_growth_rate_pct"]
    if growth is not None:
        if growth >= 10:
            _flag("acquisition", "healthy", f"{growth}% monthly customer growth")
        elif growth >= 3:
            _flag("acquisition", "watch", f"{growth}% monthly growth — steady but modest")
        else:
            _flag("acquisition", "critical", f"{growth}% monthly growth is flat")

    healthy = sum(1 for f in flags if f["status"] == "healthy")
    critical = sum(1 for f in flags if f["status"] == "critical")
    overall = "healthy" if critical == 0 and healthy >= 3 else ("critical" if critical >= 2 else "watch")
    return {"overall": overall, "flags": flags}


def recommendations(e: Dict[str, Any], health: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    critical = [f["domain"] for f in health["flags"] if f["status"] == "critical"]
    if "unit-economics" in critical:
        recs.append("Lower CAC (channel concentration, self-serve onboarding) or raise prices before scaling spend.")
    if "retention" in critical:
        recs.append("Fix churn first: add onboarding health checks, win-back campaigns, and support SLAs.")
    if "expansion" in critical:
        recs.append("Build expansion motion: usage-based pricing tiers, seat/feature upsell, annual contracts.")
    if "acquisition" in critical:
        recs.append("Re-evaluate acquisition mix; test 2-3 new channels against CAC baseline.")
    if e["ltv_cac_ratio"] is not None and e["ltv_cac_ratio"] >= 4:
        recs.append("LTV:CAC above 4:1 — safe to increase acquisition budget.")
    if (e["cac"] is not None and e["arpu"] and e["cac"] > e["arpu"] * 3
            and (e["payback_months"] or 0) > 12):
        recs.append("CAC exceeds 3x monthly ARPU with long payback — pricing or efficiency intervention needed.")
    if e["payback_months"] is not None and e["payback_months"] > 18:
        recs.append("Long payback (>18mo): shift mix toward expansion revenue and upfront/annual plans.")
    if not recs:
        recs.append("Metrics are in a good band — focus on compounding: scale winning channels and segment offers.")
    return recs[:6]


def build_plan(recs: List[str]) -> List[Dict[str, str]]:
    phases = ["Days 1-30: stabilization", "Days 31-60: optimization", "Days 61-90: scale"]
    plan = []
    for i, phase in enumerate(phases, start=1):
        items = recs[(i - 1) % len(recs): (i - 1) % len(recs) + 2] if recs else ["Define north-star metric"]
        plan.append({"phase": phase, "focus": "; ".join(items),
                     "key_results": ["One metric moved", "One experiment shipped"]})
    return plan


def cmd_report(args: argparse.Namespace) -> None:
    with open(args.metrics, encoding="utf-8") as fh:
        m = json.load(fh)
    e = compute_unit_economics(m)
    health = health_report(e)
    recs = recommendations(e, health)
    plan = build_plan(recs)
    out = {"metrics": m, "unit_economics": e, "health": health,
           "recommendations": recs, "plan_90_days": plan}
    if args.json:
        print(json.dumps(out, indent=2))
        return
    print("[Unit Economics]")
    for k, v in e.items():
        print(f"  {k:<24} {v}")
    print(f"\n[Health: {health['overall']}]")
    for f in health["flags"]:
        print(f"  [{f['status']:>8}] {f['domain']:<16} {f['note']}")
    print("\n[Recommendations]")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r}")
    print("\n[90-day plan]")
    for p in plan:
        print(f"  {p['phase']}: {p['focus']}")


def cmd_template(_args: argparse.Namespace) -> None:
    tpl = {
        "customers": 1200,
        "new_customers_monthly": 60,
        "churned_customers_monthly": 18,
        "monthly_revenue": 96000,
        "arr": 1152000,
        "gross_margin": 0.8,
        "monthly_marketing_spend": 15000,
        "monthly_sales_spend": 5000,
        "nrr": 108,
    }
    out = _args.out or "metrics.example.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(tpl, fh, indent=2)
    print(f"Template metrics written to {out}. Fill in real numbers, then run report.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="growth_intelligence",
        description="All-in-one business growth intelligence engine")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True
    p = sub.add_parser("report", help="analyze a metrics JSON")
    p.add_argument("metrics")
    p.add_argument("--json", action="store_true")
    t = sub.add_parser("template", help="write an editable metrics template")
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


DISPATCH = {"report": cmd_report, "template": cmd_template}


if __name__ == "__main__":
    sys.exit(main())