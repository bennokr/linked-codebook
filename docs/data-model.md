# Data model

<!-- Generated from spec/profile.yaml by scripts/generate.py. Do not edit. -->

## Profile

A dataset and its columns.

| Slot | Type | Required | Description |
| --- | --- | --- | --- |
| `title` | string | no | Name of the dataset. |
| `description` | string | no | Definition of the dataset, column or value. |
| `identifier` | string | no | Persistent identifier of the dataset. A DOI or URL is preferred. |
| `license` | string | no | IRI of the license, or a statement of the terms of use. |
| `citation` | string | no | Preferred citation. |
| `access_rights` | string | no | Who may access the dataset. |
| `landing_page` | string | no | IRI of a web page about the dataset. |
| `columns` | list of Column | yes | Columns, in table order. |

## Column

One column of the table, described as a variable.

| Slot | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Header of the column, exactly as in the table. |
| `label` | string | no | Human-readable name of the column or value. |
| `description` | string | no | Definition of the dataset, column or value. |
| `datatype` | Datatype | no | How values are stored. |
| `level` | Level | no | Level of measurement. |
| `unit` | string | no | Unit as text, for example years. |
| `unit_iri` | string | no | IRI of the unit, for example from QUDT. |
| `variable` | string | no | IRI of the variable concept the column measures. |
| `values` | list of Value | no | Codes of the column with their labels. |
| `missing_values` | list of string | no | Codes that mean no value and have no label. |
| `missing_range` | Range | no | Numbers that mean no value. |
| `mappings` | list of Mapping | no | Links to concepts. |

## Value

A code that occurs in a column, with its label.

| Slot | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | string | yes | The code as stored in the table, as text. |
| `label` | string | no | Human-readable name of the column or value. |
| `description` | string | no | Definition of the dataset, column or value. |
| `missing` | boolean | no | True if the code means no value. |
| `mappings` | list of Mapping | no | Links to concepts. |

## Mapping

A link from a column or value to a concept. It is approved when it has a reviewer_id.

| Slot | Type | Required | Description |
| --- | --- | --- | --- |
| `match_type` | MatchType | yes | How the concept relates to the column or value. |
| `object_id` | string | yes | IRI of the concept. |
| `object_label` | string | no | Name of the concept. |
| `confidence` | float | no | Confidence between 0 and 1. |
| `provenance` | string | no | Where the link came from, for example the name of a service. |
| `retrieved_at` | string | no | When the link was made, as an ISO 8601 date or time. |
| `reviewer_id` | string | no | Who approved the link. A link without a reviewer is a draft. |
| `description` | string | no | Definition of the dataset, column or value. |

## Range

An inclusive range of numbers.

| Slot | Type | Required | Description |
| --- | --- | --- | --- |
| `low` | float | yes | Smallest number. |
| `high` | float | yes | Largest number. |

## Datatype

Storage type, named as in CSV on the Web.

| Value | Meaning |
| --- | --- |
| `string` |  |
| `number` |  |
| `integer` |  |
| `boolean` |  |
| `date` |  |
| `datetime` |  |

## Level

Level of measurement, as defined by DSV.

| Value | Meaning |
| --- | --- |
| `categorical` | dsv:CategoricalDataType |
| `nominal` | dsv:NominalDataType |
| `ordinal` | dsv:OrdinalDataType |
| `numerical` | dsv:NumericalDataType |
| `interval` | dsv:IntervalDataType |
| `ratio` | dsv:RatioDataType |

## MatchType

Relation of a concept to a column or value, as defined by SKOS.

| Value | Meaning |
| --- | --- |
| `exact` | skos:exactMatch |
| `close` | skos:closeMatch |
| `broad` | skos:broadMatch |
| `narrow` | skos:narrowMatch |
| `related` | skos:relatedMatch |
