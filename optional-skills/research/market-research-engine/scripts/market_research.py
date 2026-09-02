#!/usr/bin/env python3
"""market_research.py - Comprehensive research & market analytics engine.

Aggregates real-time data (RSS feeds), competitor tracking, and lexicon
sentiment analysis to automate deep-dive market research and actionable
insights.  Outputs a structured "research pack" the agent turns into a brief.

Stdlib only.  RSS via urllib + xml.etree; sentiment via a built-in lexicon
(no external NLP deps).
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any, Dict, List, Optional

UA = "Mozilla/5.0 (compatible; arcen-market-research/1.0)"
STOPWORDS = set("""a an and are as at be by for from has he her his in is it its of
on or that the their them they this to was were will with you your""".split())

POSITIVE = {
    "up", "rise", "rising", "gain", "gains", "growth", "growing", "record",
    "beats", "beat", "outperform", "strong", "strength", "bullish", "rally",
    "surge", "soar", "profit", "profitability", "win", "wins", "recover",
    "recovery", "expanded", "momentum", "optimism", "boost", "partnership",
    "expansion", "launch", "success", "successful", "awarded", "innovation",
    "profits", "secured",
}
NEGATIVE = {
    "down", "fall", "falling", "drop", "loss", "losses", "decline",
    "bearish", "slump", "stumble", "miss", "misses", "weak", "weakness",
    "layoff", "layoffs", "lawsuit", "scrutiny", "risk", "risks", "ban",
    "crackdown", "fraud", "hack", "breach", "short", "selloff", "plunge",
    "tumble", "concern", "outage", "recall", "delay", "delayed",
    "breach", "crisis", "fails", "collapses"
}


def _get(url: str, timeout: int = 25, retries: int = 2) -> bytes:
    delay = 1.0
    last: Exception = RuntimeError("no attempts")
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Fetch failed: {last}")


def fetch_rss(url: str, limit: int = 20) -> List[Dict[str, Any]]:
    raw = _get(url)
    items: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise RuntimeError(f"Not a valid RSS/Atom feed: {e}") from e
    for node in root.iter():
        if node.tag.split("}")[-1] != "item" and node.tag.split("}")[-1] != "entry":
            continue
        title = _child_text(node, "title")
        link = _child_text(node, "link")
        summary = _child_text(node, "description") or _child_text(node, "summary")
        published = _child_text(node, "pubDate") or _child_text(node, "published")
        items.append({"title": title, "link": link, "summary": summary,
                      "published": published})
        if len(items) >= limit:
            break
    return items


def _child_text(parent: ET.Element, tag: str) -> str:
    for el in parent.iter():
        if el.tag.split("}")[-1] == tag:
            text = (el.text or "").strip()
            if text:
                return text
            if el.tag.split("}")[-1] == "link" and el.get("href"):
                return el.get("href")
    return ""


def sentiment(text: str) -> Dict[str, Any]:
    text = (text or "").lower()
    words = re.findall(r"[a-z][a-z'-]+", text)
    pos = sum(1 for w in words if w in POSITIVE)
    neg = sum(1 for w in words if w in NEGATIVE)
    total = pos + neg
    if total == 0:
        label = "neutral"
    else:
        ratio = pos / total
        label = "positive" if ratio >= 0.62 else ("negative" if ratio <= 0.38 else "mixed")
    return {"positive": pos, "negative": neg, "total_terms": total,
            "label": label, "score": round((pos - neg) / max(total, 1), 3)}


def _token_freq(texts: List[str], n: int = 15) -> List[Dict[str, int]]:
    counter: Counter[str] = Counter()
    for text in texts:
        for w in re.findall(r"[a-z][a-z'-]{2,}", (text or "").lower()):
            if w not in STOPWORDS:
                counter[w] += 1
    return [{"term": k, "count": v} for k, v in counter.most_common(n)]


def competitor_matrix(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """rows: [{name, category, pricing, rating, mentions, sentiment_bias}]"""
    matrix = []
    for r in rows:
        rating = float(r.get("rating") or 0)
        mentions = int(r.get("mentions") or 0)
        matrix.append({
            "name": r.get("name"),
            "category": r.get("category") or "",
            "pricing": r.get("pricing") or "",
            "rating": rating,
            "mention_share_pct": mentions,
            "positioning_notes": r.get("notes") or "",
        })
    matrix.sort(key=lambda x: x["mention_share_pct"], reverse=True)
    return {"competitors": matrix,
            "top_competitor": matrix[0]["name"] if matrix else None,
            "suggestions": _competitive_suggestions(matrix)}


def _competitive_suggestions(matrix: List[Dict[str, Any]]) -> List[str]:
    s: List[str] = []
    if matrix:
        top = max(matrix, key=lambda x: x["rating"])
        s.append(f"Highest-rated competitor: {top['name']} ({top['rating']}) — study its positioning.")
        low = min(matrix, key=lambda x: x["rating"])
        if low["rating"] < 4:
            s.append(f"Rating-weak spot to attack: {low['name']} ({low['rating']}).")
    return s


def build_brief(topic: str, context: str = "") -> Dict[str, Any]:
    return {
        "topic": topic,
        "context": context,
        "objective": f"Understand the current state, players, and momentum around {topic}.",
        "questions": [
            f"What is the latest concrete signal (metric, event, launch) for {topic}?",
            f"Who are the top 3-5 players/competitors and how do they differ?",
            f"What is the dominant sentiment in recent coverage of {topic}?",
            f"What risks or controversies are surrounding {topic} right now?",
            "What would a defensible recommendation be, and what evidence supports it?",
        ],
        "data_sources": [
            "RSS feeds (rss command)",
            "competitor matrix (competitors command)",
            "sentiment over recent headlines (sentiment command)",
            "web/search tool exploration",
        ],
        "deliverables": ["summary.md", "evidence.json", "recommendations.md"],
    }


def cmd_brief(args: argparse.Namespace) -> None:
    b = build_brief(args.topic, args.context)
    print(json.dumps(b, indent=2))


def cmd_rss(args: argparse.Namespace) -> None:
    feeds = args.feeds.split(",") if args.feeds else []
    if not feeds and args.feed_file:
        feeds = [l.strip() for l in open(args.feed_file, encoding="utf-8") if l.strip()]
    all_items: List[Dict[str, Any]] = []
    for f in feeds:
        try:
            got = fetch_rss(f, args.limit)
            for it in got:
                it["feed"] = f
            all_items.extend(got)
        except Exception as e:  # noqa: BLE001
            if args.json:
                all_items.append({"feed": f, "error": str(e)})
            else:
                print(f"[!] {f}: {e}", file=sys.stderr)
    if args.json:
        print(json.dumps({"count": len(all_items), "items": all_items}, indent=2))
        return
    for it in all_items[: args.limit * 3]:
        sent = sentiment(f"{it['title']} {it['summary']}")
        print(f"[{sent['label']:>8}] {it['title'][:100]}")
        if it.get("link"):
            print(f"          {it['link']}")


def cmd_sentiment(args: argparse.Namespace) -> None:
    text = args.text
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    if not text:
        print(json.dumps({"error": "No text (--text or --file required)"}))
        sys.exit(1)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    results = []
    for s in sentences:
        if len(s.strip()) < 10:
            continue
        r = sentiment(s)
        results.append({"sentence": s.strip(), **r})
    combined = sentiment(text)
    out = {"overall": combined, "sentences": results,
           "top_terms": _token_freq([s["sentence"] for s in results])}
    print(json.dumps(out, indent=2))


def cmd_competitors(args: argparse.Namespace) -> None:
    with open(args.input, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = data if isinstance(data, list) else data.get("competitors", [])
    if not rows:
        print(json.dumps({"error": "Empty competitor list"}))
        sys.exit(1)
    print(json.dumps(competitor_matrix(rows), indent=2))


def cmd_pack(args: argparse.Namespace) -> None:
    """Assemble everything the agent already gathered into one research pack."""
    results: Dict[str, Any] = {"topic": args.topic, "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                               "sections": {}}
    if args.brief:
        results["sections"]["brief"] = build_brief(args.brief)
    competitors: List[Dict[str, Any]] = []
    if args.competitors:
        with open(args.competitors, encoding="utf-8") as fh:
            data = json.load(fh)
        competitors = data if isinstance(data, list) else data.get("competitors", [])
        results["sections"]["competitors"] = competitor_matrix(competitors)
    if args.feeds:
        feeds = args.feeds.split(",")
        items = []
        for f in feeds:
            try:
                items.extend(fetch_rss(f, 15))
            except Exception as e:  # noqa: BLE001
                items.append({"feed": f, "error": str(e)})
        results["sections"]["headlines"] = items
        results["sections"]["mentions_sentiment"] = sentiment(
            " ".join((i.get("title") or "") + " " + (i.get("summary") or "") for i in items))
        results["sections"]["top_terms"] = _token_freq(
            [(i.get("title") or "") + " " + (i.get("summary") or "") for i in items])
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
    print(json.dumps(results, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="market_research",
        description="Comprehensive research & market analytics engine")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p = sub.add_parser("brief", help="build a research brief")
    p.add_argument("topic")
    p.add_argument("--context", default="")

    p = sub.add_parser("rss", help="fetch and assess RSS feeds")
    p.add_argument("--feeds", default="")
    p.add_argument("--feed-file", default=None)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("sentiment", help="lexicon sentiment over text/file")
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--file", default=None)

    p = sub.add_parser("competitors", help="competitor matrix from JSON")
    p.add_argument("input")

    p = sub.add_parser("pack", help="assemble a full research pack")
    p.add_argument("topic")
    p.add_argument("--brief", default="")
    p.add_argument("--competitors", default=None)
    p.add_argument("--feeds", default="")
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


DISPATCH = {
    "brief": cmd_brief,
    "rss": cmd_rss,
    "sentiment": cmd_sentiment,
    "competitors": cmd_competitors,
    "pack": cmd_pack,
}


if __name__ == "__main__":
    sys.exit(main())