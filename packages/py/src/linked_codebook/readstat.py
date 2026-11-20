"""Reading the variables of a statistical file (SPSS, Stata, SAS) into a profile, as defined by spec/readstat.yaml."""

import re
from typing import Any, cast

from .constants import READSTAT as RULES
from .jsonld import clean
from .types import Column, Profile, Value

Variable = dict[str, Any]
EXTENDED = re.compile(RULES["extended_missing"])
FORMATS = [(re.compile(rule["pattern"]), rule["datatype"]) for rule in RULES["formats"]]


def code_of(value: Any) -> str | None:  # noqa: ANN401
    """A value or missing value as the text of a code; whole numbers have no decimal point."""
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def datatype_of(variable: Variable) -> str:
    kind = variable.get("type")
    if kind == RULES["string_type"]:
        return "string"
    found: str | None = next(
        (datatype for pattern, datatype in FORMATS if pattern.match(variable.get("format") or "")), None
    )
    if found:
        return found
    return "integer" if kind in RULES["integer_types"] else "number"


def level_of(variable: Variable) -> str | None:
    level = RULES["measure"].get(str(variable.get("measure") or 0))
    return level or (RULES["labelled_level"] if variable.get("valueLabels") else None)


def missing_of(variable: Variable) -> tuple[dict[str, float] | None, list[str]]:
    """The one range of missing numbers, and the single missing values."""
    ranges = [(code_of(r["lo"]), code_of(r["hi"]), r["lo"], r["hi"]) for r in variable.get("missingRanges") or []]
    spans = [(lo, hi) for text_lo, text_hi, lo, hi in ranges if text_lo != text_hi]
    if len(spans) > 1:
        message = f"{variable['name']}: more than one range of missing values"
        raise ValueError(message)
    codes = [text for text, other, _, _ in ranges if text == other and text is not None]
    return ({"low": float(spans[0][0]), "high": float(spans[0][1])} if spans else None), codes


def column_of(variable: Variable) -> Column:
    span, single = missing_of(variable)
    labelled = [(code_of(pair["value"]), pair["label"]) for pair in variable.get("valueLabels") or []]
    values = [
        clean({"code": code, "label": label, "missing": True if code in single or EXTENDED.match(code or "") else None})
        for code, label in labelled
        if code is not None
    ]
    unlabelled = [code for code in single if code not in {value["code"] for value in values}]
    return cast(
        "Column",
        clean(
            {
                "name": variable["name"],
                "label": variable.get("label") or None,
                "datatype": datatype_of(variable),
                "level": level_of(variable),
                "values": cast("list[Value]", values),
                "missing_values": unlabelled,
                "missing_range": span,
            },
        ),
    )


def from_readstat(variables: Any) -> Profile:  # noqa: ANN401
    """Reads the variables of a statistical file (SPSS, Stata or SAS) into a profile.

    `variables` is a list of dicts with the keys of ReadStat; see section 15 of the specification. Value labels do not
    make a list closed: SPSS and Stata allow codes without a label.
    """
    listed = variables.get("variables") if isinstance(variables, dict) else variables
    if not listed:
        message = "no variables found"
        raise ValueError(message)
    return {"columns": [column_of(variable) for variable in listed]}
