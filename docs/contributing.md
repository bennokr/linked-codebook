# Contributing

## Set up

```bash
make setup
```

This needs [uv](https://docs.astral.sh/uv/), Node 22 and `make`.

## Make a change

| To change | Edit | Then run |
| --- | --- | --- |
| A slot, class or enumeration | `spec/profile.yaml` | `make generate` |
| A term of the JSON-LD form, an IRI template or an alias | `spec/jsonld.yaml` | `make pin` and `make generate` |
| The SSSOM columns or prefixes | `spec/sssom.yaml` | `make generate` |
| An inference limit or pattern | `spec/inference.yaml` | `make generate` |
| The Frictionless projection | `spec/frictionless.yaml` | `make generate` |
| A command | `spec/commands.yaml` and both `cli` files | `make generate` |
| The behaviour | both libraries | `make golden`, and read the diff |

`make generate` rewrites the JSON Schema, the types, the constants of both libraries and the generated pages of these docs. CI fails if the files in the repository are not up to date.

`make pin` fetches the published vocabularies and checks that every term the JSON-LD form uses is defined there. It needs network access.

## Keep both libraries equal

Every case in `conformance/<command>/<case>/` has the input files `in1.*`, `in2.*`, the expected output `out` and, if the exit code is not 0, the file `code`. Both libraries must print `out` exactly. `make golden` rewrites the expected outputs with the TypeScript command line. Check the diff by hand before you commit it: the files are the specification by example.

Regular expressions in the specification use only syntax that JavaScript and Python share, and match the whole text.

## Keep the code short

`budget.yaml` limits the number of statements in each library. `make budget` counts them with the Python `ast` module and with the TypeScript compiler. Lint rules limit the complexity and the length of functions. Raise a budget only with a reason.

## Docs

The pages in `docs/` are Markdown. Pages marked as generated are written by `make generate`.

## Release

Other projects install the libraries from the test page, as described in the [README](../README.md). A version is released when its two packages are in `releases/`. The packages of a version that is not released are rebuilt from the current sources with every deploy and can change, so no project should depend on them.

1. Raise the version in `packages/ts/package.json`, `packages/py/pyproject.toml`, the install commands of the README and the line `Draft, version …` of the specification. `make versions` checks that they agree, and `make check` runs it.
2. Add the version to the [changelog](changelog.md).
3. Run `make generate` and `make check`, then `make release`, and commit the files in `releases/`.

`make release` refuses to overwrite a released version. Never edit or replace a released file: projects keep its checksum.
