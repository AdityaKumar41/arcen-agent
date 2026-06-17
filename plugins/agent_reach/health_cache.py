"""Channel health cache for Agent-Reach.

Caches `agent-reach doctor` results for 1 hour (configurable) so the agent
doesn't re-probe every channel on each tool call. The cache is stored as JSON
in the Arcen home directory so it persists across sessions and is profile-aware.

The health report is used by reach_web_read's routing logic to skip known-broken
channels and try the next backend immediately.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

from arcen_constants import get_arcen_home

logger = logging.getLogger(__name__)

# How long (seconds) to trust cached doctor results before re-running
_CACHE_TTL_SECONDS = 3600  # 1 hour

_CACHE_FILENAME = "agent_reach_health.json"


def _cache_path() -> Path:
    return Path(get_arcen_home()) / _CACHE_FILENAME


def _load_cache() -> Optional[dict]:
    """Load the cached health report if it exists and is still fresh."""
    try:
        path = _cache_path()
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = data.get("_cached_at", 0)
        if time.time() - cached_at > _CACHE_TTL_SECONDS:
            logger.debug("agent-reach health cache expired, will re-probe.")
            return None
        return data
    except Exception as exc:
        logger.debug("Failed to load agent-reach health cache: %s", exc)
        return None


def _save_cache(report: dict) -> None:
    """Persist a health report to disk with a timestamp."""
    try:
        path = _cache_path()
        report["_cached_at"] = time.time()
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("Failed to save agent-reach health cache: %s", exc)


def invalidate_cache() -> None:
    """Remove the health cache (e.g. after install / channel reconfiguration)."""
    try:
        path = _cache_path()
        if path.exists():
            path.unlink()
    except Exception as exc:
        logger.debug("Failed to invalidate agent-reach health cache: %s", exc)


def get_channel_health(force_refresh: bool = False) -> dict:
    """Return the channel health report, refreshing from agent-reach doctor if stale.

    Returns a dict with keys per channel, e.g.:
      {
        "web":      {"status": "ok", "backend": "Jina Reader", ...},
        "youtube":  {"status": "ok", "backend": "yt-dlp",      ...},
        "twitter":  {"status": "no_cookie", ...},
        ...
        "_cached_at": 1718651234.5,
        "_raw": "<raw doctor output>",
      }

    If agent-reach is not installed or doctor fails, returns an empty dict.
    """
    if not force_refresh:
        cached = _load_cache()
        if cached is not None:
            return cached

    try:
        result = subprocess.run(
            ["agent-reach", "doctor", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        raw_output = result.stdout.strip()
        try:
            parsed = json.loads(raw_output)
            report = {**parsed, "_raw": raw_output}
        except json.JSONDecodeError:
            # Older agent-reach without --json flag — store raw text only
            report = {"_raw": raw_output}

        _save_cache(report)
        return report
    except FileNotFoundError:
        # agent-reach not installed yet
        return {}
    except subprocess.TimeoutExpired:
        logger.warning("agent-reach doctor timed out (>60s)")
        return {}
    except Exception as exc:
        logger.debug("agent-reach doctor failed: %s", exc)
        return {}


def is_channel_healthy(channel: str) -> bool:
    """Return True if the named channel is reported as healthy (or unknown).

    Errs on the side of optimism — if there's no health data we assume the
    channel is worth trying rather than silently skipping it.
    """
    health = get_channel_health()
    ch = health.get(channel)
    if ch is None:
        return True  # No data → assume ok
    if isinstance(ch, dict):
        return ch.get("status", "ok") in ("ok", "unknown")
    return True
