# TypeScript

```bash
npm install linked-codebook
```

The package needs Node 22.18 or later, or a browser, and has no dependencies. It installs the command `linked-codebook` (see [Command line](cli.md)) and exports the types of the data model.

<!-- api-imports: written by scripts/generate.py from the exports -->
```ts
import {
  build,
  canonical,
  conditions,
  evaluateCondition,
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
  missingness,
  observe,
  parse,
  parseCondition,
  run,
  tableSpec,
  tableWarnings,
  toFrictionless,
  toSssom,
  toTables,
  unmatchedSssom,
  validate,
} from 'linked-codebook';
```
<!-- /api-imports -->

<!-- api: written by scripts/generate.py from the docstrings -->
| Function | Description |
| --- | --- |
| `build(profile)` | Writes a profile as JSON-LD with the DSV ontology. |
| `canonical(value)` | JSON with sorted keys and two-space indentation, so that every implementation prints the same text. |
| `conditions(profile)` | The parsed `applies_when` of every column that has one, or the reason it could not be parsed. |
| `evaluateCondition(node, row, options?)` | Evaluates a condition tree for a row `{ name: cell }`: true, false or null (unknown). `node` is a tree from `parseCondition`. `options.blank` says what a blank value is. With 'value' (the default, as in REDCap) a blank is the empty value: it equals another blank and differs from anything else, so `[a] <> 1` is true when `a` is blank; only ordering a blank is unknown. With 'unknown' (as in SQL) every comparison with a blank is unknown. |
| `fromReadstat(variables)` | Reads the variables of a statistical file (SPSS, Stata or SAS) into a profile. `variables` is the variables as `statfmt` delivers them, or the dataset that holds them (see `StatVariable` and [section 15 of the specification](specification.md#15-statistical-files)). Value labels do not make a list closed: SPSS and Stata allow codes without a label. |
| `fromRedcap(text)` | Reads a REDCap data dictionary (CSV text) into a profile. |
| `fromSssom(text, profile)` | Reads SSSOM TSV text into a profile that holds only the mappings found in it. The profile has the columns and values of `profile` that the text maps. A subject is found by its IRI or else by the label of the column; rows with other subjects are dropped. |
| `fromTables(tables)` | Reads a profile from tables: sheet name to rows, the first row holding the headers. Cells may be text, numbers, booleans or `null`. Throws an error that names the sheet and row for a cell that does not fit its header or a row that refers to something that does not exist. |
| `infer(data, detect?)` | Proposes a profile for a table `{ name: [cells] }`: the datatype and measurement level of every column. Categorical columns also get their `observed` codes. With a `detect` function, text columns also get the `language` that `inferLanguage` finds. |
| `inferColumn(cells, options?)` | Proposes the datatype and measurement level of one column, as `{ datatype, level? }`. `level` is left out when the column has none. `options.name` marks identifiers, `options.identifier` says whether the column is one, `options.labelled` counts value labels and `options.limits` replaces the limits on distinct values. |
| `inferLanguage(cells, detect)` | The language of a column of prose, as `{ language, share, cells }`, or undefined. `detect` maps a text to a lower-case BCP 47 tag, or to `null` when it cannot tell. The result is `undefined` if the column is not mostly prose or the answers do not agree. Up to `sample` prose cells, evenly spaced, are given to `detect`; the most common answer wins, and counts only when it is the answer for `min_share` of the cells that were asked. A cell that the detector cannot place counts against the share; ties go to the smaller tag. See [section 7.1 of the specification](specification.md#71-language-of-a-text-column). |
| `isIdentifierName(name)` | Whether a column name marks an identifier: `id`, `row number`, `respno` or anything ending in `_id`. |
| `isNumeric(cell)` | True for a number, or for text that is a plain number. |
| `merge(base, incoming)` | Completes `base` with what `incoming` says. Columns, values and mappings are matched by name, code and concept. |
| `missingness(profile, data, options?)` | Counts, for each column of the profile that the data has, how its values divide. `data` is `{ name: cells }`. `present` is a value; `declared` counts the codes that mean no value; `blank` is an empty cell, divided by the rule `applies_when` into `blank_not_applicable` (skipped by design), `blank_applicable` (missing although the question applied) and `blank_unknown` (the rule cannot be decided). `answered_not_applicable` counts values in rows where the rule says the question does not apply. `options.blank` is how rules treat a blank, as in `evaluateCondition`. With 'value' (the default, as in REDCap) a declared missing code is an ordinary value in a rule; with 'unknown' it is a blank and makes the rule unknown. |
| `observe(cells)` | The codes of a column with how often each occurs, in order of first occurrence. Missing values are left out. |
| `parse(document, options?)` | Reads DSV JSON-LD, nested or as a flat graph, into a profile. A variable IRI that is the one this library would write is left out, unless `options.explicit` is set. |
| `parseCondition(text)` | Parses a condition of skip logic (REDCap branching logic or a SQL `WHERE` subset) into a tree. Throws an error for text that is not one, or that uses what the language does not have. |
| `run(args, texts)` | The command line as a function: runs a command on the texts of the files it names. It returns `{ stdout, code }` and does no input or output itself. See [Command line](cli.md). |
| `tableSpec` | The sheets, headers and kinds of cells of the table format, as in `spec/table.yaml`. An application can use it to check the cells of a workbook before it hands them over. |
| `tableWarnings(tables)` | The sheets and headers of tables that `fromTables` does not use. These are the sheets and headers it does not know, and the headers of the earlier workbook. |
| `toFrictionless(profile)` | Writes a profile as a Frictionless Table Schema. Slots of the dataset are kept in the extension property. |
| `toSssom(profile)` | Writes the mappings of a profile as SSSOM TSV text. |
| `toTables(profile)` | Writes a profile as tables. Observed counts are left out: they describe one copy of the data. |
| `unmatchedSssom(text, profile)` | The labels of the rows of an SSSOM text that match no column, value or match type of the profile. |
| `validate(document)` | Checks a profile against the model, or a JSON-LD document against the vocabularies. Returns a list of errors; it is empty if the document conforms. |
<!-- /api -->

Functions take and return plain objects and do not change their arguments.

## Types

The types of the data model (`Profile`, `Column`, `Value`, `Mapping`, …) are generated from `spec/profile.yaml` and exported as they are (see [Data model](data-model.md)). The other exported types describe the arguments and results of the functions:

<!-- api-types: written by scripts/generate.py from the docstrings -->
| Name | Definition | Description |
| --- | --- | --- |
| `Cell` | `string \| number \| boolean \| null` | One value of a column that `infer`, `inferColumn`, `inferLanguage` and `observe` read. |
| `Condition` | `string \| number \| Record<string, unknown>` | A node of the tree that `parseCondition` returns and `evaluateCondition` takes. It is a variable, a value, or an operator with its operands (see [section 13 of the specification](specification.md#13-conditions)). The tree is shaped like [JsonLogic](https://jsonlogic.com): `{ "==": [{ "var": "smoker" }, "1"] }`. |
| `Data` | `Record<string, unknown[]>` | Column name to cells: the data that `missingness` reads. |
| `Detector` | `(text: string) => string \| null \| undefined` | A language detector: a function from a text to a lower-case BCP 47 tag, or to `null` when it cannot tell. `infer` and `inferLanguage` take one. See [Language detectors](language.md). |
| `EvaluateOptions` | `{ blank?: 'value' \| 'unknown' }` | The third argument of `evaluateCondition` and `missingness`. |
| `FoundLanguage` | `{ language: string; share: number; cells: number }` | The result of `inferLanguage`: the tag, the share of the asked cells that gave it, and how many cells were asked. |
| `Inferred` | `{ datatype: Datatype; level?: Level }` | The result of `inferColumn`. |
| `Options` | `{ name?: string; identifier?: boolean; labelled?: boolean; limits?: Partial<Record<'text' \| 'number', number>> }` | The second argument of `inferColumn`. |
| `Result` | `{ stdout: string; code: number }` | What `run` returns: the output text and the exit code. |
| `StatVariable` | `{ name: string; label?: string \| null; type?: number; format?: string \| null; measure?: number; valueLabels?: { value: Cell; label: string }[] \| null; missingRanges?: { lo: Cell; hi: Cell }[] \| null }` | One variable as a ReadStat-based reader delivers it, for `fromReadstat`. See [section 15 of the specification](specification.md#15-statistical-files). |
| `Tables` | `Record<string, unknown[][]>` | Sheet name to rows, the first row holding the headers: what `fromTables` reads and `toTables` writes. Cells may be text, numbers, booleans or `null`. |
<!-- /api-types -->

## Language of text columns

`infer` takes a detector as a second argument and then adds `language` to the columns of prose. The package does not include a detector. [Language detectors](language.md) lists detectors that work and shows how to connect them.

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
