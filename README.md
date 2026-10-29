# Linked Codebook

A codebook describes the variables of a table: their names, datatypes, units, value labels and missing codes.
Linked Codebook adds links from variables and values to concepts in vocabularies and ontologies.

This repository holds

- the **specification** of the data model and its serializations ([`docs/`](docs/index.md)),
- a **TypeScript** library and command line ([`packages/ts`](packages/ts)),
- a **Python** library and command line ([`packages/py`](packages/py)),
- a **conformance suite** that both libraries pass ([`conformance/`](conformance)),
- a **test page** that runs both libraries in the browser: <https://bennokr.github.io/linked-codebook/>.

Both libraries have no dependencies and give the same output for the same input.

## Example

```bash
linked-codebook infer data.json > profile.json       # propose datatypes and levels
linked-codebook build profile.json > profile.jsonld  # write DSV JSON-LD
linked-codebook to-sssom profile.json > mappings.tsv # write the links as SSSOM
linked-codebook to-frictionless profile.json > schema.json # write a Frictionless Table Schema
linked-codebook validate profile.jsonld              # check the terms against their vocabularies
```

Neither package is on npm or PyPI yet. Both are built for every release of the test page, and named by version:

```bash
npm install https://bennokr.github.io/linked-codebook/linked-codebook-0.2.1.tgz
pip install https://bennokr.github.io/linked-codebook/linked_codebook-0.2.1-py3-none-any.whl
```

Only the current version is kept there. Raise the version in `packages/ts/package.json` and `packages/py/pyproject.toml` for every change that other projects should receive.

## Development

```bash
make setup     # install the tools
make generate  # rebuild schema, types and constants from spec/*.yaml
make check     # lint, test and check the size of the code
make smoke     # open the test page in a browser
```

See [Contributing](docs/contributing.md).

## License

MIT
