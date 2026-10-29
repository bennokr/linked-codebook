"""IRIs of the nodes that are written."""

import re
from re import Match
from urllib.parse import quote

from .constants import IRIS, JSONLD
from .types import Column, Profile


def fill(kind: str, values: dict[str, str]) -> str:
    """Fills the IRI template of a node kind. Placeholders that are not IRIs are percent-encoded."""

    def part(match: Match[str]) -> str:
        name = match[1]
        value = values.get(name, "")
        return value if name in JSONLD["raw"] else quote(value, safe="-_.!~*'()")

    return re.sub(r"\{(\w+)\}", part, IRIS.get(kind, ""))


def dataset_iri(profile: Profile) -> str:
    identifier = profile.get("identifier", "")
    if re.match(r"(https?:|urn:)", identifier):
        return identifier
    return fill("dataset", {"id": identifier or profile.get("title") or "unnamed"})


def variable_iri(dataset: str, column: Column) -> str:
    """The IRI of the variable of a column: the one it declares, or one made from its name."""
    variable = column.get("variable")
    return fill("variable", {"dataset": dataset, "name": column["name"]}) if variable is None else variable


def code_iri(variable: str, code: str) -> str:
    return fill("code", {"variable": variable, "code": code})
