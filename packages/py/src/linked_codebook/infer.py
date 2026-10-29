"""Inferring the datatype and level of a column from its values."""

import math
import re
from collections.abc import Mapping, Sequence
from typing import Literal, cast

from .constants import INFERENCE as RULES
from .types import Datatype, Level, Profile

Cell = str | int | float | bool | None
Kind = Literal["empty", "boolean", "date", "datetime", "categorical", "number", "text"]

NUMBER, LEADING_ZERO, DATE, DOTTED, TIME = (
    re.compile(RULES["patterns"][name]) for name in ("number", "leading_zero", "date", "dotted_date", "time")
)
IDENTIFIER = re.compile(RULES["identifier_names"])
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_missing(cell: Cell) -> bool:
    return cell is None or (isinstance(cell, str) and cell in RULES["missing"])


def is_numeric(cell: Cell) -> bool:
    if isinstance(cell, bool):
        return False
    if isinstance(cell, int | float):
        return math.isfinite(cell)
    return (
        isinstance(cell, str)
        and NUMBER.fullmatch(cell) is not None
        and LEADING_ZERO.fullmatch(cell) is None
        and math.isfinite(float(cell))
    )


def number(cell: Cell) -> float:
    return float(cast("str | float", cell))


def is_integer(cell: Cell) -> bool:
    return number(cell).is_integer()


def is_day(year: int, month: int, day: int) -> bool:
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return 1 <= month <= 12 and 1 <= day <= DAYS[month - 1] + (1 if leap and month == 2 else 0)


def is_time(text: str) -> bool:
    found = TIME.fullmatch(text)
    return found is not None and int(found[1]) < 24 and int(found[2]) < 60 and int(found[3] or 0) < 60


def date_kind(cell: Cell) -> Literal["date", "datetime"] | None:
    """A date, or a date with a time, in ISO 8601 or day.month.year form."""
    iso = DATE.fullmatch(str(cell))
    dotted = DOTTED.fullmatch(str(cell))
    if iso:
        valid = is_day(int(iso[1]), int(iso[2]), int(iso[3])) and (not iso[4] or is_time(iso[4]))
        return ("datetime" if iso[4] else "date") if valid else None
    return "date" if dotted and is_day(int(dotted[3]), int(dotted[2]), int(dotted[1])) else None


def is_sequence(values: list[Cell], distinct: int) -> bool:
    """1, 2, 3, and so on without a gap: a row counter."""
    counting = all(number(value) == index + number(values[0]) for index, value in enumerate(values))
    return len(values) >= RULES["sequence_from"] and distinct == len(values) and counting


def is_prose(cell: Cell) -> bool:
    text = str(cell)
    return (
        len(text) > RULES["prose"]["characters"]
        or re.search(r"[\r\n]", text) is not None
        or len(text.strip().split()) > RULES["prose"]["words"]
    )


def is_text_category(values: list[Cell], distinct: int) -> bool:
    few = distinct <= RULES["small"] or distinct / len(values) <= RULES["text_share"]
    return len(values) >= 3 and not any(is_prose(value) for value in values) and distinct < len(values) and few


def is_categorical(
    values: list[Cell], name: str, *, labelled: bool, identifier: bool | None, limits: Mapping[str, int]
) -> bool:
    distinct = len({(isinstance(value, str), isinstance(value, bool), value) for value in values})
    if IDENTIFIER.fullmatch(name.lower()) is not None if identifier is None else identifier:
        return False
    if not all(is_numeric(value) for value in values):
        return distinct <= limits["text"] and (labelled or is_text_category(values, distinct))
    if is_sequence(values, distinct):
        return False
    return (
        distinct <= limits["text"]
        if labelled
        else all(is_integer(value) for value in values) and distinct <= limits["number"] and distinct < len(values)
    )


def kind_of(
    values: list[Cell], name: str, *, labelled: bool, identifier: bool | None, limits: Mapping[str, int]
) -> Kind:
    dates = [date_kind(value) for value in values]
    if not values:
        return "empty"
    if all(isinstance(value, bool) for value in values):
        return "boolean"
    if all(dates):
        return "datetime" if "datetime" in dates else "date"
    if is_categorical(values, name, labelled=labelled, identifier=identifier, limits=limits):
        return "categorical"
    return "number" if all(is_numeric(value) for value in values) else "text"


def infer_column(
    cells: Sequence[Cell],
    name: str = "",
    *,
    labelled: bool = False,
    identifier: bool | None = None,
    limits: Mapping[str, int] | None = None,
) -> dict[str, Datatype | Level]:
    """Proposes a datatype and a level for the values of a column."""
    values = [cell for cell in cells if not is_missing(cell)]
    kind = kind_of(values, name, labelled=labelled, identifier=identifier, limits={**RULES["limits"], **(limits or {})})
    level: Level | None = RULES["level"].get(kind)
    datatype: Datatype = "string"
    if kind in ("boolean", "date", "datetime"):
        datatype = cast("Datatype", kind)
    elif values and all(is_numeric(value) for value in values):
        datatype = "integer" if all(is_integer(value) for value in values) else "number"
    return {"datatype": datatype, "level": level} if level else {"datatype": datatype}


def infer(data: Mapping[str, Sequence[Cell]]) -> Profile:
    """Proposes a datatype and a level for every column of `{name: [values]}`."""
    return cast("Profile", {"columns": [{"name": name, **infer_column(cells, name)} for name, cells in data.items()]})
