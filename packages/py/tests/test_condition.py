"""Conditions: evaluation with a blank as a value (REDCap) and as unknown (SQL), and the missingness report."""

import pytest
from linked_codebook import evaluate_condition, missingness, parse_condition
from linked_codebook.types import Profile  # noqa: TC002

# text, row, result when a blank is a value (the default), result when a blank is unknown
CASES = [
    ("[a] = 1", {"a": "1"}, True, True),
    ("[a] = 1", {"a": 1.0}, True, True),
    ("[a] = 1", {"a": ""}, False, None),
    ("[a] <> 1", {"a": None}, True, None),
    ("[a] = [b]", {}, True, None),
    ("[a] = '' ", {"a": " "}, True, True),
    ("[a] = 1 and [b] = 1", {"a": "2"}, False, False),
    ("[a] = 1 and [b] = 1", {"a": "1"}, False, None),
    ("[a] = 1 or [b] = 1", {"a": "1"}, True, True),
    ("[a] = 1 or [b] = 1", {"a": "2"}, False, None),
    ("not [a] = 1", {"a": "2"}, True, True),
    ("a in (1, 2)", {"a": "2"}, True, True),
    ("a in (1, 2)", {}, False, None),
    ("a IS NULL", {}, True, True),
    ("a < 10", {"a": "9"}, True, True),
    ("a < 10", {"a": "007"}, True, True),
    ("a < 10", {}, None, None),
    ("d >= '2020-01-01'", {"d": "2021-05-05"}, True, True),
]


@pytest.mark.parametrize(("text", "row", "as_value", "as_unknown"), CASES)
def test_evaluation_of_a_blank(text: str, row: dict, as_value: object, as_unknown: object) -> None:  # type: ignore[type-arg]
    tree = parse_condition(text)
    assert evaluate_condition(tree, row) is as_value
    assert evaluate_condition(tree, row, blank="unknown") is as_unknown


def test_blank_must_be_value_or_unknown() -> None:
    with pytest.raises(ValueError, match="blank must be"):
        evaluate_condition(parse_condition("a = 1"), {}, blank="zero")


PROFILE = {
    "columns": [
        {"name": "smoker", "missing_values": ["9"]},
        {"name": "cigs", "applies_when": "[smoker] = '1'"},
    ]
}
DATA = {"smoker": ["1", "0", "9", ""], "cigs": ["", "", "", ""]}


def test_blank_controlling_answer_is_not_applicable_as_redcap_decides() -> None:
    report = missingness(PROFILE, DATA)  # type: ignore[arg-type]
    assert report["columns"]["cigs"] == {
        "blank": 4,
        "blank_applicable": 1,
        "blank_not_applicable": 3,
        "present": 0,
    }
    assert report["columns"]["smoker"] == {"blank": 1, "declared": {"9": 1}, "present": 2}


def test_missing_code_of_the_controlling_question_makes_the_rule_unknown_when_blank_is_unknown() -> None:
    report = missingness(PROFILE, DATA, blank="unknown")  # type: ignore[arg-type]
    assert report["columns"]["cigs"] == {
        "blank": 4,
        "blank_applicable": 1,
        "blank_not_applicable": 1,
        "blank_unknown": 2,
        "present": 0,
    }


def test_a_float_nan_is_blank() -> None:
    """A data frame holds a missing number as NaN; it must not be a value that is less than 60."""
    nan = float("nan")
    assert evaluate_condition(parse_condition("[a] < 60"), {"a": nan}, blank="unknown") is None
    assert evaluate_condition(parse_condition("[a] is null"), {"a": nan}) is True
    profile: Profile = {"columns": [{"name": "a"}]}
    assert missingness(profile, {"a": [1.0, nan, None, ""]})["columns"]["a"] == {"present": 1, "blank": 3}
