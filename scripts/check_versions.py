"""Fails if a version number in the docs or the packages is not the version of the release."""

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    version = json.loads((ROOT / "packages/ts/package.json").read_text())["version"]
    found = {
        "packages/py/pyproject.toml": tomllib.loads((ROOT / "packages/py/pyproject.toml").read_text())["project"][
            "version"
        ]
    }
    patterns = [r"linked[-_]codebook-(\d+\.\d+\.\d+)", r"Draft, version (\d+\.\d+\.\d+)"]
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        if path.name == "changelog.md":
            continue
        text = path.read_text()
        for pattern in patterns:
            for number in re.findall(pattern, text):
                found[f"{path.relative_to(ROOT)}: {pattern}"] = number
    changelog = (ROOT / "docs/changelog.md").read_text()
    found["docs/changelog.md: first heading"] = re.search(r"^## (\d+\.\d+\.\d+)", changelog, re.MULTILINE).group(1)  # type: ignore[union-attr]
    wrong = {where: number for where, number in found.items() if number != version}
    for where, number in wrong.items():
        print(f"{where}: {number}, but the version is {version}")
    return int(bool(wrong))


if __name__ == "__main__":
    sys.exit(main())
