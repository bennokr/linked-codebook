# Language detectors

`infer` can add the language of a free-text column to a profile. The language is stored in the slot `language` as a lower-case [BCP 47](https://www.rfc-editor.org/info/bcp47) tag, and written to JSON-LD as `dct:language`. Linked Codebook does not include a detector. The application passes one in, and the specification defines when the detector is asked and when its answers are accepted.

## Why the application supplies the detector

A language detector is a statistical model, and different models disagree on some texts. Models also change between libraries and between versions of one library. If the specification named a detector, the Python and TypeScript libraries could not give the same output, and every installation would carry the weight of a model. The specification therefore defines the decision rule (section 7.1 of the [specification](specification.md#71-language-of-a-text-column)). Both libraries pass the same [test cases](https://github.com/bennokr/linked-codebook/blob/main/spec/cases/language.json), which use a fake detector.

## The detector function

A detector is a function from a text to a lower-case BCP 47 tag. It returns nothing when it cannot tell.

| Language | Type |
| --- | --- |
| TypeScript | `Detector = (text: string) => string \| null \| undefined` |
| Python | `Detector = Callable[[str], str \| None]` |

The library applies these rules:

- Only columns of prose are examined. A value is prose if it has more than 80 characters, a line break, or more than 7 words. A column needs at least 3 prose values, and at least half of its values must be prose.
- At most 200 prose values are passed to the detector, evenly spaced over the column.
- The most common tag becomes the language of the column if at least 0.8 of the values gave it. A value for which the detector returns nothing counts against that share.
- The result is `{ language, share, cells }` (from `infer_language` or `inferLanguage`), or nothing. `infer(data, detect)` writes `language` into the profile of every column that has a result.

The limits are in [`spec/language.yaml`](https://github.com/bennokr/linked-codebook/blob/main/spec/language.yaml).

The detector has to return BCP 47 tags such as `en`, `nl` and `pt-br`. Some detectors return the three-letter codes of ISO 639-3 (`eng`, `nld`), and their output needs a mapping, as in the snippets below. `validate` reports a tag that does not match the pattern of the model.

## Choosing a detector

The table lists the detectors that the maintainer tried while developing the protocol. The data and scripts of that comparison are not part of this repository, so check a detector on your own texts before relying on it.

| Detector | Runs in | Result |
| --- | --- | --- |
| [franc-min](https://www.npmjs.com/package/franc-min) (npm) | Node, browsers | It works well and is the choice for TypeScript. It returns ISO 639-3 codes, and `und` when it cannot tell, so its output needs a mapping. |
| [py3langid](https://pypi.org/project/py3langid/) (PyPI) | Python, Pyodide | It works well and is the choice for Python. |
| [tinyld](https://www.npmjs.com/package/tinyld) (npm) | Node, browsers | It returns language tags for texts that are not prose, such as names, codes and short labels. |
| [lingua](https://pypi.org/project/lingua-language-detector/) (PyPI) | Python | It is not available in Pyodide, so it cannot run on the [test page](https://bennokr.github.io/linked-codebook/) or in other in-browser Python. It works on a server. |
| [langdetect](https://pypi.org/project/langdetect/) (PyPI) | Python | It is unmaintained: its last release, 1.0.9, is from May 2021. Its answers vary between runs unless `DetectorFactory.seed` is set. |

An application that runs the library in both Node and Python uses two different models, which can disagree on a text. If that matters, record which detector made a profile.

## Examples

Both examples were run with franc-min 6.2.0, iso-639-3 3.0.1 and py3langid 0.4.0.

### TypeScript with franc-min

```bash
npm install linked-codebook franc-min iso-639-3
```

```ts
import { franc } from 'franc-min';
import { iso6393To1 } from 'iso-639-3';
import { infer, type Detector } from 'linked-codebook';

// franc returns ISO 639-3 ("eng"), or "und" when it cannot tell.
// BCP 47 uses the two-letter code where there is one.
const detect: Detector = (text) => {
  const code = franc(text);
  return code === 'und' ? null : (iso6393To1[code] ?? code);
};

const profile = infer({ note: ['A long free-text answer …', '…'] }, detect);
```

### Python with py3langid

```bash
pip install linked-codebook py3langid
```

```python
from py3langid.langid import classify

from linked_codebook import infer


def detect(text: str) -> str | None:
    tag, _score = classify(text)  # a two-letter ISO 639-1 code such as "en"
    return tag


profile = infer({"note": ["A long free-text answer …", "…"]}, detect)
```

`classify` always returns an answer, even for a text it cannot recognise. This is acceptable here, because only prose is examined and a column whose answers disagree is rejected by the 0.8 rule.

### One column

```python
from linked_codebook import infer_language

found = infer_language(values, detect)  # {"language": "en", "share": 0.97, "cells": 200}, or None
```

## The command line

The `infer` command does not set `language`, because a command line cannot take a function. To add a language, call `infer` from a program as shown above, or set the `language` of a column in the profile yourself.
