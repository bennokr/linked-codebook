# Changelog

## 0.9.0

- Added the slots `format` (how dates or numbers are written, in the notation of the source; Frictionless `format`), `minimum` and `maximum` (limits of a numeric column), `group` (the form of a REDCap field, or any named group of columns) and `identifying` (true if the values identify a person or a record). JSON-LD keys `minimumValue`, `maximumValue`, `columnGroup`, `identifying`; Frictionless `constraints.minimum` and `maximum`; `group` and `identifying` in `x-linked-codebook`.
- `from-redcap` reads Form Name (`group`), Identifier? (`identifying`) and numeric Text Validation Min and Max.
- Added tables: `from-tables`, `to-tables` and `check-tables`, with `fromTables`, `toTables`, `tableWarnings` and the Python equivalents. A set of sheets (Columns, Values, Mappings, Dataset) is read and written with the headers of the model. `closed` is only on `Columns`; missing codes only on `Values`. Workbook files are opened by the application; see section 12 of the specification.
- `from-redcap` reads CSV as Python's `csv` module does (a quote inside an unquoted field is text; text after a closing quote continues the field). The TypeScript reader used to reject a PhenX dictionary that Python read; with the change, both libraries print identical output for all 985 PhenX REDCap dictionaries (35,541 columns).
- Conditions are evaluated as REDCap does by default (`blank: value`): a blank is the empty value, so `[a] <> 1` is true when `a` is blank. `blank: unknown` gives the SQL reading (every comparison with a blank is unknown). The REDCap behaviour comes from university guides and a community knowledge base, not from REDCap's own documentation.
- Added conditions: `parse-condition` and `conditions` (`parse_condition`, `parseCondition`, `evaluate_condition`, `evaluateCondition`). One syntax reads REDCap branching logic and a subset of SQL `WHERE` into a JsonLogic-shaped tree and evaluates it in three values (true, false, unknown). 2,649 of the 2,650 different rules of the PhenX REDCap dictionaries parse, identically in both libraries.
- Added `missingness`: for a profile and data, how values divide into present values, declared missing codes and blanks, and the blanks into skipped by design, missing although applicable, and unknown.
- Added `from-readstat`: the variables of an SPSS, Stata or SAS file (as ReadStat-based readers deliver them) become columns, with variable and value labels, measure, format, and user-defined and extended missing values.
- The statement budgets rise by the size of the tables module (Python 563 to 1060, TypeScript 499 to 948; conditions, missingness and statistical files are about 300 statements in each library).

## 0.8.0

- Added the command `from-redcap`, `fromRedcap` and `from_redcap`: a REDCap data dictionary (CSV) becomes a profile. Dropdown, radio, yes/no, true/false and checkbox fields get closed value lists; text validation types give datatypes; the rules are in `spec/redcap.yaml`.
- Added the slot `applies_when`: the condition under which a column has a value, as the source writes it (REDCap branching logic). Written to JSON-LD as `appliesWhen`.

## 0.7.0

- Added the slot `source`: the IRI of a web page that documents the column. It is written as `dct:source` on the variable concept, and read from there or from the column property.
- For ordinal columns, the code concepts carry `schema:position`, and readers order the codes by it, because RDF has no order. Closed ordinal lists also set the Frictionless `categoriesOrdered`.

## 0.6.2

- Validation of JSON-LD skips keys whose term is null or a keyword such as `@nest`, as JSON-LD does, instead of failing.

## 0.6.1

- Python: `rows` read from JSON-LD is an integer, not a float.

## 0.6.0

- Added the slot `closed`: the values of a column are all the codes it may hold. Only closed lists become Frictionless `categories`; written to JSON-LD as `codeBookClosed`.
- Added the slot `observed`: codes found in the data with their counts, separate from the declared `values`. `infer` fills it for categorical columns, and `observe` computes it for one column.
- Validation reports observed codes outside a closed list.

## 0.5.0

- Added the option `explicit` of reading, which keeps variable IRIs that the library would write itself.

## 0.4.0

- Added the slots `rows` and `completeness`, which are written as DSV summary statistics.
- Integers are checked in profiles.

## 0.3.1

- Times may end in ` UTC`.

## 0.3.0

- Added the option `identifier` of the inference.

## 0.2.1

- Rows of SSSOM files are also matched to columns by the end of the subject IRI.

## 0.2.0

- Added the Frictionless Table Schema projection and the command `to-frictionless`.
- Added the option `limits` of the inference, `unmatchedSssom` and `isNumeric`.
- Written documents no longer contain empty objects.

## 0.1.0

First version of the specification, the TypeScript library, the Python library, the conformance suite and the test page.
