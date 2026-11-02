"""Conditions: three-valued evaluation, and the missingness report that uses it."""

import pytest
from linked_codebook import evaluate_condition, missingness, parse_condition


@pytest.mark.parametrize(
    ("text", "row", "expected"),
    [
        ("[a] = 1", {"a": "1"}, True),
        ("[a] = 1", {"a": 1.0}, True),
        ("[a] = 1", {"a": ""}, None),
        ("[a] <> 1", {"a": None}, None),
        ("[a] = '' ", {"a": " "}, True),
        ("[a] = 1 and [b] = 1", {"a": "2"}, False),
        ("[a] = 1 and [b] = 1", {"a": "1"}, None),
        ("[a] = 1 or [b] = 1", {"a": "1"}, True),
        ("[a] = 1 or [b] = 1", {"a": "2"}, None),
        ("not [a] = 1", {"a": "2"}, True),
        ("a in (1, 2)", {"a": "2"}, True),
        ("a in (1, 2)", {}, None),
        ("a IS NULL", {}, True),
        ("a < 10", {"a": "9"}, True),
        ("a < 10", {"a": "007"}, True),
        ("d >= '2020-01-01'", {"d": "2021-05-05"}, True),
    ],
)
def test_evaluation_is_three_valued(text: str, row: dict, expected: object) -> None:  # type: ignore[type-arg]
    assert evaluate_condition(parse_condition(text), row) is expected


def test_missing_code_of_the_controlling_question_makes_the_rule_unknown() -> None:
    profile = {
        "columns": [
            {"name": "smoker", "missing_values": ["9"]},
            {"name": "cigs", "applies_when": "[smoker] = '1'"},
        ]
    }
    data = {"smoker": ["1", "0", "9", ""], "cigs": ["", "", "", ""]}
    report = missingness(profile, data)  # type: ignore[arg-type]
    assert report["columns"]["cigs"] == {
        "blank": 4,
        "blank_applicable": 1,
        "blank_not_applicable": 1,
        "blank_unknown": 2,
        "present": 0,
    }
    assert report["columns"]["smoker"] == {"blank": 1, "declared": {"9": 1}, "present": 2}
