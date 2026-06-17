"""Smart URL router for Agent-Reach.

Given any URL or query string, returns the recommended Arcen tool name so
callers can decide whether to use a specialised channel or fall back to Jina.

The router detects domain patterns and maps them to the reach_* tools that
have the best chance of returning high-quality content (subtitles, structured
JSON, authenticated reads, etc.) rather than generic HTML.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Domain → tool mapping
# ---------------------------------------------------------------------------

_DOMAIN_MAP: list[tuple[re.Pattern[str], str]] = [
    # Twitter / X
    (re.compile(r"(?:^|\.)(twitter|x)\.com$", re.I), "reach_twitter"),
    # YouTube variants: youtube.com AND youtu.be (the .be TLD, not regex optional)
    (re.compile(r"(?:^|\.)youtube\.com$", re.I), "reach_youtube"),
    (re.compile(r"(?:^|\.)youtu\.be$", re.I), "reach_youtube"),
    # Bilibili
    (re.compile(r"(?:^|\.)bilibili\.com$", re.I), "reach_bilibili"),
    # Reddit
    (re.compile(r"(?:^|\.)reddit\.com$", re.I), "reach_reddit"),
    # GitHub — repos/issues/PRs
    (re.compile(r"(?:^|\.)github\.com$", re.I), "reach_github"),
    # Known RSS-only feed domains
    (re.compile(r"^hnrss\.org$", re.I), "reach_rss"),
    (re.compile(r"^feeds\.", re.I), "reach_rss"),
    (re.compile(r"^rss\.", re.I), "reach_rss"),
]

# Common RSS/Atom path patterns — match .xml, .rss, .atom extensions or
# path segments explicitly named feed/rss/atom
_RSS_PATH_RE = re.compile(
    r"(?:\.(?:xml|rss|atom)(?:[/?#]|$)"   # file extension
    r"|(?:^|/)(?:feed|rss|atom)(?:/[^/]*)?$"  # path segment
    r")",
    re.I,
)


def route_url(url: str) -> str:
    """Return the recommended reach_* tool name for *url*.

    Falls back to ``"reach_web_read"`` for anything that doesn't match a
    specialised channel. Callers should still use ``reach_web_read`` as the
    single entry-point — it calls this function internally and dispatches.
    """
    if not url:
        return "reach_web_read"

    # Strip leading/trailing whitespace
    url = url.strip()

    # Try to parse; if it has no scheme assume https
    if not url.startswith(("http://", "https://", "feed://", "ftp://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return "reach_web_read"

    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""

    # Check known social/video domains first
    for pattern, tool in _DOMAIN_MAP:
        if pattern.search(hostname):
            return tool

    # RSS/Atom heuristic: path contains feed-like segment
    if _RSS_PATH_RE.search(path):
        return "reach_rss"

    # Default — Jina Reader handles anything
    return "reach_web_read"


def is_social_platform(url: str) -> bool:
    """Return True if *url* is a social platform that may need auth."""
    tool = route_url(url)
    return tool in ("reach_twitter", "reach_reddit")


def describe_route(url: str) -> dict:
    """Return a dict with routing decision metadata (useful for debugging)."""
    tool = route_url(url)
    return {
        "url": url,
        "routed_to": tool,
        "requires_auth": is_social_platform(url),
    }
