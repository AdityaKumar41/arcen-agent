#!/usr/bin/env python3
"""ecommerce_optimizer.py - E-commerce strategy & optimization engine.

Evaluates store metrics, customer behavior, and inventory turnover to
automatically generate dynamic pricing, conversion-rate-optimization, and
scaling strategies.

Input: a store metrics JSON.  Stdlib only.
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


def diagnose(m: Dict[str, Any]) -> Dict[str, Any]:
    visitors = _num(m, "monthly_visitors")
    orders = _num(m, "monthly_orders")
    revenue = _num(m, "monthly_revenue")
    products = _num(m, "products")
    skus = _num(m, "skus") or products

    conv = orders / visitors * 100 if visitors else 0.0
    aov = revenue / orders if orders else 0.0
    carts = _num(m, "monthly_carts")
    cart_conv = orders / carts * 100 if carts else 0.0
    add_to_cart_rate = carts / visitors * 100 if visitors else 0.0
    repeat = _num(m, "repeat_purchase_rate_pct")
    returns = _num(m, "return_rate_pct")
    avg_order_value = aov
    margin = _num(m, "gross_margin") or 0.4

    # Inventory turnover = COGS / avg inventory value
    cogs = revenue * (1 - margin)
    avg_inventory = _num(m, "avg_inventory_value")
    turnover = cogs / avg_inventory if avg_inventory else None
    slow = _num(m, "slow_skus"); fast = _num(m, "fast_skus")

    issues: List[str] = []
    if visitors and conv < 1.5:
        issues.append("Conversion rate is low (<1.5%) — traffic is not converting")
    elif visitors and conv > 4:
        issues.append("Healthy conversion — throttle on CRO, focus on scaling traffic/AOV")
    if add_to_cart_rate and add_to_cart_rate < 3:
        issues.append("Low add-to-cart rate — product pages/pricing/UX on PDP need work")
    if cart_conv and cart_conv < 40:
        issues.append("Checkout drop-off (cart->order <40%) — simplify checkout, add trust badges")
    if aov and aov < 50:
        issues.append("Very low AOV — introduce bundles/threshold free shipping to raise it")
    if repeat is not None and repeat < 20:
        issues.append(f"Repeat purchase only {repeat}% — weak retention/CRM")
    if returns and returns > 15:
        issues.append(f"High return rate ({returns}%) — check sizing/quality/expectations")
    if turnover is not None:
        if turnover < 3:
            issues.append(f"Slow inventory velocity ({turnover:.1f}x/yr) — cash trapped in stock")
        elif turnover > 12:
            issues.append(f"Very fast turnover ({turnover:.1f}x/yr) — watch stockouts")
    if slow and skus and slow / skus > 0.3:
        issues.append(">30% of SKUs are slow-moving — liquidation/discount or cull assortment")

    return {
        "conversion_rate_pct": round(conv, 2),
        "add_to_cart_rate_pct": round(add_to_cart_rate, 2),
        "cart_to_order_pct": round(cart_conv, 2),
        "aov": round(aov, 2),
        "repeat_purchase_rate_pct": repeat,
        "return_rate_pct": returns,
        "inventory_turnover_x": round(turnover, 2) if turnover is not None else None,
        "issues": issues,
        "severity": "critical" if len(issues) >= 3 else ("watch" if issues else "healthy"),
    }


def price_recommendations(m: Dict[str, Any], diag: Dict[str, Any]) -> List[Dict[str, Any]]:
    margin = _num(m, "gross_margin") or 0.4
    aov = diag["aov"]
    recs: List[Dict[str, Any]] = []
    if aov:
        recs.append({
            "action": "threshold free shipping",
            "rationale": f"AOV {aov:.2f} low — free-shipping threshold +5-10% above AOV lifts order size",
            "impact_metric": "AOV",
        })
        bundle = {
            "action": "bundle best-sellers with slow SKUs",
            "rationale": "Raises AOV and moves slow inventory without a discount fire-sale",
            "impact_metric": "AOV + inventory turnover",
        }
        recs.append(bundle)
    if margin < 0.3:
        recs.append({
            "action": "review anchor pricing / supplier renegotiation",
            "rationale": f"Gross margin {margin:.0%} is thin — before raising prices, improve COGS",
            "impact_metric": "margin",
        })
    elasticity = _num(m, "price_elasticity") or 1.2
    recs.append({
        "action": "test price increase on inelastic, differentiated SKUs",
        "rationale": f"Elasticity est. {elasticity} — selected SKUs can take +5-10% with minimal volume loss",
        "impact_metric": "revenue",
    })
    if diag.get("cart_to_order_pct", 100) < 40:
        recs.append({
            "action": "add 'today only' urgency + abandoned-cart email",
            "rationale": "Checkout leakage — urgency + cart email recover 2-5% of lost orders",
            "impact_metric": "conversion",
        })
    return recs


def cro_plan(diag: Dict[str, Any]) -> List[str]:
    steps: List[str] = []
    if diag["conversion_rate_pct"] < 1.5:
        steps.append("Run A/B on hero value-prop and CTA copy above the fold")
        steps.append("Add trust signals (reviews widget, payment badges) near buy buttons")
    if diag.get("add_to_cart_rate_pct", 100) < 3:
        steps.append("A/B product images, price display, and size guide on PDPs")
    if diag.get("cart_to_order_pct", 100) < 40:
        steps.append("Shorten checkout to 1 page; add guest checkout + Apple/Google Pay")
        steps.append("Add progress bar + trust badges at checkout")
    if diag["repeat_purchase_rate_pct"] is not None and diag["repeat_purchase_rate_pct"] < 20:
        steps.append("Launch loyalty/points + email win-back flows for lapsed customers")
    if not steps:
        steps.append("Funnel is healthy — A/B incremental improvements: shipping offer, bundles, subscription options")
    return steps[:5]


def scaling_plan(m: Dict[str, Any], diag: Dict[str, Any]) -> List[str]:
    plans: List[str] = []
    if diag["conversion_rate_pct"] >= 4:
        plans.append("Conversion is strong — scale paid/affiliate traffic into the funnel")
    elif diag["conversion_rate_pct"] >= 1.5:
        plans.append("Conversion is okay — improve it 30% before heavy paid scaling")
    else:
        plans.append("Fix conversion first; scaling traffic now wastes budget")
    if diag["inventory_turnover_x"] is not None and diag["inventory_turnover_x"] > 12:
        plans.append("Fast stock velocity — add reorder-point alerts and safety stock")
    if diag["inventory_turnover_x"] is not None and diag["inventory_turnover_x"] < 3:
        plans.append("Slow stock — run targeted liquidation campaigns to free cash")
    plans.append("Expand internationally if shipping/supply chain can absorb it")
    return plans


def cmd_diagnose(args: argparse.Namespace) -> None:
    with open(args.metrics, encoding="utf-8") as fh:
        m = json.load(fh)
    diag = diagnose(m)
    prices = price_recommendations(m, diag)
    cro = cro_plan(diag)
    scaling = scaling_plan(m, diag)
    out = {"diagnosis": diag, "pricing_recommendations": prices,
           "cro_plan": cro, "scaling_plan": scaling}
    if args.json:
        print(json.dumps(out, indent=2))
        return
    print(f"[Diagnosis: {diag['severity']}]")
    print(f"  conv {diag['conversion_rate_pct']}% | ATC {diag['add_to_cart_rate_pct']}% | "
          f"cart->order {diag['cart_to_order_pct']}% | AOV ${diag['aov']:.2f} | "
          f"turnover {diag['inventory_turnover_x']}")
    for i in diag["issues"]:
        print(f"  ! {i}")
    print("\n[Pricing]")
    for r in prices:
        print(f"  - {r['action']} -> {r['impact_metric']}")
    print("\n[CRO]")
    for s in cro:
        print(f"  - {s}")
    print("\n[Scaling]")
    for s in scaling:
        print(f"  - {s}")


def cmd_template(_args: argparse.Namespace) -> None:
    tpl = {
        "monthly_visitors": 50000,
        "monthly_carts": 5200,
        "monthly_orders": 2700,
        "monthly_revenue": 86400,
        "products": 400,
        "skus": 780,
        "avg_inventory_value": 60000,
        "slow_skus": 220,
        "fast_skus": 130,
        "gross_margin": 0.42,
        "repeat_purchase_rate_pct": 24,
        "return_rate_pct": 9,
        "price_elasticity": 1.2,
    }
    out = _args.out or "store.example.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(tpl, fh, indent=2)
    print(f"Template store metrics written to {out}. Fill in real numbers, then run diagnose.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecommerce_optimizer",
        description="E-commerce strategy & optimization engine")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True
    p = sub.add_parser("diagnose", help="analyze store metrics")
    p.add_argument("metrics")
    p.add_argument("--json", action="store_true")
    t = sub.add_parser("template", help="write an editable store metrics template")
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


DISPATCH = {"diagnose": cmd_diagnose, "template": cmd_template}


if __name__ == "__main__":
    sys.exit(main())