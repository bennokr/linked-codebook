# Type profiling

`infer` and `infer_column` (`inferColumn` in TypeScript) propose a datatype and a measurement level for a column from its values. They only propose: a person, or a source that says more such as a REDCap dictionary or a statistical file, can override the result, and `merge` lets declared values win over inferred ones. The rules are section 7 of the [specification](specification.md#7-column-type-profiling).

The numbers and patterns of the rules are not in the code of either library. Both read the same file, `spec/inference.yaml`, so they give the same answer for the same values, and a person can read the limits and change them.

## How a column is classified

The values `null`, the empty text and the values listed under `missing` are ignored. The kind of the column is the first of these that applies:

| Kind | Datatype | Measurement level |
| --- | --- | --- |
| empty | `string` | none |
| boolean | `boolean` | `categorical` |
| date, datetime | `date`, `datetime` | none |
| categorical | as for the values | `categorical` |
| number | `integer` if all are whole, else `number` | `numerical` |
| text | `string` | none |

The measurement level of each kind is the `level` entry of the file. A column is categorical if its name is not an identifier name and either its values are few and are not prose (text), or they are a few whole numbers that are not a counter (numbers), or it has value labels. Section 7 of the specification has the exact rule.

## The rule file

This is a copy of [`spec/inference.yaml`](https://github.com/bennokr/linked-codebook/blob/main/spec/inference.yaml). The documentation generator (`make generate`) refreshes it, so it cannot differ from the file the libraries read.

<!-- inference.yaml: copied from spec/inference.yaml by scripts/generate.py -->
```yaml
# How datatype and measurement level are inferred from the values of a column.
# Patterns match the whole text. They use only syntax that JavaScript and Python share.
limits:
  text: 50     # most distinct values of a text column that can still be categorical
  number: 8    # the same for a numeric column
small: 8       # this many distinct values always count as few
text_share: 0.1  # otherwise distinct values are at most this share of all values
prose: {characters: 80, words: 7}
sequence_from: 9  # an unbroken run of integers is a counter when it has more than 8 values
identifier_names: "id|row.?number|resp?no|.*_id"  # matched against the lower-cased name
missing: ["", "\\N"]
patterns:
  number: "[-+]?(?:[0-9]+\\.?[0-9]*|\\.[0-9]+)(?:[eE][-+]?[0-9]+)?"
  leading_zero: "[-+]?0[0-9].*"
  date: "([0-9]{4})-([0-9]{2})-([0-9]{2})(?:[T ](.+))?"
  dotted_date: "([0-9]{1,2})\\.([0-9]{1,2})\\.([0-9]{4})"
  time: "([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\\.[0-9]{1,9})?)?(?:Z| UTC|[+-][0-9]{2}:[0-9]{2})?"
level: {number: numerical, categorical: categorical, boolean: categorical}
```
<!-- /inference.yaml -->

## The fields

| Field | Meaning |
| --- | --- |
| `limits.text` | The most distinct values that a text column, or a column with value labels, can have and still be categorical. |
| `limits.number` | The same for a column of whole numbers without value labels. It is lower, because a few distinct numbers are less often codes than a few distinct words. |
| `small` | A text column with at most this many distinct values counts as having few. |
| `text_share` | Otherwise a text column has few distinct values if at most this share of its values are distinct. The values must also be at least 3 and fewer distinct than the number of values. |
| `prose` | A value is prose if it has more characters or more words than this, or a line break. A text column with prose is text, not categories. |
| `sequence_from` | Whole numbers that count up without a gap, with at least this many values, are a row counter and not codes. |
| `identifier_names` | A pattern matched against the lower-case name of the column. A column with an identifier name is never categorical. |
| `missing` | Values that are ignored, besides `null`. |
| `patterns` | Patterns for a number, for a number with a leading zero (which is text, such as `007`), for a date, for a date written `d.m.yyyy` and for the time of a datetime. They match the whole text and use only syntax that JavaScript and Python share. |
| `level` | The measurement level that each kind of column gets. |

## Changing the limits

A caller can replace `limits.text` and `limits.number`, say whether a column is an identifier, and say whether it has value labels. Everything else in the file is fixed by the specification, so that the libraries stay in step.

```python
from linked_codebook import infer_column

sites = [f"site {i % 40}" for i in range(400)]  # 40 distinct values in 400 cells
infer_column(sites)  # {'datatype': 'string', 'level': 'categorical'}
infer_column(sites, limits={"text": 30})  # {'datatype': 'string'}

scores = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 2  # 10 distinct whole numbers
infer_column(scores)  # {'datatype': 'integer', 'level': 'numerical'}
infer_column(scores, limits={"number": 12})  # {'datatype': 'integer', 'level': 'categorical'}
```

```ts
import { inferColumn } from 'linked-codebook';

inferColumn(sites, { limits: { text: 30 } });    // { datatype: 'string' }
inferColumn(scores, { limits: { number: 12 } }); // { datatype: 'integer', level: 'categorical' }
```

`infer` takes no limits: it profiles every column of a table with the limits of the file. Use `infer_column` for a column that needs other limits, and write the result into the profile.
