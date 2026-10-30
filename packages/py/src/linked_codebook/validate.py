"""Checking profiles against the model and JSON-LD against the vocabularies."""

from typing import Any

from .constants import JSONLD, SCHEMA, VOCABULARY
from .read import local, show

DEFINITIONS: dict[str, dict[str, Any]] = SCHEMA["$defs"]
KINDS = {
    bool: "boolean",
    int: "number",
    float: "number",
    str: "string",
    list: "array",
    dict: "object",
    type(None): "null",
}


def conform(value: Any, rule: dict[str, Any], path: str) -> list[str]:  # noqa: ANN401
    """Errors of a value against the JSON Schema, which is generated from the model."""
    resolved = {**DEFINITIONS[local(rule["$ref"])], **rule} if "$ref" in rule else rule
    kind = KINDS[type(value)]
    whole = resolved.get("type") == "integer" and kind == "number" and float(value).is_integer()
    if "type" in resolved and kind != resolved["type"] and not whole:
        return [f"{path}: expected {resolved['type']}"]
    if "enum" in resolved and value not in resolved["enum"]:
        return [f"{path}: {show(value)} is not one of {', '.join(resolved['enum'])}"]
    if kind == "number" and not resolved.get("minimum", float("-inf")) <= value <= resolved.get(
        "maximum", float("inf")
    ):
        return [f"{path}: out of range"]
    properties = resolved.get("properties", {})
    missing = [
        f"{path}: {key} is required" for key in resolved.get("required", []) if kind == "object" and key not in value
    ]
    own = [
        error
        for key, member in (value.items() if kind == "object" else [])
        for error in (
            conform(member, properties[key], f"{path}/{key}")
            if key in properties
            else [f"{path}/{key}: unknown property"]
        )
    ]
    listed = [
        error
        for index, item in enumerate(value if kind == "array" and "items" in resolved else [])
        for error in conform(item, resolved["items"], f"{path}/{index}")
    ]
    return [*missing, *own, *listed]


def unlisted(column: dict[str, Any]) -> list[str]:
    """Codes found in the data that a closed list does not allow."""
    allowed = [*(value.get("code") for value in column.get("values", [])), *column.get("missing_values", [])]
    found = [entry.get("code") for entry in column.get("observed", [])] if column.get("closed") else []
    return [
        f"{column.get('name')}: code {code} occurs in the data but not in the closed list"
        for code in found
        if code not in allowed
    ]


def repeated(profile: dict[str, Any]) -> list[str]:
    """Names that must not occur twice in a list, and codes outside a closed list."""

    def twice(names: list[Any]) -> list[Any]:
        return [name for index, name in enumerate(names) if name is not None and names.index(name) != index]

    columns = profile.get("columns", [])
    return [
        *(f"column {name} occurs twice" for name in twice([column.get("name") for column in columns])),
        *(
            f"{column.get('name')}: code {code} occurs twice"
            for column in columns
            for code in twice([value.get("code") for value in column.get("values", [])])
        ),
        *(error for column in columns for error in unlisted(column)),
    ]


KNOWN = {f"{entry['namespace']}{term}" for entry in VOCABULARY["vocabularies"].values() for term in entry["terms"]}


def expand(term: str, context: dict[str, Any]) -> str:
    """Expands a key or type of JSON-LD to an IRI through the context."""
    entry = context.get(term, term)
    target = entry["@id"] if isinstance(entry, dict) else entry
    prefix, _, rest = target.partition(":")
    base = context.get(prefix)
    return str(base + rest if isinstance(base, str) and base != target and rest else target)


def undefined_terms(value: Any, context: dict[str, Any]) -> list[str]:  # noqa: ANN401
    """Errors for terms of a JSON-LD document that no pinned vocabulary defines."""
    if isinstance(value, list):
        return [error for item in value for error in undefined_terms(item, context)]
    if not isinstance(value, dict):
        return []
    types = value.get("@type", [])
    # A key whose term is null is dropped by JSON-LD; one mapped to a keyword (such as @nest) is not a property.
    keys = [
        key
        for key in value
        if not key.startswith("@")
        and key not in JSONLD["extensions"]
        and not str(context.get(key, "")).startswith("@")
        and (key not in context or context[key] is not None)
    ]
    terms = [*keys, *(show(kind) for kind in (types if isinstance(types, list) else [types]))]
    unknown = [term for term in terms if expand(term, context) not in KNOWN and term not in JSONLD["accepted"]]
    below = [
        error
        for key, child in value.items()
        if key != "@context" and (key not in context or context[key] is not None)
        for error in undefined_terms(child, context)
    ]
    return [*(f"{term}: not defined by a pinned vocabulary" for term in unknown), *below]


def validate(document: Any) -> list[str]:  # noqa: ANN401
    """Checks a profile against the model, or a JSON-LD document against the vocabularies."""
    record = document if isinstance(document, dict) else {}
    if "@context" not in record:
        return list(dict.fromkeys([*conform(document, SCHEMA, ""), *repeated(record)]))
    context = record["@context"]
    return list(dict.fromkeys(undefined_terms(document, context if isinstance(context, dict) else JSONLD["context"])))
