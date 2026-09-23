# RDSO Drawings — Master Project Specification

**Status:** Canonical project document  
**Purpose:** Single source of project direction, architecture, implementation roadmap, data contracts, UX requirements, validation gates, and agent handoff rules.  
**Supersedes:** Multiple overlapping documents previously maintained under `docs/`.  
**Archive policy:** Historical/source documents are retained under `docs/archive/` for traceability; new project decisions belong here.

---

## 1. Executive Direction

RDSO-Drawings is evolving from a drawing/PDF visualization prototype into an **offline-first Railway Engineering Knowledge System**.

The product combines:

1. RDSO drawings and drawing revisions.
2. Railway manuals, codes, specifications, letters and circulars.
3. Engineering components, assemblies, materials, measurements and requirements.
4. Evidence and provenance down to document/page/section/clause/drawing region.
5. Search, graph exploration, revision analysis and engineering workflows.
6. Evidence-grounded question answering and future AI assistance.
7. Learning, analytics and knowledge-gap detection.

The graph is **not the product by itself**. It is the relationship and navigation layer over an authoritative knowledge core.

### Core product loop

```text
User question / drawing / identifier
        ↓
Search / retrieval
        ↓
Canonical entity or provision
        ↓
Structured facts + relationships
        ↓
Evidence / source
        ↓
Related knowledge / revisions
        ↓
Engineering workflow / answer
        ↓
Verification / feedback
```

### Non-negotiable principles

- Evidence before explanation.
- Canonical data before visualization.
- Source facts before AI inference.
- Revision awareness everywhere.
- Explicit uncertainty and conflicts.
- Offline-first operation.
- Human review for safety-relevant facts.
- Deterministic, reproducible ingestion.
- Small validated increments instead of broad rewrites.
- One canonical knowledge core, many interfaces.
- UI must never become the authoritative data store.

---

## 2. Current Baseline

The existing application must be improved incrementally rather than replaced.

### Existing product surfaces

- `index.html` offline application entry point.
- Three.js knowledge graph.
- Search and entity-selection surfaces.
- Intelligence drawer.
- Semantic graph modes.
- Drawing/component views.
- Manual/Code universe.
- Existing PDF/source assets.
- Existing ingestion and canonicalization scripts.
- Existing browser and data-validation tests.

### Historical manual-ingestion baseline

The September 2026 session record reported:

- 6 official railway manuals ingested.
- 1,485 manual pages used for deep chapter extraction.
- 83 chapters catalogued.
- 2,731 statutory clauses extracted.
- 2,157 canonical nodes.
- 3,256 typed edges.
- 121,229 search-index tokens.
- 100% referential integrity in the recorded validation run.
- 8/8 browser/CDP verification tests passed in that recorded run.

These numbers are **baseline/session metrics, not permanent acceptance targets**. Always regenerate current metrics before making claims about the present repository state.

The six recorded manuals were:

1. IRPWM 2024 (ACS 1–14) — 530 pages.
2. USFD Manual 2026 — 157 pages.
3. AT Weld Manual 2022 — 49 pages.
4. FBW Manual 2022 CS 1–5 — 69 pages.
5. Indian Railways Track Machine Manual 2020 — 458 pages.
6. Small Track Machines Manual 2024 — 222 pages.

---

## 3. Product Domains

Maintain two primary knowledge universes.

### 3.1 Manual / Codes universe

Contains:

- manuals;
- editions/revisions;
- chapters;
- sections/subsections;
- clauses/provisions;
- tables;
- figures;
- evidence;
- topics/concepts;
- requirements;
- procedures;
- authorities;
- inspection/acceptance criteria;
- limits/tolerances;
- failures and safety information;
- cross-references;
- letters/circulars where introduced.

### 3.2 Drawing universe

Contains:

- drawings;
- drawing revisions;
- sheets;
- notes;
- components;
- assemblies;
- subassemblies;
- dimensions;
- tolerances;
- materials;
- BOM items;
- geometry;
- drawing-specific requirements and evidence.

### 3.3 Cross-domain rule

For the current release, **do not create direct Manual ↔ Drawing graph edges in the base KG**.

If future integration is required, use a dedicated relationship/evidence layer with:

- source;
- page/sheet/region;
- extraction method;
- confidence;
- verification status.

Candidate future predicates include:

- REFERENCES
- APPLIES_TO
- ILLUSTRATED_BY
- DEFINED_IN
- SPECIFIED_BY
- RELATED_TO

This prevents manual chapters from being polluted by random drawing-derived concepts—the central problem the manual KG v2 work was designed to solve.

---

## 4. Target Architecture

```text
SOURCE LAYER
  PDFs / drawings / manuals / images / field data
        ↓
INGESTION
  parsing / OCR / layout / tables / title blocks
        ↓
EVIDENCE
  pages / clauses / regions / quotes / crops / provenance
        ↓
CANONICAL KNOWLEDGE
  entities / facts / requirements / revisions / relationships
        ↓
RETRIEVAL + GRAPH
  full text / vector / hierarchy / graph / cross-reference
        ↓
APPLICATION
  search / document detail / graph / revisions / workflows / learning
        ↓
OPTIONAL INTELLIGENCE
  grounded QA / semantic retrieval / AI copilot
```

### Authoritative ownership rule

No frontend feature owns engineering truth.

The canonical data/evidence layer owns truth; every interface consumes it.

---

## 5. Canonical Identity and Document Model

Separate logical identity from physical source identity.

```text
DOCUMENT_FAMILY
  ↓
DOCUMENT / MANUAL / CODE / DRAWING
  ↓
EDITION / REVISION
  ↓
SOURCE_FILE
  ↓
PAGE / SHEET
  ↓
CHAPTER / SECTION / CLAUSE / REGION
```

Every canonical entity should have:

- stable machine-safe ID;
- entity type;
- human-readable name;
- aliases;
- status;
- provenance;
- verification state where applicable.

Never use filenames or display names as canonical identity.

Source files should retain content hashes, especially SHA-256.

### Version relationships

Support:

- HAS_EDITION
- HAS_REVISION
- SUPERSEDES
- AMENDS
- MODIFIES
- CORRECTS
- VALID_DURING
- WITHDRAWN_BY

Never infer supersession merely because one document is newer. The source must establish the relationship or applicability logic must explicitly support it.

---

## 6. Manual Structural Contract

Manual structure is authoritative and document-first.

```text
MANUAL
  └── CHAPTER
       └── SECTION
            └── SUBSECTION
                 └── CLAUSE / PROVISION
```

When a manual is selected, the first expansion must show **only its registered chapters**.

A manual must have:

1. Stable document ID.
2. Deterministic ordered chapter registry.
3. One CHAPTER node per registered chapter.
4. One manual-to-chapter ownership edge per chapter.
5. Stable chapter IDs.
6. Page ranges.
7. Structure status.
8. Source-derived semantic content below the structural layer.
9. Provenance on source-derived structural children.

### Derived section/subsection layer

Sections/subsections may be derived conservatively from clause numbering when authoritative headings are unavailable.

Such nodes must be explicitly marked as:

`DERIVED_FROM_CLAUSE_NUMBERING`

They must retain source document, page, source reference/text, extraction method, confidence, and chapter ownership.

A later heading-aware extractor may enrich or replace this derived layer without changing chapter ownership.

### Orphan headings

If a source heading implies a numeric parent that was not extracted:

- preserve the observed heading;
- do not invent the missing parent;
- attach it to the authoritative chapter as a fallback;
- record that the parent was unavailable.

Missing structure is a data-quality signal, not permission to fabricate hierarchy.

---

## 7. Manual Structural Artifacts

The following may be first-class structural artifacts:

- TABLE
- FIGURE
- EVIDENCE

Each must carry:

- deterministic ID;
- source document;
- source page;
- source section/reference;
- source text;
- extraction method;
- confidence;
- parent chapter.

Only label-driven, evidence-backed artifacts should become structural nodes. Random semantic mentions must not create direct manual children.

### Heading coverage diagnostics

The ingestion pipeline should track:

- pages with detected source headings;
- pages containing useful clauses/tables/figures/evidence but no source heading;
- heading coverage ratio;
- empty-content pages.

These diagnostics should drive future extraction improvements without weakening the deterministic hierarchy.

---

## 8. Engineering Knowledge Model

### Entity families

Documents:

- DOCUMENT
- DOCUMENT_FAMILY
- MANUAL
- EDITION
- SOURCE_FILE
- PAGE
- SECTION
- CLAUSE
- TABLE
- FIGURE
- EVIDENCE

Engineering:

- DRAWING
- DRAWING_REVISION
- ASSEMBLY
- SUBASSEMBLY
- COMPONENT
- SUBCOMPONENT
- MATERIAL
- GEOMETRY
- EQUIPMENT
- TOOL
- PART
- BOM_ITEM
- SPARE_PART

Requirements/operations:

- REQUIREMENT
- SPECIFICATION
- STANDARD
- CODE
- TOLERANCE
- MEASUREMENT
- CONSTRAINT
- ACCEPTANCE_CRITERION
- INSPECTION_CRITERION
- PROCEDURE
- SOP
- INSPECTION
- MAINTENANCE_ACTION
- FAILURE_MODE
- DEFECT
- HAZARD
- CAUSE
- EFFECT
- MITIGATION
- AUTHORITY
- ORGANIZATION
- LOCATION
- TOPIC

### Controlled relationships

Use directional, typed relationships such as:

```text
CONTAINS
HAS_EDITION
HAS_REVISION
HAS_PAGE
HAS_SECTION
HAS_CLAUSE
HAS_TABLE
HAS_FIGURE
HAS_EVIDENCE

REFERENCES
CITES
SUPPORTS
APPLIES_TO
GOVERNS
REQUIRES
PROHIBITS
ALLOWS
EXCEPTION_TO

PART_OF
ASSEMBLES
ASSEMBLED_FROM
MATES_WITH
INTERFACES_WITH
CONNECTED_TO
INSTALLED_ON
FASTENED_BY
SPECIFIED_BY
CONSTRAINED_BY
MEASURED_BY
INSPECTED_BY
TESTED_BY
ACCEPTED_BY

PERFORMED_BY
APPROVED_BY
DOCUMENTED_BY
PRECEDES
FOLLOWED_BY
DEPENDS_ON

SUPERSEDES
AMENDS
MODIFIES
CORRECTS
CONFLICTS_WITH
DERIVED_FROM
USED_IN
PROCURED_AS
REPLACED_BY
HAS_BOM_ITEM
HAS_SPARE
```

New relationships must be defined in the controlled vocabulary, validated, documented, and covered by fixtures/tests before broad use.

---

## 9. Engineering Facts

Relationships alone are insufficient. Important values must be first-class facts.

Examples:

- measurements;
- tolerances;
- limits;
- time periods;
- thresholds;
- quantities;
- materials;
- authority;
- responsibility;
- required documents;
- inspection intervals;
- acceptance criteria.

For numeric values store:

- value;
- unit;
- nominal/min/max/bounds where applicable;
- measurement/fact type;
- applicability;
- evidence;
- verification status.

Distinguish:

- specified;
- measured;
- observed;
- derived;
- inferred.

An inferred value must never be presented as an official requirement.

---

## 10. Evidence and Provenance Contract

Every safety-relevant or decision-relevant claim must be traceable.

Evidence should support:

- source document;
- edition/revision;
- page/sheet;
- chapter/section/clause;
- source text;
- image/region/crop where applicable;
- extraction method;
- extraction timestamp;
- confidence;
- verification status;
- reviewer/review date where applicable.

Controlled evidence states:

- EXTRACTED
- VERIFIED
- DERIVED
- INFERRED
- CONFLICTING
- REJECTED
- UNKNOWN

Required navigation:

```text
Answer
  → Provision / Fact
    → Evidence
      → Source page / sheet / crop
```

The user must not need to manually locate the cited source.

---

## 11. Ingestion Pipeline

The deterministic pipeline is:

```text
Source files
  ↓
Validate + hash
  ↓
Classify document
  ↓
Extract native PDF text/layout
  ↓
OCR only where required
  ↓
Detect metadata
  ↓
Detect hierarchy
  ↓
Extract clauses/provisions
  ↓
Extract tables/figures/notes
  ↓
Extract references
  ↓
Extract entities/facts/requirements
  ↓
Normalize
  ↓
Resolve identities
  ↓
Score confidence
  ↓
Human review for uncertain/critical content
  ↓
Canonical publication
  ↓
Validate
  ↓
Build full-text/vector/graph exports
```

### Raw/intermediate/canonical separation

```text
data/
  manuals/
    raw/
    intermediate/
    canonical/
    evidence/
    indexes/
  drawings/
  shared/
~~~

Never overwrite raw source extraction with normalized output.

---

## 12. Drawing Extraction

Drawings are engineering artifacts, not ordinary PDFs.

Extract when available:

- drawing number;
- title;
- revision;
- issue/effective date;
- sheet number;
- scale;
- units;
- title-block fields;
- dimensions;
- tolerances;
- materials/grades;
- notes/callouts;
- BOM;
- part/assembly references;
- referenced drawings;
- approvals;
- supersession information.

Use deterministic extraction first for identifiers, dates, revisions and dimensions; layout/OCR/computer vision for difficult structures; human review for critical dimensions and requirements.

Machine-extracted dimensions remain unverified until validated.

---

## 13. Manuals and Codes Extraction

The manual pipeline must capture:

- manual identity;
- edition/revision;
- chapter/section hierarchy;
- clauses;
- definitions;
- requirements;
- procedures;
- responsibilities;
- authorities;
- inspection/acceptance criteria;
- exceptions;
- tables;
- figures;
- notes/warnings;
- cross-references;
- limits/tolerances;
- terminology and aliases;
- source evidence.

A procedure should preserve source-defined ordering.

A rule may be decomposed as:

```text
CONDITION
 → REQUIREMENT
 → ACTION / PROCEDURE
 → AUTHORITY
 → DOCUMENTATION
 → INSPECTION / ACCEPTANCE
 → EXCEPTION
```

This structured interpretation never replaces the original provision text.

---

## 14. Cross-References

References are first-class relationships.

Store:

- source provision;
- target manual/document;
- target edition;
- target chapter/section/paragraph;
- reference text;
- evidence;
- resolution state.

Resolution states:

- RESOLVED
- AMBIGUOUS
- BROKEN
- EXTERNAL
- NOT_FOUND

Cross-reference resolution is required for reliable multi-hop question answering.

---

## 15. Hybrid Retrieval

Do not build `PDF → embeddings → chatbot`.

Use:

```text
Question
  ├── exact identifier search
  ├── full-text search
  ├── metadata filtering
  ├── semantic/vector search
  └── graph/cross-reference traversal
            ↓
      candidate evidence
            ↓
        re-ranking
            ↓
      applicability check
            ↓
      conflict check
            ↓
      evidence set
```

Ranking should generally prioritize:

1. exact identifier/provision;
2. exact title/name;
3. lexical relevance;
4. metadata relevance;
5. semantic similarity;
6. graph/context relevance.

Vector search must not replace structural/lexical retrieval.

---

## 16. Question Understanding and Grounded QA

Classify questions such as:

- RULE_LOOKUP
- PROCEDURE_LOOKUP
- AUTHORITY_LOOKUP
- SOURCE_LOOKUP
- EXCEPTION_LOOKUP
- COMPARISON
- DEPENDENCY_LOOKUP

Extract:

- activity/work;
- department;
- component/equipment;
- context/location;
- rule type;
- authority;
- time/version;
- named manual;
- known identifier.

### QA pipeline

```text
User question
  ↓
Intent + entity extraction
  ↓
Hierarchy filtering
  ↓
Hybrid retrieval
  ↓
Cross-reference expansion
  ↓
Graph traversal
  ↓
Evidence re-ranking
  ↓
Version/applicability check
  ↓
Conflict check
  ↓
Bounded evidence context
  ↓
LLM synthesis
  ↓
Citation verification
  ↓
Answer
```

The LLM must never receive unrestricted corpus context when a bounded evidence set can be supplied.

---

## 17. Answer Contract

A standard engineering answer should expose:

1. Direct answer.
2. Applicable requirement/rule.
3. Procedure/ordered steps.
4. Authority/responsibility.
5. Exceptions.
6. Related provisions.
7. Manual/document.
8. Edition/revision.
9. Chapter/section/paragraph.
10. Page/sheet.
11. Evidence excerpt.
12. Applicability/status.
13. Confidence/verification.
14. Conflict warning where applicable.

Every substantive claim should be traceable.

---

## 18. Conflict and Applicability Handling

Never silently resolve conflicting requirements.

When conflicts exist, show:

- both provisions;
- source versions;
- scope;
- dates;
- explicit precedence if documented;
- evidence.

If precedence cannot be established:

**Conflict/ambiguity detected — manual verification required.**

Do not select a provision merely because retrieval ranked it higher.

---

## 19. Search and UX

The primary workflow is:

```text
Search
  ↓
Results
  ↓
Entity / Provision detail
  ↓
Evidence / Source
  ↓
Related knowledge
  ↓
Graph exploration
```

Search must support:

- drawing number;
- drawing title;
- component;
- material;
- standard/specification;
- manual/document;
- clause/requirement;
- revision;
- defect/failure;
- procedure/inspection;
- measurement/tolerance;
- general engineering keywords.

### Result cards

Show:

- entity type;
- display name;
- canonical ID where useful;
- revision/edition;
- short description;
- evidence/source indicator.

For drawings show number + title together.

### Context preservation

Navigation must preserve:

- search query;
- selected entity;
- graph mode;
- filters;
- revision context.

### Accessibility

- keyboard navigation;
- visible focus;
- accessible labels;
- no colour-only meaning;
- readable at increased zoom;
- explicit empty/loading/error states;
- bounded large result sets.

---

## 20. Knowledge Graph UX

The graph is a supporting surface.

Required interactions:

- focus entity;
- expand one hop;
- filter entity types;
- filter relationship types;
- highlight path;
- explain why connected;
- open evidence from edge/fact;
- preserve context;
- return to previous state.

For manuals:

```text
Manual
  → Chapter
    → Section
      → Provision
        → Related knowledge
```

Semantic neighborhoods should expand on demand rather than flooding the universe.

---

## 21. Recommended Data/Technology Architecture

Initial low-cost architecture:

| Concern | Direction |
|---|---|
| Processing | Python |
| PDF | PyMuPDF |
| OCR | OCRmyPDF/Tesseract; PaddleOCR where justified |
| Database | PostgreSQL |
| Full text | PostgreSQL FTS |
| Vector | pgvector |
| Graph | Relational graph initially |
| API | FastAPI |
| Frontend | Existing application, modularized incrementally |
| Local AI | Configurable local inference |
| Cloud AI | Provider abstraction |
| Validation | JSON Schema + pytest |
| Browser testing | E2E/CDP |

Neo4j/Apache AGE/OpenSearch should be introduced only when workload evidence justifies the operational cost.

PostgreSQL remains the authoritative metadata/evidence registry.

---

## 22. Repository Direction

Keep the existing root application stable during migration.

Target direction:

```text
RDSO-Drawings/
├── index.html
├── manuals/
├── drawings/
├── data/
│   ├── manuals/
│   │   ├── raw/
│   │   ├── intermediate/
│   │   ├── canonical/
│   │   ├── evidence/
│   │   └── indexes/
│   ├── drawings/
│   └── shared/
├── scripts/
│   ├── manuals/
│   ├── drawings/
│   ├── ingestion/
│   ├── validation/
│   └── search/
├── src/
│   ├── knowledge/
│   ├── manuals/
│   ├── drawings/
│   ├── evidence/
│   ├── search/
│   ├── graph/
│   └── qa/
├── tests/
│   ├── manuals/
│   ├── drawings/
│   ├── knowledge/
│   ├── search/
│   └── qa/
└── docs/
    ├── PROJECT_MASTER.md
    └── archive/
```

Do not create all target directories at once. Migrate incrementally.

---

## 23. Historical/Existing Pipeline Components

The previous implementation record identified these important components:

- `scripts/build_source_registry.py`
- `scripts/segment_manuals.py`
- `scripts/extract_candidates.py`
- `scripts/ingest_all_manual_chapters.py`
- `scripts/build_canonical_pipeline.py`
- `scripts/validate_knowledge_graph.py`
- `scripts/build_updated_app.py`
- `tests/verify_kg_manuals.js`

The exact current state must be inspected before modifying or replacing any of them.

Existing generated artifacts previously included:

- source registry;
- extracted pages;
- candidate entities/relationships;
- normalized measurements;
- review queue;
- canonical nodes/edges;
- requirements;
- graph export;
- search index;
- manual knowledge export.

Generated metrics must always be regenerated rather than trusted from historical documentation.

---

## 24. Validation Gates

### Gate A — Source

- file exists;
- hash recorded;
- source identity valid;
- duplicates detected.

### Gate B — Structure

- valid manual root;
- deterministic chapter order;
- chapter ownership;
- valid section/subsection ownership;
- page bounds valid.

### Gate C — Identity

- stable IDs;
- no accidental duplicates;
- aliases explicit;
- source file and logical document identities separated.

### Gate D — Graph

- valid endpoints;
- controlled relationship vocabulary;
- correct direction;
- no duplicate logical edges;
- no impossible revision cycles;
- Manual/Drawing isolation enforced.

### Gate E — Evidence

- every evidence reference resolves;
- page/sheet exists;
- provenance complete;
- verification state valid.

### Gate F — Engineering semantics

- units normalized;
- bounds coherent;
- applicability explicit;
- conflicts represented;
- inferred values distinguished.

### Gate G — Publication

Only validated canonical data feeds production search/graph exports.

---

## 25. Continuous Engineering Loop

Every implementation iteration should follow:

```text
Inspect current repository
  ↓
Check recent work / overlap
  ↓
Select one coherent task
  ↓
Implement smallest safe change
  ↓
Run focused tests
  ↓
Run relevant validation
  ↓
Run regression suite
  ↓
Inspect actual UI/data output
  ↓
Commit only validated work
  ↓
Record next priority
  ↓
Repeat
```

If a continuous GitHub workflow is used, it should:

1. rebuild authoritative manual structure;
2. rebuild canonical KG;
3. validate structure/isolation/provenance;
4. run publication validation;
5. detect generated-data drift;
6. report failures;
7. refresh deterministic artifacts only when appropriate.

---

## 26. Implementation Roadmap

### P0 — Foundation and reliability

1. Inspect current repository state.
2. Confirm current manual inventory.
3. Confirm current chapter/section/provision coverage.
4. Validate source registry and hashes.
5. Validate evidence integrity.
6. Establish one unified validation command.
7. Establish reproducible regression baseline.
8. Add CI validation.

**Exit:** deterministic canonical data can be validated reproducibly.

### P1 — Manual structure and browsing

1. Complete manual hierarchy.
2. Chapter tree.
3. Section/subsection navigation.
4. Provision detail.
5. Source page opening.
6. Search result cards.
7. Context preservation.

**Exit:** a user can browse manuals structurally and reach source evidence.

### P2 — Evidence and cross-reference intelligence

1. Evidence registry.
2. Source highlighting/crops.
3. Cross-reference extraction.
4. Reference resolution.
5. Broken/ambiguous reference dashboard.
6. Evidence-backed graph edges.

**Exit:** multi-hop source navigation works reliably.

### P3 — Drawing intelligence

1. Drawing identity.
2. Revision lineage.
3. Title-block extraction.
4. Notes/tables/BOM.
5. Dimensions/tolerances.
6. Drawing evidence.
7. Revision comparison.

**Exit:** drawings become structured engineering artifacts.

### P4 — Engineering graph intelligence

1. Typed relationship filters.
2. Dependency trace.
3. Failure analysis.
4. Procurement/BOM.
5. Inspection mode.
6. Path finding.
7. Why-connected explanation.

**Exit:** graph answers concrete engineering relationship questions.

### P5 — Hybrid retrieval

1. Exact search.
2. Full-text search.
3. Metadata filters.
4. Vector retrieval.
5. Graph traversal.
6. Re-ranking.

**Exit:** natural-language queries retrieve relevant evidence.

### P6 — Evidence-grounded QA

1. Intent detection.
2. Retrieval.
3. Evidence ranking.
4. Version/applicability checks.
5. Conflict detection.
6. Answer synthesis.
7. Citation verification.

**Exit:** questions produce source-backed answers.

### P7 — Reliability, learning and analytics

1. Regression question suite.
2. Answer evaluation.
3. Learning paths.
4. Flashcards/practice questions.
5. Knowledge-gap detection.
6. Search analytics.
7. Review queues.

### P8 — Optional AI copilot / digital twin

Only after evidence integrity and retrieval are mature:

- Ask the Graph;
- explain this node;
- compare revisions;
- explain conflicts;
- generate learning material;
- drawing-to-geometry mapping;
- inspection overlays;
- grounded AI copilot.

---

## 27. First Manual Pilot Strategy

Do not semantically ingest all manuals simultaneously.

Select one complete approximately 500-page manual and prove:

```text
PDF
 → source registry
 → page segmentation
 → hierarchy
 → provisions
 → evidence
 → cross-references
 → search
 → question
 → grounded answer
 → citation
```

Then scale the same deterministic pipeline to the remaining manuals.

This reduces extraction risk and prevents the UI from becoming the debugging environment.

---

## 28. Pilot Acceptance Criteria

For one complete manual:

- all pages registered;
- hierarchy represented;
- chapter order deterministic;
- provisions preserved where detectable;
- source pages resolvable;
- full-text search works;
- representative natural-language queries retrieve evidence;
- citations resolve;
- source page opens;
- cross-references resolve or are explicitly classified;
- uncertain extraction is flagged;
- no answer is generated without retrieved evidence;
- regression tests exist;
- rerunning ingestion produces deterministic structural output.

---

## 29. AI Guardrails

The AI layer must:

1. Never invent a rule.
2. Never invent a paragraph number.
3. Never invent a page/sheet.
4. Never invent dimensions or standards.
5. Never silently change source meaning.
6. Never present inference as official text.
7. Never ignore version/applicability conflicts.
8. Prefer primary source evidence.
9. Preserve citations.
10. Surface uncertainty.
11. Require human verification for unresolved or safety-critical conflicts.

---

## 30. Offline-First and Security

Offline-capable functions should include:

- manual browsing;
- drawing browsing;
- full-text search;
- source viewing;
- evidence inspection;
- graph exploration;
- revision comparison;
- local calculations;
- local QA where a local model is configured;
- exports/reports.

Security/reliability requirements:

- immutable raw sources;
- content hashes;
- audit logs;
- no secrets in datasets;
- controlled model/provider configuration;
- access control for central deployments;
- safe uploaded-document handling;
- no silent source replacement.

---

## 31. Metrics

Measure outcomes, not implementation volume.

### Search

- exact identifier success;
- zero-result rate;
- relevant-result rate;
- time to useful provision/entity.

### Evidence

- important facts with evidence;
- evidence resolution rate;
- verification coverage.

### Revision

- structured revision lineage coverage;
- comparison success;
- downstream impact coverage.

### Graph

- successful path queries;
- useful relationship exploration;
- unnecessary expansion reduction.

### QA

- citation coverage;
- unsupported-claim rate;
- conflict detection;
- human validation rate.

### Data quality

- dangling references;
- broken cross-references;
- duplicate entities;
- stale editions;
- unresolved conflicts;
- low-confidence candidates;
- review queue age.

Do not optimize for node count, edge count, animation complexity, or embedding count.

---

## 32. Testing Strategy

Maintain multiple layers:

### Data tests

- schema validation;
- ID uniqueness;
- relationship integrity;
- manual/drawing isolation;
- provenance completeness;
- page bounds;
- version consistency.

### Extraction tests

- representative manual chapter fixtures;
- heading detection;
- clause parsing;
- table/figure extraction;
- reference resolution.

### Search tests

- exact identifier;
- chapter/provision;
- natural-language query;
- no-result behavior;
- revision filtering.

### Browser/E2E

At minimum validate:

- application startup;
- manual universe;
- manual chapter expansion;
- search;
- result selection;
- provision detail;
- source/evidence navigation;
- drawing workflow;
- graph focus;
- context restoration.

The historical 8-test manual CDP suite should be treated as a regression asset, not as proof of current health.

---

## 33. Agent Handoff Protocol

Before every change:

1. Inspect current HEAD.
2. Inspect recent commits.
3. Inspect active PRs/work.
4. Inspect exact files to change.
5. Identify overlapping changes.
6. Do not overwrite active work.

Choose one small coherent task.

Every iteration should report:

```text
Inspected:
- current HEAD
- relevant files
- active work

Changed:
- files
- behavior

Validation:
- tests
- data validation
- build/manual checks

Commit:
- SHA
- message

Next priority:
- one task
~~~

Use conventional commits such as:

- feat(search): ...
- feat(kg): ...
- fix(graph): ...
- test(manuals): ...
- docs(architecture): ...

Never commit generated junk or secrets.

---

## 34. Guardrails Against Premature Complexity

Do not prematurely:

- rewrite the entire frontend;
- replace Three.js;
- migrate all IDs;
- introduce Neo4j/PostgreSQL/OpenSearch merely for architectural fashion;
- build an LLM answer layer before evidence integrity;
- rebuild the entire graph without demonstrated need;
- delete legacy data without reference audits;
- remove source PDFs;
- optimize graph appearance instead of engineering workflows.

Prefer:

- deterministic extraction;
- evidence visibility;
- revision context;
- structured facts;
- controlled relationships;
- focused regression tests;
- incremental migration;
- offline operation.

---

## 35. Final Target State

```text
                 RAILWAY ENGINEERING KNOWLEDGE SYSTEM

Sources
  ↓
Document Structure
  ↓
Evidence + Provenance
  ↓
Canonical Knowledge Core
  ├── Manuals / Codes
  ├── Drawings
  ├── Requirements
  ├── Procedures
  ├── Components
  ├── Revisions
  ├── Failures
  └── BOM / Procurement
          ↓
  Search + Graph + Versions
          ↓
  Hybrid Retrieval
          ↓
  Evidence Ranking
          ↓
  Grounded Answer / Workflow
          ↓
  Source Page / Drawing Sheet
```

The end state is not a larger graph.

It is a system where an engineer can move from a question, drawing number, component, rule, or requirement to the relevant canonical knowledge, applicable revision, supporting evidence, related engineering context, and actionable workflow—with uncertainty and conflicts visible.

---

## 36. Canonical Project Decision

From this point forward:

**This file is the project-level source of truth for architecture, roadmap, quality gates, and implementation direction.**

Historical plans and session records remain available only as archived evidence.

New project decisions should update this document rather than create another parallel blueprint.
