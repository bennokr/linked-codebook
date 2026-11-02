# Changelog

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
