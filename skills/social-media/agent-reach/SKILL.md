---
name: agent-reach
description: "Internet capability layer: read & search Twitter, Reddit, YouTube, GitHub, Bilibili, RSS, TikTok, Threads, Bluesky, Substack, Medium, any URL — zero API fees."
version: 1.1.0
author: Panniantong/Agent-Reach + Arcen
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [agent-reach]
  install: "pip install https://github.com/Panniantong/agent-reach/archive/main.zip && agent-reach install"
metadata:
  arcen:
    tags: [internet, social-media, twitter, reddit, youtube, github, bilibili, rss, tiktok, threads, bsky, web, search, free]
    homepage: https://github.com/Panniantong/agent-reach
---

# Agent-Reach — Internet Capability Layer

Agent-Reach gives you access to the entire internet — Twitter, Reddit, YouTube,
GitHub, Bilibili, RSS, TikTok, Threads, Bluesky, Medium, Substack, and any webpage — without paying for APIs. Zero config
for most platforms, cookie-based for social ones.

**Use the Arcen tools** (`reach_web_read`, `reach_youtube`, etc.) directly — or
call the upstream CLIs via the terminal if you prefer fine-grained control.

---

## Quick Decision Guide

When a user wants to "read", "check", "summarise", or "search" something:

| User says... | Use... |
|---|---|
| Any URL → read it | `reach_web_read` (auto-routes to best channel) |
| Read a tweet / X post | `reach_twitter action=read url=...` |
| Search Twitter / X | `reach_twitter action=search query=...` |
| Read/summarise a YouTube video | `reach_youtube url=...` |
| Search / read Reddit | `reach_reddit action=search query=...` |
| GitHub repo info / issues / PRs | `reach_github action=repo repo=owner/repo` |
| Parse an RSS/Atom feed | `reach_rss url=...` |
| Search Bilibili | `reach_bilibili action=search query=...` |
| Search the entire web (free) | `reach_search query=...` |
| "What can reach do?" / channel broken | `reach_doctor` |

**Single-entry-point shortcut**: `reach_web_read` auto-detects the platform
from the URL (including TikTok, Threads, Bluesky, Substack, Medium) and routes to the right channel. Start here when you're unsure.

---

## Supported Platforms

### 🌐 Web — any URL (zero config, always available)

**Arcen tool:** `reach_web_read url=<url>`

**Upstream CLI (direct):**
```bash
curl -sL -H "Accept: text/plain" "https://r.jina.ai/https://example.com"
```

Jina Reader strips ads, navigation, and noise — returns clean Markdown. Works
on any public URL including paywalled-but-indexable content, Substack, Medium, TikTok, Threads, and Bluesky.

---

### 📺 YouTube / Video (zero config, yt-dlp)

**Arcen tool:** `reach_youtube url=<youtube-url>`

**Upstream CLI (direct):**
```bash
# Get video metadata
yt-dlp --dump-json --no-playlist "https://youtube.com/watch?v=VIDEO_ID"

# Download subtitles (VTT) — English auto-generated
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format vtt \
       --skip-download --no-playlist -o /tmp/sub "VIDEO_URL"

# List available subtitle languages
yt-dlp --list-subs --no-playlist "VIDEO_URL"

# Twitch, Vimeo, SoundCloud, and 1800+ other sites work the same way
```

**Notes:**
- Bilibili is **NOT** handled by yt-dlp — use `reach_bilibili` instead (Bilibili 412-blocked yt-dlp)
- For private/age-gated YouTube videos, `yt-dlp --cookies-from-browser chrome` may help
- If no subtitles exist, `reach_youtube` returns metadata only (title, description, duration)

---

### 📦 GitHub (zero config for public repos, `gh auth login` for private)

**Arcen tool:** `reach_github action=<action> repo=owner/repo`

**Upstream CLI (direct):**
```bash
# Repo overview
gh repo view fastapi/fastapi

# List issues
gh issue list -R fastapi/fastapi --limit 20 --json number,title,state,url

# Read issue #1234
gh issue view 1234 -R fastapi/fastapi --json number,title,body,comments

# List PRs
gh pr list -R fastapi/fastapi --limit 20

# Read a file
gh api repos/fastapi/fastapi/contents/README.md | jq -r '.content' | base64 -d

# Search repos
gh search repos "machine learning framework" --limit 10 --json name,description,stargazersCount

# Auth login (for private repos, fork, issue creation)
gh auth login
```

---

### 📡 RSS / Atom (zero config, feedparser)

**Arcen tool:** `reach_rss url=<feed-url>`

**Upstream CLI (direct — via Python):**
```bash
python3 -c "
import feedparser, json
feed = feedparser.parse('https://hnrss.org/frontpage')
for e in feed.entries[:10]:
    print(e.title, '-', e.link)
"
```

**Common useful feeds:**
- Hacker News: `https://hnrss.org/frontpage` (or `/newest`, `/ask`, `/show`)
- GitHub releases: `https://github.com/OWNER/REPO/releases.atom`
- Reddit subreddit: `https://www.reddit.com/r/SUBREDDIT.rss`
- YouTube channel: `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`

---

### 📺 Bilibili (zero config via bili-cli)

**Arcen tool:** `reach_bilibili action=search query=<keyword>`
**Arcen tool:** `reach_bilibili action=video url=<bilibili-url>`

**Upstream CLI (direct):**
```bash
# Search videos
bili search "AI tutorial" --limit 10

# Get video info by BV ID or URL
bili info BV1xx411c7mD
bili info "https://www.bilibili.com/video/BV1xx411c7mD"
```

**Important:** yt-dlp is **blocked by Bilibili** (HTTP 412). Always use bili-cli
for Bilibili. If bili-cli returns errors, run `reach_doctor` to check status.

---

### 🔍 Web Search — Exa (auto-configured, free)

**Arcen tool:** `reach_search query=<natural language query>`

**Direct fallback (Jina Search):**
```bash
curl -sL "https://s.jina.ai/what+is+the+best+LLM+framework+2025"
```

Exa provides semantic (neural) search — better than keyword search for research
queries. It's the same engine agent-reach uses after `agent-reach install`.

---

### 🐦 Twitter / X (cookie required)

**Arcen tool:** `reach_twitter action=read url=<tweet-url>`
**Arcen tool:** `reach_twitter action=search query=<keyword>`
**Arcen tool:** `reach_twitter action=timeline query=<username>`

**Setup (one-time):**
1. Log in to twitter.com in your browser
2. Install [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) extension
3. Click Cookie-Editor → Export → "Netscape" format → Copy
4. Save to a file, e.g. `~/.config/twitter-cookies.txt`
5. Run: `twitter config set cookies ~/.config/twitter-cookies.txt`

**Upstream CLI (direct):**
```bash
# Read a tweet
twitter get "https://x.com/user/status/1234567890"

# Search tweets
twitter search "Claude AI" --limit 20

# Get user timeline
twitter timeline @anthropic --limit 20

# User info
twitter user @anthropic
```

> ⚠️ Use a **dedicated alt account** for Twitter/X automation — platform may
> detect non-browser API calls. Never use your main account.

---

### 📖 Reddit (auth required — OpenCLI or rdt-cli)

**Arcen tool:** `reach_reddit action=search query=<keyword>`
**Arcen tool:** `reach_reddit action=post url=<reddit-post-url>`
**Arcen tool:** `reach_reddit action=hot subreddit=<subreddit>`

**Setup Option A — OpenCLI (desktop, reuses browser session):**
```bash
pip install opencli
opencli reddit login          # opens browser, no cookie copy needed
```

**Setup Option B — rdt-cli (servers/headless):**
```bash
pip install rdt-cli
# 1. Log in to reddit.com in browser
# 2. Export cookies with Cookie-Editor (Netscape format)
# 3. Configure:
rdt config set cookies ~/.config/reddit-cookies.txt
```

**Upstream CLI (direct):**
```bash
# Search (OpenCLI)
opencli reddit search "best python web framework" --subreddit programming --limit 20

# Read a post + comments (rdt-cli)
rdt post "https://www.reddit.com/r/python/comments/xxxxx/post_title/"

# Hot posts in subreddit
opencli reddit hot r/MachineLearning --limit 20
```

---

## Diagnosing Issues

### Run health check
```bash
# Via Arcen tool
reach_doctor

# Via CLI
agent-reach doctor
```

Doctor tells you:
- Which backend is currently active for each channel
- Whether backends are healthy or broken
- Exact fix instructions for each problem

### Common fixes

| Problem | Fix |
|---|---|
| `twitter-cli not found` | `pip install twitter-cli` then re-export cookies |
| `bili-cli` errors | `pip install bili-cli` — yt-dlp is blocked by Bilibili |
| Reddit 403 | Cookies expired → re-export and reconfigure |
| `gh` not found | `brew install gh` (macOS) or `sudo apt install gh` (Linux) |
| `yt-dlp` outdated | `pip install -U yt-dlp` |
| agent-reach outdated | `pip install https://github.com/Panniantong/agent-reach/archive/main.zip` |

---

## Install / Update

```bash
# Initial install
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install           # installs Node.js, gh, mcporter, Exa

# Update to latest
pip install --upgrade https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install           # updates channel routing

# Check what's installed
agent-reach doctor

# Safe mode (no auto system installs, just tells you what to do)
agent-reach install --safe
```

---

## Backend Priority (what runs under the hood)

| Platform | Primary → Fallback |
|---|---|
| Web | Jina Reader (https://r.jina.ai) |
| Twitter | twitter-cli → OpenCLI → bird |
| YouTube | yt-dlp (subtitles + metadata) |
| GitHub | gh CLI |
| Bilibili | bili-cli → OpenCLI (yt-dlp retired — 412 blocked) |
| Reddit | OpenCLI → rdt-cli |
| RSS | feedparser |
| Search | Exa (via mcporter MCP) → Jina Search |

Agent-Reach maintains this routing and updates it when platforms change.
You never need to update backend selection yourself.
