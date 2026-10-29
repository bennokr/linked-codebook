from pathlib import Path

import pytest
from linked_codebook import build, from_sssom, infer_column, merge, parse, run, validate
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
