# Rationale

This page explains the main design decisions of the profile and the libraries, and compares the profile with other standards.

The notes on other standards say how each claim was checked: *Code* means the source was read, *Spec* means the text of the specification was fetched, and *Memory* means the claim was not re-checked and should be verified before use.

## Decisions

| Question | Decision |
| --- | --- |
| How is a variable linked to a concept? | A mapping is an SSSOM record with a subject, predicate, object, justification, confidence and reviewer. It is approved when it has a `reviewer_id`, because SSSOM has no `approved` slot. Only approved mappings are written to JSON-LD, so unreviewed suggestions do not appear there as statements. |
| What are datatype and level? | They are two slots. `datatype` is a CSVW name, and `level` is the DSV level of measurement (`nominal`, `ordinal`, `numerical` and so on). A flag has the level `nominal`. |
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

The specification therefore defines the decision rule and leaves out the detector (section 7.1). The rule says which values are passed to the detector (prose only, at most 200, evenly spaced) and when its answers are accepted (at least 0.8 of them agree). The detector is a function from a text to a BCP 47 tag that the application supplies. The conformance cases use a fake detector whose answer is written into the text, so both libraries reach the same decision from the same answers. [Language detectors](language.md) lists detectors that work.

As a result, the `infer` command cannot detect languages, and the `language` in a profile depends on the detector that produced it. The profile does not record the detector or its version.

## Why visions is not used

[visions](https://github.com/dylan-profiler/visions) is a Python library of semantic data types for data analysis. It could have supplied the inference of datatypes and levels. The reasons it is not used follow from the requirements of this project. No benchmark of visions against `infer` was run.

- **Both libraries must agree.** The TypeScript and Python libraries print the same text for the same input, and the conformance suite checks it. visions exists only for Python, and its types follow the behaviour of Python and pandas, for example what a `Series` can be converted to. A second implementation cannot reproduce those rules from a specification.
- **Dependencies.** Version 0.8.2 on PyPI requires numpy, pandas, networkx, attrs, multimethod and puremagic. The libraries have no dependencies and have to run in Pyodide and in a browser.
- **A different question.** The profile needs a CSVW datatype and a DSV level for a column of JSON values, with limits that a person can read and change (`spec/inference.yaml`), such as at most 50 distinct values for a text column to count as categories. visions assigns a column of a data frame to a type in its own hierarchy.

A project that already uses pandas can take the types from visions and write them into a profile, because `infer` only proposes values.

## Other standards

| Standard | What it models at variable level | Relation to the profile |
| --- | --- | --- |
| **DSV** (*Spec*) | `dsvo:Column` → `dsvo:ColumnProperty` → `dsvo:hasVariable` and `dsvo:hasCodeBook`; `dsvo:statisticalDataType`; completeness | The base of the JSON-LD. It has no terms for label, unit, missing codes or mappings, so CSVW, SKOS, QUDT and schema.org fill in. |
| **DISCO / DDI-RDF** (*Spec*) | `disco:Variable`, `disco:RepresentedVariable`, `disco:concept`, `disco:representation`, `disco:universe`, `disco:question`, `disco:isValid` | Value labels use the same SKOS shape. DISCO adds the question, the universe and the conceptual/represented split. |
| **DDI-Codebook 2.5** (*Memory*) | `<var>` with label, `<catgry>`, valid and invalid ranges, `@nature`, `@intrvl`, question, universe | The richest description of one variable. It has the missing ranges the others drop. |
| **DDI-CDI** (*Memory*) | Conceptual, represented and instance variables; sentinel value domains | The principled home for missing codes. Heavy for an editor. |
| **Croissant 1.0** (*Spec*) | `cr:Field`: name, description, `dataType`, `equivalentProperty`, `references`, `source` | Good for ML discovery. Nothing on unit, missing codes or level. |
| **Frictionless Table Schema** (*Memory*) | `name`, `title`, `type`, `format`, `missingValues`, `constraints`, `categories`, `rdfType` | The closest in size. The profile can be projected onto it (`to-frictionless`). |
| **CSVW** (*Memory*) | `name`, `titles`, `datatype`, `null`, `propertyUrl`, `valueUrl` | Used for names, titles, datatype and nulls. The profile writes `csvw:title`. `titles` is a key of CSVW metadata documents, not a term of its vocabulary; readers still accept it. |
| **schema.org** `variableMeasured` (*Memory*) | `PropertyValue`: name, description, `unitText`, `unitCode`, `propertyID` | Not written. Adding it is the cheapest route to dataset search engines. |
| **SDMX / Data Cube** (*Memory*) | Dimensions, measures, attributes, code lists | The statistical-agency counterpart of codebooks. |
| **SPSS system files** | Label, value labels, up to three missing codes or a range plus one, level, display format | The source of most real codebooks. |
| **SSSOM** (*Spec*) | `subject_id`, `predicate_id`, `object_id`, `mapping_justification`, `confidence`, `mapping_date`, `reviewer_id`, `mapping_provider`, `comment` | The exchange format for mappings. |

None of these standards models ordinal order in RDF (the profile uses `schema:position`), and only DDI models missing ranges.
