# Command line

```
linked-codebook <command> <file>...
```

The TypeScript package and the Python package install the same command. Both read the files that the arguments name, write the result to standard output and give the same output.

<!-- commands: generated from spec/commands.yaml by scripts/generate.py -->
| Command | Files | Result |
| --- | --- | --- |
| `normalize` | profile | Print a profile, read from profile JSON or DSV JSON-LD, as canonical JSON. |
| `build` | profile | Print a profile as DSV JSON-LD. |
| `to-sssom` | profile | Print the mappings of a profile as SSSOM TSV. |
| `from-sssom` | sssom, profile | Print the mappings in an SSSOM TSV file for the columns and codes of a profile. |
| `merge` | base, incoming | Print the first profile completed with the second. |
| `infer` | data | Print a profile with the datatype and level of every column of a JSON object of value lists. |
| `validate` | document | Check a profile against the model, or DSV JSON-LD against the vocabularies. Exit code 1 if it does not conform. |
| `from-redcap` | dictionary | Print a profile read from a REDCap data dictionary CSV. |
| `to-frictionless` | profile | Print the profile as a Frictionless Table Schema, with the other slots in the property x-linked-codebook. |
| `from-tables` | tables | Print a profile read from tables, a JSON object of sheet names and rows (the first row holds the headers). |
| `to-tables` | profile | Print the profile as tables, a JSON object of sheet names and rows. |
| `check-tables` | tables | List the sheets and headers of tables that a reader does not use. Prints ok if there are none. |
| `parse-condition` | condition | Print a condition of skip logic, REDCap branching logic or a SQL WHERE subset, as a JSON tree. |
| `conditions` | profile | Print the parsed applies_when of every column of a profile that has one, or why it could not be parsed. |
| `missingness` | profile, data | Print how the values of each column divide into values, declared missing codes and blanks, and the blanks into skipped by design, missing and unknown, for a JSON object of value lists. |
| `from-readstat` | variables | Print a profile read from the variables of a statistical file (SPSS, Stata, SAS), as JSON from a ReadStat-based reader. |
<!-- /commands -->

A *profile* file is profile JSON or DSV JSON-LD. A *data* file is a JSON object that maps each column name to a list of its values.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | The command succeeded. |
| 1 | `validate` found errors. |
| 2 | The arguments or an input were not valid. The message is on standard output. |

## In a browser or another program

The command is the function `run(args, texts)`. It takes the arguments, and the text of every file that they name, and returns the standard output and the exit code. It does not read files or write output, so it runs in Node, in Python and in a browser. The [test page](https://bennokr.github.io/linked-codebook/) calls it from TypeScript and, through Pyodide, from Python.
