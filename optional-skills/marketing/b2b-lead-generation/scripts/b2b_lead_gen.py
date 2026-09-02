#!/usr/bin/env python3
"""b2b_lead_gen.py - Automated B2B lead generation pipeline.

Multi-channel prospecting and enrichment engine:
  - prospect  : build lead records from a seed list (company names / domains)
  - verify    : local email heuristics (syntax, disposable/role accounts)
  - score     : lead scoring (firmographic + readiness)
  - sequence  : personalized multi-touch outreach cadence builder
  - export    : CRM-sync exports (CSV / HubSpot-style JSON)

Discovery/enrichment of exact contacts is done by the agent (web/search tools);
this script is the pipeline that dedupes, verifies, scores, sequences, and
exports.  Stdlib only.  Data lives in a local JSON store.
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STORE = os.path.join(SCRIPT_DIR, "..", "leads.json")

# Well-known disposable domains (heuristic; not exhaustive).
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "sharklasers.com", "tempmail.com",
    "10minutemail.com", "yopmail.com", "throwaway.com", "mailnesia.com",
    "spam4.me", "mintemail.com", "getnada.com", "inboxbear.com",
}
ROLE_PREFIXES = {"info", "sales", "support", "admin", "webmaster", "noreply",
                 "no-reply", "contact", "help", "hello", "billing", "team"}
VALID_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_email(email: str) -> Dict[str, Any]:
    email = (email or "").strip().lower()
    base = {"email": email, "syntax_ok": False, "disposable": False,
            "role_account": False, "verdict": "invalid"}
    if not VALID_EMAIL.match(email):
        return base
    base["syntax_ok"] = True
    local, _, domain = email.partition("@")
    base["disposable"] = domain in DISPOSABLE_DOMAINS
    base["role_account"] = local in ROLE_PREFIXES or _has_plus(local) is False and local in ROLE_PREFIXES
    if base["disposable"]:
        base["verdict"] = "block_disposable"
    elif base["role_account"]:
        base["verdict"] = "flag_role"
    else:
        base["verdict"] = "ok"
    return base


def _has_plus(local: str) -> bool:
    return "+" in local


def lead_score(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Firmographic + readiness scoring, 0-100."""
    s = 0
    reasons: List[str] = []
    employees = int(lead.get("employees") or 0)
    funding = float(lead.get("funding_usd") or 0)
    if employees >= 500:
        s += 25; reasons.append("enterprise size")
    elif employees >= 50:
        s += 15; reasons.append("SME size")
    elif employees >= 5:
        s += 8
    if funding >= 5_000_000:
        s += 15; reasons.append("well funded")
    elif funding >= 1_000_000:
        s += 10; reasons.append("seed+ funded")
    intent = (lead.get("intent") or "").lower()
    for kw, pts in (("download", 10), ("trial", 10), ("demo", 10), ("visit", 5),
                    ("competitor", 8), ("hiring", 4)):
        if kw in intent:
            s += pts
            reasons.append(f"intent:{kw}")
    if lead.get("tech_stack"):
        s += 5; reasons.append("fits stack")
    if lead.get("email_verified") in (True, "ok"):
        s += 10; reasons.append("verified contact")
    elif lead.get("email_verified") == "invalid":
        s -= 15; reasons.append("bad contact")
    s = max(0, min(100, s))
    bucket = "hot" if s >= 70 else ("warm" if s >= 40 else "cold")
    return {"score": s, "bucket": bucket, "reasons": reasons}


def build_sequence(lead: Dict[str, Any], touches: int = 5
                   ) -> List[Dict[str, Any]]:
    name = _first_name(lead.get("name") or "there")
    company = lead.get("company") or ""
    cadence_days = [0, 2, 6, 12, 20]
    mode = {0: "email", 1: "email", 2: "email", 3: "linkedin", 4: "email"}
    steps = []
    for i in range(min(touches, len(cadence_days))):
        day = cadence_days[i]
        steps.append({
            "touch": i + 1,
            "day_offset": day,
            "channel": mode.get(day, "email"),
            "personalization_hooks": [
                f"mention {lead.get('role') or 'their role'}",
                f"reference {company}",
                f"flag a specific pain: {lead.get('pain_point') or 'hard to measure ROI'}",
            ],
            "subject_template": {
                0: f"Quick idea for {company}",
                2: f"Re: helping {name} at {company}",
                4: f"{name}, circling back",
            }.get(i, f"Touch {i+1} — {company}"),
        })
    return steps


def _first_name(full: str) -> str:
    return full.strip().split(" ")[0] if full else "there"


# --- store helpers ------------------------------------------------------------

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


def _save(store: str, leads: List[Dict[str, Any]]) -> None:
    with open(_store_path(store), "w", encoding="utf-8") as fh:
        json.dump(leads, fh, indent=2)


# --- commands -----------------------------------------------------------------

def cmd_prospect(args: argparse.Namespace) -> None:
    leads = _load(args.store)
    seed = args.company_list
    items = seed.split(",") if os.sep not in seed and not os.path.exists(seed) else seed
    if isinstance(items, str):
        companies = [l.strip() for l in open(items, encoding="utf-8") if l.strip()]
    else:
        companies = [c.strip() for c in items if c.strip()]
    before = {l.get("company", "").lower() for l in leads}
    added = 0
    for i, company in enumerate(companies):
        if company.lower() in before:
            continue
        leads.append({"company": company, "source": args.source, "status": "new",
                      "added": date.today().isoformat(),
                      "industry": args.industry or "", "notes": args.notes or ""})
        before.add(company.lower())
        added += 1
    _save(args.store, leads)
    out = {"added": added, "total": len(leads)}
    if args.json:
        print(json.dumps(out, indent=2))
        return
    print(f"Prospected {added} new leads (total {len(leads)}) into {args.store}")


def _enrich(lead: Dict[str, Any]) -> Dict[str, Any]:
    # Fill available contact fields from the record where present.
    if lead.get("email"):
        v = validate_email(lead["email"])
        lead["email_verified"] = v["verdict"]
        lead["email_flags"] = {k: v[k] for k in ("syntax_ok", "disposable", "role_account")}
    if lead.get("name") and not lead.get("first_name"):
        lead["first_name"] = _first_name(lead["name"])
    return lead


def cmd_verify(args: argparse.Namespace) -> None:
    leads = [_enrich(l) for l in _load(args.store)]
    _save(args.store, leads)
    valid = [l for l in leads if l.get("email_verified") == "ok"]
    flagged = [l for l in leads if l.get("email_verified") in ("flag_role", "block_disposable")]
    invalid = [l for l in leads if l.get("email_verified") == "invalid"]
    if args.json:
        print(json.dumps({"valid": len(valid), "flagged": len(flagged),
                          "invalid": len(invalid), "leads": leads}, indent=2))
        return
    print(f"Valid {len(valid)} | flagged {len(flagged)} | invalid {len(invalid)}")
    for l in flagged:
        print(f"  [flag] {l.get('company')} {l.get('email')} ({l.get('email_verified')})")


def cmd_score(args: argparse.Namespace) -> None:
    leads = [_enrich(l) for l in _load(args.store)]
    out = []
    for l in leads:
        sc = lead_score(l)
        out.append({**l, "score": sc["score"], "bucket": sc["bucket"],
                    "score_reasons": sc["reasons"]})
    _save(args.store, out)  # persist score
    out.sort(key=lambda x: x["score"], reverse=True)
    if args.json:
        print(json.dumps({"count": len(out), "leads": out}, indent=2))
        return
    print(f"{'Score':>6} {'Bucket':<5} {'Company':<24} {'Contact':<22}")
    for l in out[:15]:
        print(f"{l['score']:>6} {l['bucket']:<5} {l.get('company','')[:24]:<24} "
              f"{(l.get('name') or l.get('email') or '')[:22]:<22}")


def cmd_sequence(args: argparse.Namespace) -> None:
    leads = _load(args.store)
    target = [l for l in leads if l.get("company", "").lower() == args.company.lower()]
    if not target:
        target = [l for l in leads if l.get("email") and l.get("email_verified") == "ok"]
    if not target:
        print(json.dumps({"error": f"No leads match {args.company}"}))
        sys.exit(1)
    sequences = []
    for l in target[: args.limit]:
        sequences.append({"company": l.get("company"), "lead": l.get("name") or l.get("email"),
                          "sequence": build_sequence(l, args.touches)})
    if args.json:
        print(json.dumps({"sequences": sequences}, indent=2))
        return
    for seq in sequences[:3]:
        print(f"[{seq['company']}] {seq['lead']}")
        for step in seq["sequence"][:3]:
            print(f"   Touch {step['touch']} (day +{step['day_offset']}) subject: {step['subject_template']}")


def cmd_export(args: argparse.Namespace) -> None:
    leads = _load(args.store)
    fmt = args.format
    if fmt == "csv":
        fields = ["company", "industry", "name", "email", "email_verified",
                  "role", "employees", "funding_usd", "intent", "score", "bucket", "status"]
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(leads)
        print(json.dumps({"wrote": args.out, "rows": len(leads)}))
    else:  # hubspot-ish JSON
        payload = {"leads": [{"properties": {k: ("v", v) if not isinstance(v, str) else v
                                              for k, v in l.items() if isinstance(v, (str, int, float))},
                              "score": l.get("score")} for l in leads]}
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(json.dumps({"wrote": args.out, "rows": len(leads)}))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="b2b_lead_gen",
                                     description="Automated B2B lead generation pipeline")
    parser.add_argument("--store", default=DEFAULT_STORE)
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p = sub.add_parser("prospect", help="add companies from a CSV/JSON/comma list")
    p.add_argument("company_list")
    p.add_argument("--source", default="manual")
    p.add_argument("--industry", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("verify", help="enrich + verify contacts")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("score", help="score leads 0-100")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("sequence", help="build outreach cadence for a company (or verified leads)")
    p.add_argument("--company", default="")
    p.add_argument("--touches", type=int, default=5)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("export", help="export to CSV or hubspot JSON")
    p.add_argument("--out", required=True)
    p.add_argument("--format", default="csv", choices=["csv", "hubspot"])
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


DISPATCH = {
    "prospect": cmd_prospect,
    "verify": cmd_verify,
    "score": cmd_score,
    "sequence": cmd_sequence,
    "export": cmd_export,
}


if __name__ == "__main__":
    sys.exit(main())