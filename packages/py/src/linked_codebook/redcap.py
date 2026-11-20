"""Reading a REDCap data dictionary."""

import csv
import io
import re
from typing import Any, cast

from .constants import REDCAP
from .infer import is_numeric
from .jsonld import clean
from .types import Column, Profile, Value

Row = dict[str, str]

WHOLE_NUMBER = re.compile(f"(?:{REDCAP['integer_code']})")


def normalize(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", header.lower())


def rows_of(text: str) -> list[Row]:
    """The dictionary rows, with the columns that are used under the names of the specification."""
    table = [row for row in csv.reader(io.StringIO(text.removeprefix("﻿"), newline="")) if any(c.strip() for c in row)]
    keys = [normalize(header) for header in table[0]] if table else []

    def cell(cells: list[str], names: list[str]) -> str:
        index = next((i for i, key in enumerate(keys) if key in names), None)
        return cells[index].strip() if index is not None and index < len(cells) else ""

    return [{slot: cell(cells, names) for slot, names in REDCAP["headers"].items()} for cells in table[1:]]


def choices_of(text: str) -> list[Value]:
    """Choices written as "1, Male | 2, Female"."""
    parts = [part.strip() for part in text.split("|") if part.strip()]
    return [
        cast("Value", clean({"code": code.strip(), "label": label.strip() if comma else None}))
        for part in parts
        for code, comma, label in [part.partition(",")]
    ]


def kind_of(kind: str, validation: str) -> dict[str, Any]:
    fixed = REDCAP["types"].get(kind)
    hit = next((rule for rule in REDCAP["validation"] if re.fullmatch(rule["pattern"], validation)), None)
    return fixed or (clean({"datatype": hit["datatype"], "level": hit.get("level")}) if hit else {"datatype": "string"})


def listed(pairs: list[list[str]]) -> list[Value]:
    return [cast("Value", clean({"code": code, "label": label})) for code, label in pairs]


def categorical(name: str, values: list[Value], common: dict[str, Any]) -> Column:
    whole = all(WHOLE_NUMBER.fullmatch(value["code"]) for value in values)
    datatype = "integer" if whole else "string"
    return cast(
        "Column",
        clean({"name": name, **common, "datatype": datatype, "level": "categorical", "values": values, "closed": True}),
    )


def columns_of(row: Row) -> list[Column]:
    name, kind = row["name"], row["type"]
    if not name or kind in REDCAP["skipped"]:
        return []
    common = {
        "label": row["label"],
        "description": row["note"],
        "applies_when": row["branching"],
        "group": row["form"],
        "identifying": row["identifier"].lower() == REDCAP["identifier_mark"] or None,
    }
    if kind == REDCAP["checkbox"]:
        return [
            categorical(
                f"{name}___{re.sub('[^a-z0-9_]', '_', choice['code'].lower())}",
                listed(REDCAP["checkbox_values"]),
                {**common, "label": f"{row['label']} ({choice.get('label', choice['code'])})"},
            )
            for choice in choices_of(row["choices"])
        ]
    builtin = REDCAP["builtin"].get(kind)
    values = listed(builtin) if builtin else choices_of(row["choices"]) if kind in REDCAP["choice_types"] else []
    if values:
        return [categorical(name, values, common)]
    limits = {slot: float(row[slot]) for slot in ("minimum", "maximum") if is_numeric(row[slot])}
    return [cast("Column", clean({"name": name, **common, **kind_of(kind, row["validation"]), **limits}))]


def from_redcap(text: str) -> Profile:
    """Reads a REDCap data dictionary (CSV text) into a profile."""
    columns = [column for row in rows_of(text) for column in columns_of(row)]
    if not columns:
        message = "no fields found"
        raise ValueError(message)
    return {"columns": columns}
