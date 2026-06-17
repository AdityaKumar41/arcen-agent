"""Agent-Reach installer helpers.

Handles lazy installation and version checking of the `agent-reach` package.
Installation is triggered on first tool use — the agent is informed about
what's happening via the tool response so it can show progress to the user.

The package is installed into the active Python environment (same venv as
Arcen itself) so it's available for subsequent calls without any PATH games.
"""

from __future__ import annotations

import importlib.util
import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Pinned floor version; bump when a new Agent-Reach feature is required.
_MIN_VERSION = "1.5.0"
# Source — the GitHub archive always tracks main; pin to a release tag when
# Agent-Reach starts publishing stable PyPI releases.
_INSTALL_SOURCE = "https://github.com/Panniantong/agent-reach/archive/main.zip"

_cached_available: Optional[bool] = None
_cached_version: Optional[str] = None


def is_agent_reach_installed() -> bool:
    """Return True if agent-reach is importable in the current environment."""
    global _cached_available
    if _cached_available is not None:
        return _cached_available
    spec = importlib.util.find_spec("agent_reach")
    _cached_available = spec is not None
    return _cached_available


def get_agent_reach_version() -> Optional[str]:
    """Return the installed agent-reach version string, or None."""
    global _cached_version
    if _cached_version is not None:
        return _cached_version
    try:
        import importlib.metadata
        _cached_version = importlib.metadata.version("agent-reach")
        return _cached_version
    except Exception:
        return None


def ensure_agent_reach_installed() -> tuple[bool, str]:
    """Ensure agent-reach is installed; install it if not.

    Returns:
        (success: bool, message: str)
            success=True  → package is ready to use
            success=False → install failed; message contains the error
    """
    global _cached_available

    if is_agent_reach_installed():
        return True, f"agent-reach {get_agent_reach_version() or 'unknown'} is ready."

    logger.info("agent-reach not found — installing from GitHub main...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", _INSTALL_SOURCE],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "unknown pip error").strip()
            logger.error("agent-reach install failed: %s", err)
            return False, (
                f"agent-reach installation failed.\n"
                f"Error: {err}\n\n"
                f"To install manually run:\n"
                f"  pip install {_INSTALL_SOURCE}\n"
                f"Then retry your command."
            )
        # Invalidate the import cache so the newly installed package is found.
        _cached_available = None
        _cached_version = None
        importlib.invalidate_caches()
        version = get_agent_reach_version() or "installed"
        logger.info("agent-reach installed successfully: %s", version)
        return True, f"agent-reach {version} installed successfully."
    except subprocess.TimeoutExpired:
        _cached_available = None
        return False, (
            "agent-reach installation timed out (>120s).\n"
            f"Please install manually: pip install {_INSTALL_SOURCE}"
        )
    except Exception as exc:
        _cached_available = None
        logger.exception("Unexpected error installing agent-reach: %s", exc)
        return False, f"agent-reach installation error: {exc}"


def get_install_hint() -> str:
    """Return a human-readable install command for the user."""
    return f"pip install {_INSTALL_SOURCE}"
