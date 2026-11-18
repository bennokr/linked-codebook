# Language detectors

`infer` can add the language of a free-text column (`language`, a lower-case [BCP 47](https://www.rfc-editor.org/info/bcp47) tag, written to JSON-LD as `dct:language`). Linked Codebook does not ship a detector. It specifies when a detector is asked and when its answers are accepted, and you supply the detector.

## Why there is no built-in detector

The language of a text can only be told by a statistical model, and two models never agree on every text. A model also differs between libraries and between versions of one library. If the specification fixed a detector, the Python and the TypeScript library could not print the same output, and a model would add its weight to a package that has no dependencies. So the specification fixes everything around the detector instead (section 7.1 of the [specification](specification.md#71-language-of-a-text-column)), and both libraries pass the same [test cases](https://github.com/bennokr/linked-codebook/blob/main/spec/cases/language.json) with a fake detector.

## The contract

A detector is a function from a text to a lower-case BCP 47 tag, or to nothing when it cannot tell:

| Language | Type |
| --- | --- |
| TypeScript | `Detector = (text: string) => string \| null \| undefined` |
| Python | `Detector = Callable[[str], str \| None]` |

What the library does with it:

- Only columns of **prose** are asked: a value is prose if it has more than 80 characters, a line break, or more than 7 words. A column needs at least 3 prose values, and at least half of its values must be prose.
- At most **200** prose values are asked, evenly spaced over the column.
- The most common tag is the language of the column if at least **0.8** of the asked values gave it. A value for which the detector gives nothing counts against that share.
- The result is `{ language, share, cells }` (`infer_language`, `inferLanguage`), or nothing. `infer(data, detect)` then writes `language` into the profile of every such column.

The limits are in [`spec/language.yaml`](https://github.com/bennokr/linked-codebook/blob/main/spec/language.yaml).

A detector has to return **BCP 47 tags** (`en`, `nl`, `pt-br`), not the three-letter codes of ISO 639-3 (`eng`, `nld`) that some of them print. Map them, as in the snippets below. `validate` rejects a tag that does not match the pattern of the model.

## Which detector

These are the maintainer's measurements, made while building the protocol. The data and the scripts are not in this repository, so treat the verdicts as findings to re-check on your own texts, not as a benchmark.

| Detector | Runs in | Verdict |
| --- | --- | --- |
| [franc-min](https://www.npmjs.com/package/franc-min) (npm) | Node, browsers | **Works.** Use it for TypeScript. Prints ISO 639-3 codes and `und` for "cannot tell", so it needs a mapping. |
| [py3langid](https://pypi.org/project/py3langid/) (PyPI) | Python, Pyodide | **Works.** Use it for Python. |
| [tinyld](https://www.npmjs.com/package/tinyld) (npm) | Node, browsers | Invents language tags for texts that are not prose (names, codes, short labels). Do not use it where a column may mix prose and other text. |
| [lingua](https://pypi.org/project/lingua-language-detector/) (PyPI) | Python | Not available in Pyodide, so it cannot run where the [test page](https://bennokr.github.io/linked-codebook/) and other in-browser tools run Python. Fine on a server. |
| [langdetect](https://pypi.org/project/langdetect/) (PyPI) | Python | Unmaintained: the last release (1.0.9) is from May 2021. It is also random unless you set `DetectorFactory.seed`, so two runs can disagree. |

Prefer a detector that is available in both of your environments, since an application that runs the library in Node and in Python should not get different languages for one file from different models. If it must be so, accept that the `language` in a profile depends on the detector that made it.

## Snippets

Both snippets were run when this page was written, with franc-min 6.2.0, iso-639-3 3.0.1 and py3langid 0.4.0.

### TypeScript with franc-min

```bash
npm install linked-codebook franc-min iso-639-3
```

```ts
import { franc } from 'franc-min';
import { iso6393To1 } from 'iso-639-3';
import { infer, type Detector } from 'linked-codebook';

// franc gives ISO 639-3 ("eng") and "und" when it cannot tell. BCP 47 wants the two-letter code where there is one.
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

`classify` always gives an answer, even for a text it cannot know. That is acceptable here because only prose is asked and the 0.8 share rule rejects a column whose answers disagree.

### Only the language of one column

```python
from linked_codebook import infer_language

found = infer_language(values, detect)  # {"language": "en", "share": 0.97, "cells": 200}, or None
```

## The command line

The `infer` command does **not** detect language. A command line cannot take a function, and the commands print the same text in both libraries. To get a `language` into a profile, call `infer` from a program as above, or set the `language` of a column in the profile yourself.
