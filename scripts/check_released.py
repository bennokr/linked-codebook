"""Fails if a published release changed: a file under releases/ must be byte-identical to the one on the base branch.

Consumers pin these files by URL and hash, so a version must never be rebuilt after it is published. Raise the version
instead. New files are fine. On main itself the base is the previous commit.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def base_ref() -> str | None:
    """The commit to compare with: origin/main, or the parent commit when this is main."""
    if git("rev-parse", "--verify", "-q", "origin/main").returncode != 0:
        git("fetch", "--depth=1", "origin", "main")
    main = git("rev-parse", "--verify", "-q", "origin/main").stdout.strip()
    head = git("rev-parse", "HEAD").stdout.strip()
    if not main:
        return None
    if main != head:
        return "origin/main"
    return "HEAD^" if git("rev-parse", "--verify", "-q", "HEAD^").returncode == 0 else None


def main() -> int:
    base = base_ref()
    if base is None:
        print("check_released: no base commit to compare with; skipped")
        return 0
    changed = []
    for path in sorted((ROOT / "releases").glob("*")):
        before = git("show", f"{base}:releases/{path.name}")
        if before.returncode == 0 and before.stdout != path.read_bytes():
            changed.append(path.name)
    if changed:
        print(f"Published releases were modified: {', '.join(changed)}. Raise the version instead of rebuilding.")
        return 1
    print(f"check_released: releases/ is unchanged against {base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
