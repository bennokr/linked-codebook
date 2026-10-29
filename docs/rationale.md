# Rationale

Why the profile looks as it does. It was written after comparing how Statlet, LinkedBayes, Modlet, semsynth,
table-text-explorer and table-interface describe variables, and how DSV and related standards do.

How claims were checked: *Code* means the repository was read. *Spec* means the specification text was fetched.
*Memory* means it was not re-read; treat those rows as leads.

## Where the projects differed

| Difference found | Status in linked-codebook |
| --- | --- |
| Variable → concept had three models: one close match without review state (Statlet), mappings outside the metadata in SSSOM (Modlet), and a record with match type, confidence, provenance and approval (LinkedBayes). | Resolved. A mapping is the LinkedBayes record in SSSOM terms. It is approved when it has a `reviewer_id`; `approved` is not an SSSOM slot. Only approved mappings enter the JSON-LD. |
| Measurement level had four vocabularies, none equal to DSV, and mixed storage with level. | Resolved. `datatype` (a CSVW name) and `level` (DSV) are separate. Statlet's `scale` is `numerical`; `flag` is `nominal`. |
| Ordinal order is lost in RDF, because code concepts are a set. | Open. The JSON arrays keep the order. RDF readers do not see it. |
| Missing values were handled three ways, and ranges were dropped. | Partly. `missing_values`, `missing` on a value and `missing_range` exist. The range is written as `missingRange`, which no vocabulary defines. |
| Variable IRIs were minted differently and lossily (`%` replaced by `-`; names slugged). | Resolved. One template, percent-encoded names, and IRIs found in files are kept. |
| Units were free text, a guessed IRI, or a mandatory IRI. | Resolved. `unit` and `unit_iri` are separate slots. |
| Value labels were sometimes a closed list and sometimes partial. | Open. The profile has no closed/partial flag. |
| Compact JSON-LD differed in keys (`dct:`/`dcterms:`, `hasUnit`/`unit`, `columns`/`column`). | Partly. One context is published. Readers ignore prefixes and accept the aliases. |
| Statlet's context defined `csvw:titles`, which CSVW does not have. | Resolved. The vocabulary check found it; the profile uses `csvw:title` and still reads `titles`. |
| Four meanings of "role" (analysis, graph node, structure, privacy). | Not in the profile. Roles stay in the projects. |
| Statistics were mixed into curated metadata. | `rows` and `completeness` exist for DSV parity. They describe the data, so importers should not take them from files. |
| Dataset-level fields differed. | The profile has title, description, identifier, license, citation, access rights and landing page. |

## semsynth and entailmap

*Code*, checked against semsynth `790c03c` and entailmap `74690e1`.

- semsynth's "SemMap" is a different model with the same name. Its files declare the context
  `https://w3id.org/semmap/context`, which returns 404, and use terms that DSV does not define
  (`dsv:QuantitativeDataType`, `dsv:ContinuousDataType`, `dsv:IdentifierDataType`).
- It nests the statistical type under `columnProperty.summaryStatistics`, keeps mappings as bare IRIs without
  review state, and uses `hadRole` for a privacy role. Its `to_privacy_frame` has no case for
  `dsv:CategoricalDataType`, so a categorical column falls through to the numeric default.
- entailmap has no such model. It covers two halves of the profile on its own: a complete SSSOM table, with a rule
  that a review date needs a reviewer, and a CSVW table-schema editor.

## Other standards

| Standard | What it models at variable level | Relation to the profile |
| --- | --- | --- |
| **DSV** (*Spec*) | `dsv:Column` → `dsv:ColumnProperty` → `dsv:hasVariable` and `dsv:hasCodeBook`; `dsv:statisticalDataType`; completeness | The base of the JSON-LD. It has no terms for label, unit, missing codes or mappings, so CSVW, SKOS, QUDT and schema.org fill in. |
| **DISCO / DDI-RDF** (*Spec*) | `disco:Variable`, `disco:RepresentedVariable`, `disco:concept`, `disco:representation`, `disco:universe`, `disco:question`, `disco:isValid` | Value labels use the same SKOS shape. DISCO adds the question, the universe and the conceptual/represented split. |
| **DDI-Codebook 2.5** (*Memory*) | `<var>` with label, `<catgry>`, valid and invalid ranges, `@nature`, `@intrvl`, question, universe | The richest description of one variable. It has the missing ranges the others drop. |
| **DDI-CDI** (*Memory*) | Conceptual, represented and instance variables; sentinel value domains | The principled home for missing codes. Heavy for an editor. |
| **Croissant 1.0** (*Spec*) | `cr:Field`: name, description, `dataType`, `equivalentProperty`, `references`, `source` | Good for ML discovery. Nothing on unit, missing codes or level. |
| **Frictionless Table Schema** (*Memory*) | `name`, `title`, `type`, `format`, `missingValues`, `constraints`, `categories`, `rdfType` | The closest in size. The profile can be projected onto it (`to-frictionless`). |
| **CSVW** (*Memory*) | `name`, `titles`, `datatype`, `null`, `propertyUrl`, `valueUrl` | Used for names, titles, datatype and nulls. |
| **schema.org** `variableMeasured` (*Memory*) | `PropertyValue`: name, description, `unitText`, `unitCode`, `propertyID` | Not written. Adding it is the cheapest route to dataset search engines. |
| **SDMX / Data Cube** (*Memory*) | Dimensions, measures, attributes, code lists | The statistical-agency counterpart of codebooks. |
| **SPSS system files** | Label, value labels, up to three missing codes or a range plus one, level, display format | The source of most real codebooks. |
| **SSSOM** (*Spec*) | `subject_id`, `predicate_id`, `object_id`, `mapping_justification`, `confidence`, `mapping_date`, `reviewer_id`, `mapping_provider`, `comment` | The exchange format for mappings. |

Two gaps stand out across all of them: nobody models ordinal order in RDF, and nobody except DDI models missing ranges.
