"""Checks the projection with the Frictionless library itself."""

import json
from pathlib import Path

import pytest
from linked_codebook import to_frictionless

frictionless = pytest.importorskip("frictionless")

PROFILE = json.loads((Path(__file__).resolve().parents[3] / "conformance/to-frictionless/full/in1.json").read_text())


def test_table_schema_is_valid_and_keeps_the_extension(tmp_path: Path) -> None:
    descriptor = to_frictionless(PROFILE)
    assert frictionless.Schema.validate_descriptor(descriptor).valid
    schema = frictionless.Schema.from_descriptor(descriptor)
    assert schema.to_descriptor() == descriptor
    path = tmp_path / "data.csv"
    path.write_text("smoker,height\n0,170.5\n1,181\n9,-5\n99,160\n")
    resource = frictionless.Resource("data.csv", basepath=str(tmp_path), schema=schema)
    assert frictionless.validate(resource).valid
    assert [row["smoker"] for row in resource.read_rows()] == [0, 1, None, None]
