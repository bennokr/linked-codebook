"""Tables: a profile survives being written and read back, and bad cells are named."""

import json
from pathlib import Path

import pytest
from linked_codebook import from_tables, table_warnings, to_tables

ROOT = Path(__file__).resolve().parents[3]
PROFILE = json.loads((ROOT / "conformance/to-tables/basic/in1.json").read_text())


def test_profile_survives_being_written_as_tables_and_read_back() -> None:
    tables = to_tables(PROFILE)
    assert from_tables(tables) == PROFILE
    assert table_warnings(tables) == []


def test_cell_that_does_not_fit_is_reported_with_its_sheet_row_and_header() -> None:
    with pytest.raises(ValueError, match="Columns row 2, minimum: 'low' is not a number"):
        from_tables({"Columns": [["name", "minimum"], ["a", "low"]]})
    with pytest.raises(ValueError, match="Values row 2"):
        from_tables({"Columns": [["name"], ["a"]], "Values": [["column", "code"], ["b", "1"]]})
