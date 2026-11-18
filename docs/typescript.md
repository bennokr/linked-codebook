# TypeScript

```bash
npm install linked-codebook
```

The package needs Node 22.18 or later, or a browser. It has no dependencies. The command `linked-codebook` is installed with it (see [Command line](cli.md)). The types of the data model are exported.

```ts
import {
  build,
  canonical,
  fromReadstat,
  fromRedcap,
  fromSssom,
  fromTables,
  infer,
  inferColumn,
  inferLanguage,
  isIdentifierName,
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
| `tableSpec` | The sheets, headers and kinds of cells of the table format, as in `spec/table.yaml`. An application can use it to check the cells of a workbook before it hands them over. |
| `tableWarnings(tables)` | The sheets and headers of tables that `fromTables` does not use. |
| `parseCondition(text)` | The tree of a condition of skip logic (REDCap branching logic or a SQL `WHERE` subset). Throws an error for text that is not one. |
| `evaluateCondition(tree, row, { blank })` | `true`, `false`, or `null` (unknown) for a row `{name: cell}`. `blank: 'unknown'` makes every comparison with a blank unknown, as in SQL; the default is REDCap's (a blank is a value). |
| `conditions(profile)` | The parsed `applies_when` of every column that has one, or why it could not be parsed. |
| `missingness(profile, data, { blank })` | How the cells of each column divide into values, declared missing codes and blanks, and the blanks into skipped, missing and unknown. `data` is `{name: cells}`. |
| `fromReadstat(variables)` | A `Profile` read from the variables of a statistical file, as `statfmt` delivers them (see section 15 of the specification). |
| `fromRedcap(text)` | A `Profile` read from a REDCap data dictionary (CSV text). |
| `fromSssom(text, profile)` | A `Profile` with only the mappings found in the SSSOM text. |
| `unmatchedSssom(text, profile)` | The labels of the SSSOM rows that match nothing in the profile. |
| `infer(data, detect?)` | A `Profile` with the datatype and level of every column of `{ name: values }`, and the `observed` codes of categorical columns. With a `detect` function, text columns also get the `language` that `inferLanguage` finds. |
| `inferLanguage(values, detect)` | `{ language, share, cells }` for a column of prose, or `undefined`. `detect` maps a text to a lower-case BCP 47 tag or `null`; see section 7.1 of the specification. |
| `isIdentifierName(name)` | Whether a column name marks an identifier (`id`, `row number`, `respno`, `*_id`). |
| `observe(values)` | The codes of one column with their counts, in order of first occurrence. |
| `inferColumn(values, options?)` | `{ datatype, level? }` for one column. `options.name` marks identifiers, `options.identifier` says whether the column is one, `options.labelled` counts value labels and `options.limits` replaces the limits on distinct values. |
| `validate(document)` | A list of errors. It is empty if the document conforms. |
| `isNumeric(value)` | True for a number, or for text that is a plain number. |
| `canonical(value)` | JSON text with sorted keys. |
| `run(args, texts)` | The [command line](cli.md) as a function. |

Functions take and return plain objects. They do not change their arguments.

## Types

The types of the data model (`Profile`, `Column`, `Value`, `Mapping`, …) are generated from `spec/profile.yaml` and exported as they are (see [Data model](data-model.md)). The other exported types describe the arguments and results of the functions:

| Type | Definition | Used by |
| --- | --- | --- |
| `Cell` | `string \| number \| boolean \| null` | One value of a column that `infer`, `inferColumn`, `inferLanguage` and `observe` read. |
| `Detector` | `(text: string) => string \| null \| undefined` | The language detector that `infer` and `inferLanguage` take; see [Language detectors](language.md). |
| `FoundLanguage` | `{ language: string; share: number; cells: number }` | The result of `inferLanguage`: the tag, the share of the asked cells that gave it, and how many cells were asked. |
| `Inferred` | `{ datatype: Datatype; level?: Level }` | The result of `inferColumn`. |
| `Options` | `{ name?, identifier?, labelled?, limits? }` | The second argument of `inferColumn`. |
| `Condition` | `string \| number \| Record<string, unknown>` | A node of the tree that `parseCondition` returns and `evaluateCondition` takes. The tree is shaped like [JsonLogic](https://jsonlogic.com): `{ "==": [{ "var": "smoker" }, "1"] }`. |
| `EvaluateOptions` | `{ blank?: 'value' \| 'unknown' }` | The third argument of `evaluateCondition` and `missingness`. |
| `Data` | `Record<string, unknown[]>` | Column name to cells: the data that `missingness` reads. |
| `Tables` | `Record<string, unknown[][]>` | Sheet name to rows, the first row holding the headers: what `fromTables` reads and `toTables` writes. |
| `StatVariable` | `{ name; label?; type?; format?; measure?; valueLabels?; missingRanges? }` | One variable as a ReadStat-based reader delivers it, for `fromReadstat`. |
| `Result` | `{ stdout: string; code: number }` | What `run` returns. |

## Language of text columns

`infer` takes a detector as a second argument and then adds `language` to the columns of prose. The package has no detector of its own: see [Language detectors](language.md) for which to use, and a snippet.

```ts
const profile = infer(data, detect); // detect: Detector
```

## Statistical files

`fromReadstat` takes the variables that [`statfmt`](https://www.npmjs.com/package/@irbisadm/statfmt) (a TypeScript port
of ReadStat for SPSS, Stata and SAS) delivers, as they are:

```ts
import { readSav } from '@irbisadm/statfmt';
import { fromReadstat } from 'linked-codebook';

const dataset = readSav(new Uint8Array(buffer)); // or readDta, readSas7bdat
const profile = fromReadstat(dataset.variables);
```

`statfmt` gives a Stata extended missing value (`.a`) as `null` in the value labels, and `fromReadstat` skips it.
