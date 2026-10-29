# Linked Codebook

Linked Codebook is a data model for the variables of a table, and the tools to read, write and check it.

| Page | Contents |
| --- | --- |
| [Specification](specification.md) | The rules that every implementation follows. |
| [Data model](data-model.md) | The slots of each class and the values of each enumeration. |
| [Vocabulary](vocabulary.md) | The terms of external vocabularies that the JSON-LD form uses. |
| [Command line](cli.md) | The commands, their inputs and exit codes. |
| [TypeScript](typescript.md) | The TypeScript library. |
| [Python](python.md) | The Python library. |
| [Contributing](contributing.md) | How to change the specification and the code. |
| [Changelog](changelog.md) | Changes per version. |

The model is written in [LinkML](https://linkml.io) in [`spec/profile.yaml`](../spec/profile.yaml).
The other files in [`spec/`](../spec) hold the rest of the specification as data.
The JSON Schema, the types of both libraries and the pages [Data model](data-model.md) and [Vocabulary](vocabulary.md) are generated from them.
