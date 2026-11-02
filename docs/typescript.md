# TypeScript

The package is not on npm yet. Install a released version as described in the [README](../README.md).

The package needs Node 22.18 or later, or a browser. It has no dependencies. The types of the data model are exported.

```ts
import {
  build,
  canonical,
  fromRedcap,
  fromSssom,
  fromTables,
  infer,
  inferColumn,
  isNumeric,
  merge,
  observe,
  parse,
  run,
  tableWarnings,
  toFrictionless,
  toSssom,
  toTables,
  unmatchedSssom,
  validate,
} from 'linked-codebook';
```

| Function | Result |
| --- | --- |
| `build(profile)` | DSV JSON-LD. |
| `parse(document, options?)` | A `Profile` read from DSV JSON-LD. `options.explicit` keeps the variable IRIs that the library would write itself. |
| `merge(base, incoming)` | `base` completed with `incoming`. |
| `toFrictionless(profile)` | A Frictionless Table Schema. |
| `toSssom(profile)` | SSSOM TSV as text. |
| `fromTables(tables)` | A `Profile` read from tables: sheet name to rows, the first row holding the headers. Cells may be text, numbers, booleans or `null`. |
| `toTables(profile)` | Tables for a profile. |
| `tableWarnings(tables)` | The sheets and headers of tables that `fromTables` does not use. |
| `fromRedcap(text)` | A `Profile` read from a REDCap data dictionary (CSV text). |
| `fromSssom(text, profile)` | A `Profile` with only the mappings found in the SSSOM text. |
| `unmatchedSssom(text, profile)` | The labels of the SSSOM rows that match nothing in the profile. |
| `infer(data)` | A `Profile` with the datatype and level of every column of `{ name: values }`, and the `observed` codes of categorical columns. |
| `observe(values)` | The codes of one column with their counts, in order of first occurrence. |
| `inferColumn(values, options?)` | `{ datatype, level? }` for one column. `options.name` marks identifiers, `options.identifier` says whether the column is one, `options.labelled` counts value labels and `options.limits` replaces the limits on distinct values. |
| `validate(document)` | A list of errors. It is empty if the document conforms. |
| `isNumeric(value)` | True for a number, or for text that is a plain number. |
| `canonical(value)` | JSON text with sorted keys. |
| `run(args, texts)` | The [command line](cli.md) as a function. |

Functions take and return plain objects. They do not change their arguments.
