#!/usr/bin/env python
"""Bump version script for Validator OOP.

Usage:
    python scripts/bump_version.py           # Bump build number only
    python scripts/bump_version.py --patch   # Bump patch version (1.0.0 -> 1.0.1)
    python scripts/bump_version.py --minor   # Bump minor version (1.0.0 -> 1.1.0)
    python scripts/bump_version.py --major   # Bump major version (1.0.0 -> 2.0.0)
    python scripts/bump_version.py --release # Create release in CHANGELOG.md
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

# Path to version file
VERSION_FILE = Path(__file__).parent.parent / "core" / "_version.py"
CHANGELOG_FILE = Path(__file__).parent.parent / "CHANGELOG.md"


def read_version_file() -> dict:
    """Read current version info from _version.py."""
    content = VERSION_FILE.read_text(encoding="utf-8")
    
    version_info = {}
    patterns = {
        "MAJOR": r"^MAJOR\s*=\s*(\d+)",
        "MINOR": r"^MINOR\s*=\s*(\d+)",
        "PATCH": r"^PATCH\s*=\s*(\d+)",
        "BUILD": r"^BUILD\s*=\s*(\d+)",
        "BUILD_DATE": r'^BUILD_DATE\s*=\s*"([^"]+)"',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            value = match.group(1)
            version_info[key] = int(value) if key != "BUILD_DATE" else value
    
    return version_info


def write_version_file(version_info: dict) -> None:
    """Write updated version info to _version.py."""
    content = f'''"""Version information for Validator OOP.

This is the single source of truth for version information.
Do not edit manually - use scripts/bump_version.py instead.
"""

from __future__ import annotations

# Semantic version
MAJOR = {version_info["MAJOR"]}
MINOR = {version_info["MINOR"]}
PATCH = {version_info["PATCH"]}

# Build metadata
BUILD = {version_info["BUILD"]}
BUILD_DATE = "{version_info["BUILD_DATE"]}"

# Computed version strings
__version__ = f"{{MAJOR}}.{{MINOR}}.{{PATCH}}"
__version_full__ = f"v{{MAJOR}}.{{MINOR}}.{{PATCH}} (build {{BUILD}}) – {{BUILD_DATE}}"

# UI version formats
VERSION_UI = f"v{{MAJOR}}.{{MINOR}}.{{PATCH}} (b{{BUILD}})"  # Za naslov okna: v1.1.0 (b124)
VERSION_REPORT = __version_full__  # Za poročila: v1.1.0 (build 124) – 2026-02-20

# Backward compatibility (deprecated - use VERSION_UI or VERSION_REPORT)
VERSION = VERSION_UI
'''
    VERSION_FILE.write_text(content, encoding="utf-8")


def create_changelog_release(version: str, release_date: str) -> bool:
    """Move [Unreleased] entries to a new version section in CHANGELOG.md."""
    if not CHANGELOG_FILE.exists():
        print(f"Warning: {CHANGELOG_FILE} not found")
        return False
    
    content = CHANGELOG_FILE.read_text(encoding="utf-8")
    
    # Check if there are unreleased changes
    unreleased_pattern = r"## \[Unreleased\]\s*\n(.*?)(?=\n---|\n## \[)"
    unreleased_match = re.search(unreleased_pattern, content, re.DOTALL)
    
    if not unreleased_match:
        print("No unreleased changes found in CHANGELOG.md")
        return False
    
    unreleased_content = unreleased_match.group(1).strip()
    if not unreleased_content:
        print("No unreleased changes to release")
        return False
    
    # Create new version section
    new_version_section = f"## [{version}] - {release_date}\n\n{unreleased_content}"
    
    # Replace unreleased section with empty one and add new version
    new_content = re.sub(
        r"(## \[Unreleased\])\s*\n.*?(?=\n---)",
        f"\\1\n\n---\n\n{new_version_section}",
        content,
        flags=re.DOTALL,
    )
    
    CHANGELOG_FILE.write_text(new_content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Bump version for Validator OOP")
    parser.add_argument("--major", action="store_true", help="Bump major version")
    parser.add_argument("--minor", action="store_true", help="Bump minor version")
    parser.add_argument("--patch", action="store_true", help="Bump patch version")
    parser.add_argument("--release", action="store_true", help="Create release in CHANGELOG")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()
    
    # Read current version
    version_info = read_version_file()
    old_version = f"{version_info['MAJOR']}.{version_info['MINOR']}.{version_info['PATCH']}"
    old_build = version_info["BUILD"]
    
    print(f"Current version: {old_version} (build {old_build})")
    
    # Determine what to bump
    if args.major:
        version_info["MAJOR"] += 1
        version_info["MINOR"] = 0
        version_info["PATCH"] = 0
    elif args.minor:
        version_info["MINOR"] += 1
        version_info["PATCH"] = 0
    elif args.patch:
        version_info["PATCH"] += 1
    
    # Always bump build number and update date
    version_info["BUILD"] += 1
    version_info["BUILD_DATE"] = date.today().isoformat()
    
    new_version = f"{version_info['MAJOR']}.{version_info['MINOR']}.{version_info['PATCH']}"
    new_build = version_info["BUILD"]
    
    print(f"New version: {new_version} (build {new_build})")
    
    if args.dry_run:
        print("Dry run - no changes made")
        return
    
    # Write updated version
    write_version_file(version_info)
    print(f"Updated {VERSION_FILE}")
    
    # Create release in CHANGELOG if requested
    if args.release:
        if create_changelog_release(new_version, version_info["BUILD_DATE"]):
            print(f"Created release {new_version} in {CHANGELOG_FILE}")
        else:
            print("No CHANGELOG release created")
    
    print("\nDone! Don't forget to commit the changes.")


if __name__ == "__main__":
    main()
