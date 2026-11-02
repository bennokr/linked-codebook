"""Reading DSV JSON-LD into a profile."""

import re
from typing import Any, cast

from .constants import ENUMS, JSONLD
from .infer import is_numeric
from .iri import dataset_iri, variable_iri
from .jsonld import Node, clean
from .types import Column, Datatype, Level, Mapping, Profile, Value

NODE_KEYS = JSONLD["node_keys"]


def local(name: str) -> str:
    """The name of a term without its prefix or namespace, so that dct:title, dcterms:title and title are alike."""
    return re.split(r"[:#/]", name)[-1]


def show(value: Any) -> str:  # noqa: ANN401
    """The text of a JSON value, as JavaScript writes it."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


def first(*values: Any) -> Any:  # noqa: ANN401
    """The first value that is present, like ?? in TypeScript."""
    return next((value for value in values if value is not None), None)


def items(value: Any) -> list[Any]:  # noqa: ANN401
    found = value if isinstance(value, list) else [] if value is None else [value]
    return [
        part
        for item in found
        for part in (items(item["@list"]) if isinstance(item, dict) and "@list" in item else [item])
    ]


def named(node: Node) -> Node:
    return {key if key.startswith("@") else local(key): value for key, value in node.items()}


def collect(document: Any) -> list[Node]:  # noqa: ANN401
    """Every object of the document, with unprefixed keys."""
    if isinstance(document, list):
        return [node for item in document for node in collect(item)]
    if not isinstance(document, dict):
        return []
    below = [node for key, value in document.items() if key != "@context" for node in collect(value)]
    return [named(document), *below]


def resolve(nodes: list[Node], value: Any) -> Node:  # noqa: ANN401
    """The node a value refers to, completed with the other nodes of the document that have its id."""
    head = next(iter(items(value)), None)
    node = named(head) if isinstance(head, dict) else {"@id": head} if isinstance(head, str) else {}
    merged: Node = {}
    for part in [*(other for other in nodes if "@id" in node and other.get("@id") == node["@id"]), node]:
        merged.update(part)
    return merged


def get(node: Node, term: str) -> Any:  # noqa: ANN401
    return next((node[name] for name in [term, *JSONLD["aliases"].get(term, [])] if name in node), None)


def text(value: Any) -> str | None:  # noqa: ANN401
    head = next(iter(items(value)), None)
    result = first(head.get("@value"), head.get("@id")) if isinstance(head, dict) else head
    return None if result is None else show(result)


def number_of(value: Any) -> float | None:  # noqa: ANN401
    found = text(value)
    return float(found) if found is not None and is_numeric(found) else None


def datatype_of(value: Any) -> Datatype | None:  # noqa: ANN401
    head = next(iter(items(value)), None)
    name = local(first(text(head.get("base") if isinstance(head, dict) else head), ""))
    known = JSONLD["datatype_aliases"].get(name, name)
    return cast("Datatype", known) if known in ENUMS["Datatype"] else None


def level_of(value: Any) -> Level | None:  # noqa: ANN401
    name = local(first(text(value), ""))
    return next(
        (cast("Level", level) for level, meaning in ENUMS["Level"].items() if local(meaning or "") == name), None
    )


def mappings_of(concept: Node) -> list[Mapping]:
    ids = (
        (match_type, text(target))
        for match_type in ENUMS["MatchType"]
        for target in items(get(concept, f"{match_type}Match"))
    )
    return [
        cast("Mapping", {"match_type": match_type, "object_id": iri, "reviewer_id": JSONLD["imported_reviewer"]})
        for match_type, iri in ids
        if iri
    ]


def values_of(nodes: list[Node], prop: Node, nulls: list[str]) -> list[Value]:
    """The codes of a code book, in the order of their positions if every code has one, else as listed."""
    scheme = resolve(nodes, get(prop, "hasCodeBook"))
    found: list[tuple[float | None, Value]] = []
    for item in items(scheme.get(local(NODE_KEYS["top"]))):
        concept = resolve(nodes, item)
        code = first(text(concept.get(local(NODE_KEYS["notation"]))), "")
        value = cast(
            "Value",
            clean(
                {
                    "code": code,
                    "label": text(concept.get(local(NODE_KEYS["label"]))),
                    "description": text(concept.get(local(NODE_KEYS["definition"]))),
                    "missing": True if code in nulls else None,
                    "mappings": mappings_of(concept),
                },
            ),
        )
        found.append((number_of(concept.get(local(NODE_KEYS["position"]))), value))
    if found and all(position is not None for position, _ in found):
        found.sort(key=lambda pair: cast("float", pair[0]))
    return [value for _, value in found]


def range_of(value: Any) -> dict[str, Any] | None:  # noqa: ANN401
    low, high = (value.get("low"), value.get("high")) if isinstance(value, dict) else [*items(value), None, None][:2]
    numbers = all(isinstance(bound, int | float) and not isinstance(bound, bool) for bound in (low, high))
    return {"low": low, "high": high} if numbers else None


def column_of(nodes: list[Node], dataset: str, node: Node, *, explicit: bool) -> Column:
    prop = resolve(nodes, get(node, "columnProperty"))
    variable = resolve(nodes, get(prop, "hasVariable"))
    statistics = resolve(nodes, first(get(node, "summaryStatistics"), get(prop, "summaryStatistics")))
    title = first(text(get(node, "titles")), text(variable.get(local(NODE_KEYS["label"]))))
    name = first(text(get(node, "name")), title, "")
    nulls = [show(null) for null in items(get(node, "nullValues"))]
    values = values_of(nodes, prop, nulls)
    iri = text(variable.get("@id"))
    return cast(
        "Column",
        clean(
            {
                "name": name,
                "label": None if title == name else title,
                "datatype": datatype_of(get(node, "datatype")),
                "description": first(
                    text(variable.get(local(NODE_KEYS["definition"]))), text(get(node, "description"))
                ),
                "level": level_of(get(statistics, "statisticalDataType")),
                "completeness": number_of(get(statistics, "columnCompleteness")),
                "unit": text(get(prop, "unitText")),
                "unit_iri": text(get(prop, "hasUnit")),
                "variable": None if not explicit and iri == variable_iri(dataset, {"name": name}) else iri,
                "source": first(text(variable.get(local(NODE_KEYS["source"]))), text(get(prop, "source"))),
                "values": values,
                "missing_values": [code for code in nulls if all(value["code"] != code for value in values)],
                **extensions_of(node),
                "mappings": mappings_of(variable),
            },
        ),
    )


def extensions_of(node: Node) -> Node:
    """The properties of a column that no vocabulary defines."""
    return clean(
        {
            "closed": get(node, "codeBookClosed") is True or None,
            "missing_range": range_of(get(node, "missingRange")),
            "applies_when": text(get(node, "appliesWhen")),
            "minimum": number_of(get(node, "minimumValue")),
            "maximum": number_of(get(node, "maximumValue")),
            "group": text(get(node, "columnGroup")),
            "identifying": get(node, "identifying") is True or None,
        },
    )


def parse(document: Any, *, explicit: bool = False) -> Profile:  # noqa: ANN401
    """Reads DSV JSON-LD, nested or as a flat graph, into a profile.

    A variable IRI that is the one this library would write is left out, unless `explicit` is set.
    """
    nodes = collect(document)
    dataset = next((node for node in nodes if get(node, "datasetSchema") is not None), {})
    schema = resolve(nodes, get(dataset, "datasetSchema"))
    columns = [resolve(nodes, item) for item in items(get(schema, "columns"))]
    if not columns:
        message = "no columns found"
        raise ValueError(message)
    fields = {slot: text(get(dataset, key)) for slot, key in JSONLD["keys"]["dataset"].items()}
    license_ = first(text(get(dataset, "license")), text(get(dataset, "rights")))
    rows = number_of(get(resolve(nodes, get(dataset, "summaryStatistics")), "numberOfRows"))
    rows = int(rows) if rows is not None and rows.is_integer() else rows
    profile = cast("Profile", clean({**fields, "license": license_, "rows": rows}))
    base = first(text(dataset.get("@id")), dataset_iri(profile))
    return {**profile, "columns": [column_of(nodes, base, column, explicit=explicit) for column in columns]}
