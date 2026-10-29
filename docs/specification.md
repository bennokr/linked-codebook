# Linked Codebook Specification

Draft, version 0.5.0

## Abstract

Linked Codebook is a data model for the variables of a table. It records the name, datatype, level of measurement, unit, value labels and missing codes of each column, and links columns and values to concepts. This document defines the model, its serializations as JSON-LD and SSSOM, the inference of datatypes and levels, merging, validation and the command line.

## Status of this document

This is a draft. It may change without notice. Changes are listed in the [changelog](changelog.md).

## Table of contents

1. [Introduction](#1-introduction)
2. [Conformance](#2-conformance)
3. [Data model](#3-data-model)
4. [Canonical JSON](#4-canonical-json)
5. [JSON-LD](#5-json-ld)
6. [SSSOM](#6-sssom)
7. [Inference](#7-inference)
8. [Merging](#8-merging)
9. [Validation](#9-validation)
10. [Frictionless](#10-frictionless)
11. [Command line](#11-command-line)
12. [References](#12-references)

## 1. Introduction

### 1.1 Purpose

A codebook, or data dictionary, describes the variables of a table. Linked Codebook adds links from variables and values to concepts, so that tables from different sources can be compared and combined.

### 1.2 Scope

This specification defines how a codebook is represented and processed. It does not define how a table is read, or how concepts are found.

### 1.3 Conventions

The key words MUST, MUST NOT, SHOULD and MAY are to be interpreted as described in [RFC 2119][rfc2119] and [RFC 8174][rfc8174] when, and only when, they appear in capitals.

Examples and notes are not normative.

### 1.4 Terminology

**profile**
: A description of a dataset and its columns.

**column**
: One column of a table, described as a variable.

**value**
: A code that occurs in a column, with its label.

**mapping**
: A link from a column or a value to a concept. A mapping that has a `reviewer_id` is *approved*. Other mappings are *drafts*.

**concept**
: A thing that has an IRI, for example an entry in a thesaurus or an ontology.

**IRI**
: An Internationalized Resource Identifier, as defined by [RFC 3987][rfc3987].

## 2. Conformance

This specification has three conformance classes.

**Profile.** A profile is a JSON document that conforms to the [data model](#3-data-model) and to the rules of [validation](#9-validation).

**JSON-LD document.** A JSON-LD document conforms if it follows [section 5](#5-json-ld) and the check of [section 9.2](#92-json-ld-documents) finds no errors.

**Processor.** A processor is a program that reads or writes profiles. It conforms if it follows sections 4 to 11 and prints, for every case of the [conformance suite](https://github.com/bennokr/linked-codebook/tree/main/conformance), exactly the expected output.

## 3. Data model

A profile is a JSON object. The classes, slots and enumerations of the model are in [Data model](data-model.md). The model is defined in LinkML, in [`spec/profile.yaml`](../spec/profile.yaml). A JSON Schema is generated from it, in [`spec/generated/profile.schema.json`](../spec/generated/profile.schema.json).

Unknown properties are errors. A processor that wants to keep extra information MUST NOT put it in a profile.

Notes:

- A column is identified by its `name`, a value by its `code` and a mapping by its `object_id`.
- The `level` is the level of measurement and the `datatype` is the way values are stored. A column of integer codes has the datatype `integer` and the level `categorical`.
- `missing_values` lists codes that mean no value and have no label. A code that has a label is a `value` with `missing` set to true.

## 4. Canonical JSON

A processor MUST print JSON in the canonical form:

- Keys of objects are sorted by code point.
- Indentation is two spaces and the text ends with a line feed.
- Numbers with no fraction have no decimal point.
- Characters other than control characters are not escaped.

The canonical form lets different implementations print the same bytes for the same data.

## 5. JSON-LD

### 5.1 Writing

A processor writes a profile as JSON-LD that uses the [DSV ontology][dsv]. The context is the one in the constants generated from [`spec/jsonld.yaml`](../spec/jsonld.yaml). The terms that the document uses are listed in [Vocabulary](vocabulary.md).

The document is one node, the dataset, with these properties.

| Node | Type | Properties |
| --- | --- | --- |
| Dataset | `dcat:Dataset`, `dsv:Dataset` | `title`, `description`, `identifier`, `citation`, `accessRights` and `landingPage` carry the slots of the same meaning. `license` is written as `license` if it starts with `http:` or `https:`, and as `rights` otherwise. `datasetSchema` is the schema node. |
| Dataset statistics | `dsv:SummaryStatistics` | `numberOfRows` carries `rows` and `numberOfColumns` the number of columns. The node is written only if the profile has `rows`. |
| Schema | `dsv:DatasetSchema` | `columns` is the list of column nodes, in table order. |
| Column | `dsv:Column` | `name`, `titles` (the label, or else the name), `datatype`, `nullValues`, `missingRange`, `columnProperty` and `summaryStatistics`. |
| Column property | `dsv:ColumnProperty` | `hasVariable` is the variable concept. `hasUnit` and `unitText` carry `unit_iri` and `unit`. `hasCodeBook` is the concept scheme of the values. |
| Summary statistics | `dsv:SummaryStatistics` | `statisticalDataType` is the meaning of the `level` and `columnCompleteness` carries `completeness`. The node is written only if one of them is set. |
| Variable concept | `skos:Concept` | `skos:prefLabel` is the label, or else the name. `skos:definition` is the description. |
| Code book | `skos:ConceptScheme` | `skos:hasTopConcept` lists a concept for every value. |
| Code concept | `skos:Concept` | `skos:notation` is the code, `skos:prefLabel` the label, `skos:definition` the description and `skos:inScheme` the code book. |

Properties without a value MUST be left out. That includes empty text, empty lists and empty objects. `nullValues` lists the `missing_values` and the codes of the values that have `missing` set. `missingRange` is the object `{ "low": …, "high": … }`. It is not defined by any vocabulary and other processors ignore it.

Only approved mappings are written. A mapping becomes the property `exactMatch`, `closeMatch`, `broadMatch`, `narrowMatch` or `relatedMatch`, according to its `match_type`, of the variable concept or of the code concept. The properties list the `object_id` values. Draft mappings, labels, confidence, provenance and reviewers are not written.

The IRI of each node is made from a template in [`spec/jsonld.yaml`](../spec/jsonld.yaml). In the templates, `{id}`, `{name}` and `{code}` are percent-encoded, as by `encodeURIComponent`. The IRI of the dataset is the `identifier` if it starts with `http:`, `https:` or `urn:`. Otherwise it is made from the identifier, the title, or the word `unnamed`. The IRI of the variable concept is the `variable` of the column, if it has one.

### 5.2 Reading

A processor MUST read documents that it wrote. It SHOULD read documents from other sources that use the same terms, nested or as a flat graph of nodes that refer to each other by `@id`. For these the following rules apply.

1. Prefixes and namespaces of keys are ignored: `dct:title`, `dcterms:title` and `title` are the same key. A processor also looks for the aliases listed in `spec/jsonld.yaml`.
2. Objects that have the same `@id` are one node.
3. The dataset is the first node that has a `datasetSchema`. Its columns may be a JSON-LD list.
4. The `name` of a column is its `csvw:name`, or else its title. The `label` is the title, unless it equals the name.
5. The `datatype` is a string or an object with a `base`. Its name without prefix is looked up in the datatype aliases. Datatypes that are not in the model are left out.
6. A code of `nullValues` that is a code of the code book sets `missing` on that value. Other codes become `missing_values`.
7. The `level` is read from the summary statistics of the column, or of its column property.
8. The `variable` is the IRI of the variable concept, unless it is the IRI that the processor would write. A processor MAY offer an option to keep that IRI too.
9. Every `…Match` property of the variable concept or a code concept becomes a mapping. The `reviewer_id` of these mappings is `imported`, because only approved mappings are written.
10. `missingRange` is an object with `low` and `high`, or a list of two numbers.
11. If the dataset has no `license`, the `rights` are used.
12. `rows` is read from `numberOfRows` of the summary statistics of the dataset and `completeness` from `columnCompleteness` of those of the column. The number of columns is not read.

A document without columns is an error.

## 6. SSSOM

### 6.1 Writing

A processor writes the mappings of a profile as [SSSOM][sssom] TSV, with one row for each mapping, in the order of the columns, and for each column the mappings of the column before the mappings of its values.

The file starts with a header of comment lines: `#curie_map:`, then one line `#  prefix: IRI` for every prefix that is used, then `#mapping_set_id: IRI`. The header line follows with the names of the columns, as listed in [`spec/sssom.yaml`](../spec/sssom.yaml).

| SSSOM column | Value |
| --- | --- |
| `subject_id` | The IRI of the variable concept, or of the code concept. IRIs that start with the IRI of the dataset and `#` are written as `ds:` and the rest. |
| `subject_label` | The label of the column or value, or else its name or code. |
| `predicate_id` | The meaning of the `match_type`, for example `skos:exactMatch`. |
| `object_id` | The `object_id`. IRIs of Wikidata are written as `wd:` and the rest, and IRIs of OBO ontologies as `PREFIX:id`. |
| `mapping_justification` | `semapv:ManualMappingCuration`. |
| `object_label`, `confidence`, `reviewer_id` | The slots of the same name. |
| `mapping_provider` | `provenance`. |
| `mapping_date` | The first ten characters of `retrieved_at`. |
| `comment` | `description`. |

Tabs and line breaks in a cell are replaced by a space. Drafts have an empty `reviewer_id`.

### 6.2 Reading

A processor reads SSSOM TSV for the columns and values of a profile it is given.

1. Lines that start with `#` and look like `#  prefix: IRI` define prefixes, in addition to those in `spec/sssom.yaml`.
2. The subject is expanded. If it is the IRI of the variable or of a code of the profile, the row belongs to that column or value. Otherwise, if the `subject_label` or the last part of the subject IRI, after `variable-` if that comes first, is the name of a column, the row belongs to that column. Case, spaces, hyphens and underscores are ignored in this comparison.
3. The `predicate_id` is matched by its name without prefix against the meanings of the match types.
4. The `confidence` is kept if it is a number.
5. Rows that match no column or no match type are dropped.

The result is a profile that has only the columns and values with mappings. It can be [merged](#8-merging) into the profile.

## 7. Inference

A processor MAY propose the datatype and the level of a column from its values. The limits and patterns are in [`spec/inference.yaml`](../spec/inference.yaml). Patterns match the whole text.

The values `null`, the empty text and `\N` are ignored. The kind of the column is the first of these that applies.

| Kind | Applies if | Datatype | Level |
| --- | --- | --- | --- |
| empty | no values are left | `string` | none |
| boolean | all values are booleans | `boolean` | `categorical` |
| date | all values are dates | `date` | none |
| datetime | all values are dates and some have a time | `datetime` | none |
| categorical | see below | as for the values | `categorical` |
| number | all values are numbers | `integer` if all are whole, else `number` | `numerical` |
| text | none of the above | `string` | none |

A *date* is `YYYY-MM-DD`, optionally followed by `T` or a space and a time `hh:mm`, `hh:mm:ss` or with fractions of seconds, and an offset (`Z`, ` UTC` or `+hh:mm`), or `d.m.yyyy`. The day MUST exist in the calendar. Dates with slashes are not recognised, because their order is ambiguous.

A *number* is a number, or text that matches the number pattern: an optional sign, digits with an optional fraction, and an optional exponent. Text with a leading zero, such as `007`, is not a number.

A column is *categorical* if its name is not an identifier and one of the following holds.

- **Text.** There are at most 50 distinct values, at least 3 values and fewer distinct values than values. Either there are at most 8 distinct values, or at most a tenth of the values are distinct. No value is prose: more than 80 characters, more than 7 words, or a line break.
- **Numbers.** All values are whole numbers, there are at most 8 distinct values and fewer distinct values than values. The values are not a sequence: 9 or more distinct values that increase by one.
- **Value labels.** If the column has value labels, at most 50 distinct values suffice, except for a sequence.

A name is an identifier name if its lower-case form matches the pattern `id|row.?number|resp?no|.*_id`. A processor MAY let its caller say whether a column is an identifier, which replaces the decision from the name.

Numeric columns have a lower limit than text columns because a few distinct numbers are less often codes than a few distinct words. A processor MAY let its caller replace the two limits of 50 and 8.

## 8. Merging

Merging adds the information in a second profile, the *incoming* profile, to a first profile, the *base*. The result has all the information of the base, changed as follows.

1. Slots that the incoming profile has override the slots of the base. Empty text and empty lists count as absent.
2. Columns, values and mappings are matched by `name`, `code` and `object_id`. Matched entries are merged by the same rules, and the others are kept.
3. Entries of the incoming profile that are not in the base are added after the entries of the base.

## 9. Validation

### 9.1 Profiles

A profile has no errors if

- it conforms to the JSON Schema of the model,
- no two columns have the same `name`, and
- no two values of a column have the same `code`.

Errors are text. For errors against the model they start with the path of the value, for example `/columns/0/datatype`.

### 9.2 JSON-LD documents

A JSON-LD document has no errors if every key and every `@type` expands, through the `@context` of the document, to an IRI that is listed in [Vocabulary](vocabulary.md). Keys that start with `@`, the extension terms in `spec/jsonld.yaml` and the accepted types in the same file are excepted. If the `@context` is not an object, the context of this specification is used.

A document is checked for the terms it uses, not for the shape of its graph.

## 10. Frictionless

A processor MAY write a profile as a [Frictionless Table Schema][frictionless]. The projection is one-way. Slots that the Table Schema has no property for are kept in the extension property `x-linked-codebook`, so that nothing is lost. The rules are in [`spec/frictionless.yaml`](../spec/frictionless.yaml).

| Profile | Table Schema |
| --- | --- |
| `columns` | `fields`, in the same order |
| `name`, `label`, `description`, `datatype` | the field properties `name`, `title`, `description`, `type` |
| `missing_values`, and the codes of values with `missing` set | the field property `missingValues` |
| `values` | the field property `categories`: `{ "value": …, "label": … }`, or only the value if there is no label |
| `level`, `unit`, `unit_iri`, `variable`, `values`, `missing_range`, `completeness`, `mappings` | the field property `x-linked-codebook` |
| the slots of the dataset | the property `x-linked-codebook` of the schema |

Codes of `integer` and `number` fields are written as numbers if they are numbers, as defined in [section 7](#7-inference), and as text otherwise.

Notes:

- Frictionless tools read `categories` but do not enforce them, and they do not know the extension property. They keep it when they read and write the schema, as tested with frictionless-py 5.21.
- A Table Schema has no title, license or citation. These are kept in the extension property, because a Data Package needs the path of a data file that a profile does not have.

## 11. Command line

The command line is defined in [Command line](cli.md). A processor MUST provide the commands listed there, MUST print the same text as every other processor and MUST use the same exit codes.

## 12. References

- [DSV][dsv]: Dataset-Variable Ontology.
- [Table Schema][frictionless]: Frictionless Data specification.
- [CSVW][csvw]: Model for Tabular Data and Metadata on the Web.
- [SKOS][skos]: Simple Knowledge Organization System Reference.
- [SSSOM][sssom]: Simple Standard for Sharing Ontological Mappings.
- [JSON-LD 1.1][jsonld]: A JSON-based Serialization for Linked Data.
- [LinkML](https://linkml.io): Linked data Modeling Language.
- [RFC 2119][rfc2119] and [RFC 8174][rfc8174]: Key words for use in RFCs.
- [RFC 3987][rfc3987]: Internationalized Resource Identifiers.

[dsv]: https://w3id.org/dsv-ontology
[frictionless]: https://specs.frictionlessdata.io/table-schema/
[csvw]: https://www.w3.org/TR/tabular-data-model/
[skos]: https://www.w3.org/TR/skos-reference/
[sssom]: https://mapping-commons.github.io/sssom/
[jsonld]: https://www.w3.org/TR/json-ld11/
[rfc2119]: https://www.rfc-editor.org/rfc/rfc2119
[rfc8174]: https://www.rfc-editor.org/rfc/rfc8174
[rfc3987]: https://www.rfc-editor.org/rfc/rfc3987
