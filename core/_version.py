"""Version information for Validator OOP.

This is the single source of truth for version information.
Do not edit manually - use scripts/bump_version.py instead.

When running from a git repository, version strings include the short commit hash
(Opcija A: avtomatska posodobitev ob vsaki spremembi kode).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _get_git_short_hash() -> str | None:
    """Return short git commit hash if available, else None."""
    try:
        # Repo root: search upward from this file (core/_version.py)
        start = Path(__file__).resolve().parent
        for directory in [start] + list(start.parents):
            if (directory / ".git").exists():
                result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and result.stdout and result.stdout.strip():
                    return result.stdout.strip()
                break
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


# Semantic version
MAJOR = 1
MINOR = 1
PATCH = 0

# Build metadata
BUILD = 125
BUILD_DATE = "2026-02-20"

# Git revision (set at import when in a git repo)
_GIT_HASH = _get_git_short_hash()

# Computed version strings
__version__ = f"{MAJOR}.{MINOR}.{PATCH}"
if _GIT_HASH:
    __version_full__ = f"v{MAJOR}.{MINOR}.{PATCH} (build {BUILD}, commit {_GIT_HASH}) – {BUILD_DATE}"
    VERSION_UI = f"v{MAJOR}.{MINOR}.{PATCH} (b{BUILD}, {_GIT_HASH})"
else:
    __version_full__ = f"v{MAJOR}.{MINOR}.{PATCH} (build {BUILD}) – {BUILD_DATE}"
    VERSION_UI = f"v{MAJOR}.{MINOR}.{PATCH} (b{BUILD})"

VERSION_REPORT = __version_full__  # Za poročila in Excel izvoz

# Backward compatibility (deprecated - use VERSION_UI or VERSION_REPORT)
VERSION = VERSION_UI
