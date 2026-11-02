# Python

The package is not on PyPI yet. Install a released version as described in the [README](../README.md).

The package needs Python 3.11 and has no dependencies. It also runs in [Pyodide](https://pyodide.org). The types of the data model are `TypedDict`s in `linked_codebook.types`.

```python
from linked_codebook import (
    build,
    canonical,
    from_readstat,
    from_redcap,
    from_sssom,
    from_tables,
    infer,
    infer_column,
    is_numeric,
    merge,
    observe,
    parse,
    run,
    table_warnings,
    to_frictionless,
    to_sssom,
    to_tables,
    unmatched_sssom,
    validate,
)
```

| Function | Result |
| --- | --- |
| `build(profile)` | DSV JSON-LD. |
| `parse(document, *, explicit=False)` | A `Profile` read from DSV JSON-LD. `explicit` keeps the variable IRIs that the library would write itself. |
| `merge(base, incoming)` | `base` completed with `incoming`. |
| `to_frictionless(profile)` | A Frictionless Table Schema. |
| `to_sssom(profile)` | SSSOM TSV as text. |
| `from_redcap(text)` | A `Profile` read from a REDCap data dictionary (CSV text). |
| `from_tables(tables)` | A `Profile` read from tables: sheet name to rows, the first row holding the headers. Cells may be text, numbers, booleans or `None`. |
| `to_tables(profile)` | Tables for a profile. |
| `TABLE_SPEC` | The sheets, headers and kinds of cells of the table format, as in `spec/table.yaml`. An application can use it to check the cells of a workbook before it hands them over. |
| `table_warnings(tables)` | The sheets and headers of tables that `from_tables` does not use. |
| `parse_condition(text)` | The tree of a condition of skip logic (REDCap branching logic or a SQL `WHERE` subset). Raises `ValueError` for text that is not one. |
| `evaluate_condition(tree, row)` | `True`, `False`, or `None` (unknown) for a row `{name: cell}`. |
| `conditions(profile)` | The parsed `applies_when` of every column that has one, or why it could not be parsed. |
| `missingness(profile, data)` | How the cells of each column divide into values, declared missing codes and blanks, and the blanks into skipped, missing and unknown. `data` is `{name: [cells]}`. |
| `from_readstat(variables)` | A `Profile` read from the variables of a statistical file, as a list of dicts with the keys of ReadStat (see section 15 of the specification). |
| `from_sssom(text, profile)` | A `Profile` with only the mappings found in the SSSOM text. |
| `unmatched_sssom(text, profile)` | The labels of the SSSOM rows that match nothing in the profile. |
| `infer(data)` | A `Profile` with the datatype and level of every column of `{name: values}`, and the `observed` codes of categorical columns. |
| `observe(values)` | The codes of one column with their counts, in order of first occurrence. |
| `infer_column(values, name="", *, labelled=False, identifier=None, limits=None)` | `{"datatype": ..., "level": ...}` for one column. `name` marks identifiers, `identifier` says whether the column is one, `labelled` counts value labels and `limits` replaces the limits on distinct values. |
| `validate(document)` | A list of errors. It is empty if the document conforms. |
| `is_numeric(value)` | True for a number, or for text that is a plain number. |
| `canonical(value)` | JSON text with sorted keys. |
| `run(args, texts)` | The [command line](cli.md) as a function. It returns `(stdout, code)`. |

Functions take and return plain dictionaries and lists. They do not change their arguments.
