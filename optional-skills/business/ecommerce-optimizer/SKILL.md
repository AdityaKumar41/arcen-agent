---
name: ecommerce-optimizer
description: "Diagnose store metrics and generate growth strategies."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [ecommerce, store, conversion, aov, inventory, pricing, cro, retail]
    category: business
    related_skills: [growth-intelligence]
    requires_toolsets: [terminal]
---

# E-commerce Strategy & Optimization Engine Skill

Evaluates store metrics, customer behavior, and inventory turnover to
automatically generate dynamic pricing, conversion-rate-optimization, and
scaling strategies.

Stdlib only. Fully offline once the store metrics file exists.

---

## When to Use

- User wants a store-side diagnosis (conversion, AOV, checkout, inventory)
- User wants dynamic pricing / bundling recommendations
- User wants a prioritized CRO test plan
- User wants to know whether to scale traffic now or fix fundamentals first

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Helper script path: `~/.arcen/skills/business/ecommerce-optimizer/scripts/ecommerce_optimizer.py`

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/business/ecommerce-optimizer/scripts/ecommerce_optimizer.py

python3 $SCRIPT template --out store.json
python3 $SCRIPT diagnose store.json
python3 $SCRIPT diagnose store.json --json
```

---

## Procedure

1. **Template** — `template --out store.json` writes the input shape
   (monthly visitors, carts, orders, revenue, SKU/inventory counts, margins,
   repeat/return rates, price elasticity).
2. **Diagnose** — computes conversion %, add-to-cart %, cart→order %,
   AOV, inventory turnover, and prints issues with a severity score.
3. **Pricing** — threshold free shipping, bundles, margin review, elasticity
   tests, checkout urgency.
4. **CRO** — prioritized test plan targeting wherever the funnel leaks.
5. **Scaling** — whether to scale spend now or fix conversion first, plus
   inventory replenishment guidance.

---

## Store Metrics Input (subset)

```json
{
  "monthly_visitors": 50000,
  "monthly_carts": 5200,
  "monthly_orders": 2700,
  "monthly_revenue": 86400,
  "products": 400,
  "skus": 780,
  "avg_inventory_value": 60000,
  "slow_skus": 220,
  "gross_margin": 0.42,
  "repeat_purchase_rate_pct": 24,
  "return_rate_pct": 9
}
```

Defaults applied when missing: gross margin 40%, products=skus.

---

## Pitfalls

- **Numbers must be real** — the diagnosis is only as good as the funnel
  inputs; pull from analytics, don't estimate.
- **Elasticity default is an assumption** — if you don't pass
  `price_elasticity`, tests still propose price moves; validate on one SKU.
- **Inventory turnover is derived** — requires `avg_inventory_value`; without
  it the inventory checks are skipped.
- **Context matters** — fashion vs consumables vs hardware have very different
  healthy turnover/AOV; interpret with the store's reality.

---

## Verification

```bash
# Should print a diagnosis with issues + pricing + CRO + scaling plans
python3 ~/.arcen/skills/business/ecommerce-optimizer/scripts/ecommerce_optimizer.py \
  template --out store.json
python3 ~/.arcen/skills/business/ecommerce-optimizer/scripts/ecommerce_optimizer.py \
  diagnose store.json
```