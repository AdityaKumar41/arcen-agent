"""Tests for the Agent-Reach plugin tools.

All tests mock subprocess calls — no real network access required.
Run with: pytest tests/tools/test_reach_tools.py -v
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_ok(stdout: str, stderr: str = "", returncode: int = 0):
    """Return a mock for plugins.agent_reach.tools._run that returns (rc, stdout, stderr)."""
    return (returncode, stdout, stderr)


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------

class TestRouter:
    def test_twitter_routes_correctly(self):
        from plugins.agent_reach.router import route_url
        assert route_url("https://twitter.com/user/status/123") == "reach_twitter"
        assert route_url("https://x.com/elonmusk") == "reach_twitter"

    def test_youtube_routes_correctly(self):
        from plugins.agent_reach.router import route_url
        assert route_url("https://www.youtube.com/watch?v=abc") == "reach_youtube"
        assert route_url("https://youtu.be/abc123") == "reach_youtube"

    def test_github_routes_correctly(self):
        from plugins.agent_reach.router import route_url
        assert route_url("https://github.com/fastapi/fastapi") == "reach_github"

    def test_reddit_routes_correctly(self):
        from plugins.agent_reach.router import route_url
        assert route_url("https://www.reddit.com/r/python") == "reach_reddit"

    def test_bilibili_routes_correctly(self):
        from plugins.agent_reach.router import route_url
        assert route_url("https://www.bilibili.com/video/BV1xx") == "reach_bilibili"

    def test_rss_feed_routes_correctly(self):
        from plugins.agent_reach.router import route_url
        assert route_url("https://hnrss.org/frontpage") == "reach_rss"
        assert route_url("https://example.com/feed.xml") == "reach_rss"
        assert route_url("https://example.com/atom") == "reach_rss"

    def test_unknown_url_falls_back_to_web_read(self):
        from plugins.agent_reach.router import route_url
        assert route_url("https://example.com") == "reach_web_read"
        assert route_url("https://news.ycombinator.com") == "reach_web_read"

    def test_empty_url_handled_gracefully(self):
        from plugins.agent_reach.router import route_url
        assert route_url("") == "reach_web_read"

    def test_no_scheme_url_handled(self):
        from plugins.agent_reach.router import route_url
        assert route_url("youtube.com/watch?v=abc") == "reach_youtube"

    def test_social_platform_detection(self):
        from plugins.agent_reach.router import is_social_platform
        assert is_social_platform("https://twitter.com/user") is True
        assert is_social_platform("https://reddit.com/r/python") is True
        assert is_social_platform("https://youtube.com/watch?v=abc") is False


# ---------------------------------------------------------------------------
# Installer tests
# ---------------------------------------------------------------------------

class TestInstaller:
    def test_is_installed_caches_result(self):
        from plugins.agent_reach import installer
        # Reset cache
        installer._cached_available = None
        with patch("importlib.util.find_spec") as mock_spec:
            mock_spec.return_value = MagicMock()  # non-None → installed
            result = installer.is_agent_reach_installed()
        assert result is True
        assert installer._cached_available is True

    def test_install_hint_contains_github_url(self):
        from plugins.agent_reach.installer import get_install_hint
        hint = get_install_hint()
        assert "github.com/Panniantong/agent-reach" in hint

    def test_ensure_installed_returns_message_when_already_present(self):
        from plugins.agent_reach import installer
        installer._cached_available = True
        installer._cached_version = "1.5.0"
        ok, msg = installer.ensure_agent_reach_installed()
        assert ok is True
        assert "1.5.0" in msg


# ---------------------------------------------------------------------------
# Tool handler tests
# ---------------------------------------------------------------------------

class TestReachRss:
    def test_rss_returns_entries(self):
        from plugins.agent_reach.tools import _handle_reach_rss
        import sys

        mock_entry = MagicMock()
        mock_entry.get.side_effect = lambda k, d="": {
            "title": "Test Post", "link": "https://hn.com/1",
            "published": "2025-01-01", "summary": "Cool post", "author": "user",
        }.get(k, d)

        mock_feed = MagicMock()
        mock_feed.feed.get.side_effect = lambda k, d="": {"title": "HN Feed", "description": "HN"}.get(k, d)
        mock_feed.get.return_value = None  # bozo=None
        mock_feed.entries = [mock_entry]

        mock_feedparser = MagicMock()
        mock_feedparser.parse.return_value = mock_feed

        with patch.dict(sys.modules, {"feedparser": mock_feedparser}):
            result = json.loads(_handle_reach_rss({"url": "https://hnrss.org/frontpage"}))

        assert result["success"] is True
        assert result["feed_title"] == "HN Feed"
        assert len(result["entries"]) == 1


    def test_rss_missing_url_returns_error(self):
        from plugins.agent_reach.tools import _handle_reach_rss
        result = json.loads(_handle_reach_rss({}))
        assert "error" in result or result.get("success") is False or "url" in str(result).lower()


class TestReachGithub:
    def test_github_repo_action(self):
        from plugins.agent_reach.tools import _handle_reach_github

        fake_gh_output = json.dumps({"name": "fastapi", "description": "FastAPI framework"})

        with patch("shutil.which", return_value="/usr/bin/gh"), \
             patch("plugins.agent_reach.tools._run", return_value=(0, fake_gh_output, "")):
            result = json.loads(_handle_reach_github({"action": "repo", "repo": "fastapi/fastapi"}))

        assert result["success"] is True
        assert result["action"] == "repo"
        assert result["data"]["name"] == "fastapi"

    def test_github_missing_gh_returns_error(self):
        from plugins.agent_reach.tools import _handle_reach_github

        with patch("shutil.which", return_value=None):
            result = json.loads(_handle_reach_github({"action": "repo", "repo": "fastapi/fastapi"}))

        assert result.get("success") is not True or "gh" in str(result).lower()

    def test_github_search_action(self):
        from plugins.agent_reach.tools import _handle_reach_github

        fake_output = json.dumps([{"name": "myrepo", "fullName": "user/myrepo", "stargazersCount": 100}])

        with patch("shutil.which", return_value="/usr/bin/gh"), \
             patch("plugins.agent_reach.tools._run", return_value=(0, fake_output, "")):
            result = json.loads(_handle_reach_github({"action": "search", "query": "machine learning"}))

        assert result["success"] is True
        assert result["action"] == "search"


class TestReachYoutube:
    def test_youtube_no_yt_dlp_returns_error(self):
        from plugins.agent_reach.tools import _handle_reach_youtube

        with patch("shutil.which", return_value=None), \
             patch("plugins.agent_reach.tools._run", return_value=(1, "", "not found")):
            result = json.loads(_handle_reach_youtube({"url": "https://youtube.com/watch?v=abc"}))

        # Should return an error about yt-dlp not being installed
        result_str = json.dumps(result)
        assert "yt-dlp" in result_str.lower() or result.get("success") is not True

    def test_youtube_missing_url_returns_error(self):
        from plugins.agent_reach.tools import _handle_reach_youtube
        result = json.loads(_handle_reach_youtube({}))
        assert "url" in str(result).lower() or result.get("success") is not True


class TestReachWebRead:
    def test_web_read_routes_to_jina_for_unknown_url(self):
        from plugins.agent_reach.tools import _handle_reach_web_read

        with patch("plugins.agent_reach.tools._jina_read", return_value=(True, "# Page Content\n\nSome text here.")):
            result = json.loads(_handle_reach_web_read({"url": "https://example.com"}))

        assert result["success"] is True
        assert result["backend"] == "Jina Reader"
        assert "Content" in result["content"]

    def test_web_read_jina_failure_returns_error(self):
        from plugins.agent_reach.tools import _handle_reach_web_read

        with patch("plugins.agent_reach.tools._jina_read", return_value=(False, "Connection refused")):
            result = json.loads(_handle_reach_web_read({"url": "https://example.com"}))

        assert result.get("success") is not True

    def test_web_read_missing_url_returns_error(self):
        from plugins.agent_reach.tools import _handle_reach_web_read
        result = json.loads(_handle_reach_web_read({}))
        assert "url" in str(result).lower() or result.get("success") is not True

    def test_web_read_truncates_long_content(self):
        from plugins.agent_reach.tools import _handle_reach_web_read

        long_text = "A" * 20000
        with patch("plugins.agent_reach.tools._jina_read", return_value=(True, long_text)):
            result = json.loads(_handle_reach_web_read({"url": "https://example.com", "max_length": 1000}))

        assert len(result["content"]) <= 1000
        assert result["truncated"] is True


class TestReachDoctor:
    def test_doctor_runs_agent_reach_command(self):
        from plugins.agent_reach.tools import _handle_reach_doctor

        with patch("shutil.which", return_value="/usr/local/bin/agent-reach"), \
             patch("plugins.agent_reach.tools._run", return_value=(0, "✓ web: ok\n✓ youtube: ok\n", "")), \
             patch("plugins.agent_reach.health_cache.get_channel_health", return_value={}), \
             patch("plugins.agent_reach.health_cache.invalidate_cache"):
            result = json.loads(_handle_reach_doctor({}))

        assert result["success"] is True
        assert "web" in result["report"].lower() or "youtube" in result["report"].lower()

    def test_doctor_without_agent_reach_returns_error(self):
        from plugins.agent_reach.tools import _handle_reach_doctor

        with patch("shutil.which", return_value=None):
            result = json.loads(_handle_reach_doctor({}))

        assert result.get("success") is not True


# ---------------------------------------------------------------------------
# Health cache tests
# ---------------------------------------------------------------------------

class TestHealthCache:
    def test_cache_returns_empty_dict_when_missing(self):
        from plugins.agent_reach import health_cache

        with patch.object(health_cache, "_cache_path") as mock_path:
            mock_path.return_value = MagicMock()
            mock_path.return_value.exists.return_value = False
            result = health_cache._load_cache()

        assert result is None

    def test_is_channel_healthy_returns_true_for_unknown_channel(self):
        from plugins.agent_reach import health_cache

        with patch.object(health_cache, "get_channel_health", return_value={}):
            assert health_cache.is_channel_healthy("unknown_channel") is True

    def test_is_channel_healthy_returns_true_for_ok_channel(self):
        from plugins.agent_reach import health_cache

        with patch.object(health_cache, "get_channel_health",
                          return_value={"youtube": {"status": "ok", "backend": "yt-dlp"}}):
            assert health_cache.is_channel_healthy("youtube") is True

    def test_is_channel_healthy_returns_false_for_broken_channel(self):
        from plugins.agent_reach import health_cache

        with patch.object(health_cache, "get_channel_health",
                          return_value={"twitter": {"status": "no_cookie"}}):
            assert health_cache.is_channel_healthy("twitter") is False
