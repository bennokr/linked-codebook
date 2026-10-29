# Python

```bash
pip install linked-codebook
```

The package needs Python 3.11 and has no dependencies. It also runs in [Pyodide](https://pyodide.org). The types of the data model are `TypedDict`s in `linked_codebook.types`.

```python
from linked_codebook import build, parse, merge, to_sssom, from_sssom, infer_column, validate, run
```

| Function | Result |
| --- | --- |
| `build(profile)` | DSV JSON-LD. |
| `parse(document)` | A `Profile` read from DSV JSON-LD. |
| `merge(base, incoming)` | `base` completed with `incoming`. |
| `to_sssom(profile)` | SSSOM TSV as text. |
| `from_sssom(text, profile)` | A `Profile` with only the mappings found in the SSSOM text. |
| `infer(data)` | A `Profile` with the datatype and level of every column of `{name: values}`. |
| `infer_column(values, name="", *, labelled=False)` | `{"datatype": ..., "level": ...}` for one column. `name` marks identifiers and `labelled` counts value labels. |
| `validate(document)` | A list of errors. It is empty if the document conforms. |
| `canonical(value)` | JSON text with sorted keys. |
| `run(args, texts)` | The [command line](cli.md) as a function. It returns `(stdout, code)`. |

Functions take and return plain dictionaries and lists. They do not change their arguments.
