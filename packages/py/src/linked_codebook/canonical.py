"""Canonical JSON text."""

import json
from typing import Any


def _plain(value: Any) -> Any:  # noqa: ANN401
    """Prints whole floats as integers, as JavaScript does."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def canonical(value: Any) -> str:  # noqa: ANN401
    """JSON with sorted keys and two-space indentation, so that every implementation prints the same text."""
    return json.dumps(_plain(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
