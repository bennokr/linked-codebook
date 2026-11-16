import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from linked_codebook import build, infer, infer_language, is_identifier_name, parse, validate

if TYPE_CHECKING:
    from linked_codebook.infer import Cell
    from linked_codebook.types import Profile

DOC = json.loads((Path(__file__).resolve().parents[3] / "spec/cases/language.json").read_text(encoding="utf-8"))


def detect(text: str) -> str | None:
    """The stub of the shared cases: the tag before the first colon, or None for ?."""
    tag = text.split(":", 1)[0]
    return None if tag == "?" else tag


@pytest.mark.parametrize("case", DOC["cases"], ids=lambda case: case["name"])
def test_language_cases(case: dict[str, Any]) -> None:
    found = infer_language(case["cells"], detect)
    assert found == case["expected"]


@pytest.mark.parametrize("name", DOC["identifier_names"])
def test_identifier_names(name: str) -> None:
    assert is_identifier_name(name) is DOC["identifier_names"][name]


def test_infer_adds_the_language_of_text_columns_only() -> None:
    data: dict[str, list[Cell]] = {
        "review": [f"nl: een lange recensie met genoeg woorden om als tekst te tellen ({i})" for i in range(10)],
        "sex": ["nl: m", "nl: f"] * 5,
        "age": [str(20 + i) for i in range(10)],
    }
    columns = {column["name"]: column for column in infer(data, detect)["columns"]}
    assert columns["review"].get("language") == "nl"
    assert "language" not in columns["sex"]
    assert "language" not in columns["age"]
    assert "language" not in infer(data)["columns"][0]


def test_language_survives_json_ld_and_validates() -> None:
    profile: Profile = {"title": "Reviews", "columns": [{"name": "review", "datatype": "string", "language": "nl"}]}
    document = build(profile)
    assert parse(document) == profile
    assert validate(document) == []
    errors = validate({**profile, "columns": [{"name": "review", "language": "Dutch!"}]})
    assert errors == ["/columns/0/language: Dutch! does not match ^[a-z]{2,3}(-[a-z0-9]{2,8})*$"]
