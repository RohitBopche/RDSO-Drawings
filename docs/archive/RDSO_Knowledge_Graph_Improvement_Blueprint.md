# RDSO Drawings — Complete Knowledge Graph Upgrade Blueprint

**Status:** Implementation handoff specification  
**Audience:** Future engineering agents, maintainers, reviewers, and product owners  
**Primary objective:** Turn the existing RDSO Drawings application into an offline-first, evidence-backed, revision-aware engineering knowledge system without destabilising the current working application.

---

## 0. Executive direction

The project should evolve from a graph/PDF viewer into a **reliable engineering knowledge system**.

The central product loop is:

```text
User task
   ↓
Search / Question
   ↓
Relevant engineering entity
   ↓
Structured facts
   ↓
Evidence / source page
   ↓
Related knowledge
   ↓
Graph / workflow / revision analysis
   ↓
Actionable engineering understanding
```

The Knowledge Graph is **not the product by itself**. It is the shared knowledge layer that powers search, drawing intelligence, evidence, revision comparison, engineering workflows, learning, analytics, and eventually an AI copilot.

### Core principles

1. **Evidence before explanation.**
2. **Canonical data before visualization.**
3. **Source facts before AI inference.**
4. **Revision awareness everywhere.**
5. **Make uncertainty visible.**
6. **Engineering workflows over decorative complexity.**
7. **Offline-first by default.**
8. **Small validated increments over large rewrites.**
9. **Human review for uncertain or safety-relevant facts.**
10. **One knowledge core, many interfaces.**

---

# 1. Current-state baseline

The current application already contains substantial value and must be treated as the baseline rather than discarded.

## 1.1 Existing architecture

Current important areas include:

```text
index.html
    ├── search UI
    ├── Three.js graph
    ├── entity/intelligence drawer
    ├── semantic graph modes
    ├── drawing/component views
    └── existing engineering interactions

scripts/
    ├── ingestion/extraction
    ├── canonical KG generation
    ├── source registry generation
    ├── exports
    └── validation utilities

data/knowledge-graph/
    ├── raw/
    ├── intermediate/
    ├── canonical/
    ├── exports/
    └── schemas/

tests/
    ├── browser/E2E checks
    └── KG/data validation tests

docs/
    ├── architecture
    ├── ontology
    └── UX specifications
```

The root `index.html` remains the compatibility entry point. Do not replace it merely for architectural cleanliness.

## 1.2 Current strengths to preserve

- Offline operation.
- Existing drawing/document datasets.
- Existing Three.js graph and semantic modes.
- Existing intelligence drawer and component views.
- Existing PDF/source assets.
- Existing extraction scripts.
- Existing canonical/intermediate/raw data separation.
- JSON-LD/Cypher interoperability direction.
- Existing browser regression tests.

## 1.3 Known architectural weaknesses

- The main application is monolithic and difficult to change safely.
- Search, graph navigation, and intelligence presentation are tightly coupled.
- Some datasets contain historical/legacy identity representations.
- Important engineering facts are not uniformly modeled as first-class evidence-backed records.
- Relationship semantics are not yet consistently enforced across all datasets.
- Evidence integrity is not yet a complete publication gate.
- The browser test suite is stronger than lower-level data/model tests.
- There is no need yet for a database/backend migration; current offline datasets should be improved first.

---

# 2. Target product architecture

The target architecture is:

```text
                    SOURCE LAYER
        PDFs / drawings / manuals / images / field data
                          │
                          ▼
                    INGESTION LAYER
       PDF parsing / OCR / tables / title blocks / regions
                          │
                          ▼
                  EVIDENCE LAYER
    pages / clauses / regions / quotes / crops / provenance
                          │
                          ▼
                 CANONICAL KNOWLEDGE
 entities / facts / measurements / requirements / revisions / edges
                          │
              ┌───────────┼────────────┐
              ▼           ▼            ▼
           SEARCH       GRAPH       QUERY ENGINE
              │           │            │
              └───────────┼────────────┘
                          ▼
                   APPLICATION LAYER
     drawing detail / evidence / revisions / workflows / learning
                          │
                          ▼
              OPTIONAL INTELLIGENCE LAYER
       semantic retrieval / AI copilot / recommendations
```

### Architectural rule

No UI feature should become the authoritative owner of engineering knowledge. UI components consume the canonical knowledge layer.

---

# 3. Canonical knowledge model

## 3.1 Entity identity

Every canonical entity must have:

- stable ID;
- entity type;
- human-readable name;
- aliases where useful;
- status;
- provenance/evidence references where applicable;
- optional domain properties;
- optional verification state.

IDs must be stable and machine-safe. Display names must never be used as database identity.

## 3.2 Recommended entity families

### Documents and sources

- `DOCUMENT_FAMILY`
- `DOCUMENT`
- `EDITION`
- `SOURCE_FILE`
- `PAGE`
- `SECTION`
- `CLAUSE`
- `TABLE`
- `FIGURE`
- `EVIDENCE`

### Drawings and engineering objects

- `DRAWING`
- `DRAWING_REVISION`
- `ASSEMBLY`
- `SUBASSEMBLY`
- `COMPONENT`
- `SUBCOMPONENT`
- `RAIL`
- `TONGUE_RAIL`
- `STOCK_RAIL`
- `SLEEPER`
- `FASTENER`
- `TIE_BAR`
- `SLIDE_CHAIR`
- `POINT_MACHINE`
- `LOCKING_DEVICE`
- `MATERIAL`
- `GEOMETRY`

### Engineering constraints and requirements

- `REQUIREMENT`
- `SPECIFICATION`
- `STANDARD`
- `CODE`
- `TOLERANCE`
- `MEASUREMENT`
- `CONSTRAINT`
- `ACCEPTANCE_CRITERION`
- `INSPECTION_CRITERION`

### Operations and safety

- `PROCEDURE`
- `SOP`
- `INSPECTION`
- `MAINTENANCE_ACTION`
- `FAILURE_MODE`
- `DEFECT`
- `HAZARD`
- `CAUSE`
- `EFFECT`
- `MITIGATION`
- `EQUIPMENT`
- `TOOL`

### Supply chain and organizational context

- `BOM_ITEM`
- `SPARE_PART`
- `ORGANIZATION`
- `DIRECTORATE`
- `LOCATION`

Entity types should be controlled by schema/configuration rather than scattered string literals throughout the UI.

---

# 4. Relationship model

Relationships must be directional, typed, validated, and meaningful.

## 4.1 Core relationship vocabulary

```text
HAS_EDITION
HAS_REVISION
HAS_PAGE
HAS_SECTION
HAS_CLAUSE
HAS_TABLE
HAS_FIGURE
HAS_EVIDENCE
SUPPORTS
CITES
REFERENCES
APPLIES_TO
CONTAINS
PART_OF
ASSEMBLES
ASSEMBLED_FROM
MATES_WITH
INTERFACES_WITH
CONNECTED_TO
INSTALLED_ON
FASTENED_BY
SPECIFIED_BY
SPECIFIES
REQUIRES
CONSTRAINED_BY
MEASURED_BY
INSPECTED_BY
TESTED_BY
ACCEPTED_BY
GOVERNS
INTRODUCED_IN
REMOVED_IN
MODIFIED_IN
SUPERSEDES
AMENDS
CORRECTS
CAUSES
CAN_CAUSE
RESULTS_IN
MITIGATED_BY
USED_IN
PROCURED_AS
REPLACED_BY
HAS_BOM_ITEM
HAS_SPARE
CONTAINS_SLEEPER
DERIVED_FROM
CONFLICTS_WITH
VALID_DURING
```

Do not create new relationship names ad hoc in frontend code.

If a new relationship is needed:

1. define it in the controlled vocabulary;
2. document its direction and meaning;
3. update schema/validator tests;
4. update graph rendering configuration;
5. add at least one representative fixture.

---

# 5. Engineering fact model

Relationships alone are insufficient for engineering knowledge. Numeric and source-specific facts must be first-class records.

Example:

```json
{
  "fact_id": "fact:drg_6275:flangeway",
  "subject_id": "drg_6275",
  "predicate": "HAS_MEASUREMENT",
  "value": {
    "value": 44,
    "unit": "mm"
  },
  "bounds": {
    "min": 41,
    "max": 45,
    "unit": "mm"
  },
  "measurement_type": "FLANGEWAY",
  "applies_to": "drg_6275",
  "evidence_ids": ["ev:irpwm:page:123:flangeway"],
  "confidence": 0.98,
  "verification_status": "VERIFIED"
}
```

## 5.1 Rules

- Never encode important numeric semantics only in free text.
- Store value and unit separately.
- Store nominal/min/max explicitly where applicable.
- Preserve original extracted representation when useful, but normalize the machine-readable value.
- Preserve source evidence.
- Distinguish measured, specified, derived, inferred, and observed values.
- Never present inferred data as an official requirement.

---

# 6. Evidence and provenance architecture

Every safety-relevant or decision-relevant engineering claim should be traceable to evidence.

## 6.1 Evidence object

Recommended structure:

```json
{
  "evidence_id": "ev:document:page:region",
  "document_id": "DOC:IRPWM:2024:ACS14",
  "source_file_id": "src:irpwm:2024:pdf",
  "page_id": "page:irpwm:2024:429",
  "section": "Track Geometry",
  "clause": "429",
  "quote": "...",
  "region": [100, 200, 800, 300],
  "extraction_method": "pdf_text",
  "confidence": 0.96,
  "verification_status": "VERIFIED",
  "verified_by": "human-review",
  "verification_note": "Checked against source page"
}
```

## 6.2 Evidence statuses

Use controlled states:

- `EXTRACTED`
- `VERIFIED`
- `DERIVED`
- `INFERRED`
- `CONFLICTING`
- `REJECTED`
- `UNKNOWN`

## 6.3 Evidence UI

Important facts should expose:

- source document;
- drawing/revision;
- page;
- section/clause;
- evidence quote/value;
- source crop/region where available;
- verification status;
- confidence;
- open-source action.

The user should be able to move from:

```text
Fact → Evidence → Page/Crop → Source document
```

without manually searching the PDF.

---

# 7. Document and drawing identity strategy

Separate these concepts:

```text
Logical document identity
        │
        ├── editions/revisions
        │
        └── physical source files
```

A document identity answers **what document is this?**

A source-file identity answers **which physical PDF/file produced this evidence?**

Do not use filenames as canonical document identity.

Do not perform a large ID migration unless actual data cleanup requires it. Existing alias mappings and audit tooling should remain available as safety mechanisms.

---

# 8. Ingestion and extraction pipeline

The ingestion pipeline should be deterministic and reviewable.

```text
PDF/image/manual
    ↓
Source registration + SHA/hash
    ↓
Page extraction
    ↓
Text extraction
    ↓
OCR fallback where required
    ↓
Title block / revision table extraction
    ↓
Notes / clauses / tables / dimensions
    ↓
Region/crop references
    ↓
Candidate entities/facts/relationships
    ↓
Normalization
    ↓
Human review queue for uncertain facts
    ↓
Canonical publication
    ↓
Validation
    ↓
Search/graph exports
```

## 8.1 Extraction rules

- Preserve raw source output.
- Never overwrite raw extraction with normalized data.
- Record extraction method.
- Record extraction timestamp.
- Record confidence.
- Keep page/region references.
- Use OCR as fallback rather than blindly replacing reliable PDF text extraction.
- Extract revision tables explicitly.
- Extract title blocks explicitly.
- Extract engineering notes separately from body text.
- Extract tables/BOMs structurally.
- Keep uncertain candidates in a review queue.

## 8.2 Drawing-specific extraction

For each drawing family, capture when available:

- drawing number;
- title;
- revision/alteration;
- effective date;
- scale;
- sheet number;
- component names;
- materials;
- dimensions;
- tolerances;
- notes;
- BOM items;
- fastening schedules;
- cross-referenced drawings;
- applicable standards;
- revision block changes;
- source regions/crops.

---

# 9. Data-quality gates

Canonical data should not be published if it fails critical validation.

## Gate A — Structural

- valid JSON/JSONL;
- schema validation;
- required fields present;
- controlled types valid.

## Gate B — Identity

- unique canonical IDs;
- no accidental duplicate logical identities;
- aliases explicit;
- source-file IDs distinct from document IDs.

## Gate C — Graph integrity

- no dangling `from`/`to` references;
- relationship vocabulary valid;
- no duplicate logical edges;
- relationship direction valid;
- revision chains do not contain impossible cycles.

## Gate D — Evidence integrity

- every evidence reference resolves;
- evidence references valid document/source/page identifiers;
- required provenance fields exist;
- verification status valid;
- source files exist or are explicitly marked unavailable.

## Gate E — Engineering semantics

- units normalized;
- bounds coherent;
- nominal values consistent;
- requirement references resolve;
- applicability is explicit;
- conflicts are represented rather than silently discarded.

## Gate F — Publication

Only validated canonical data may feed the production search index/export.

---

# 10. Search architecture

Search should become the primary entry point for engineering tasks.

## 10.1 Searchable concepts

Support:

- drawing number;
- drawing title;
- component/part;
- material;
- standard/specification;
- document/manual;
- clause;
- requirement;
- revision/alteration;
- defect/failure mode;
- procedure/SOP;
- measurement/tolerance;
- engineering keyword.

## 10.2 Ranking

Use layered ranking:

```text
Exact identifier
    > exact name
    > normalized token match
    > prefix match
    > alias match
    > metadata match
    > text relevance
    > semantic similarity
```

Do not introduce semantic embeddings until lexical search and metadata filtering are reliable.

## 10.3 Search result cards

Every result should show:

- entity type;
- display name;
- canonical ID where useful;
- revision/edition;
- short engineering description;
- evidence/source indicator;
- optional status/confidence indicator.

For drawings, show drawing number + title together.

## 10.4 Search workflow

```text
Search query
   ↓
Ranked result list
   ↓
Select entity
   ↓
Focused entity detail
   ↓
Evidence / source
   ↓
Related knowledge
   ↓
Graph
```

The query and context must survive navigation.

---

# 11. Drawing Intelligence page/panel

A drawing entity should have a predictable information architecture.

## Required sections

1. **Identity**
   - drawing number;
   - title;
   - family/category.

2. **Applicability**
   - current/applicable revision;
   - validity/effective period;
   - supersession status.

3. **Revision history**
   - chronological timeline;
   - revision change summary;
   - source evidence.

4. **Engineering content**
   - components;
   - assemblies;
   - dimensions;
   - tolerances;
   - materials;
   - notes.

5. **Standards and requirements**
   - governing standards;
   - explicit requirements;
   - acceptance criteria.

6. **Procedures and inspection**
   - procedures;
   - inspection criteria;
   - maintenance actions.

7. **Related knowledge**
   - related drawings;
   - components;
   - documents;
   - failure modes.

8. **Evidence**
   - source document;
   - page/region;
   - verified facts.

9. **Graph**
   - focused graph entry point.

---

# 12. Revision intelligence

Revision information should be treated as engineering data, not merely a label.

## 12.1 Revision model

```text
DRAWING
  └── HAS_REVISION → R1
  └── HAS_REVISION → R2
  └── HAS_REVISION → R3

R3 ──SUPERSEDES──> R2
R2 ──SUPERSEDES──> R1
```

## 12.2 Revision comparison

A revision comparison should combine:

1. visual diff;
2. text/notes diff;
3. structured fact diff;
4. BOM diff;
5. relationship/graph diff;
6. applicability diff;
7. impact summary;
8. source evidence.

Example categories:

```text
ADDED
REMOVED
MODIFIED
UNCHANGED
CONFLICTING
UNKNOWN
```

## 12.3 Revision impact analysis

Given a changed component/requirement, identify:

```text
Revision change
    ↓
Affected component
    ↓
Assemblies / drawings
    ↓
Standards / requirements
    ↓
Inspection procedures
    ↓
Failure modes / mitigations
    ↓
Procurement/BOM implications
```

---

# 13. Graph intelligence

The graph should answer questions, not merely display connections.

## 13.1 Semantic modes

Maintain the existing graph engine but add purpose-driven modes:

- **Explore** — general neighborhood.
- **Revision Impact** — what changed and what it affects.
- **Dependency Trace** — component → drawing → requirement → inspection.
- **Failure Analysis** — failure → cause → component → inspection → mitigation.
- **Procurement/BOM** — drawing → BOM → spares.
- **Field Inspection** — component → criterion → measurement → acceptance.
- **Learning** — concept and prerequisite relationships.

## 13.2 Graph interactions

Required interactions:

- focus entity;
- expand one hop;
- expand selected relationship types;
- filter entity types;
- filter relationship types;
- path between two entities;
- explain why two entities are connected;
- open evidence from a relationship/fact;
- hide irrelevant neighborhoods;
- return to prior context;
- preserve search/revision state.

## 13.3 “Why connected?”

For any selected edge, explain:

```text
Component A
    ↓ INTERFACES_WITH
Component B
    ↓
Evidence: Drawing T-6155, Alt 13, page/region
```

If the edge is derived rather than directly stated, show that distinction.

---

# 14. Engineering relationship intelligence

Build reusable path templates.

## 14.1 Component path

```text
Component
  → USED_IN / PART_OF
Drawing / Assembly
  → SPECIFIED_BY
Standard / Specification
  → REQUIRES / GOVERNS
Requirement
  → INSPECTED_BY
Inspection procedure
```

## 14.2 Failure path

```text
Failure Mode
  → CAN_CAUSE / RESULTS_IN
Effect
  → CAUSED_BY / CAUSES
Cause
  → AFFECTS
Component
  → INSPECTED_BY
Inspection
  → ACCEPTED_BY
Acceptance criterion
  → MITIGATED_BY
Maintenance action
```

## 14.3 Procedure path

```text
Procedure
  → USES
Equipment/tool
  → MEASURES
Measurement
  → VALIDATES
Acceptance criterion
  → SUPPORTED_BY
Evidence
```

## 14.4 Procurement path

```text
Drawing
  → HAS_BOM_ITEM
BOM item
  → PROCURED_AS
Part/spare
  → HAS_SPARE / REPLACED_BY
Spare strategy
```

These paths should be queryable without requiring the user to understand graph implementation details.

---

# 15. Evidence-backed Engineering Answer Cards

A reusable answer-card model should become the primary presentation unit for important engineering facts.

## Card structure

```text
┌─────────────────────────────────────────────┐
│ Engineering fact                            │
│                                             │
│ Summary                                     │
│ Applicability / revision                    │
│ Critical parameter(s)                       │
│ Related component(s)                        │
│ Risk / action                               │
│                                             │
│ Evidence                                    │
│ Document · page · clause · crop             │
│ Verification · confidence                   │
│                                             │
│ [Open Source] [Open Graph] [Compare]        │
└─────────────────────────────────────────────┘
```

Answer Cards should work for:

- dimensions;
- tolerances;
- drawing identity;
- revision applicability;
- standards;
- inspection criteria;
- failure mitigations;
- BOM/spares;
- procedures.

---

# 16. Question / Answer interface

Only introduce a natural-language answer layer after evidence retrieval is reliable.

## Question pipeline

```text
Question
  ↓
Intent/entity extraction
  ↓
Canonical search
  ↓
Metadata filtering
  ↓
Graph traversal
  ↓
Evidence retrieval
  ↓
Conflict detection
  ↓
Answer synthesis
  ↓
Citations + uncertainty
```

## Required behaviour

Answers must distinguish:

- directly stated source facts;
- structured graph relationships;
- derived calculations;
- inferred conclusions;
- unresolved conflicts.

Never fabricate engineering requirements.

If sources conflict, expose the conflict and revision context instead of silently selecting one value.

---

# 17. Learning system

The Knowledge Graph can become a training system without creating a separate knowledge base.

## Learning objects

- drawing lesson;
- component lesson;
- concept;
- standard/requirement explanation;
- worked engineering example;
- failure case;
- inspection exercise;
- quiz;
- flashcard;
- revision comparison exercise.

## Learning graph

```text
Concept
  ↓ prerequisite
Concept
  ↓ illustrated_by
Drawing
  ↓ contains
Component
  ↓ constrained_by
Requirement
  ↓ inspected_by
Procedure
```

## Learning progression

1. Identify.
2. Understand.
3. Trace.
4. Compare.
5. Apply.
6. Diagnose.
7. Verify.

Add spaced repetition only after the basic content model is stable.

---

# 18. Field engineering mode

The application should support constrained field usage.

## Field mode priorities

- fast search;
- large readable text;
- drawing identity;
- applicable revision;
- critical dimensions/tolerances;
- inspection checklist;
- evidence source;
- component identification;
- offline source access;
- minimal graph complexity.

A field user should not need to operate the 3D graph to answer a routine engineering question.

---

# 19. Procurement and BOM intelligence

Use structured BOM data rather than static UI calculations.

Capabilities:

- BOM by drawing/revision;
- BOM comparison between revisions;
- spare-part mapping;
- quantity calculation;
- procurement buffer rules;
- changed-item highlighting;
- source evidence;
- exportable purchase list.

Every calculated quantity should show:

```text
input quantity
× rule/buffer
= calculated requirement
```

The rule and source should be inspectable.

---

# 20. Digital twin direction

The existing 3D capabilities should become synchronized with the knowledge core.

```text
Graph entity
   ↕
Physical component
   ↕
3D geometry
   ↕
Drawing region
   ↕
Measurement
   ↕
Requirement
   ↕
Inspection/failure
```

## Required future capabilities

- technical orthographic view;
- exploded assembly;
- component isolation;
- source drawing overlay;
- revision overlays;
- measurement callouts;
- component-to-source navigation;
- graph-to-geometry selection;
- geometry-to-evidence navigation.

Do not rebuild the 3D engine before the knowledge mappings are reliable.

---

# 21. UI/UX architecture

## 21.1 Primary information architecture

```text
Home
├── Search
├── Drawings
├── Components
├── Standards / Requirements
├── Revisions
├── Failures / Inspections
├── Procurement
├── Learning
└── Graph Explorer
```

## 21.2 Task-oriented home

Prioritize tasks such as:

- Explore Drawing
- Find Current Revision
- Compare Revisions
- Trace Component
- Investigate Failure
- Inspect Component
- Calculate Spares
- Open Source Evidence
- Learn Component

## 21.3 Graph presentation

Keep the immersive/cosmic visualization as an optional exploration mode.

Add a technical mode emphasizing:

- readable labels;
- engineering values;
- relationship names;
- evidence;
- revision context;
- clear selection state.

## 21.4 Context preservation

Preserve:

- search query;
- selected entity;
- active semantic mode;
- graph filters;
- revision context;
- breadcrumb state.

Example:

```text
Search: T-6155
  / Drawing T-6155
  / Revision Alt 13
  / Requirement
```

---

# 22. Frontend modularization strategy

Do not perform a risky one-shot rewrite of `index.html`.

Gradually introduce modules:

```text
src/
├── app/
│   ├── state
│   ├── routing
│   └── bootstrap
├── knowledge/
│   ├── entities
│   ├── facts
│   ├── relationships
│   └── queries
├── search/
├── evidence/
├── revisions/
├── graph/
├── workflows/
├── learning/
├── twin/
└── ui/
```

Migration pattern:

```text
Existing index.html
      ↓
Extract one coherent responsibility
      ↓
Add tests
      ↓
Wire module back into existing app
      ↓
Validate offline behaviour
      ↓
Repeat
```

The application must remain usable throughout the migration.

---

# 23. Backend/database direction

Do **not** introduce a backend merely because the project is called a Knowledge Graph.

## Current phase

Use validated local JSON/JSONL datasets and generated indexes.

## Introduce SQLite when

- queries become difficult to maintain in JSON;
- local joins become frequent;
- filtering becomes slow;
- transactional local updates become necessary.

## Introduce PostgreSQL when

- multi-user synchronization is required;
- authoritative server-side workflows emerge;
- permissions/auditing require a service boundary;
- dataset size and concurrent querying justify it.

## Introduce Neo4j when

- graph traversal/algorithms become a demonstrated bottleneck;
- multi-hop query requirements exceed practical relational/local approaches;
- graph analytics deliver measurable product value.

Database technology must follow workload evidence, not precede it.

---

# 24. Hybrid and semantic search

Implement in layers.

### Level 1 — lexical

- exact;
- prefix;
- token;
- alias;
- normalized identifier.

### Level 2 — metadata

- entity type;
- drawing family;
- revision;
- document;
- standard;
- status;
- applicability.

### Level 3 — graph retrieval

- neighbors;
- paths;
- dependencies;
- revision lineage.

### Level 4 — semantic retrieval

- embeddings;
- concept similarity;
- natural-language retrieval.

### Level 5 — hybrid ranking

Combine lexical, metadata, semantic, and graph signals.

Every result should still retain evidence/source metadata.

---

# 25. Performance strategy

Optimize based on measured bottlenecks.

## Frontend

- lazy-load heavy modules;
- virtualize large result lists;
- avoid rebuilding the full graph unnecessarily;
- cache normalized entity lookups;
- debounce search input;
- limit graph neighborhood expansion;
- use Web Workers for expensive local computation where justified.

## Data

- precompute compact search indexes;
- avoid repeatedly parsing large source files at runtime;
- separate source assets from query indexes;
- cache derived calculations.

## Graph

- render only visible neighborhoods;
- cap default hops;
- progressively load secondary relationships;
- disable expensive animation in technical/field mode.

Do not optimize before measuring.

---

# 26. Accessibility

Minimum requirements:

- keyboard-accessible search;
- visible focus state;
- semantic labels;
- no colour-only information;
- readable contrast;
- browser zoom support;
- accessible result selection;
- screen-reader-friendly metadata where practical;
- non-graph alternatives for all critical engineering information.

The graph must never be the only way to access a critical fact.

---

# 27. Security and reliability

## Security

- do not execute source-file content;
- sanitize imported text before rendering;
- avoid arbitrary HTML injection from extracted PDF text;
- keep external network access optional;
- do not store secrets in datasets;
- validate imported field submissions;
- maintain provenance for externally supplied observations.

## Reliability

- preserve original source files;
- hash source files;
- make generated datasets reproducible;
- keep audit logs for manual verification;
- fail closed on invalid canonical data;
- distinguish unavailable source from absent evidence.

---

# 28. Testing strategy

The current E2E tests should remain, but the test pyramid must become broader.

## Level 1 — schema/unit tests

Test:

- entity validation;
- edge validation;
- evidence validation;
- requirement validation;
- measurement normalization;
- identifier normalization;
- relationship vocabulary;
- duplicate detection;
- conflict detection.

## Level 2 — data-integrity tests

Test:

- dangling references;
- duplicate IDs;
- invalid entity types;
- invalid relationships;
- invalid evidence IDs;
- broken revision chains;
- invalid measurements;
- broken requirement references.

## Level 3 — extraction fixtures

Maintain representative fixtures for:

- title block;
- revision table;
- dimensions;
- tolerance;
- BOM;
- notes;
- OCR region;
- cross-reference.

## Level 4 — application tests

Test:

- search;
- result selection;
- drawing detail;
- evidence navigation;
- revision comparison;
- graph focus;
- graph filters;
- context preservation.

## Level 5 — E2E smoke tests

Retain representative flows such as:

```text
Open app
→ search T-6155
→ select drawing
→ inspect revision
→ open evidence
→ focus graph
→ return to search
```

Also preserve manual/document-specific checks already present in the repository.

---

# 29. CI and validation workflow

Create a reproducible validation entry point.

Recommended command concept:

```text
validate_all
├── schema validation
├── graph integrity
├── evidence integrity
├── identity audit
├── requirement validation
├── extraction fixture tests
├── frontend/unit tests
└── E2E smoke tests
```

CI should eventually run on:

- pull requests;
- main branch changes;
- data/schema changes.

Generated artifacts should not be committed unless they are intentional, reproducible project assets.

---

# 30. Data conflict model

Engineering sources can disagree. The system must represent disagreement explicitly.

Example:

```text
Fact A
  value = 44 mm
  revision = Alt 13
  evidence = Source A

Fact B
  value = 43 mm
  revision = older source
  evidence = Source B

Fact A ──CONFLICTS_WITH──> Fact B
```

Resolution should consider:

- revision precedence;
- document authority;
- applicability period;
- verification status;
- evidence quality.

Do not delete conflicting historical facts merely to produce a cleaner graph.

---

# 31. Analytics and knowledge health

Build analytics for system quality, not vanity metrics.

## Knowledge coverage

Track:

- drawings with revisions;
- entities with evidence;
- facts with verification;
- requirements with source references;
- broken references;
- unresolved conflicts;
- extraction confidence;
- review queue size.

## Product analytics

Track locally where appropriate:

- most searched drawings;
- failed searches;
- frequently opened evidence;
- common graph paths;
- revision comparisons;
- learning weak topics.

Avoid collecting unnecessary personal information.

---

# 32. Knowledge-gap detection

Once data quality is mature, identify missing knowledge automatically.

Examples:

```text
Drawing exists
   ↓
Component exists
   ↓
No governing requirement found
   → knowledge gap
```

```text
Requirement exists
   ↓
No inspection procedure linked
   → workflow gap
```

```text
Failure mode exists
   ↓
No evidence-backed mitigation
   → safety knowledge gap for review
```

Knowledge-gap detection must create review tasks, not silently invent relationships.

---

# 33. Human review workflow

Uncertain extraction should become a queue.

```text
Candidate fact
   ↓
Confidence / rule evaluation
   ↓
LOW or SAFETY-RELEVANT
   ↓
Review queue
   ↓
Accept / edit / reject / mark conflict
   ↓
Canonical publication
```

Review records should preserve:

- reviewer;
- timestamp;
- original candidate;
- decision;
- reason/notes;
- resulting canonical fact.

---

# 34. Offline-first contract

The following should remain usable without network access:

- drawing search;
- drawing detail;
- graph exploration;
- source/PDF viewing;
- revision comparison;
- learning content;
- local calculations;
- evidence inspection;
- report generation.

Optional online features may include:

- remote synchronization;
- cloud AI;
- collaboration;
- centralized analytics.

Offline operation is a product requirement, not merely a technical convenience.

---

# 35. Reporting and export

Provide engineering-oriented exports:

- PDF/printable answer card;
- revision comparison report;
- BOM/procurement report;
- inspection report;
- failure analysis report;
- evidence package;
- JSON-LD;
- Cypher;
- machine-readable JSON.

Every report should preserve source references.

---

# 36. Implementation roadmap

## Phase 0 — Stabilize the foundation

### Done / existing foundation

- ontology contract;
- entity/edge schemas;
- canonical graph integrity validation;
- identity alias mapping;
- identity reference audit;
- search-to-evidence UX specification.

### Remaining

1. basic canonical-data cleanup;
2. evidence integrity validator;
3. unified validation command;
4. regression baseline;
5. CI workflow.

**Exit criterion:** canonical data can be validated reproducibly and failures are actionable.

---

## Phase 1 — Search and drawing intelligence

Priority order:

1. search result normalization;
2. search result entity cards;
3. `T-6155` search regression;
4. drawing detail view;
5. revision timeline;
6. source/evidence panel;
7. related knowledge panel;
8. graph focus from entity;
9. context-preserving breadcrumbs.

**Exit criterion:** a user can search a drawing and reach verified engineering information without manually operating the graph.

---

## Phase 2 — Evidence and revision intelligence

1. evidence registry integrity;
2. source crop viewer;
3. evidence cards;
4. revision lineage;
5. visual revision diff;
6. text/notes diff;
7. structured engineering diff;
8. BOM diff;
9. graph/dependency diff;
10. revision impact summary;
11. conflict dashboard.

**Exit criterion:** the user can determine what changed, where the evidence is, and what downstream knowledge may be affected.

---

## Phase 3 — Engineering graph intelligence

1. typed relationship filters;
2. dependency trace;
3. failure analysis mode;
4. procurement/BOM mode;
5. field inspection mode;
6. path finding;
7. “Why connected?”;
8. evidence-aware edges;
9. graph query primitives.

**Exit criterion:** graph exploration answers concrete engineering relationship questions.

---

## Phase 4 — Engineering workflows

1. Engineering Answer Cards;
2. drawing lookup;
3. component trace;
4. requirements lookup;
5. inspection workflow;
6. failure investigation;
7. BOM/spares calculation;
8. report export;
9. field mode.

**Exit criterion:** common engineering tasks can be completed faster than navigating raw drawings alone.

---

## Phase 5 — Question interface

1. query intent detection;
2. canonical retrieval;
3. graph traversal;
4. evidence retrieval;
5. answer cards;
6. citations;
7. confidence/verification indicators;
8. conflict-aware answers;
9. multi-hop questions.

**Exit criterion:** questions produce source-backed answers with explicit uncertainty.

---

## Phase 6 — Learning

1. concept pages;
2. drawing/component lessons;
3. guided learning paths;
4. quizzes;
5. flashcards;
6. revision exercises;
7. weak-topic analytics;
8. spaced repetition.

**Exit criterion:** the same canonical knowledge supports structured training without duplicating source truth.

---

## Phase 7 — Semantic intelligence

1. semantic indexing;
2. hybrid ranking;
3. concept similarity;
4. knowledge-gap detection;
5. query expansion;
6. graph-aware retrieval.

**Exit criterion:** natural-language and conceptual search improves recall without degrading evidence traceability.

---

## Phase 8 — AI copilot

Capabilities:

- Ask the Graph;
- Explain This Node;
- Why Was This Changed?;
- summarize evidence;
- compare revisions;
- trace dependencies;
- explain conflicts;
- generate learning material from verified knowledge.

Hard requirements:

- retrieval first;
- source citations;
- revision awareness;
- uncertainty disclosure;
- no invented engineering requirements.

---

## Phase 9 — Digital twin maturation

1. graph ↔ geometry mapping;
2. drawing region ↔ geometry mapping;
3. technical orthographic mode;
4. exploded views;
5. revision overlays;
6. component-to-source navigation;
7. inspection overlays;
8. performance optimization.

---

# 37. First 20 implementation tasks

| Priority | Task | Type | Exit condition |
| --- | --- | --- | --- |
| P0.1 | Evidence integrity validator | Data quality | All evidence refs resolve |
| P0.2 | Unified validation CLI | Tooling | One command validates publication data |
| P0.3 | Regression baseline | Testing | Representative suite is reproducible |
| P0.4 | CI validation workflow | Reliability | PR/main validation is automated |
| P1.1 | Search result cards | UX | Results expose useful entity context |
| P1.2 | T-6155 search flow | UX/test | Search → drawing works reliably |
| P1.3 | Drawing detail | UX | Core drawing metadata is visible |
| P1.4 | Revision timeline | UX/data | Revisions are navigable |
| P1.5 | Evidence panel | UX/provenance | Facts link to source evidence |
| P1.6 | Related knowledge panel | UX/graph | Key relationships are browsable |
| P1.7 | Focused graph entry | UX/graph | Entity opens focused in graph |
| P1.8 | Context preservation | UX | Search/revision state survives navigation |
| P2.1 | Revision structured diff | Intelligence | Facts/BOM/relations compare |
| P2.2 | Revision impact graph | Intelligence | Downstream impacts are traceable |
| P2.3 | Why connected? | Graph | Edge explanation shows basis/evidence |
| P2.4 | Dependency trace | Graph | Standard engineering paths are queryable |
| P3.1 | Engineering Answer Card | Workflow | Important facts have reusable presentation |
| P3.2 | Failure investigation flow | Workflow | Failure → cause → inspection → mitigation works |
| P3.3 | Procurement/BOM workflow | Workflow | BOM/spares calculation is evidence-linked |
| P4.1 | Question interface | Retrieval | Natural-language question returns sourced results |
| P4.2 | Evidence-backed answer layer | AI/retrieval | Every claim is traceable |

---

# 38. Acceptance criteria for the first user-visible milestone

The first meaningful milestone is complete when a user can:

1. Open the application offline.
2. Search for `T-6155`.
3. See a clearly identified drawing result.
4. See drawing number, title, and revision context.
5. Select the drawing without manually finding its graph node.
6. See core engineering metadata.
7. See related source/evidence where available.
8. Open the source page/crop when available.
9. Navigate to related requirements/components/procedures.
10. Open the graph with the drawing focused.
11. Return without losing search context.
12. Distinguish verified, extracted, derived, and unresolved information.

This milestone must not require:

- a new backend;
- a new database;
- a complete frontend rewrite;
- an LLM;
- a graph dataset rebuild;
- canonical ID migration.

---

# 39. Definition of Done for Knowledge Core v1

Knowledge Core v1 is complete when:

- every important entity has a stable ID;
- entity types are controlled;
- relationships use a controlled vocabulary;
- revisions are structured;
- important facts are first-class records;
- measurements have normalized units;
- evidence is first-class;
- evidence references resolve;
- source files are identifiable and hashed;
- verification status is explicit;
- confidence is explicit where meaningful;
- conflicts can be represented;
- canonical data passes validation;
- revision lineage is queryable;
- search uses canonical data;
- graph uses canonical data;
- source evidence is reachable from facts;
- ingestion is reproducible;
- representative tests exist;
- the frontend is not the canonical data store.

---

# 40. Agent handoff protocol

This section is specifically for another implementation agent taking over the repository.

## Before every change

1. Inspect `main` HEAD.
2. Inspect recent commits.
3. Inspect open pull requests.
4. Inspect the exact files/areas you intend to change.
5. Determine whether another active change overlaps.
6. Do not overwrite, revert, or duplicate active work.

## Select work in this order

```text
1. current-system audit / P0 reliability
2. UX / information architecture
3. search / evidence
4. graph architecture/interactions
5. drawing/document intelligence
6. learning/analytics
7. performance/accessibility/security/testing
```

Choose **one small coherent task** per iteration.

## Implementation rules

- Prefer the smallest safe change.
- Reuse existing data and mechanisms.
- Avoid broad rewrites.
- Do not introduce infrastructure without a demonstrated need.
- Add or update a focused test.
- Validate before committing.
- Do not commit generated junk or secrets.
- Do not commit if validation fails.
- Record failures and the next recommended action.

## Commit rules

Use conventional commit messages such as:

```text
feat(search): improve drawing result selection
feat(kg): validate evidence references
test(search): cover T-6155 result flow
docs(architecture): define evidence lifecycle
fix(graph): preserve selected entity context
```

## Completion report

Every iteration should report:

```text
Inspected:
- files/areas
- current HEAD
- active PRs

Changed:
- files
- behaviour

Validation:
- tests
- lint/type/build
- manual checks

Commit:
- SHA
- message

Next priority:
- one recommended task
```

---

# 41. Guardrails for future agents

## Do not do these prematurely

- rewrite the entire frontend;
- replace Three.js;
- introduce Neo4j without workload evidence;
- introduce PostgreSQL merely for architectural fashion;
- build an LLM answer layer before evidence integrity;
- migrate every identifier at once;
- rebuild the graph dataset without a demonstrated need;
- delete legacy data without reference audits;
- remove source PDFs;
- make graph appearance the primary success metric.

## Prefer these

- improve one workflow at a time;
- make evidence visible;
- make revision context explicit;
- turn free-text engineering values into structured facts;
- validate every canonical publication;
- keep source links intact;
- add focused regression tests;
- measure before optimizing;
- preserve offline functionality.

---

# 42. Recommended file/module evolution

The following target layout is illustrative; do not create all directories at once.

```text
RDSO-Drawings/
├── index.html                         # compatibility entry point during migration
├── docs/
│   ├── RDSO_Knowledge_Graph_Improvement_Blueprint.md
│   ├── UX_SEARCH_WORKFLOW.md
│   ├── REPO_STRUCTURE.md
│   └── architecture/
├── scripts/
│   ├── ingestion/
│   ├── validation/
│   ├── migration/
│   └── export/
├── src/
│   ├── app/
│   ├── knowledge/
│   ├── search/
│   ├── evidence/
│   ├── revisions/
│   ├── graph/
│   ├── workflows/
│   ├── learning/
│   ├── twin/
│   └── ui/
├── data/
│   └── knowledge-graph/
│       ├── raw/
│       ├── intermediate/
│       ├── canonical/
│       ├── exports/
│       └── schemas/
├── tests/
│   ├── unit/
│   ├── data/
│   ├── extraction/
│   └── e2e/
├── lib/
└── crops/
```

Migration should be incremental and reversible.

---

# 43. Practical example: T-6155

Use `T-6155` as the first end-to-end reference workflow because it exercises drawing identity, revisions, components, engineering details, and source evidence.

Expected experience:

```text
User types: T-6155
        ↓
Drawing result
  T-6155 — Curved Switch Assembly
  Revision: applicable/current
        ↓
Drawing detail
  Identity
  Revision history
  Components
  Key dimensions
  Standards
  Requirements
  Procedures
        ↓
Evidence
  Source PDF
  Page/region
  Verified facts
        ↓
Related knowledge
  T-6155/1
  tie bar
  slide chairs
  relevant standards
  inspection procedures
        ↓
Graph
  T-6155 focused
  relevant paths highlighted
        ↓
Return
  Search query preserved
```

This is a reference acceptance flow, not a request to hard-code T-6155-specific logic into the application.

---

# 44. Success metrics

Measure outcomes rather than implementation volume.

## Search

- successful search-to-entity rate;
- zero-result rate;
- time to first useful entity;
- exact-identifier success rate.

## Evidence

- percentage of important facts with evidence;
- evidence resolution success;
- verified/unverified visibility.

## Revision

- percentage of drawings with structured revision lineage;
- successful revision comparisons;
- impacted entities identified.

## Graph

- successful path queries;
- useful relationship exploration;
- unnecessary graph expansion reduction.

## Engineering workflows

- time to answer common questions;
- BOM calculation accuracy;
- inspection workflow completion;
- report generation success.

## Data health

- dangling references;
- unresolved conflicts;
- low-confidence candidates;
- review queue age;
- schema failures.

Avoid optimizing for node count, edge count, animation complexity, or visual novelty.

---

# 45. Final target state

The mature platform should look conceptually like this:

```text
                         RDSO KNOWLEDGE SYSTEM

 Sources ──→ Evidence ──→ Canonical Knowledge ──→ Retrieval
   │              │               │                  │
   │              │               ├── Search          │
   │              │               ├── Graph           │
   │              │               ├── Revisions       │
   │              │               ├── Requirements    │
   │              │               ├── Failures        │
   │              │               ├── BOM             │
   │              │               └── Learning        │
   │              │                                  │
   └──────────────┴──────────────────────────────────┤
                                                      ▼
                                               User Workflows
                                                      │
                     ┌────────────────────────────────┼─────────────────────┐
                     ▼                ▼               ▼                     ▼
                 Engineer         Field User      Learner             Analyst
                     │                │               │                     │
                     └────────────────┴───────────────┴─────────────────────┘
                                      │
                                      ▼
                              Optional AI Copilot
                         grounded in evidence + graph
```

The desired end state is **not simply a larger graph**. It is a system in which an engineer can reliably move from a question or drawing identifier to the relevant entity, understand its revision and relationships, inspect the underlying evidence, and continue into the appropriate engineering workflow.

---

# 46. Immediate next action for the implementation agent

Start with **P0 reliability only if the validation gaps are still present**. Otherwise begin **P1.1 Search Result Cards**.

The preferred sequence is:

```text
1. Reinspect current repository state.
2. Confirm no overlapping active work.
3. Verify evidence-integrity gap.
4. If present: implement evidence validator + focused tests.
5. Add/strengthen unified validation command.
6. Establish regression baseline.
7. Implement Search Result Cards.
8. Validate T-6155.
9. Implement Drawing Detail.
10. Implement Evidence Panel.
11. Implement Revision Timeline.
12. Implement Related Knowledge.
13. Implement Why Connected?.
14. Continue through the roadmap one validated increment at a time.
```

**Do not skip directly to AI, semantic search, database migration, or a frontend rewrite.**

---

# 47. Blueprint completion statement

This document is the strategic and implementation handoff for the next agent. It defines:

- the product direction;
- target architecture;
- canonical ontology;
- relationship model;
- fact/measurement model;
- evidence/provenance model;
- ingestion pipeline;
- validation gates;
- search experience;
- drawing intelligence;
- revision intelligence;
- graph interactions;
- engineering workflows;
- question/answer architecture;
- learning system;
- field mode;
- procurement/BOM intelligence;
- digital twin direction;
- UI modularization;
- backend decision criteria;
- semantic retrieval strategy;
- performance/accessibility/security requirements;
- testing/CI strategy;
- human review and conflict handling;
- phased roadmap;
- first implementation priorities;
- acceptance criteria;
- agent handoff protocol.

The implementation objective is simple:

> **Build a trustworthy engineering knowledge core first, then make every interface—Search, Drawing Intelligence, Evidence, Graph, Revision Analysis, Inspection, Procurement, Learning, Digital Twin, and AI—consume that same source of truth.**
