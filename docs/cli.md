# Command line

```
linked-codebook <command> <file>...
```

The TypeScript package and the Python package install the same command. Both read the files that the arguments name, write the result to standard output and give the same output.

| Command | Files | Result |
| --- | --- | --- |
| `normalize` | profile | The profile as canonical JSON. |
| `build` | profile | The profile as DSV JSON-LD. |
| `to-frictionless` | profile | The profile as a Frictionless Table Schema. |
| `to-sssom` | profile | The mappings of the profile as SSSOM TSV. |
| `from-sssom` | sssom, profile | The mappings in the SSSOM file for the columns and codes of the profile. |
| `merge` | base, incoming | The first profile completed with the second. |
| `infer` | data | A profile with the datatype and level of every column. |
| `validate` | document | `ok`, or one error per line. |

A *profile* file is profile JSON or DSV JSON-LD. A *data* file is a JSON object that maps each column name to a list of its values.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | The command succeeded. |
| 1 | `validate` found errors. |
| 2 | The arguments or an input were not valid. The message is on standard output. |

## In a browser or another program

The command is the function `run(args, texts)`. It takes the arguments, and the text of every file that they name, and returns the standard output and the exit code. It does not read files or write output, so it runs in Node, in Python and in a browser. The [test page](https://bennokr.github.io/linked-codebook/) calls it from TypeScript and, through Pyodide, from Python.
