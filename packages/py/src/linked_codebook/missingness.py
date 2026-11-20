"""Why values are missing: declared codes, skipped questions, and answers that were left out."""

from collections import Counter
from typing import Any

from .condition import blank, evaluate, parse_condition
from .infer import is_numeric
from .jsonld import clean
from .types import Column, Profile

Data = dict[str, list[Any]]


def declared_codes(column: Column) -> set[str]:
    values = column.get("values", [])
    return {*column.get("missing_values", []), *(value["code"] for value in values if value.get("missing"))}


def is_declared(cell: Any, codes: set[str], column: Column) -> bool:  # noqa: ANN401
    """True for a code that is declared to mean no value, or a number in the declared range."""
    limits = column.get("missing_range")
    in_range = bool(limits) and is_numeric(cell) and limits["low"] <= float(cell) <= limits["high"]  # type: ignore[index]
    return str(cell) in codes or in_range


def rows_of(data: Data) -> list[dict[str, Any]]:
    count = max((len(cells) for cells in data.values()), default=0)
    return [{name: cells[i] if i < len(cells) else None for name, cells in data.items()} for i in range(count)]


def answers_of(profile: Profile, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The rows as a rule sees them: a declared missing code is no answer, so it becomes None."""
    columns = {column["name"]: (declared_codes(column), column) for column in profile["columns"]}
    return [
        {name: None if name in columns and is_declared(cell, *columns[name]) else cell for name, cell in row.items()}
        for row in rows
    ]


def applicability(
    column: Column, rows: list[dict[str, Any]], blank: str
) -> tuple[list[bool | None] | None, str | None]:
    """For each row whether the column applies, or None for the column if it has no rule; the error if it fails."""
    rule = column.get("applies_when")
    if not rule:
        return None, None
    try:
        tree = parse_condition(rule)
    except ValueError as error:
        return None, str(error)
    return [evaluate(tree, row, blank=blank) for row in rows], None


BLANK_KINDS = {True: "blank_applicable", False: "blank_not_applicable", None: "blank_unknown"}


def kind_of(cell: Any, state: bool | None, ruled: bool, declared: tuple[set[str], Column]) -> str:  # noqa: ANN401, FBT001
    """What a cell is: blank (and, if the column has a rule, why), a declared missing code, or an answer."""
    if blank(cell):
        return BLANK_KINDS[state] if ruled else "blank"
    if is_declared(cell, *declared):
        return "declared"
    return "answered_not_applicable" if state is False else "present"


def column_report(
    column: Column, rows: list[dict[str, Any]], answers: list[dict[str, Any]], blank: str
) -> dict[str, Any]:
    name, codes = column["name"], declared_codes(column)
    applies, error = applicability(column, answers, blank)
    counts: Counter[str] = Counter()
    declared: Counter[str] = Counter()
    for index, row in enumerate(rows):
        state = None if applies is None else applies[index]
        kind = kind_of(row[name], state, applies is not None, (codes, column))
        if kind == "declared":
            declared[str(row[name])] += 1
            continue
        counts[kind] += 1
        if kind.startswith("blank_"):
            counts["blank"] += 1
        if kind == "answered_not_applicable":
            counts["present"] += 1
    totals = {"present": counts["present"], "blank": counts["blank"]}
    return clean({**counts, **totals, "declared": dict(declared), "rule_error": error})


def missingness(profile: Profile, data: Data, *, blank: str = "value") -> dict[str, Any]:
    """Counts, for each column of the profile that the data has, how its values divide.

    `data` is `{name: [cells]}`. `present` is a value; `declared` counts the codes that mean no value; `blank` is an
    empty cell, divided by the rule `applies_when` into `blank_not_applicable` (skipped by design), `blank_applicable`
    (missing although the question applied) and `blank_unknown` (the rule cannot be decided). `answered_not_applicable`
    counts values in rows where the rule says the question does not apply.

    The argument `blank` is how rules treat a blank, as in `evaluate_condition`. With "value" (the default, as in
    REDCap) a declared missing code is an ordinary value in a rule; with "unknown" it is a blank and makes the rule
    unknown.
    """
    rows = rows_of(data)
    answers = rows if blank == "value" else answers_of(profile, rows)
    columns = {c["name"]: column_report(c, rows, answers, blank) for c in profile["columns"] if c["name"] in data}
    return {"rows": len(rows), "columns": columns}


def conditions(profile: Profile) -> dict[str, Any]:
    """The parsed `applies_when` of every column that has one, or the reason it could not be parsed."""
    found: dict[str, Any] = {}
    for column in profile["columns"]:
        rule = column.get("applies_when")
        if not rule:
            continue
        try:
            found[column["name"]] = {"condition": parse_condition(rule)}
        except ValueError as error:
            found[column["name"]] = {"error": str(error)}
    return found
