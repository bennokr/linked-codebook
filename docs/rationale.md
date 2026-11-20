# Rationale

This page explains the main design decisions of the profile and the libraries, and compares the profile with other standards.

## Decisions

| Question | Decision |
| --- | --- |
| How is a variable linked to a concept? | A mapping is an [SSSOM](https://mapping-commons.github.io/sssom/) record with a subject, predicate, object, justification, confidence and reviewer. It is approved when it has a `reviewer_id`, because SSSOM has no `approved` slot. Only approved mappings are written to JSON-LD, so unreviewed suggestions do not appear there as statements. |
| What are datatype and measurement level? | They are two slots. `datatype` is a [CSVW](https://www.w3.org/TR/tabular-metadata/) name, and `level` is the [DSV](https://w3id.org/dsv-ontology) measurement level (`categorical`, `nominal`, `ordinal`, `numerical`, `interval` or `ratio`). Inference and REDCap give a boolean or yes/no column the coarse level `categorical`; `nominal` and `ordinal` come from a source that says more, such as the measure of a statistical file, or from a person. |
| How is the order of an ordinal column kept in RDF? | The code concepts of a column form a set, and RDF has no order. The code concepts of ordinal columns therefore carry `schema:position`, and readers order them by it. Frictionless gets `categoriesOrdered`. |
| How are missing values described? | `missing_values` lists codes, `missing` on a value marks a labelled code, and `missing_range` holds the numeric ranges that SPSS and DDI declare. No vocabulary defines a range, so it is written as `lc:missing_range`. |
| How are variable IRIs made? | One template builds them from percent-encoded names, so different names give different IRIs. An IRI found in a file is kept. |
| How is a unit stored? | `unit` holds the text and `unit_iri` holds an IRI, because many sources have only the text. |
| How are value labels stored? | `closed` says that a list is complete. The codes counted in the data are stored separately in `observed`, so a sample is never taken for the domain of a column. |
| Which JSON-LD keys are used? | One context is published and embedded in every document. Readers ignore prefixes and accept the aliases of older documents. |
| Where are roles (analysis, graph node, privacy)? | Outside the profile, because they depend on how a codebook is used. |
| Where are statistics stored? | `rows` and `completeness` exist for parity with DSV. They describe the data, so an importer should not take them from a file. |
| Where is skip logic stored? | `applies_when` keeps the source expression, for example REDCap branching logic. A condition is parsed into a tree and evaluated with three values (true, false and unknown), so that `missingness` can distinguish a skipped question from a missing answer. |
| How is the language of a text column found? | By a detector that the application supplies. See the next section. |

## The language protocol

A language detector is a statistical model, and different models disagree on some texts. Two libraries that must print the same output for the same input cannot each embed a model. A bundled model would also give up the rule that both libraries have no dependencies, and not every Python detector runs in Pyodide.

The specification therefore defines the decision rule and leaves out the detector ([section 7.1](specification.md#71-language-of-a-text-column)). The rule says which values are passed to the detector (prose only, at most 200, evenly spaced) and when its answers are accepted (at least 0.8 of them agree). The detector is a function from a text to a BCP 47 tag that the application supplies. The conformance cases use a fake detector whose answer is written into the text, so both libraries reach the same decision from the same answers. [Language detectors](language.md) lists detectors that work.

As a result, the `infer` command cannot detect languages, and the `language` in a profile depends on the detector that produced it. The profile does not record the detector or its version.

## Other standards

| Standard | What it models at variable level | Relation to the profile |
| --- | --- | --- |
| **[DSV](https://w3id.org/dsv-ontology)** | `dsvo:Column` → `dsvo:ColumnProperty` → `dsvo:hasVariable` and `dsvo:hasCodeBook`; `dsvo:statisticalDataType` (nominal, ordinal, interval, ratio); completeness | The base of the JSON-LD. It has no terms for label, unit, a list of missing codes or mappings (its only missing-value term, `dsvo:missingValueFormat`, is a format string), so CSVW, SKOS, QUDT and schema.org fill in. |
| **[DISCO / DDI-RDF](https://rdf-vocabulary.ddialliance.org/discovery.html)** | `disco:Variable` (a `skos:Concept`), `disco:RepresentedVariable`, `disco:basedOn`, `disco:concept`, `disco:representation`, `disco:universe`, `disco:question`; `disco:isValid` marks a code as valid or missing | Value labels use the same SKOS shape. DISCO adds the question and the universe, and links a variable to a reusable represented variable. It does not model conceptual variables. |
| **[DDI-Codebook 2.5](https://ddialliance.org/ddi-codebook_v2.5)** | `<var>` with `labl`, `catgry`, `valrng`, `invalrng`, `qstn` and `universe`, and the attributes `@nature` (nominal, ordinal, interval, ratio, percent, other) and `@intrvl` (discrete, contin) | The richest description of one variable. `invalrng` holds missing values as `item` and `range` elements. |
| **[DDI-CDI](https://ddialliance.org/Specification/DDI-CDI/)** | `ConceptualVariable`, `RepresentedVariable` and `InstanceVariable`; `SentinelValueDomain` and `SubstantiveValueDomain` | The principled home for missing codes: sentinel values are kept apart from the values that describe the subject matter. Heavy for an editor. |
| **[Croissant 1.0](https://docs.mlcommons.org/croissant/docs/croissant-spec.html)** | `cr:Field`: name, description, `dataType`, `equivalentProperty`, `references`, `source` | Good for ML discovery. Nothing on unit, missing codes or measurement level. |
| **[Frictionless Table Schema](https://datapackage.org/standard/table-schema/)** (version 2) | `name`, `title`, `description`, `type`, `format`, `rdfType`, `constraints`, `missingValues` (also on a field), `categories` and `categoriesOrdered` (string and integer fields) | The closest in size. The profile can be projected onto it (`to-frictionless`). Version 1 has no `categories` and allows `missingValues` only on the schema. |
| **[CSVW](https://www.w3.org/TR/tabular-metadata/)** | `name`, `titles`, `datatype`, `null`, `propertyUrl`, `valueUrl` | Used for names, titles, datatype and nulls. The profile writes `csvw:title`. `titles` is a key of CSVW metadata documents, not a term of its vocabulary; readers still accept it. |
| **[schema.org](https://schema.org/variableMeasured) `variableMeasured`** | `PropertyValue`: name, description, `unitText`, `unitCode`, `propertyID`; `StatisticalVariable` is also accepted | Not written. Adding it is the cheapest route to dataset search engines. |
| **[SDMX](https://sdmx.org/standards/) and [RDF Data Cube](https://www.w3.org/TR/vocab-data-cube/)** | Dimensions, measures, attributes and code lists (`qb:DimensionProperty`, `qb:MeasureProperty`, `qb:AttributeProperty`, `qb:codeList`) | The statistical-agency counterpart of codebooks. |
| **[SPSS variables](https://pspp.benpfaff.org/manual/language/datasets/variables.html)** (system files) | Label, value labels, up to three discrete missing values or, for numeric variables, a range with one more discrete value; measurement level (nominal, ordinal, scale); print and write formats | The source of most real codebooks. |
| **[SSSOM](https://mapping-commons.github.io/sssom/)** | `subject_id`, `predicate_id`, `object_id`, `mapping_justification`, `confidence`, `mapping_date`, `reviewer_id`, `mapping_provider`, `comment` | The exchange format for mappings. |

None of these standards models ordinal order in RDF (the profile uses `schema:position`). Only the DDI standards and SPSS files model ranges of missing values.
