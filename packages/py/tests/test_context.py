"""The context that is published as a file is the one that `build` embeds."""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
from linked_codebook import build

SCRIPT = Path(__file__).resolve().parents[3] / "scripts/context.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("context_script", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", ["context.py", *args])
    return int(load_script().main())


def test_the_published_context_is_the_embedded_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert run(monkeypatch, str(tmp_path)) == 0
    published = json.loads((tmp_path / "context.jsonld").read_text())["@context"]
    assert published == build({"columns": [{"name": "a"}]})["@context"]


def test_a_released_context_is_never_replaced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert run(monkeypatch, str(tmp_path), "--released-only") == 0
    (released,) = tmp_path.glob("context-*.jsonld")
    released.write_text("{}\n")
    assert run(monkeypatch, str(tmp_path), "--released-only") == 1
    assert released.read_text() == "{}\n"
