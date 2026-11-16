"""The constants that are generated from spec/*.yaml."""

import json
from importlib.resources import files
from typing import Any

_ALL: dict[str, Any] = json.loads(files(__package__).joinpath("constants.json").read_text(encoding="utf-8"))

ENUMS: dict[str, dict[str, str | None]] = _ALL["enums"]
INFERENCE: dict[str, Any] = _ALL["inference"]
LANGUAGE: dict[str, Any] = _ALL["language"]
JSONLD: dict[str, Any] = _ALL["jsonld"]
SCHEMA: dict[str, Any] = _ALL["schema"]
SSSOM: dict[str, Any] = _ALL["sssom"]
VOCABULARY: dict[str, Any] = _ALL["vocabulary"]
IRIS: dict[str, str] = JSONLD["iris"]
COMMANDS: dict[str, Any] = _ALL["commands"]
FRICTIONLESS: dict[str, Any] = _ALL["frictionless"]
REDCAP: dict[str, Any] = _ALL["redcap"]
TABLE: dict[str, Any] = _ALL["table"]
CONDITION: dict[str, Any] = _ALL["condition"]
READSTAT: dict[str, Any] = _ALL["readstat"]
