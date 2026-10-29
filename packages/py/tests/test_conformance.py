from pathlib import Path

import pytest
from linked_codebook import build, from_sssom, infer_column, merge, parse, run, unmatched_sssom, validate
from linked_codebook.constants import VOCABULARY
from linked_codebook.types import Profile

ROOT = Path(__file__).resolve().parents[3] / "conformance"
CASES = sorted(path for path in ROOT.glob("*/*") if path.is_dir())


@pytest.mark.parametrize("case", CASES, ids=lambda case: f"{case.parent.name}/{case.name}")
def test_conformance(case: Path) -> None:
    files = sorted(path.name for path in case.glob("in*"))
    stdout, code = run([case.parent.name, *files], {name: (case / name).read_text(encoding="utf-8") for name in files})
    expected_code = int((case / "code").read_text()) if (case / "code").exists() else 0
    assert stdout == (case / "out").read_text(encoding="utf-8")
    assert code == expected_code


PROFILE: Profile = {
    "title": "Example",
    "columns": [
        {
            "name": "sex",
            "label": "Sex",
            "datatype": "string",
            "level": "nominal",
            "values": [{"code": "1", "label": "Male"}, {"code": "9", "label": "Unknown", "missing": True}],
        },
    ],
}


def test_json_ld_round_trip() -> None:
    assert parse(build(PROFILE)) == PROFILE
    assert validate(build(PROFILE)) == []


def test_merge_with_itself() -> None:
    assert merge(PROFILE, PROFILE) == PROFILE


def test_sssom_without_mappings_is_empty() -> None:
    assert from_sssom("subject_id\tpredicate_id\tobject_id\n", PROFILE) == {"columns": []}


def test_value_labels_make_a_column_categorical() -> None:
    codes = [index % 30 for index in range(60)]
    assert infer_column(codes).get("level") == "numerical"
    assert infer_column(codes, labelled=True).get("level") == "categorical"
    assert "level" not in infer_column(["a", "b", "a", "b", "a", "b"], "patient_id")


def test_every_term_is_in_its_vocabulary() -> None:
    assert VOCABULARY["unverified"] == []


def test_limits_can_be_raised() -> None:
    codes = [index % 12 for index in range(120)]
    assert infer_column(codes).get("level") == "numerical"
    assert infer_column(codes, limits={"number": 12}).get("level") == "categorical"


def test_unmatched_rows_are_listed() -> None:
    tsv = "subject_id\tsubject_label\tpredicate_id\tobject_id\nx:1\tnope\tskos:exactMatch\thttp://e/1\nx:2\tsex\tskos:exactMatch\thttp://e/2\n"
    assert unmatched_sssom(tsv, PROFILE) == ["nope"]


def test_a_known_identifier_overrides_the_name() -> None:
    codes = [1, 2, 1, 2, 1, 2]
    assert infer_column(codes, "id", identifier=False).get("level") == "categorical"
    assert infer_column(codes, "group", identifier=True).get("level") == "numerical"


def test_statistics_survive_json_ld() -> None:
    counted: Profile = {"rows": 3, "columns": [{"name": "a", "completeness": 0.5}]}
    assert parse(build(counted)) == counted
    assert validate(counted) == []
    assert validate({"rows": 1.5, "columns": []}) != []
