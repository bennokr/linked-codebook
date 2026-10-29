# TypeScript

```bash
npm install linked-codebook
```

The package needs Node 22 or a browser. It has no dependencies. The types of the data model are exported.

```ts
import { build, parse, merge, toSssom, fromSssom, inferColumn, validate, run } from 'linked-codebook';
```

| Function | Result |
| --- | --- |
| `build(profile)` | DSV JSON-LD. |
| `parse(document)` | A `Profile` read from DSV JSON-LD. |
| `merge(base, incoming)` | `base` completed with `incoming`. |
| `toSssom(profile)` | SSSOM TSV as text. |
| `fromSssom(text, profile)` | A `Profile` with only the mappings found in the SSSOM text. |
| `infer(data)` | A `Profile` with the datatype and level of every column of `{ name: values }`. |
| `inferColumn(values, options?)` | `{ datatype, level? }` for one column. `options.name` marks identifiers and `options.labelled` counts value labels. |
| `validate(document)` | A list of errors. It is empty if the document conforms. |
| `canonical(value)` | JSON text with sorted keys. |
| `run(args, texts)` | The [command line](cli.md) as a function. |

Functions take and return plain objects. They do not change their arguments.
