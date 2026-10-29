"""Writing a profile as DSV JSON-LD."""

import re
from typing import Any

from .constants import ENUMS, JSONLD
from .iri import code_iri, dataset_iri, fill, variable_iri
from .types import Column, Mapping, Profile

Node = dict[str, Any]

KEYS = JSONLD["keys"]
NODE_KEYS = JSONLD["node_keys"]
TYPES = JSONLD["types"]


def clean(node: Node) -> Node:
    """Drops the entries that have no value."""
    return {key: value for key, value in node.items() if value is not None and value not in ("", [])}


def pick(source: Any, slots: dict[str, str]) -> Node:  # noqa: ANN401
    return clean({key: source.get(slot) for slot, key in slots.items()})


def links(mappings: list[Mapping]) -> dict[str, list[str]]:
    """Only approved links are asserted; a link is approved when it has a reviewer."""
    result: dict[str, list[str]] = {}
    for mapping in (mapping for mapping in mappings if mapping.get("reviewer_id")):
        result.setdefault(f"{mapping['match_type']}Match", []).append(mapping["object_id"])
    return result


def concept(iri: str, label: str | None, definition: str | None, mappings: list[Mapping]) -> Node:
    return clean({"@id": iri, "@type": TYPES["concept"], NODE_KEYS["label"]: label, NODE_KEYS["definition"]: definition, **links(mappings)})


def code_book(column: Column, variable: str) -> Node | None:
    scheme = fill("scheme", {"variable": variable})
    top = [
        clean(
            {
                **concept(code_iri(variable, value["code"]), value.get("label"), value.get("description"), value.get("mappings", [])),
                NODE_KEYS["in_scheme"]: {"@id": scheme},
                NODE_KEYS["notation"]: value["code"],
            },
        )
        for value in column.get("values", [])
    ]
    return {"@id": scheme, "@type": TYPES["scheme"], NODE_KEYS["top"]: top} if top else None


def column_node(dataset: str, column: Column) -> Node:
    variable = variable_iri(dataset, column)
    label = column.get("label", column["name"])
    values = column.get("values", [])
    nulls = [*column.get("missing_values", []), *(value["code"] for value in values if value.get("missing"))]
    ids = {"dataset": dataset, "name": column["name"]}
    level = column.get("level")
    statistics = {"@id": fill("statistics", ids), "@type": TYPES["statistics"], "statisticalDataType": ENUMS["Level"].get(level)}
    return clean(
        {
            "@id": fill("column", ids),
            "@type": TYPES["column"],
            **pick(column, KEYS["column"]),
            "titles": label,
            "nullValues": nulls,
            "missingRange": column.get("missing_range"),
            "columnProperty": clean(
                {
                    "@id": fill("property", ids),
                    "@type": TYPES["property"],
                    "hasVariable": concept(variable, label, column.get("description"), column.get("mappings", [])),
                    "hasUnit": column.get("unit_iri"),
                    "unitText": column.get("unit"),
                    "hasCodeBook": code_book(column, variable),
                },
            ),
            "summaryStatistics": statistics if level else None,
        },
    )


def build(profile: Profile) -> Node:
    """Writes a profile as JSON-LD with the DSV ontology."""
    dataset = dataset_iri(profile)
    license_ = profile.get("license")
    license_key = "license" if re.match(r"https?:", license_ or "") else "rights"
    return clean(
        {
            "@context": JSONLD["context"],
            "@id": dataset,
            "@type": TYPES["dataset"],
            **pick(profile, KEYS["dataset"]),
            license_key: license_,
            "datasetSchema": {
                "@id": fill("schema", {"dataset": dataset}),
                "@type": TYPES["schema"],
                "columns": [column_node(dataset, column) for column in profile["columns"]],
            },
        },
    )
