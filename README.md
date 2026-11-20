# Linked Codebook

A codebook describes the variables of a table: their names, datatypes, units, value labels and missing codes.
Linked Codebook adds links from variables and values to concepts in vocabularies and ontologies. It also records when a question applies and which answers mean "no value".

It reads and writes that description in several forms and checks it:

- **Read from** a [REDCap](https://projectredcap.org) data dictionary, SPSS, Stata and SAS files (through a ReadStat-based reader), spreadsheet-like tables, or the values of a table (`infer`).
- **Write to** [DSV](https://w3id.org/dsv-ontology) JSON-LD, [SSSOM](https://mapping-commons.github.io/sssom/) mappings, a [Frictionless Table Schema](https://specs.frictionlessdata.io/table-schema/) or tables.
- **Skip logic:** REDCap branching logic and a SQL `WHERE` subset are parsed into a tree and evaluated in three values (true, false, unknown).
- **Missingness:** for a codebook and data, how the cells of each column divide into values, declared missing codes and blanks, and the blanks into *skipped by design*, *missing although applicable* and *unknown*.
- **Language:** the language of a free-text column, found by a detector that you supply ([Language detectors](docs/language.md)).

This repository holds

- the **specification** of the data model and its serializations ([`docs/`](docs/index.md), published at <https://bennokr.github.io/linked-codebook/docs/>),
- a **TypeScript** library and command line ([`packages/ts`](packages/ts)),
- a **Python** library and command line ([`packages/py`](packages/py)),
- a **conformance suite** that both libraries pass ([`conformance/`](conformance)),
- a **test page** that runs both libraries in the browser: <https://bennokr.github.io/linked-codebook/>.

Both libraries have no dependencies and give the same output for the same input.

## Install

```bash
pip install linked-codebook   # Python 3.11 or later; also runs in Pyodide
npm install linked-codebook   # Node 22.18 or later, or a browser
```

Every release is also on the [test page](https://bennokr.github.io/linked-codebook/), named by version, for projects that pin a file and its checksum:

```bash
npm install https://bennokr.github.io/linked-codebook/linked-codebook-0.11.0.tgz
pip install https://bennokr.github.io/linked-codebook/linked_codebook-0.11.0-py3-none-any.whl
```

## Example

In a REDCap dictionary, `packs_per_day` is asked only of smokers:

```bash
linked-codebook from-redcap dictionary.csv > profile.json
linked-codebook conditions profile.json
```

```json
{ "packs_per_day": { "condition": { "==": [{ "var": "smoker" }, "1"] } } }
```

With the data, the blanks in `packs_per_day` are counted by cause:

```bash
linked-codebook missingness profile.json data.json
```

```json
{
  "columns": {
    "packs_per_day": { "blank": 3, "blank_applicable": 1, "blank_not_applicable": 2, "present": 1 }
  },
  "rows": 4
}
```

Two of the three blanks belong to non-smokers, who were never asked, and one belongs to a smoker who did not answer. The output also lists the other columns, which are left out here.

## Commands

The Python and the TypeScript package install the same command and print the same text. The [command line](docs/cli.md) page has the files and exit codes of each.

| To | Commands |
| --- | --- |
| Read a codebook from a source | `from-redcap`, `from-readstat`, `from-tables`, `from-sssom`, `infer` |
| Write it in another form | `build` (DSV JSON-LD), `to-sssom`, `to-frictionless`, `to-tables` |
| Combine and clean | `merge`, `normalize` |
| Check | `validate`, `check-tables` |
| Skip logic and missing values | `parse-condition`, `conditions`, `missingness` |

`infer` proposes datatypes and measurement levels from the values. It sets `language` only when a program passes a detector (see [Language detectors](docs/language.md)).

## Use as a library

```python
from linked_codebook import from_redcap, build, validate

profile = from_redcap(open("dictionary.csv").read())
document = build(profile)  # DSV JSON-LD
assert validate(document) == []
```

```ts
import { fromRedcap, build, validate } from 'linked-codebook';

const profile = fromRedcap(text);
const document = build(profile);
console.log(validate(document)); // []
```

See [Python](docs/python.md) and [TypeScript](docs/typescript.md) for every function and type.

## Development

```bash
make setup     # install the tools
make generate  # rebuild schema, types and constants from spec/*.yaml
make check     # lint, test and check the size of the code
make smoke     # open the test page in a browser
make docs      # build the documentation site
```

See [Contributing](docs/contributing.md).

### Documentation

The pages in `docs/` are Markdown, built into a site with [VitePress](https://vitepress.dev): `make docs` builds it into `site/dist/docs` and fails on a broken link, and `npx vitepress dev docs` serves it while you edit. Pages that are marked as generated in their source are written by `make generate`; edit `spec/` instead. Link to files outside `docs/` with their GitHub URL, because the site does not contain them. Anchors are those of GitHub (`#71-language-of-a-text-column`).

The Pages workflow publishes the site below the test page: the test page at <https://bennokr.github.io/linked-codebook/> and the docs at `/docs/`.

## License

MIT
