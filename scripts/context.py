"""Writes the JSON-LD context of the current version as a file: ``context.jsonld`` and ``context-<version>.jsonld``.

The context is the one that ``build`` embeds in every document, so a document can name the file instead of carrying it::

    {"@context": "https://bennokr.github.io/linked-codebook/context-0.11.0.jsonld", ...}

A versioned file never changes once it is released (``make release`` puts it in ``releases/``).
``context.jsonld`` is the context of the current sources. With ``--released-only``, the unversioned file is left
out, and a versioned file that exists with a different text is an error. Without it, an existing versioned file
is kept as it is.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages/py/src"))

from linked_codebook.constants import JSONLD  # noqa: E402


def text() -> str:
    """The context as the text of a JSON-LD file."""
    return json.dumps({"@context": JSONLD["context"]}, indent=2, ensure_ascii=False) + "\n"


def version() -> str:
    """The version of the Python package, which ``make versions`` keeps equal to the TypeScript one."""
    return str(tomllib.loads((ROOT / "packages/py/pyproject.toml").read_text())["project"]["version"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--released-only", action="store_true", help="write only context-<version>.jsonld, and never change it"
    )
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    versioned = args.directory / f"context-{version()}.jsonld"
    if versioned.exists() and versioned.read_text() != text() and args.released_only:
        print(f"{versioned} exists and differs from the current context. Raise the version.")
        return 1
    if not versioned.exists():
        versioned.write_text(text())
    if not args.released_only:
        (args.directory / "context.jsonld").write_text(text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
