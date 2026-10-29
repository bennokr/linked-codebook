"""The `linked-codebook` command."""

import sys
from pathlib import Path

from .cli import run


def main() -> None:
    args = sys.argv[1:]
    texts = {file: Path(file).read_text(encoding="utf-8") for file in args[1:] if Path(file).is_file()}
    stdout, code = run(args, texts)
    sys.stdout.write(stdout)
    sys.exit(code)


if __name__ == "__main__":
    main()
