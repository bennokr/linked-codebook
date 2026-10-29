"""Writing a profile as a Frictionless Table Schema."""

from .constants import FRICTIONLESS as RULES
from .infer import is_numeric
from .jsonld import Node, clean, pick
from .types import Column, Profile


def typed(code: str, datatype: str | None) -> str | float:
    """A code as the value its field type expects, so that numbers stay numbers."""
    return float(code) if datatype in ("integer", "number") and is_numeric(code) else code


def field_of(column: Column) -> Node:
    values = column.get("values", [])
    datatype = column.get("datatype")
    return clean(
        {
            **pick(column, RULES["field"]),
            "missingValues": [
                *column.get("missing_values", []),
                *(value["code"] for value in values if value.get("missing")),
            ],
            "categories": [
                {"value": typed(value["code"], datatype), "label": value["label"]}
                if value.get("label")
                else typed(value["code"], datatype)
                for value in values
            ],
            RULES["extension"]: pick(column, {slot: slot for slot in RULES["extension_slots"]}),
        },
    )


def to_frictionless(profile: Profile) -> Node:
    """Writes a profile as a Frictionless Table Schema.

    Slots of the dataset are kept in the extension property.
    """
    dataset = {key: value for key, value in profile.items() if key != "columns"}
    return clean({"fields": [field_of(column) for column in profile["columns"]], RULES["extension"]: clean(dataset)})
