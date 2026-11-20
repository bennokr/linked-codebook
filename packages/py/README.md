# linked-codebook (Python)

Read, write and check codebooks of tables whose variables are linked to concepts.

```bash
pip install linked-codebook
```

The package has no dependencies, needs Python 3.11 or later, and also runs in [Pyodide](https://pyodide.org). It installs the
command `linked-codebook`. A [TypeScript package](https://www.npmjs.com/package/linked-codebook) gives the same output.

```python
from linked_codebook import build, from_redcap, validate

profile = from_redcap(open("dictionary.csv").read())  # a REDCap data dictionary
document = build(profile)  # DSV JSON-LD
assert validate(document) == []
```

Documentation: <https://bennokr.github.io/linked-codebook/docs/>. Source: <https://github.com/bennokr/linked-codebook>.
