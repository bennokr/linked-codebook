# Changelog

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
