"""Resolve ARCEN_HOME for standalone skill scripts.

Skill scripts may run outside the Arcen process (e.g. system Python,
nix env, CI) where ``arcen_constants`` is not importable.  This module
provides the same ``get_arcen_home()`` and ``display_arcen_home()``
contracts as ``arcen_constants`` without requiring it on ``sys.path``.

When ``arcen_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``arcen_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``ARCEN_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from arcen_constants import display_arcen_home as display_arcen_home
    from arcen_constants import get_arcen_home as get_arcen_home
except (ModuleNotFoundError, ImportError):

    def get_arcen_home() -> Path:
        """Return the Arcen home directory (default: ~/.arcen).

        Mirrors ``arcen_constants.get_arcen_home()``."""
        val = os.environ.get("ARCEN_HOME", "").strip()
        return Path(val) if val else Path.home() / ".arcen"

    def display_arcen_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``arcen_constants.display_arcen_home()``."""
        home = get_arcen_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
