"""Mappings as SSSOM TSV."""

import re
from typing import Any, cast

from .constants import ENUMS, INFERENCE, SSSOM
from .iri import code_iri, dataset_iri, variable_iri
from .jsonld import clean
from .read import local, show
from .types import Column, Mapping, Profile

Prefixes = dict[str, str]
Row = dict[str, str]
NUMBER = re.compile(INFERENCE["patterns"]["number"])


def cell(value: Any) -> str:  # noqa: ANN401
    return re.sub(r"[\t\r\n]+", " ", "" if value is None else show(value))


def shorten(iri: str, prefixes: Prefixes) -> str:
    """Shortens an IRI to a CURIE where SSSOM tools expect one, and records the prefix."""
    obo = re.fullmatch(SSSOM["obo"], iri)
    known = next(((prefix, base) for prefix, base in SSSOM["compact"].items() if iri.startswith(base)), None)
    pair = (obo[1], iri[: len(iri) - len(obo[2])]) if obo else known
    if pair is None:
        return iri
    prefixes[pair[0]] = pair[1]
    return f"{pair[0]}:{iri[len(pair[1]) :]}"


def row(subject: str, label: str, mapping: Mapping, prefixes: Prefixes) -> str:
    slots = {
        "subject_id": subject,
        "subject_label": label,
        "predicate_id": ENUMS["MatchType"].get(mapping["match_type"]) or "",
        "object_id": shorten(mapping["object_id"], prefixes),
        "mapping_justification": SSSOM["justification"],
        **{name: cell(cast("dict[str, Any]", mapping).get(slot)) for slot, name in SSSOM["fields"].items()},
    }
    slots["mapping_date"] = slots["mapping_date"][:10]
    return "\t".join(slots.get(name, "") for name in SSSOM["columns"])


def rows(dataset: str, column: Column, prefixes: Prefixes) -> list[str]:
    variable = variable_iri(dataset, column)

    def short(iri: str) -> str:
        return f"{SSSOM['subject_prefix']}:{iri[len(dataset) + 1 :]}" if iri.startswith(f"{dataset}#") else iri

    own = [
        row(short(variable), column.get("label", column["name"]), mapping, prefixes)
        for mapping in column.get("mappings", [])
    ]
    coded = [
        row(short(code_iri(variable, value["code"])), value.get("label", value["code"]), mapping, prefixes)
        for value in column.get("values", [])
        for mapping in value.get("mappings", [])
    ]
    return [*own, *coded]


def to_sssom(profile: Profile) -> str:
    """Writes the mappings of a profile as SSSOM TSV."""
    dataset = dataset_iri(profile)
    prefixes: Prefixes = {**SSSOM["prefixes"], SSSOM["subject_prefix"]: f"{dataset}#"}
    body = [line for column in profile["columns"] for line in rows(dataset, column, prefixes)]
    header = [
        "#curie_map:",
        *(f"#  {prefix}: {base}" for prefix, base in prefixes.items()),
        f"#mapping_set_id: {dataset}#mappings",
    ]
    return "\n".join([*header, "\t".join(SSSOM["columns"]), *body]) + "\n"


def expand(value: str, prefixes: Prefixes) -> str:
    prefix, _, rest = value.partition(":")
    base = prefixes.get(prefix)
    return value if re.match(r"(https?|urn):", value) or base is None else base + rest


def read_table(text: str) -> tuple[Prefixes, list[Row]]:
    """The prefixes and the rows of an SSSOM TSV text."""
    lines = [line for line in re.split(r"\r?\n", text) if line.strip()]
    prefixes: Prefixes = {**SSSOM["prefixes"], **SSSOM["compact"]}
    for line in lines:
        declared = re.fullmatch(r"#\s+(\S+?):\s+(\S+)", line)
        if declared:
            prefixes[declared[1]] = declared[2]
    header, *table = (line for line in lines if not line.startswith("#"))
    names = header.split("\t")
    return prefixes, [
        {name: (line.split("\t") + [""] * len(names))[index].strip() for index, name in enumerate(names)}
        for line in table
    ]


def mapping_of(row: Row, prefixes: Prefixes) -> Mapping | None:
    predicate = local(expand(row.get("predicate_id", ""), prefixes))
    kind = next((key for key, meaning in ENUMS["MatchType"].items() if local(meaning or "") == predicate), None)
    fields: dict[str, Any] = {slot: row.get(name) for slot, name in SSSOM["fields"].items()}
    if fields["confidence"] is not None:
        fields["confidence"] = float(fields["confidence"]) if NUMBER.fullmatch(fields["confidence"]) else None
    if not kind or not row.get("object_id"):
        return None
    return cast("Mapping", clean({"match_type": kind, "object_id": expand(row["object_id"], prefixes), **fields}))


def from_sssom(text: str, profile: Profile) -> Profile:
    """Reads SSSOM TSV into the columns and values of a profile that it maps.

    A subject is found by its IRI or else by the label of the column; rows with other subjects are dropped.
    """
    prefixes, table = read_table(text)
    dataset = dataset_iri(profile)
    targets: list[tuple[str, str, str | None]] = []
    for column in profile["columns"]:
        variable = variable_iri(dataset, column)
        targets += [
            (variable, column["name"], None),
            *((code_iri(variable, value["code"]), column["name"], value["code"]) for value in column.get("values", [])),
        ]
    found = []
    for line in table:
        subject = expand(line.get("subject_id", ""), prefixes)
        target = next((t for t in targets if t[0] == subject), None) or next(
            (t for t in targets if t[2] is None and t[1] == line.get("subject_label")), None
        )
        mapping = mapping_of(line, prefixes)
        if target and mapping:
            found.append((target[1], target[2], mapping))
    columns = []
    for column in profile["columns"]:
        mine = [(code, mapping) for name, code, mapping in found if name == column["name"]]
        values = [
            {"code": value["code"], "mappings": [mapping for code, mapping in mine if code == value["code"]]}
            for value in column.get("values", [])
        ]
        mappings = [mapping for code, mapping in mine if code is None]
        if mappings or any(value["mappings"] for value in values):
            columns.append(
                clean(
                    {
                        "name": column["name"],
                        "mappings": mappings,
                        "values": [value for value in values if value["mappings"]],
                    }
                )
            )
    return cast("Profile", {"columns": columns})
