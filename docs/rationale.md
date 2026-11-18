# Rationale

Why the profile and the libraries look as they do, and what was left out.

How claims about other standards were checked: *Code* means the source was read. *Spec* means the specification text was fetched. *Memory* means it was not re-read; treat those rows as leads.

## Decisions

| Question | Decision |
| --- | --- |
| How is a variable linked to a concept? | A mapping is an SSSOM record: subject, predicate, object, justification, confidence, reviewer. It counts as approved when it has a `reviewer_id`; `approved` is not an SSSOM slot. Only approved mappings enter the JSON-LD, so a suggestion never becomes a claim. |
| Storage type or measurement level? | Two slots. `datatype` is a CSVW name; `level` is the DSV level of measurement (`nominal`, `ordinal`, `numerical`, …). A flag is `nominal`. |
| How does an ordinal order survive RDF? | RDF has no order, and the code concepts of a column are a set. The code concepts of ordinal columns carry `schema:position`, and readers order by it. Frictionless gets `categoriesOrdered`. |
| How are missing values described? | `missing_values` (codes), `missing` on a value, and `missing_range` for the numeric ranges that SPSS and DDI declare. No vocabulary defines the range, so it is written under `lc:missing_range`. |
| How are variable IRIs made? | One template, with percent-encoded names, so no two names collide. An IRI found in a file is kept. |
| Units | `unit` (text) and `unit_iri` are separate slots, because a unit is often only text. |
| Value labels | `closed` says that a list is complete. The codes counted in the data are kept apart, in `observed`, so a sample never becomes a domain. |
| Which JSON-LD keys? | One context is published and embedded in every document. Readers ignore prefixes and accept the aliases of older documents. |
| Roles (analysis, graph node, privacy)? | Not in the profile. They depend on the use of a codebook, not on the table. |
| Statistics? | `rows` and `completeness` exist for parity with DSV. They describe the data, so an importer should not take them from a file. |
| Where is skip logic kept? | `applies_when` keeps the source expression (REDCap branching logic). A condition parses into a tree and evaluates in three values (true, false, unknown), so that `missingness` can tell a skipped question from a missing answer. |
| Is a detector part of the library? | No; see below. |

## The language protocol

A language detector is a statistical model, and two models disagree on some texts. Two libraries that must print the same output for the same input cannot both embed a model, and one model per library would give two answers. Bundling one would also break the rule that both libraries have no dependencies, and Pyodide cannot run every Python detector.

So the specification defines the decision rule and not the detector (section 7.1): which values are asked (prose only, at most 200, evenly spaced), and when the answers are accepted (at least 0.8 of them agree). The detector is a function that the application supplies, `text → BCP 47 tag | nothing`. The conformance cases run the rule with a fake detector whose answer is written into the text, so both libraries reach the same decision from the same answers. [Language detectors](language.md) says which ones to use.

The price is that `infer` on the command line cannot detect language, and that the `language` in a profile depends on the detector that made it. A model version is not recorded in the profile.

## Why not visions

[visions](https://github.com/dylan-profiler/visions) is a Python library of semantic data types (a type system for data analysis) and could have supplied the inference of datatypes and levels. It was not adopted. The reasons are constraints of this project, not the result of a comparison: no benchmark of visions against `infer` was run.

- **Two libraries must agree.** The TypeScript and the Python library print the same text for the same input, and a conformance suite checks it. visions is Python only, and its types are defined by Python and pandas behaviour (what a `Series` can be coerced to), which cannot be written down as rules that a second implementation follows.
- **Dependencies.** The version on PyPI at the time of writing (0.8.2) requires numpy, pandas, networkx, attrs, multimethod and puremagic. The libraries have none, and have to run in Pyodide and in a browser without them.
- **Different question.** The profile needs a CSVW datatype and a DSV level for a column of JSON values, with limits that a person can read and change (`spec/inference.yaml`): at most 50 distinct values for a text column to count as categories, and so on. visions answers which of its type hierarchy a data frame column belongs to.

If a project already has pandas and wants visions' types, it can use them and pass the result to the profile as it is; the `infer` function is a proposal, not a requirement.

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

Two gaps stand out across all of them: none of them models ordinal order in RDF (the profile uses `schema:position`), and nobody except DDI models missing ranges.
