"""Agent-Reach plugin for Arcen — internet capability layer.

Registers 9 tools that give the agent zero-config access to social platforms,
video transcripts, GitHub, RSS feeds, and any webpage:

  reach_web_read   — any URL → clean markdown via Jina Reader (smart-routes
                     to the best channel based on domain)
  reach_youtube    — YouTube (+ 1800 sites) transcript via yt-dlp
  reach_github     — GitHub repo/issue/PR reader via gh CLI
  reach_rss        — RSS/Atom feed parser via feedparser
  reach_bilibili   — Bilibili search + video detail via bili-cli
  reach_search     — free web search via Exa (auto-configured by agent-reach)
  reach_twitter    — read/search Twitter via twitter-cli (cookie required)
  reach_reddit     — search/read Reddit via OpenCLI/rdt-cli (auth required)
  reach_doctor     — health-check all channels via `agent-reach doctor`

The zero-config tools (reach_web_read, reach_youtube, reach_github, reach_rss,
reach_bilibili, reach_search, reach_doctor) are always available once
agent-reach is installed.  The social tools (reach_twitter, reach_reddit)
additionally require platform credentials — their check_fn returns True even
without credentials so they appear in `arcen tools`, but the handler surfaces
a clear setup message if the cookie/auth is not yet configured.

Installation is handled lazily on first use via plugins.agent_reach.installer.
"""

from __future__ import annotations

from plugins.agent_reach.tools import (
    # schemas
    REACH_BILIBILI_SCHEMA,
    REACH_DOCTOR_SCHEMA,
    REACH_GITHUB_SCHEMA,
    REACH_REDDIT_SCHEMA,
    REACH_RSS_SCHEMA,
    REACH_SEARCH_SCHEMA,
    REACH_TWITTER_SCHEMA,
    REACH_WEB_READ_SCHEMA,
    REACH_YOUTUBE_SCHEMA,
    # check functions
    _check_reach_available,
    _check_reach_social,
    # handlers
    _handle_reach_bilibili,
    _handle_reach_doctor,
    _handle_reach_github,
    _handle_reach_reddit,
    _handle_reach_rss,
    _handle_reach_search,
    _handle_reach_twitter,
    _handle_reach_web_read,
    _handle_reach_youtube,
)

# (name, schema, handler, check_fn, emoji)
_TOOLS = [
    ("reach_web_read",  REACH_WEB_READ_SCHEMA,  _handle_reach_web_read,  _check_reach_available, "🌐"),
    ("reach_youtube",   REACH_YOUTUBE_SCHEMA,   _handle_reach_youtube,   _check_reach_available, "📺"),
    ("reach_github",    REACH_GITHUB_SCHEMA,    _handle_reach_github,    _check_reach_available, "📦"),
    ("reach_rss",       REACH_RSS_SCHEMA,       _handle_reach_rss,       _check_reach_available, "📡"),
    ("reach_bilibili",  REACH_BILIBILI_SCHEMA,  _handle_reach_bilibili,  _check_reach_available, "📺"),
    ("reach_search",    REACH_SEARCH_SCHEMA,    _handle_reach_search,    _check_reach_available, "🔍"),
    ("reach_twitter",   REACH_TWITTER_SCHEMA,   _handle_reach_twitter,   _check_reach_social,    "🐦"),
    ("reach_reddit",    REACH_REDDIT_SCHEMA,    _handle_reach_reddit,    _check_reach_social,    "📖"),
    ("reach_doctor",    REACH_DOCTOR_SCHEMA,    _handle_reach_doctor,    _check_reach_available, "🩺"),
]


def register(ctx) -> None:
    """Register all Agent-Reach tools. Called once by the plugin loader."""
    for name, schema, handler, check_fn, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="reach",
            schema=schema,
            handler=handler,
            check_fn=check_fn,
            emoji=emoji,
        )
