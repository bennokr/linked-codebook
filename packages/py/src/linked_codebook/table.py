"""Reading and writing a profile as tables, as defined by spec/table.yaml."""

import re
from typing import Any, cast

from .constants import ENUMS, TABLE
from .infer import is_numeric
from .jsonld import clean
from .types import Column, Profile

Tables = dict[str, list[list[Any]]]
Record = dict[str, Any]

SHEETS = TABLE["sheets"]
TRUE = ("true", "yes", "1")
FALSE = ("false", "no", "0")


def key(name: Any) -> str:  # noqa: ANN401
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def show(value: Any) -> str:  # noqa: ANN401
    """A cell as text: booleans as true and false, whole numbers without a decimal point."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def convert(raw: Any, kind: str, where: str) -> Any:  # noqa: ANN401
    """The value of a cell of the given kind, or None if the cell is blank."""
    text = "" if raw is None else show(raw)
    if not text:
        return None
    if kind == "text":
        return text
    if kind in ("number", "integer"):
        if not is_numeric(text) or (kind == "integer" and not float(text).is_integer()):
            message = f"{where}: '{text}' is not a{'n integer' if kind == 'integer' else ' number'}"
            raise ValueError(message)
        return int(float(text)) if kind == "integer" else float(text)
    if kind == "boolean":
        if text.lower() not in (*TRUE, *FALSE):
            message = f"{where}: '{text}' is not true or false"
            raise ValueError(message)
        return text.lower() in TRUE
    if text not in ENUMS[kind]:
        message = f"{where}: '{text}' is not one of {', '.join(ENUMS[kind])}"
        raise ValueError(message)
    return text


def sheet_of(tables: Tables, sheet: str) -> list[list[Any]]:
    wanted = key(SHEETS[sheet]["title"])
    return next((rows for name, rows in tables.items() if key(name) == wanted), [])


def records(tables: Tables, sheet: str) -> list[tuple[int, Record]]:
    """The rows of a sheet with a number (as in a spreadsheet) and the converted cells under their header."""
    rows = sheet_of(tables, sheet)
    spec = SHEETS[sheet]
    heads = [key(head) for head in rows[0]] if rows else []
    found = []
    for number, row in enumerate(rows[1:], start=2):
        if not any(cell is not None and show(cell) for cell in row):
            continue
        record: Record = {}
        for header in spec["headers"]:
            kind = spec["kinds"][header]
            index = heads.index(key(header)) if key(header) in heads else None
            raw = row[index] if index is not None and index < len(row) else None
            record[header] = convert(raw, kind, f"{spec['title']} row {number}, {header}")
        found.append((number, clean(record)))
    return found


def require(record: Record, sheet: str, number: int) -> None:
    for header in SHEETS[sheet]["required"]:
        if header not in record:
            message = f"{SHEETS[sheet]['title']} row {number}: {header} is required"
            raise ValueError(message)


def read_columns(tables: Tables) -> dict[str, Column]:
    columns: dict[str, Column] = {}
    for number, record in records(tables, "columns"):
        require(record, "columns", number)
        low, high = record.pop("missing_low", None), record.pop("missing_high", None)
        if (low is None) != (high is None):
            message = f"Columns row {number}: missing_low and missing_high go together"
            raise ValueError(message)
        if record["name"] in columns:
            message = f"Columns row {number}: column {record['name']} is listed twice"
            raise ValueError(message)
        columns[record["name"]] = cast("Column", clean({**record, "missing_range": clean({"low": low, "high": high})}))
    if not columns:
        message = "no columns found: the Columns sheet needs a name header and one row per column"
        raise ValueError(message)
    return columns


def read_values(tables: Tables, columns: dict[str, Column]) -> None:
    for number, record in records(tables, "values"):
        require(record, "values", number)
        column = columns.get(record["column"])
        if column is None:
            message = f"Values row {number}: column {record['column']} is not on the Columns sheet"
            raise ValueError(message)
        value = clean({k: record.get(k) for k in ("code", "label", "description")})
        if record.get("missing") and len(value) == 1:
            column.setdefault("missing_values", []).append(record["code"])
        else:
            column.setdefault("values", []).append(cast("Any", {**value, **clean({"missing": record.get("missing")})}))


def read_mappings(tables: Tables, columns: dict[str, Column]) -> None:
    for number, record in records(tables, "mappings"):
        require(record, "mappings", number)
        column = columns.get(record["column"])
        if column is None:
            message = f"Mappings row {number}: column {record['column']} is not on the Columns sheet"
            raise ValueError(message)
        target: Any = column
        if "code" in record:
            target = next((v for v in column.get("values", []) if v["code"] == record["code"]), None)
            if target is None:
                message = f"Mappings row {number}: {record['code']} is not a code of {record['column']} on Values"
                raise ValueError(message)
        mapping = {k: v for k, v in record.items() if k not in ("column", "code")}
        target.setdefault("mappings", []).append(mapping)


def read_dataset(tables: Tables) -> Record:
    spec = SHEETS["dataset"]
    keys = spec["headers"]
    found: Record = {}
    for number, row in enumerate(sheet_of(tables, "dataset")[1:], start=2):
        name = next((k for k in keys if row and key(row[0]) == key(k)), None)
        if name is not None and len(row) > 1:
            found[name] = convert(row[1], spec["kinds"][name], f"Dataset row {number}")
    return clean(found)


def from_tables(tables: Tables) -> Profile:
    """Reads a profile from tables: sheet name to rows, the first row holding the headers.

    Cells may be text, numbers, booleans or None. Raises ValueError, naming the sheet and row, for a cell that does
    not fit its header or a row that refers to something that does not exist.
    """
    columns = read_columns(tables)
    read_values(tables, columns)
    read_mappings(tables, columns)
    return cast("Profile", {**read_dataset(tables), "columns": list(columns.values())})


def table_warnings(tables: Tables) -> list[str]:
    """What a reader does not use: sheets and headers it does not know, and headers of the earlier workbook."""
    titles = {key(spec["title"]): sheet for sheet, spec in SHEETS.items()}
    warnings = []
    for name, rows in tables.items():
        sheet = titles.get(key(name))
        if sheet is None:
            warnings.append(f"sheet {name} is not used")
            continue
        known = {key(h) for h in [*SHEETS[sheet]["headers"], *(["key", "value"] if sheet == "dataset" else [])]}
        retired = {key(h) for h in TABLE["retired"].get(sheet, [])}
        heads = (show(h) for h in (rows[0] if rows else []) if h is not None)
        warnings += [
            f"{SHEETS[sheet]['title']} header {head} is not used"
            for head in heads
            if key(head) in retired or key(head) not in known
        ]
    return warnings


def column_record(column: Column) -> Record:
    limits = cast("dict[str, Any]", column.get("missing_range", {}))
    slots = {name: column.get(name) for name in SHEETS["columns"]["headers"] if not name.startswith("missing_")}
    return clean({**slots, "missing_low": limits.get("low"), "missing_high": limits.get("high")})


def value_records(column: Column) -> list[Record]:
    name = column["name"]
    slots = ("code", "label", "description", "missing")
    values = [clean({"column": name, **{slot: v.get(slot) for slot in slots}}) for v in column.get("values", [])]
    return [*values, *({"column": name, "code": code, "missing": True} for code in column.get("missing_values", []))]


def mapping_records(column: Column) -> list[Record]:
    owners = [({}, column), *(({"code": v["code"]}, v) for v in column.get("values", []))]
    return [
        clean({"column": column["name"], **owner, **mapping})
        for owner, holder in owners
        for mapping in cast("list[Any]", holder.get("mappings", []))
    ]


def grid(sheet: str, rows: list[Record]) -> list[list[str]]:
    """A sheet of the headers that have a cell somewhere, in the order of the specification."""
    spec = SHEETS[sheet]
    heads = [h for h in spec["headers"] if h in spec["required"] or any(h in row for row in rows)]
    return [heads, *([show(row[h]) if h in row else "" for h in heads] for row in rows)]


def to_tables(profile: Profile) -> Tables:
    """Writes a profile as tables. Observed counts are left out: they describe one copy of the data."""
    columns = profile["columns"]
    records_of = {
        "columns": [column_record(c) for c in columns],
        "values": [r for c in columns for r in value_records(c)],
        "mappings": [r for c in columns for r in mapping_records(c)],
    }
    shown = {sheet: rows for sheet, rows in records_of.items() if rows or sheet == "columns"}
    tables = {SHEETS[sheet]["title"]: grid(sheet, rows) for sheet, rows in shown.items()}
    given = cast("dict[str, Any]", profile)
    dataset = [[name, show(given[name])] for name in SHEETS["dataset"]["headers"] if given.get(name) is not None]
    if dataset:
        tables[SHEETS["dataset"]["title"]] = [["key", "value"], *dataset]
    return tables
