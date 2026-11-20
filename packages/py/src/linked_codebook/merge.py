"""Merging two profiles."""

from typing import Any, cast

from .types import Profile

# The slot that identifies the entries of each list of objects.
IDENTIFIERS = {"columns": "name", "values": "code", "observed": "code", "mappings": "object_id"}


def join(base: Any, incoming: Any, slot: str) -> Any:  # noqa: ANN401
    identifier = IDENTIFIERS.get(slot)
    if isinstance(base, dict) and isinstance(incoming, dict):
        return {key: join(base.get(key), incoming.get(key), key) for key in {**base, **incoming}}
    if identifier and isinstance(base, list) and isinstance(incoming, list):

        def key(entry: Any) -> Any:  # noqa: ANN401
            return entry.get(identifier) if isinstance(entry, dict) else None

        def found(entries: list[Any], entry: Any) -> Any:  # noqa: ANN401
            return next((other for other in entries if key(other) == key(entry)), None)

        return [
            join(entry, found(incoming, entry), "")
            for entry in [*base, *(entry for entry in incoming if found(base, entry) is None)]
        ]
    return base if incoming is None or incoming in ("", []) else incoming


def merge(base: Profile, incoming: Profile) -> Profile:
    """Completes `base` with what `incoming` says.

    Columns, values and mappings are matched by name, code and concept.
    """
    return cast("Profile", join(base, incoming, ""))
