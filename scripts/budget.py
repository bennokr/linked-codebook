"""Fails if the libraries have more statements than the budget in budget.yaml allows."""

import ast
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GENERATED = {"types.py"}


def python_statements() -> int:
    files = [path for path in (ROOT / "packages/py/src").rglob("*.py") if path.name not in GENERATED]
    nodes = [node for path in files for node in ast.walk(ast.parse(path.read_text()))]
    docstrings = [node for node in nodes if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)]
    return sum(isinstance(node, ast.stmt) for node in nodes) - len(docstrings)


def typescript_statements() -> int:
    command = ["node", "scripts/count-statements.ts", "packages/ts/src"]
    return int(subprocess.run(command, check=True, capture_output=True, text=True, cwd=ROOT).stdout)


def main() -> int:
    budget = yaml.safe_load((ROOT / "budget.yaml").read_text())
    counts = {"python": python_statements(), "typescript": typescript_statements()}
    for language, count in counts.items():
        print(f"{language}: {count} statements, budget {budget[language]}")
    return int(any(count > budget[language] for language, count in counts.items()))


if __name__ == "__main__":
    sys.exit(main())
