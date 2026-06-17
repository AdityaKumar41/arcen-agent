"""Agent-Reach tool handlers and schemas for Arcen.

All 9 tools follow the standard Arcen tool pattern: handlers accept (args, **kw)
and return a JSON string. Schemas follow the OpenAI function-calling format.

Zero-config tools (always available once agent-reach is installed):
  reach_web_read   — smart-routed URL reader (Jina, yt-dlp, gh, bili, rss...)
  reach_youtube    — YouTube/video transcript + metadata via yt-dlp
  reach_github     — GitHub repo/issue/PR via gh CLI
  reach_rss        — RSS/Atom feed via feedparser
  reach_bilibili   — Bilibili search + video detail via bili-cli
  reach_search     — semantic web search via Exa (free)
  reach_doctor     — channel health report via agent-reach doctor

Social tools (always shown, graceful error if not configured):
  reach_twitter    — Twitter/X read + search via twitter-cli (cookie required)
  reach_reddit     — Reddit search + post reader via OpenCLI/rdt-cli
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import quote as _url_quote

from tools.registry import tool_error, tool_result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Availability checks
# ---------------------------------------------------------------------------


def _check_reach_available() -> bool:
    """Always show zero-config reach tools; installer handles lazy setup."""
    return True


def _check_reach_social() -> bool:
    """Social tools are always shown so users discover them.
    Actual auth errors are surfaced at call time with a clear setup message.
    """
    return True


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], *, timeout: int = 60, input_text: str | None = None) -> tuple[int, str, str]:
    """Run *cmd*, return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_text,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as exc:
        return 127, "", f"Command not found: {cmd[0]} — {exc}"
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except Exception as exc:
        return 1, "", f"Unexpected error running {cmd[0]}: {exc}"


def _ensure_installed(package: str) -> tuple[bool, str]:
    """Pip-install *package* if it's not importable. Returns (ok, msg)."""
    if shutil.which(package) or _cmd_available(package):
        return True, f"{package} is available."
    try:
        rc, _, err = _run(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            timeout=120,
        )
        if rc != 0:
            return False, f"pip install {package} failed: {err.strip()}"
        return True, f"{package} installed."
    except Exception as exc:
        return False, str(exc)


def _cmd_available(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _jina_read(url: str, timeout: int = 30) -> tuple[bool, str]:
    """Fetch *url* via Jina Reader (https://r.jina.ai/). Returns (ok, text)."""
    jina_url = f"https://r.jina.ai/{url}"
    rc, stdout, stderr = _run(
        ["curl", "-sL", "--max-time", str(timeout),
         "-H", "Accept: text/plain",
         "-H", "X-Return-Format: markdown",
         jina_url],
        timeout=timeout + 5,
    )
    if rc != 0 or not stdout.strip():
        return False, stderr.strip() or "Jina Reader returned empty response."
    return True, stdout.strip()


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

REACH_WEB_READ_SCHEMA = {
    "name": "reach_web_read",
    "description": (
        "Smart internet reader — reads ANY URL and returns clean text/markdown. "
        "Automatically routes to the best channel per domain: "
        "Twitter/X → twitter-cli, YouTube → yt-dlp (subtitles), "
        "GitHub → gh CLI, Bilibili → bili-cli, Reddit → OpenCLI, "
        "RSS feeds → feedparser, everything else → Jina Reader. "
        "Zero API key required for most platforms. "
        "Use this as your single entry-point for reading URLs from any platform."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to read. Include full https:// scheme.",
            },
            "format": {
                "type": "string",
                "enum": ["markdown", "text"],
                "description": "Preferred output format. Default: markdown.",
                "default": "markdown",
            },
            "max_length": {
                "type": "integer",
                "description": "Truncate output to this many characters. 0 = no limit. Default: 8000.",
                "default": 8000,
            },
        },
        "required": ["url"],
    },
}

REACH_YOUTUBE_SCHEMA = {
    "name": "reach_youtube",
    "description": (
        "Get transcript, subtitles, and metadata from YouTube videos (and 1800+ "
        "other sites: Vimeo, Twitch, SoundCloud, etc.) via yt-dlp. "
        "Returns the video title, description, and full subtitle/transcript text. "
        "No API key needed. Use this when a user asks to summarise or quote a video."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "YouTube (or other video site) URL.",
            },
            "lang": {
                "type": "string",
                "description": "Preferred subtitle language code (e.g. 'en', 'zh-Hans'). "
                               "Falls back to auto-generated captions. Default: en.",
                "default": "en",
            },
        },
        "required": ["url"],
    },
}

REACH_GITHUB_SCHEMA = {
    "name": "reach_github",
    "description": (
        "Read GitHub repositories, issues, pull requests, and file contents via "
        "the official `gh` CLI. Works on public repos immediately; private repos "
        "require `gh auth login`. "
        "Supports: repo overview, issue list/detail, PR list/detail, file content, "
        "release notes, and raw repo search."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["repo", "issues", "issue", "prs", "pr", "file", "releases", "search"],
                "description": (
                    "repo — overview of owner/repo. "
                    "issues — list open issues. "
                    "issue — single issue by number. "
                    "prs — list open PRs. "
                    "pr — single PR by number. "
                    "file — read a file path inside the repo. "
                    "releases — latest releases. "
                    "search — search repos by query string."
                ),
            },
            "repo": {
                "type": "string",
                "description": "owner/repo (e.g. 'fastapi/fastapi'). Required for all actions except 'search'.",
            },
            "number": {
                "type": "integer",
                "description": "Issue or PR number. Required for 'issue' and 'pr' actions.",
            },
            "path": {
                "type": "string",
                "description": "File path inside the repo. Required for 'file' action.",
            },
            "query": {
                "type": "string",
                "description": "Search query string. Required for 'search' action.",
            },
            "limit": {
                "type": "integer",
                "description": "Max results for list actions. Default: 20.",
                "default": 20,
            },
        },
        "required": ["action"],
    },
}

REACH_RSS_SCHEMA = {
    "name": "reach_rss",
    "description": (
        "Parse any RSS or Atom feed and return a list of recent entries with "
        "title, link, summary, and published date. Works with any publicly "
        "accessible feed URL. Zero config, zero API key. "
        "Great for news sites, HN, tech blogs, podcasts, YouTube channels, etc."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "RSS or Atom feed URL.",
            },
            "limit": {
                "type": "integer",
                "description": "Max entries to return. Default: 15.",
                "default": 15,
            },
        },
        "required": ["url"],
    },
}

REACH_BILIBILI_SCHEMA = {
    "name": "reach_bilibili",
    "description": (
        "Search Bilibili and get video details including title, description, "
        "view count, and subtitle/transcript via bili-cli. "
        "No login required for search and public video info. "
        "Use this for Chinese video content — Bilibili blocks yt-dlp, "
        "bili-cli is the correct backend."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "video"],
                "description": "search — find videos by keyword. video — get detail for a video URL or BV ID.",
            },
            "query": {
                "type": "string",
                "description": "Search keyword. Required for 'search' action.",
            },
            "url": {
                "type": "string",
                "description": "Bilibili video URL or BV ID (e.g. BV1xx411c7mD). Required for 'video' action.",
            },
            "limit": {
                "type": "integer",
                "description": "Max search results. Default: 10.",
                "default": 10,
            },
        },
        "required": ["action"],
    },
}

REACH_SEARCH_SCHEMA = {
    "name": "reach_search",
    "description": (
        "Free semantic web search powered by Exa AI (via agent-reach's mcporter "
        "integration). Returns highly relevant results with full-text excerpts — "
        "better than keyword search for research queries. "
        "Falls back to a direct Exa API call if mcporter MCP is unavailable. "
        "Zero API key required (uses agent-reach's shared Exa access)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query.",
            },
            "limit": {
                "type": "integer",
                "description": "Max results. Default: 10.",
                "default": 10,
            },
            "type": {
                "type": "string",
                "enum": ["auto", "keyword", "neural"],
                "description": "Search type. 'auto' lets Exa decide (recommended). Default: auto.",
                "default": "auto",
            },
        },
        "required": ["query"],
    },
}

REACH_TWITTER_SCHEMA = {
    "name": "reach_twitter",
    "description": (
        "Read and search Twitter/X posts without paying for the API ($0 vs $215/month). "
        "Supports: reading a tweet by URL, searching tweets by keyword or hashtag, "
        "reading a user's timeline, and reading Twitter articles. "
        "Requires one-time Cookie setup: export cookies from browser via Cookie-Editor "
        "extension, then tell the agent 'set up Twitter reach' to configure. "
        "Uses twitter-cli as primary backend with OpenCLI as fallback."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "search", "timeline", "user"],
                "description": (
                    "read — fetch a single tweet by URL. "
                    "search — search tweets by keyword/hashtag. "
                    "timeline — get recent tweets from a user. "
                    "user — get user profile info."
                ),
            },
            "url": {
                "type": "string",
                "description": "Tweet URL. Required for 'read' action.",
            },
            "query": {
                "type": "string",
                "description": "Search query or username. Required for 'search', 'timeline', 'user' actions.",
            },
            "limit": {
                "type": "integer",
                "description": "Max tweets to return. Default: 20.",
                "default": 20,
            },
        },
        "required": ["action"],
    },
}

REACH_REDDIT_SCHEMA = {
    "name": "reach_reddit",
    "description": (
        "Search and read Reddit posts and comments. Bypasses Reddit's 403 server-IP "
        "blocks that prevent direct scraping. "
        "Supports: searching a subreddit, reading a post with comments, "
        "and listing hot posts in a subreddit. "
        "Requires setup: either OpenCLI (reuses your desktop browser session) "
        "or cookie export via Cookie-Editor. Tell the agent 'set up Reddit reach' "
        "for guided setup."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "post", "hot", "new"],
                "description": (
                    "search — search across Reddit or within a subreddit. "
                    "post — read a post and its top comments by URL. "
                    "hot — list hot posts in a subreddit. "
                    "new — list new posts in a subreddit."
                ),
            },
            "query": {
                "type": "string",
                "description": "Search query. Required for 'search' action.",
            },
            "url": {
                "type": "string",
                "description": "Reddit post URL. Required for 'post' action.",
            },
            "subreddit": {
                "type": "string",
                "description": "Subreddit name (without r/). Used for 'hot', 'new', 'search' to scope results.",
            },
            "limit": {
                "type": "integer",
                "description": "Max posts/comments to return. Default: 20.",
                "default": 20,
            },
        },
        "required": ["action"],
    },
}

REACH_DOCTOR_SCHEMA = {
    "name": "reach_doctor",
    "description": (
        "Run `agent-reach doctor` to health-check all internet channels and show "
        "which backends are active, broken, or need credentials. "
        "Use this to diagnose why a channel isn't working, see which backend "
        "is currently selected for each platform, and get fix instructions. "
        "Results are cached for 1 hour; pass force_refresh=true to re-probe now."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "force_refresh": {
                "type": "boolean",
                "description": "Re-run doctor even if cached results are fresh. Default: false.",
                "default": False,
            },
            "channel": {
                "type": "string",
                "description": "Check only this specific channel (e.g. 'twitter', 'youtube'). "
                               "Omit to check all channels.",
            },
        },
        "required": [],
    },
}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _handle_reach_web_read(args: dict, **kw) -> str:
    """Smart-routed URL reader — dispatches to the best channel per domain."""
    from plugins.agent_reach.router import route_url

    url = (args.get("url") or "").strip()
    if not url:
        return tool_error("reach_web_read requires a 'url' parameter.")

    max_len = int(args.get("max_length") or 8000)
    routed_to = route_url(url)

    # Dispatch to the correct specialised handler (avoids code duplication)
    _dispatch: dict[str, Any] = {
        "reach_twitter":  lambda: _handle_reach_twitter({"action": "read", "url": url}, **kw),
        "reach_youtube":  lambda: _handle_reach_youtube({"url": url}, **kw),
        "reach_github":   lambda: _handle_reach_github({"action": "repo", "repo": _github_repo_from_url(url)}, **kw),
        "reach_bilibili": lambda: _handle_reach_bilibili({"action": "video", "url": url}, **kw),
        "reach_reddit":   lambda: _handle_reach_reddit({"action": "post", "url": url}, **kw),
        "reach_rss":      lambda: _handle_reach_rss({"url": url}, **kw),
    }

    if routed_to in _dispatch:
        result_str = _dispatch[routed_to]()
        # Append routing metadata
        try:
            parsed = json.loads(result_str)
            parsed["_routed_via"] = routed_to
            return tool_result(parsed)
        except Exception:
            return result_str

    # Default: Jina Reader
    ok, text = _jina_read(url)
    if not ok:
        return tool_error(
            f"Jina Reader failed to read {url}.\nError: {text}\n\n"
            "Tip: run reach_doctor to check channel health."
        )
    content = text[:max_len] if max_len > 0 else text
    truncated = max_len > 0 and len(text) > max_len
    return tool_result({
        "success": True,
        "url": url,
        "content": content,
        "backend": "Jina Reader",
        "truncated": truncated,
        "_routed_via": "reach_web_read",
    })


def _github_repo_from_url(url: str) -> str:
    """Extract 'owner/repo' from a github.com URL, or return the raw string."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    except Exception:
        pass
    return url


def _handle_reach_youtube(args: dict, **kw) -> str:
    """Extract transcript and metadata from a YouTube (or compatible) video."""
    url = (args.get("url") or "").strip()
    if not url:
        return tool_error("reach_youtube requires a 'url' parameter.")

    lang = (args.get("lang") or "en").strip()

    if not _cmd_available("yt-dlp"):
        ok, msg = _ensure_installed("yt-dlp")
        if not ok:
            return tool_error(
                f"yt-dlp is not installed.\n{msg}\n\n"
                "Install with: pip install yt-dlp\n"
                "Or run: reach_doctor to check channel health."
            )

    # Get video info as JSON
    rc, info_json, err = _run(
        ["yt-dlp", "--dump-json", "--no-playlist", "--quiet", url],
        timeout=30,
    )
    metadata: dict = {}
    if rc == 0 and info_json.strip():
        try:
            metadata = json.loads(info_json)
        except json.JSONDecodeError:
            pass

    # Download subtitles to a temp file
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_path = os.path.join(tmpdir, "sub")
        rc_sub, _, err_sub = _run(
            [
                "yt-dlp",
                "--write-subs", "--write-auto-subs",
                "--sub-lang", lang,
                "--sub-format", "vtt",
                "--skip-download",
                "--no-playlist",
                "--quiet",
                "-o", sub_path,
                url,
            ],
            timeout=60,
        )

        transcript = ""
        # Find the downloaded .vtt file
        for fname in os.listdir(tmpdir):
            if fname.endswith(".vtt"):
                raw = open(os.path.join(tmpdir, fname), encoding="utf-8", errors="ignore").read()
                # Strip VTT header and timestamps for clean text
                lines = []
                for line in raw.splitlines():
                    line = line.strip()
                    if (line.startswith("WEBVTT") or "-->" in line
                            or line.isdigit() or not line):
                        continue
                    # Remove HTML tags
                    import re
                    line = re.sub(r"<[^>]+>", "", line)
                    if line:
                        lines.append(line)
                transcript = " ".join(lines)
                break

    if not transcript:
        # Fallback: return metadata only
        return tool_result({
            "success": True,
            "url": url,
            "title": metadata.get("title", ""),
            "channel": metadata.get("uploader", ""),
            "duration_seconds": metadata.get("duration"),
            "description": (metadata.get("description") or "")[:1000],
            "transcript": None,
            "transcript_note": (
                f"No subtitles available in language '{lang}'. "
                "Try lang='en' or check if the video has auto-captions."
            ),
            "backend": "yt-dlp",
        })

    return tool_result({
        "success": True,
        "url": url,
        "title": metadata.get("title", ""),
        "channel": metadata.get("uploader", ""),
        "duration_seconds": metadata.get("duration"),
        "description": (metadata.get("description") or "")[:500],
        "transcript": transcript[:12000],
        "transcript_truncated": len(transcript) > 12000,
        "backend": "yt-dlp",
    })


def _handle_reach_github(args: dict, **kw) -> str:
    """Read GitHub repos, issues, PRs, files, and search via gh CLI."""
    action = (args.get("action") or "repo").strip()
    repo = (args.get("repo") or "").strip()
    number = args.get("number")
    path = (args.get("path") or "").strip()
    query = (args.get("query") or "").strip()
    limit = min(int(args.get("limit") or 20), 100)

    if not _cmd_available("gh"):
        return tool_error(
            "The `gh` CLI is not installed.\n"
            "Install it with: brew install gh  (macOS)\n"
            "            or: sudo apt install gh  (Linux)\n"
            "Then run: gh auth login  (for private repos)\n"
            "Public repos work without auth."
        )

    if action == "search":
        if not query:
            return tool_error("reach_github 'search' requires a 'query' parameter.")
        rc, out, err = _run(
            ["gh", "search", "repos", query, "--limit", str(limit), "--json",
             "name,fullName,description,stargazersCount,language,url"],
            timeout=30,
        )
    elif action == "repo":
        if not repo:
            return tool_error("reach_github 'repo' requires a 'repo' parameter (owner/repo).")
        rc, out, err = _run(
            ["gh", "repo", "view", repo, "--json",
             "name,owner,description,stargazerCount,forkCount,openIssueCount,"
             "primaryLanguage,licenseInfo,url,homepageUrl,topics,createdAt,updatedAt,"
             "repositoryTopics,readme"],
            timeout=30,
        )
    elif action == "issues":
        if not repo:
            return tool_error("reach_github 'issues' requires a 'repo' parameter.")
        rc, out, err = _run(
            ["gh", "issue", "list", "-R", repo, "--limit", str(limit),
             "--json", "number,title,state,labels,createdAt,url,author"],
            timeout=30,
        )
    elif action == "issue":
        if not repo or not number:
            return tool_error("reach_github 'issue' requires 'repo' and 'number' parameters.")
        rc, out, err = _run(
            ["gh", "issue", "view", str(number), "-R", repo,
             "--json", "number,title,state,body,labels,comments,author,createdAt,url"],
            timeout=30,
        )
    elif action == "prs":
        if not repo:
            return tool_error("reach_github 'prs' requires a 'repo' parameter.")
        rc, out, err = _run(
            ["gh", "pr", "list", "-R", repo, "--limit", str(limit),
             "--json", "number,title,state,labels,createdAt,url,author"],
            timeout=30,
        )
    elif action == "pr":
        if not repo or not number:
            return tool_error("reach_github 'pr' requires 'repo' and 'number' parameters.")
        rc, out, err = _run(
            ["gh", "pr", "view", str(number), "-R", repo,
             "--json", "number,title,state,body,labels,files,reviews,author,createdAt,url"],
            timeout=30,
        )
    elif action == "file":
        if not repo or not path:
            return tool_error("reach_github 'file' requires 'repo' and 'path' parameters.")
        rc, out, err = _run(
            ["gh", "api", f"repos/{repo}/contents/{path.lstrip('/')}"],
            timeout=30,
        )
        if rc == 0 and out.strip():
            try:
                data = json.loads(out)
                import base64
                content_b64 = data.get("content", "")
                content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                return tool_result({
                    "success": True, "repo": repo, "path": path,
                    "content": content[:10000],
                    "truncated": len(content) > 10000,
                    "backend": "gh CLI",
                })
            except Exception as exc:
                return tool_error(f"Failed to decode file content: {exc}\nRaw: {out[:500]}")
    elif action == "releases":
        if not repo:
            return tool_error("reach_github 'releases' requires a 'repo' parameter.")
        rc, out, err = _run(
            ["gh", "release", "list", "-R", repo, "--limit", str(limit),
             "--json", "name,tagName,publishedAt,isLatest,url"],
            timeout=30,
        )
    else:
        return tool_error(f"Unknown action '{action}'. Valid: repo, issues, issue, prs, pr, file, releases, search.")

    if rc != 0:
        return tool_error(
            f"gh CLI returned error (exit {rc}) for action '{action}'.\n"
            f"stderr: {err.strip() or '(none)'}\n"
            f"stdout: {out.strip()[:300] or '(none)'}\n\n"
            "If this is a private repo, run: gh auth login"
        )

    try:
        data = json.loads(out)
        return tool_result({"success": True, "action": action, "repo": repo, "data": data, "backend": "gh CLI"})
    except json.JSONDecodeError:
        return tool_result({"success": True, "action": action, "repo": repo, "raw": out[:8000], "backend": "gh CLI"})


def _handle_reach_rss(args: dict, **kw) -> str:
    """Parse an RSS/Atom feed and return recent entries."""
    url = (args.get("url") or "").strip()
    limit = min(int(args.get("limit") or 15), 100)

    if not url:
        return tool_error("reach_rss requires a 'url' parameter.")

    # Try importing feedparser
    try:
        import feedparser  # type: ignore
    except ImportError:
        ok, msg = _ensure_installed("feedparser")
        if not ok:
            return tool_error(f"feedparser not installed: {msg}\nInstall with: pip install feedparser")
        try:
            import feedparser  # type: ignore  # noqa: F811
        except ImportError:
            return tool_error("feedparser installed but still not importable — try restarting.")

    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        return tool_error(f"feedparser failed to parse '{url}': {exc}")

    if feed.get("bozo") and not feed.get("entries"):
        exc = feed.get("bozo_exception")
        return tool_error(
            f"Failed to parse RSS feed at '{url}'.\n"
            f"Error: {exc}\n\n"
            "Check that the URL is a valid RSS/Atom feed."
        )

    entries = []
    for entry in feed.entries[:limit]:
        entries.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": (entry.get("summary") or "")[:500],
            "author": entry.get("author", ""),
        })

    return tool_result({
        "success": True,
        "feed_title": feed.feed.get("title", ""),
        "feed_url": url,
        "feed_description": feed.feed.get("description", "")[:300],
        "entry_count": len(entries),
        "entries": entries,
        "backend": "feedparser",
    })


def _handle_reach_bilibili(args: dict, **kw) -> str:
    """Search Bilibili or get video details via bili-cli."""
    action = (args.get("action") or "search").strip()
    query = (args.get("query") or "").strip()
    url = (args.get("url") or "").strip()
    limit = min(int(args.get("limit") or 10), 50)

    # Check bili-cli availability
    if not _cmd_available("bili"):
        # Try agent-reach install to set it up
        return tool_error(
            "bili-cli is not installed. Agent-Reach uses bili-cli for Bilibili access.\n\n"
            "Install via agent-reach:\n"
            "  pip install https://github.com/Panniantong/agent-reach/archive/main.zip\n"
            "  agent-reach install\n\n"
            "Or install bili-cli directly:\n"
            "  pip install bili-cli\n\n"
            "Run reach_doctor to check the Bilibili channel status."
        )

    if action == "search":
        if not query:
            return tool_error("reach_bilibili 'search' requires a 'query' parameter.")
        rc, out, err = _run(
            ["bili", "search", query, "--limit", str(limit)],
            timeout=30,
        )
    elif action == "video":
        target = url or query
        if not target:
            return tool_error("reach_bilibili 'video' requires a 'url' or BV ID.")
        rc, out, err = _run(
            ["bili", "info", target],
            timeout=30,
        )
    else:
        return tool_error(f"Unknown action '{action}'. Valid: search, video.")

    if rc != 0:
        return tool_error(
            f"bili-cli error (exit {rc}) for action '{action}'.\n"
            f"stderr: {err.strip() or '(none)'}\n"
            f"stdout: {out.strip()[:300] or '(none)'}\n\n"
            "Run reach_doctor to check Bilibili channel health."
        )

    return tool_result({
        "success": True,
        "action": action,
        "raw_output": out[:8000],
        "backend": "bili-cli",
    })


def _handle_reach_search(args: dict, **kw) -> str:
    """Semantic web search via Exa (free tier via agent-reach)."""
    query = (args.get("query") or "").strip()
    limit = min(int(args.get("limit") or 10), 50)
    search_type = (args.get("type") or "auto").strip()

    if not query:
        return tool_error("reach_search requires a 'query' parameter.")

    # Try agent-reach's exa_search channel
    rc, out, err = _run(
        ["agent-reach", "search", "--query", query,
         "--limit", str(limit), "--type", search_type],
        timeout=45,
    )

    if rc == 0 and out.strip():
        try:
            data = json.loads(out)
            return tool_result({
                "success": True,
                "query": query,
                "results": data,
                "backend": "Exa via agent-reach",
            })
        except json.JSONDecodeError:
            return tool_result({
                "success": True,
                "query": query,
                "raw": out[:8000],
                "backend": "Exa via agent-reach",
            })

    # Fallback: Jina Reader search (https://s.jina.ai)
    jina_search_url = f"https://s.jina.ai/{_url_quote(query)}"
    ok, text = _jina_read(jina_search_url, timeout=30)
    if ok and text:
        return tool_result({
            "success": True,
            "query": query,
            "results_text": text[:8000],
            "backend": "Jina Search (fallback)",
            "note": "Exa via agent-reach unavailable; using Jina Search as fallback.",
        })

    return tool_error(
        f"reach_search failed for query '{query}'.\n"
        f"agent-reach error: {err.strip() or out.strip() or 'unknown'}\n\n"
        "Ensure agent-reach is installed and configured:\n"
        "  pip install https://github.com/Panniantong/agent-reach/archive/main.zip\n"
        "  agent-reach install\n"
        "Then run reach_doctor to verify the search channel."
    )


def _handle_reach_twitter(args: dict, **kw) -> str:
    """Read and search Twitter/X via twitter-cli."""
    action = (args.get("action") or "read").strip()
    url = (args.get("url") or "").strip()
    query = (args.get("query") or "").strip()
    limit = min(int(args.get("limit") or 20), 100)

    # Check twitter-cli
    if not _cmd_available("twitter"):
        return tool_error(
            "twitter-cli is not installed or not configured.\n\n"
            "Setup steps:\n"
            "1. Install: pip install twitter-cli  (or agent-reach will do it)\n"
            "2. Export your Twitter cookies using the Cookie-Editor browser extension\n"
            "3. Tell the agent: 'help me set up Twitter reach'\n\n"
            "Agent-Reach setup command:\n"
            "  pip install https://github.com/Panniantong/agent-reach/archive/main.zip\n"
            "  agent-reach install\n\n"
            "Run reach_doctor to see Twitter channel status."
        )

    if action == "read":
        if not url:
            return tool_error("reach_twitter 'read' requires a 'url' parameter (tweet URL).")
        rc, out, err = _run(["twitter", "get", url], timeout=30)
    elif action == "search":
        if not query:
            return tool_error("reach_twitter 'search' requires a 'query' parameter.")
        rc, out, err = _run(
            ["twitter", "search", query, "--limit", str(limit)],
            timeout=30,
        )
    elif action == "timeline":
        if not query:
            return tool_error("reach_twitter 'timeline' requires a 'query' parameter (username).")
        rc, out, err = _run(
            ["twitter", "timeline", query, "--limit", str(limit)],
            timeout=30,
        )
    elif action == "user":
        if not query:
            return tool_error("reach_twitter 'user' requires a 'query' parameter (username).")
        rc, out, err = _run(["twitter", "user", query], timeout=30)
    else:
        return tool_error(f"Unknown action '{action}'. Valid: read, search, timeline, user.")

    if rc != 0:
        stderr = err.strip()
        if "cookie" in stderr.lower() or "auth" in stderr.lower() or "login" in stderr.lower():
            return tool_error(
                "Twitter authentication required.\n"
                "Your Twitter cookies are missing or expired.\n\n"
                "To reconfigure:\n"
                "1. Log in to twitter.com in your browser\n"
                "2. Export cookies with Cookie-Editor extension (Export → Netscape format)\n"
                "3. Tell the agent 'help me reconfigure Twitter reach'\n\n"
                "Run reach_doctor to see the current Twitter channel status."
            )
        return tool_error(
            f"twitter-cli error (exit {rc}) for action '{action}'.\n"
            f"Error: {stderr or out.strip()[:300] or 'unknown'}"
        )

    return tool_result({
        "success": True,
        "action": action,
        "raw_output": out[:8000],
        "backend": "twitter-cli",
    })


def _handle_reach_reddit(args: dict, **kw) -> str:
    """Search and read Reddit via OpenCLI or rdt-cli."""
    action = (args.get("action") or "search").strip()
    query = (args.get("query") or "").strip()
    url = (args.get("url") or "").strip()
    subreddit = (args.get("subreddit") or "").strip()
    limit = min(int(args.get("limit") or 20), 100)

    # Try rdt-cli first, then opencli
    backend = None
    for candidate in ["rdt", "opencli"]:
        if _cmd_available(candidate):
            backend = candidate
            break

    if backend is None:
        return tool_error(
            "No Reddit backend is installed (checked: rdt-cli, opencli).\n\n"
            "Setup options:\n"
            "A) OpenCLI (desktop, reuses browser session — easiest):\n"
            "   pip install opencli\n"
            "   opencli reddit login\n\n"
            "B) rdt-cli (cookie-based, works on servers):\n"
            "   pip install rdt-cli\n"
            "   Export Reddit cookies with Cookie-Editor, then:\n"
            "   rdt config set cookies <path-to-cookies.txt>\n\n"
            "Run reach_doctor to check Reddit channel status."
        )

    if action == "search":
        if not query:
            return tool_error("reach_reddit 'search' requires a 'query' parameter.")
        cmd = [backend, "reddit", "search", query, "--limit", str(limit)]
        if subreddit:
            cmd += ["--subreddit", subreddit]
    elif action == "post":
        if not url:
            return tool_error("reach_reddit 'post' requires a 'url' parameter (Reddit post URL).")
        cmd = [backend, "reddit", "post", url, "--comments", str(limit)]
    elif action in ("hot", "new"):
        if not subreddit:
            return tool_error(f"reach_reddit '{action}' requires a 'subreddit' parameter.")
        cmd = [backend, "reddit", action, f"r/{subreddit}", "--limit", str(limit)]
    else:
        return tool_error(f"Unknown action '{action}'. Valid: search, post, hot, new.")

    rc, out, err = _run(cmd, timeout=30)

    if rc != 0:
        stderr = err.strip()
        if any(kw in stderr.lower() for kw in ("cookie", "auth", "login", "403", "unauthorized")):
            return tool_error(
                "Reddit authentication required or cookies expired.\n\n"
                "To reconfigure:\n"
                "1. Log in to reddit.com in your browser\n"
                "2. Export cookies with Cookie-Editor extension\n"
                "3. Run: rdt config set cookies <path-to-cookies.txt>\n"
                "   Or: opencli reddit login (if using OpenCLI)\n\n"
                "Run reach_doctor to see Reddit channel status."
            )
        return tool_error(
            f"{backend} error (exit {rc}) for Reddit action '{action}'.\n"
            f"Error: {stderr or out.strip()[:300] or 'unknown'}"
        )

    return tool_result({
        "success": True,
        "action": action,
        "raw_output": out[:8000],
        "backend": backend,
    })


def _handle_reach_doctor(args: dict, **kw) -> str:
    """Run agent-reach doctor and return channel health report."""
    from plugins.agent_reach.health_cache import get_channel_health, invalidate_cache

    force_refresh = bool(args.get("force_refresh", False))
    channel_filter = (args.get("channel") or "").strip().lower()

    if force_refresh:
        invalidate_cache()

    if not _cmd_available("agent-reach"):
        return tool_error(
            "agent-reach CLI is not installed.\n\n"
            "Install it with:\n"
            "  pip install https://github.com/Panniantong/agent-reach/archive/main.zip\n"
            "  agent-reach install\n\n"
            "After installation, agent-reach doctor will show channel health."
        )

    # Run doctor directly to get fresh terminal output (more readable than JSON)
    cmd = ["agent-reach", "doctor"]
    if channel_filter:
        cmd += ["--channel", channel_filter]

    rc, out, err = _run(cmd, timeout=60)
    combined = (out + "\n" + err).strip()

    # Also try to get structured JSON for caching
    health = get_channel_health(force_refresh=force_refresh)

    if rc != 0 and not combined:
        return tool_error(
            f"agent-reach doctor failed (exit {rc}).\n"
            f"Error: {err.strip() or 'unknown'}\n\n"
            "Try reinstalling: pip install https://github.com/Panniantong/agent-reach/archive/main.zip"
        )

    return tool_result({
        "success": True,
        "report": combined[:10000],
        "structured": health if health else None,
        "cached": not force_refresh and bool(health.get("_cached_at")),
        "backend": "agent-reach doctor",
    })
