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

Every case in `conformance/<command>/<case>/` has the input files `in1.*`, `in2.*`, the expected output `out` and, if the exit code is not 0, the file `code`. Both libraries must print `out` exactly. `make golden` rewrites the expected outputs with the TypeScript command line. Check the diff by hand before you commit it, because these files define the expected behaviour by example.

Regular expressions in the specification use only syntax that JavaScript and Python share, and match the whole text.

## Keep the code short

`budget.yaml` limits the number of statements in each library. `make budget` counts them with the Python `ast` module and with the TypeScript compiler. Lint rules limit the complexity and the length of functions. Raise a budget only with a reason.

## Docs

The pages in `docs/` are Markdown, built into a site with [VitePress](https://vitepress.dev): `make docs` builds it into `site/dist/docs` and fails on a broken link. `npx vitepress dev docs` serves it while you edit. Pages marked as generated are written by `make generate`. Link to files outside `docs/` with their GitHub URL, because the site does not contain them. Anchors are those of GitHub (`#71-language-of-a-text-column`).

The site is published with the test page by the Pages workflow: the test page at <https://bennokr.github.io/linked-codebook/> and the docs below it, at `/docs/`.

## Release

Other projects install the libraries from PyPI and npm (`pip install linked-codebook`, `npm install linked-codebook`), or from the test page, which serves every released file by name for projects that pin a checksum. A version is released when its two packages and its context are in `releases/`. The packages of a version that is not released are rebuilt from the current sources with every deploy and can change, so no project should depend on them.

1. Raise the version in `packages/ts/package.json`, `packages/py/pyproject.toml`, the install commands of the README and the line `Draft, version …` of the specification. `make versions` checks that they agree, and `make check` runs it.
2. Add the version to the [changelog](changelog.md). The text of that section becomes the text of the GitHub release.
3. Run `make generate` and `make check`, then `make release`, and commit the files in `releases/`: the npm tarball, the wheel and `context-<version>.jsonld`.
4. After the commit is on `main`, tag it `v<version>` (for example `v0.11.0`) and push the tag. The [Release workflow](https://github.com/bennokr/linked-codebook/blob/main/.github/workflows/release.yml) checks that the tag is the version of both packages, runs the checks again, and publishes the files of `releases/` to PyPI and npm, so every channel serves the same bytes. Then it creates the GitHub release with those files attached.

`make release` refuses to overwrite a released version. Never edit or replace a released file: projects keep its checksum. A version that was published to PyPI or npm cannot be published again, even after it is deleted, so raise the version.

### One-time setup of the registries

- **PyPI:** at <https://pypi.org/manage/account/publishing/> add a *pending* trusted publisher for the project `linked-codebook`: owner `bennokr`, repository `linked-codebook`, workflow `release.yml`, environment `pypi`. No token is stored.
- **npm:** the first release needs a token, because trusted publishing is set up on a package that exists. Create a granular token that may publish `linked-codebook` (read and write, 2FA bypass) and save it as the secret `NPM_TOKEN` of the GitHub environment `npm`. After the first release, add a trusted publisher on npmjs.com (package settings, GitHub Actions: user `bennokr`, repository `linked-codebook`, workflow `release.yml`, environment `npm`; npm does not check it when you save, so a typo shows up as a failed publish), then delete the token and the secret. The workflow installs npm 11.5.1 or later for this, and publishes with provenance.
- **GitHub environments:** create the environments `pypi` and `npm`, and require a review on them if a tag alone should not be enough to publish.

### The JSON-LD context as a file

`build` embeds the JSON-LD context in every document, so a document needs nothing else. The same context is published as a file, for documents or tools that would rather name it: `https://bennokr.github.io/linked-codebook/context-<version>.jsonld` for a version, which never changes once released, and `https://bennokr.github.io/linked-codebook/context.jsonld` for the current sources. `scripts/context.py` writes it from the same constants that `build` uses; a test checks that the two are equal.
