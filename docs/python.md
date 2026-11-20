# Python

```bash
pip install linked-codebook
```

The package needs Python 3.11, has no dependencies, and also runs in [Pyodide](https://pyodide.org). It installs the command `linked-codebook` (see [Command line](cli.md)). The types of the data model are `TypedDict`s in `linked_codebook.types`.

<!-- api-imports: written by scripts/generate.py from the exports -->
```python
from linked_codebook import (
    build,
    canonical,
    conditions,
    evaluate_condition,
    from_readstat,
    from_redcap,
    from_sssom,
    from_tables,
    infer,
    infer_column,
    infer_language,
    is_identifier_name,
    is_numeric,
    merge,
    missingness,
    observe,
    parse,
    parse_condition,
    run,
    table_warnings,
    to_frictionless,
    to_sssom,
    to_tables,
    unmatched_sssom,
    validate,
    Detector,
    Result,
    TABLE_SPEC,
)
```
<!-- /api-imports -->

<!-- api: written by scripts/generate.py from the docstrings -->
| Function | Description |
| --- | --- |
| `build(profile)` | Writes a profile as JSON-LD with the DSV ontology. |
| `canonical(value)` | JSON with sorted keys and two-space indentation, so that every implementation prints the same text. |
| `conditions(profile)` | The parsed `applies_when` of every column that has one, or the reason it could not be parsed. |
| `evaluate_condition(node, row, *, blank="value")` | Evaluates a condition tree for a row `{name: cell}`: True, False or None (unknown). `node` is a tree from `parse_condition`. `blank` says what a blank value is. With "value" (the default, as in REDCap) a blank is the empty value: it equals another blank and differs from anything else, so `[a] <> 1` is true when `a` is blank; only ordering a blank is unknown. With "unknown" (as in SQL) every comparison with a blank is unknown. |
| `from_readstat(variables)` | Reads the variables of a statistical file (SPSS, Stata or SAS) into a profile. `variables` is a list of dicts with the keys of ReadStat; see [section 15 of the specification](specification.md#15-statistical-files). Value labels do not make a list closed: SPSS and Stata allow codes without a label. |
| `from_redcap(text)` | Reads a REDCap data dictionary (CSV text) into a profile. |
| `from_sssom(text, profile)` | Reads SSSOM TSV text into a profile that holds only the mappings found in it. The profile has the columns and values of `profile` that the text maps. A subject is found by its IRI or else by the label of the column; rows with other subjects are dropped. |
| `from_tables(tables)` | Reads a profile from tables: sheet name to rows, the first row holding the headers. Cells may be text, numbers, booleans or `None`. Raises `ValueError`, naming the sheet and row, for a cell that does not fit its header or a row that refers to something that does not exist. |
| `infer(data, detect=None)` | Proposes a profile for a table `{name: [cells]}`: the datatype and measurement level of every column. Categorical columns also get their `observed` codes. With a `detect` function, text columns also get the `language` that `infer_language` finds. |
| `infer_column(cells, name="", *, labelled=False, identifier=None, limits=None)` | Proposes the datatype and measurement level of one column, as `{"datatype": ..., "level": ...}`. `level` is left out when the column has none. `name` marks identifiers, `identifier` says whether the column is one, `labelled` counts value labels and `limits` replaces the limits on distinct values. |
| `infer_language(cells, detect)` | The language of a column of prose, as `{"language", "share", "cells"}`, or None. `detect` maps a text to a lower-case BCP 47 tag, or to None when it cannot tell. The result is None if the column is not mostly prose or the answers do not agree. Up to `sample` prose cells, evenly spaced, are given to `detect`; the most common answer wins, and counts only when it is the answer for `min_share` of the cells that were asked. A cell that the detector cannot place counts against the share; ties go to the smaller tag. See [section 7.1 of the specification](specification.md#71-language-of-a-text-column). |
| `is_identifier_name(name)` | Whether a column name marks an identifier: `id`, `row number`, `respno` or anything ending in `_id`. |
| `is_numeric(cell)` | True for a number, or for text that is a plain number. |
| `merge(base, incoming)` | Completes `base` with what `incoming` says. Columns, values and mappings are matched by name, code and concept. |
| `missingness(profile, data, *, blank="value")` | Counts, for each column of the profile that the data has, how its values divide. `data` is `{name: [cells]}`. `present` is a value; `declared` counts the codes that mean no value; `blank` is an empty cell, divided by the rule `applies_when` into `blank_not_applicable` (skipped by design), `blank_applicable` (missing although the question applied) and `blank_unknown` (the rule cannot be decided). `answered_not_applicable` counts values in rows where the rule says the question does not apply. The argument `blank` is how rules treat a blank, as in `evaluate_condition`. With "value" (the default, as in REDCap) a declared missing code is an ordinary value in a rule; with "unknown" it is a blank and makes the rule unknown. |
| `observe(cells)` | The codes of a column with how often each occurs, in order of first occurrence. Missing values are left out. |
| `parse(document, *, explicit=False)` | Reads DSV JSON-LD, nested or as a flat graph, into a profile. A variable IRI that is the one this library would write is left out, unless `explicit` is set. |
| `parse_condition(text)` | Parses a condition of skip logic (REDCap branching logic or a SQL `WHERE` subset) into a tree. Raises `ValueError` for text that is not one, or that uses what the language does not have. |
| `run(args, texts)` | The command line as a function: runs a command on the texts of the files it names. It returns `(stdout, code)` and does no input or output itself. See [Command line](cli.md). |
| `TABLE_SPEC` | The sheets, headers and kinds of cells of the table format, as in `spec/table.yaml`. An application can use it to check the cells of a workbook before it hands them over. |
| `table_warnings(tables)` | The sheets and headers of tables that `from_tables` does not use. These are the sheets and headers it does not know, and the headers of the earlier workbook. |
| `to_frictionless(profile)` | Writes a profile as a Frictionless Table Schema. Slots of the dataset are kept in the extension property. |
| `to_sssom(profile)` | Writes the mappings of a profile as SSSOM TSV text. |
| `to_tables(profile)` | Writes a profile as tables. Observed counts are left out: they describe one copy of the data. |
| `unmatched_sssom(text, profile)` | The labels of the rows of an SSSOM text that match no column, value or match type of the profile. |
| `validate(document)` | Checks a profile against the model, or a JSON-LD document against the vocabularies. Returns a list of errors; it is empty if the document conforms. |
<!-- /api -->

Functions take and return plain dictionaries and lists and do not change their arguments.

## Types

The types of the data model (`Profile`, `Column`, `Value`, `Mapping`, …) are `TypedDict`s in `linked_codebook.types`, generated from `spec/profile.yaml` (see [Data model](data-model.md)). The package also exports two names for the arguments and results of the functions:

<!-- api-types: written by scripts/generate.py from the docstrings -->
| Name | Definition | Description |
| --- | --- | --- |
| `Detector` | `Callable[[str], str \| None]` | A language detector: a function from a text to a lower-case BCP 47 tag, or to None when it cannot tell. `infer` and `infer_language` take one. See [Language detectors](language.md). |
| `Result` | `NamedTuple(stdout: str, code: int)` | What `run` returns: the output text and the exit code. |
<!-- /api-types -->

## Language of text columns

`infer` takes a detector as a second argument and then adds `language` to the columns of prose. The package does not include a detector. [Language detectors](language.md) lists detectors that work and shows how to connect them.

```python
profile = infer(data, detect)  # detect: Detector
```

## Statistical files

`from_readstat` takes the variables of an SPSS, Stata or SAS file as ReadStat delivers them. With `pyreadstat`
(tested with `read_sav`; `user_missing=True` is needed to get the declared missing values):

```python
import pyreadstat
from linked_codebook import from_readstat

_, meta = pyreadstat.read_sav("survey.sav", metadataonly=True, user_missing=True)  # or read_dta, read_sas7bdat
MEASURE = {"nominal": 1, "ordinal": 2, "scale": 3}
TYPES = {"string": 0, "int8": 1, "int16": 2, "int32": 3, "float": 4, "double": 5}

variables = [
    {
        "name": name,
        "label": meta.column_names_to_labels[name],
        "type": TYPES[meta.readstat_variable_types[name]],
        "format": meta.original_variable_types[name],
        "measure": MEASURE.get(meta.variable_measure[name], 0),
        "valueLabels": [{"value": v, "label": t} for v, t in meta.variable_value_labels.get(name, {}).items()],
        "missingRanges": meta.missing_ranges.get(name, []),
    }
    for name in meta.column_names
]
profile = from_readstat(variables)
```

The Stata extended missing values (`.a` to `.z`) are not tested with `pyreadstat`; the specification says how to pass them.
