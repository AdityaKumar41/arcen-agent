#!/usr/bin/env python3
"""marketing_hub.py - Comprehensive marketing automation hub.

End-to-end orchestrator for multi-channel content: a workspace-backed campaign
manager that plans a content calendar, tracks per-channel performance, and
reports on what is working so an agent (or human) can post and iterate.

Persistence: a JSON workspace under the skill directory or --workdir.
Stdlib only.  No posting APIs are called here -- content execution happens via
the platform tools / agent; this hub keeps the plan and the metrics coherent.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WORKDIR = os.path.join(SCRIPT_DIR, "..", "workspace")

CHANNELS = ["newsletter", "social", "blog", "ads", "community", "cold_email"]


def _ws_path(workdir: str):
    p = os.path.abspath(workdir)
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, "marketing_hub.json")


def _load(workdir: str) -> Dict[str, Any]:
    fp = _ws_path(workdir)
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as fh:
            return json.load(fh)
    return {"campaigns": {}, "content": [], "metrics": [], "sequences": []}


def _save(workdir: str, data: Dict[str, Any]) -> None:
    with open(_ws_path(workdir), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


# --- planning -----------------------------------------------------------------

def plan_calendar(campaign: Dict[str, Any], start: str, days: int) -> List[Dict[str, Any]]:
    channels = campaign.get("channels") or ["social"]
    cadence = campaign.get("cadence", "daily")
    freq_per_week = {"daily": 7, "weekdays": 5, "weekly": 1, "biweekly": 0.5}.get(cadence, 5)
    start_dt = _parse_date(start)
    items: List[Dict[str, Any]] = []
    for d in range(days):
        dt = start_dt + timedelta(days=d)
        if cadence == "weekdays" and dt.weekday() >= 5:
            continue
        if freq_per_week < 1 and d % 14 != 0:
            continue
        for ch in channels:
            items.append({
                "date": dt.isoformat(),
                "channel": ch,
                "type": _default_type(ch),
                "status": "draft",
                "title": f"{campaign.get('name','campaign')} — {ch} — day {d+1}",
                "copy": "",
                "links": [],
            })
    return items


def _default_type(channel: str) -> str:
    return {"newsletter": "email", "social": "post", "blog": "article",
            "ads": "ad", "community": "thread", "cold_email": "email"}.get(channel, "post")


def _parse_date(text: str) -> datetime:
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.combine(date.today(), datetime.min.time())


# --- metrics ------------------------------------------------------------------

def upsert_metric(data: Dict[str, Any], channel: str, period: str,
                  impressions: float, clicks: float, conversions: float,
                  spend: float = 0.0, revenue: float = 0.0) -> None:
    rec = next((m for m in data["metrics"] if m.get("channel") == channel
                and m.get("period") == period), None)
    if rec is None:
        rec = {"channel": channel, "period": period}
        data["metrics"].append(rec)
    rec.update({"impressions": impressions, "clicks": clicks,
                "conversions": conversions, "spend": spend, "revenue": revenue})


def _ctr(m: Dict[str, Any]) -> float:
    if not m.get("impressions"):
        return 0.0
    return round(m["clicks"] / m["impressions"] * 100, 2)


def performance_report(data: Dict[str, Any]) -> Dict[str, Any]:
    by_ch = defaultdict(lambda: {"impressions": 0.0, "clicks": 0.0,
                                 "conversions": 0.0, "spend": 0.0, "revenue": 0.0})
    for m in data["metrics"]:
        agg = by_ch[m["channel"]]
        for k in ("impressions", "clicks", "conversions", "spend", "revenue"):
            agg[k] += m.get(k, 0)
    rows = []
    for ch, agg in by_ch.items():
        ctr = round(agg["clicks"] / agg["impressions"] * 100, 2) if agg["impressions"] else 0.0
        cr = round(agg["conversions"] / agg["clicks"] * 100, 2) if agg["clicks"] else 0.0
        roas = round(agg["revenue"] / agg["spend"], 2) if agg["spend"] else None
        cpa = round(agg["spend"] / agg["conversions"], 2) if agg["conversions"] else None
        rows.append({**agg, "channel": ch, "ctr_pct": ctr, "conv_rate_pct": cr,
                     "roas": roas, "cpa": cpa})
    rows.sort(key=lambda r: (r.get("roas") if r.get("roas") is not None else -1), reverse=True)
    total = {"impressions": sum(r["impressions"] for r in rows),
             "clicks": sum(r["clicks"] for r in rows),
             "conversions": sum(r["conversions"] for r in rows),
             "spend": sum(r["spend"] for r in rows),
             "revenue": sum(r["revenue"] for r in rows)}
    total["ctr_pct"] = round(total["clicks"] / total["impressions"] * 100, 2) if total["impressions"] else 0
    total["roas"] = round(total["revenue"] / total["spend"], 2) if total["spend"] else None
    best = rows[0]["channel"] if rows else None
    return {"channels": rows, "totals": total, "best_channel": best,
            "insights": _insights(rows, total)}


def _insights(rows, total) -> List[str]:
    insights = []
    if total.get("roas"):
        if total["roas"] >= 3:
            insights.append("Overall ROAS healthy (>=3x) — scale winning channels.")
        elif total["roas"] < 1:
            insights.append("Overall ROAS <1x — increase targeting or pause spend.")
    if rows:
        best = max(rows, key=lambda r: r.get("ctr_pct") or 0)
        if best["ctr_pct"] >= 5:
            insights.append(f"{best['channel']} has standout CTR ({best['ctr_pct']}%) — double down there.")
        worst = min(rows, key=lambda r: r.get("ctr_pct") or 0)
        if worst["ctr_pct"] < 1:
            insights.append(f"{worst['channel']} CTR under 1% — refresh creative/offer.")
    return insights


# --- CLI ----------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    data = _load(args.workdir)
    if data["campaigns"]:
        print(json.dumps({"error": "Workspace already has campaigns"}))
        return
    print(json.dumps({"message": f"Workspace ready at {_ws_path(args.workdir)}"},
                     indent=2))


def cmd_add_campaign(args: argparse.Namespace) -> None:
    data = _load(args.workdir)
    channels = [c.strip() for c in args.channels.split(",") if c.strip()] or ["social"]
    camp = {"name": args.name, "goal": args.goal, "audience": args.audience,
            "channels": channels, "cadence": args.cadence, "start": args.start}
    data["campaigns"][args.name] = camp
    _save(args.workdir, data)
    print(json.dumps({"campaign": camp}, indent=2))


def cmd_plan(args: argparse.Namespace) -> None:
    data = _load(args.workdir)
    camp = data["campaigns"].get(args.name)
    if not camp:
        print(json.dumps({"error": f"Unknown campaign '{args.name}'"}))
        sys.exit(1)
    calendar = plan_calendar(camp, camp.get("start") or args.start or date.today().isoformat(),
                             args.days)
    data["content"] = [c for c in data["content"] if c.get("campaign") != args.name] + [
        {**c, "campaign": args.name} for c in calendar]
    _save(args.workdir, data)
    if args.json:
        print(json.dumps({"campaign": args.name, "items": len(calendar),
                          "calendar": calendar}, indent=2))
        return
    print(f"Planned {len(calendar)} items for '{args.name}'")
    for c in calendar[:15]:
        print(f"  {c['date']} {c['channel']:<12} {c['type']:<10} {c['title']}")
    if len(calendar) > 15:
        print(f"  ... and {len(calendar)-15} more (see --json)")


def cmd_status(args: argparse.Namespace) -> None:
    data = _load(args.workdir)
    counts = defaultdict(int)
    for c in data["content"]:
        counts[c["status"]] += 1
    if args.json:
        print(json.dumps({"by_status": dict(counts), "campaigns": list(data["campaigns"])},
                         indent=2))
        return
    print("Status:")
    for k in ("draft", "scheduled", "published", "failed"):
        if counts.get(k):
            print(f"  {k:<12} {counts[k]}")


def cmd_mark(args: argparse.Namespace) -> None:
    data = _load(args.workdir)
    # Update by campaign+date+channel if given, else all drafts for campaign
    updated = 0
    for c in data["content"]:
        if c.get("campaign") != args.name:
            continue
        if args.date and c["date"] != args.date:
            continue
        if args.channel and c["channel"] != args.channel:
            continue
        c["status"] = args.status
        updated += 1
    _save(args.workdir, data)
    print(json.dumps({"updated": updated}, indent=2))


def cmd_metric(args: argparse.Namespace) -> None:
    data = _load(args.workdir)
    upsert_metric(data, args.channel, args.period, args.impressions, args.clicks,
                  args.conversions, args.spend, args.revenue)
    _save(args.workdir, data)
    print(json.dumps({"updated": args.channel, "period": args.period}, indent=2))


def cmd_report(args: argparse.Namespace) -> None:
    data = _load(args.workdir)
    rep = performance_report(data)
    if args.json:
        print(json.dumps(rep, indent=2))
        return
    t = rep["totals"]
    print(f"{'Channel':<14}{'Imp':>14}{'Clicks':>10}{'CTR%':>8}{'Conv':>7}{'Spend':>10}{'Rev':>12}{'ROAS':>7}")
    for r in rep["channels"]:
        roas = f"{r['roas']:.2f}" if r["roas"] is not None else "-"
        print(f"{r['channel']:<14}{r['impressions']:>14,.0f}{r['clicks']:>10,.0f}{r['ctr_pct']:>8.2f}"
              f"{r['conversions']:>7,.0f}${r['spend']:>9,.0f}${r['revenue']:>11,.0f}{roas:>7}")
    total_roas = f"{t['roas']:.2f}" if t.get("roas") is not None else "-"
    print(f"{'TOTAL':<14}{t['impressions']:>14,.0f}{t['clicks']:>10,.0f}{t['ctr_pct']:>8.2f}"
          f"{t['conversions']:>7,.0f}${t['spend']:>9,.0f}${t['revenue']:>11,.0f}{total_roas:>7}")
    print("\nInsights:")
    for i in rep["insights"]:
        print(f"  - {i}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="marketing_hub",
        description="Comprehensive marketing automation hub (plan, track, report).",
    )
    parser.add_argument("--workdir", default=DEFAULT_WORKDIR)
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    sub.add_parser("init", help="create/verify workspace")

    p = sub.add_parser("add-campaign", help="create a campaign")
    p.add_argument("--name", required=True)
    p.add_argument("--goal", default="awareness")
    p.add_argument("--audience", default="")
    p.add_argument("--channels", default="social")
    p.add_argument("--cadence", default="daily",
                   choices=["daily", "weekdays", "weekly", "biweekly"])
    p.add_argument("--start", default=None)

    p = sub.add_parser("plan", help="generate content calendar for a campaign")
    p.add_argument("--name", required=True)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--start", default=None)
    p.add_argument("--json", action="store_true")

    sub.add_parser("status", help="content status counts")

    p = sub.add_parser("mark", help="set content status")
    p.add_argument("--name", required=True)
    p.add_argument("--status", default="scheduled",
                   choices=["draft", "scheduled", "published", "failed"])
    p.add_argument("--date", default=None)
    p.add_argument("--channel", default=None)

    p = sub.add_parser("metric", help="record a period's channel performance")
    p.add_argument("--channel", required=True)
    p.add_argument("--period", default=date.today().isoformat())
    p.add_argument("--impressions", type=float, default=0.0)
    p.add_argument("--clicks", type=float, default=0.0)
    p.add_argument("--conversions", type=float, default=0.0)
    p.add_argument("--spend", type=float, default=0.0)
    p.add_argument("--revenue", type=float, default=0.0)

    p = sub.add_parser("report", help="performance + insights dashboard")
    p.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    fn = DISPATCH[args.command]
    try:
        fn(args)
    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted by user"}))
        return 130
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


DISPATCH = {
    "init": cmd_init,
    "add-campaign": cmd_add_campaign,
    "plan": cmd_plan,
    "status": cmd_status,
    "mark": cmd_mark,
    "metric": cmd_metric,
    "report": cmd_report,
}


if __name__ == "__main__":
    sys.exit(main())