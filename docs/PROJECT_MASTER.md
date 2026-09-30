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

> **Correction (§37):** the "2,731 clauses", "2,157 nodes / 3,256 edges" and later "7,321 nodes / 9,305 edges / 8,370 facts" figures are not reproducible from the repository. Quote only `data/knowledge-graph/reports/metrics.json` (generated). At HEAD after P0-R.1/R.2: 6,830 canonical nodes, 9,037 edges, 1,838 manual clauses, 361 tolerance nodes.

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

---

## 37. Independent Audit of P0/P1 Delivery (2026-09-29)

**Scope:** verify the P0 (Foundation) and P1 (Manual browsing) completion claims in `docs/gemini/` against the repository at HEAD `04df0ab`, and against the product goal: an offline, self-improving, intelligent search/QA system over the railway manuals.
**Method:** re-ran `scripts/validate_all.py`, `pytest` and `tests/verify_kg_manuals.js` (headless Chromium), then inspected canonical data (`data/knowledge-graph/`), the UI data bundle and the Q&A code path directly.
**Verdict:** P0/P1 are **structurally delivered but not up to the mark**. The plumbing (hierarchy, tree, PDF page-jump, breadcrumbs) works and is reproducible. The knowledge content underneath it is thin, partly mislabelled as verified, and the QA layer is hand-authored rather than retrieval-based. P0/P1 should be treated as **PARTIAL**, not COMPLETE. Do not start P2 on the current data without the P0-R/P1-R remediation below.

### 37.1 Reproduction of the claimed results

| Claim (`docs/gemini/`) | Re-run result | Notes |
|---|---|---|
| 11/11 validation gates pass | **Reproduced** (after `pip install jsonschema pytest`) | Fresh env fails Gates A, E, G, H on missing dependencies; the gate runner should self-diagnose or install. |
| 126/126 pytest | **Reproduced** | |
| 11/11 CDP tests in `verify_kg_manuals.js` | **Reproduced** | Only with local flag patches: the test hard-codes Windows Chrome paths and a `C:\Users\LENOVO` artifact dir; it cannot run on Linux CI as written. |
| CI validation exists | **Partially true** | `ci.yml` runs Gates A–K only on `main`. Browser/CDP tests are not in CI. |

Passing gates do not imply data quality. Gates check referential integrity and shape, not content (see 37.2).

### 37.2 Claim vs. verified reality (side by side)

| # | Claim in P0/P1 reports | Verified reality | Severity |
|---|---|---|---|
| 1 | "2,731 statutory clauses" (P1 report §2.1, Master §2) | Canonical store has **1,838** clause nodes (IRPWM 673, STMM 396, TMM 349, USFD 174, FBW 131, AT Weld 115). Raw extraction detected 3,699 clause-like markers; 2,731 is not reproducible from any file. | High |
| 2 | "7,321 nodes / 9,305 edges / 8,370 facts" | Canonical: **6,469 nodes / 8,370 edges**. The UI adds the legacy `rdso_manuals_knowledge.json` (1,838 clauses + 361 tolerances) at runtime to reach 7,321/9,305. "8,370 facts" is the **edge list re-emitted** (`facts` and `edges` both 8,370), not engineering facts. | High |
| 3 | "One canonical knowledge core" (Master §1, §21) | **Two competing sources**: `data/knowledge-graph/canonical/*` and legacy `data/rdso_manuals_knowledge.json` + `manual_content_index.js`. TOLERANCE nodes (e.g. Check-rail 41–45 mm in Test 5) exist only in the legacy file; canonical has 0 TOLERANCE nodes. | High |
| 4 | "Statutory verbatim provision text on clause cards" | Canonical clause nodes have **empty text** (`desc` is `"..."` for 1,838/1,838; `Manual Ref` and `Key Rule` empty for all). Text lives only in evidence quotes hard-capped at **300 chars** and in the UI bundle. | High |
| 5 | Requirements complete | `requirements.jsonl` has 3,772 rows: **1,555 have statement `"..."`**; **1,934 IDs match no node** (legacy `CLAUSE:IRPWM:PARA_101` scheme, plus `TOL:`/`REQ:`). Gates pass anyway. | High |
| 6 | Evidence-verified (Gate D) | **100% of nodes (6,469), requirements (3,772) and evidence (1,875) are `verification_status: verified`**, including automatic text extraction at confidence 0.95. Violates "human review for safety-relevant facts". Fact provenance for structural HAS_CLAUSE edges is stamped `raster_blueprint_crop_and_transcription`, confidence 1.0, `VERIFIED`, which is false (they were text-parsed). | High |
| 7 | Evidence-backed graph edges (Master §10) | **0 of 8,370 edges carry an evidence reference.** Only 300 HAS_EVIDENCE edges (one evidence node per ~6 clauses). Evidence records lack page number and bbox; page is only inferable via `page_id`. | High |
| 8 | "Complete manual hierarchy" | Hierarchy nodes exist (83 chapters, 2,082 sections, 1,819 subsections) but clause coverage is partial: IRPWM 1,738 detected vs 673 kept (~39%); TMM 1,062 vs 349; STMM is the reverse (179 detected vs 396 kept). IRPWM clause IDs include impossible paragraph numbers (`CH_02:PARA_5300`, `PARA_5164`, `PARA_2243`…, 18 IDs above 1600 in a manual that ends near 1500): table/figure numbers parsed as paragraphs. | High |
| 9 | "Source registry and hashes validated" (P0.4) | The 6 manual PDFs have SHA-256 in `raw/source_registry.jsonl`; the 12 `documents.jsonl` rows carry none. Nothing re-verifies file hashes against disk in CI. | Medium |
| 10 | "1,485 pages ingested" | 1,485 manual pages registered, but **64 pages have no extractable text** (USFD 32/157 = 20%, FBW 13/69, IRPWM 14, TMM 4, AT Weld 1). No OCR path exists, so those pages are invisible to search. | High |
| 11 | "Search result cards" (P1.6) | UI cards work, but search is over token lists in a 7.5 MB `search_index.json` produced by the pipeline and the in-page filter; there is no BM25/inverted index, no stemming/synonyms, no rank tuning beyond a hand patch (`scratch/fix_search_ranking.py`). | Medium |
| 12 | "Natural-language Q&A" (Phase 5 UI) | `answerEngineeringQuestion` is a **regex intent detector plus 13 hand-written `CANONICAL_QA_DATABASE` answers**, each with hard-coded `confidence: 0.9x` and `VERIFIED`. Questions outside those 13 topics fall to a substring filter. This is not retrieval, is not grounded per query, and the reported confidence is not computed. Intent labels were tuned to the test queries (Alt 11, Alt 12 etc.). | High |
| 13 | Cross-references (P2 prerequisite; P1 checklist item) | 404 "Para NNN" and 236 "Annexure" mentions in IRPWM raw text; **5 REFERENCES edges** in the graph; no resolver, no RESOLVED/AMBIGUOUS/NOT_FOUND classification. | High |
| 14 | "Self-improving / learning" (Learning system, Phase 6) | The "learning system" is a UI quiz/flashcard front-end over static content. `review_queue.jsonl` holds **2 hand-written items**. No query logging, no feedback capture, no gap detection, no regression question suite, no re-ingestion loop. The system does not improve itself. | High |
| 15 | Offline-first | Achieved for the UI (no external URLs found in `index.html`; local Three.js). But ~48 MB of JSON/JS is loaded into the browser at start, and 22 MB `rdso_kg_data.js` duplicates canonical data. No local search engine or embedding index. | Medium |
| 16 | Repo hygiene / handoff protocol §33 | Commit `04df0ab` bundles docs, `index.html` (+405/−68), tests and 30+ regenerated PNGs in one non-conventional message; `__pycache__` `.pyc` files, `index.html.bak` and 7 `scratch/` scripts are tracked despite `.gitignore`. Gemini docs reference `f:\my git project\...` paths and were written as "read-only master", so the record diverged from this file. | Medium |
| 17 | P1 pilot acceptance (Master §28) | `P1_MANUAL_PILOT_PLAN.md` shows all 10 acceptance boxes **unchecked**, yet P1 is declared complete. Criteria such as cross-ref classification, deterministic rerun and "zero ungrounded claims" are unmet. | High |

### 37.3 What is genuinely good (keep)

- Deterministic source registry and per-page raw extraction (`raw/extracted_pages.jsonl`, 1,544 pages with text, headings, detected clauses).
- Six-manual chapter tree (83 chapters), universe isolation from drawings, Gates F–K enforcing it.
- Page-anchored PDF viewer (`#page=N`), breadcrumbs, back-to-search: working UX plumbing, verified in a real browser.
- 126 pytest tests and a single validation entry point (`validate_all.py`).
- Research workspace with a Docling benchmark harness (`research/`, `scripts/research/`), the right seed for better extraction.

### 37.4 P0/P1 exit-criteria status after audit

| Phase | Gemini status | Audited status | Reason |
|---|---|---|---|
| P0.1–P0.3 inventory/coverage | COMPLETE | **PARTIAL** | Inventory correct; coverage numbers wrong (rows 1, 2, 8). |
| P0.4 registry + hashes | COMPLETE | **PARTIAL** | Hashes recorded but not enforced (row 9). |
| P0.5 evidence integrity | COMPLETE | **FAIL** | Integrity gate is shape-only; evidence lacks page/bbox, edges unevidenced, false provenance (rows 6, 7). |
| P0.6 unified command | COMPLETE | **PASS** | Add dependency bootstrap. |
| P0.7 regression baseline | COMPLETE | **PARTIAL** | Data regression only; no retrieval/QA regression, browser tests not portable (37.1). |
| P0.8 CI | COMPLETE | **PARTIAL** | Gates only; no browser tests, `main` only. |
| P1 hierarchy/tree/navigation | COMPLETE | **PASS (structure)** | Content under nodes is empty (rows 4, 8). |
| P1 provision detail | COMPLETE | **FAIL (canonical)** | Works only from legacy bundle (rows 3, 4). |
| P1 source page opening | COMPLETE | **PASS** | Whole-page jump only; no highlight/crop (P2.2). |
| P1 search cards / context | COMPLETE | **PASS (UI)** | Underlying ranking is basic (row 11). |

### 37.5 Remediation plan (ordered; each is one small validated increment)

**P0-R (must precede P2):**
1. Make canonical the only source: fold legacy clauses/tolerances into canonical, generate `rdso_kg_data.js` from it, delete the runtime merge, add a gate failing on divergence.
2. Store full clause text in canonical (`text`, `page_start/end`, `bbox` when available); fix the 1,934 dangling requirement IDs and 1,555 empty statements; add gates for empty text and dangling IDs.
3. Re-baseline provenance: extraction output is `machine_extracted` (not `verified`) until human-reviewed; remove false `raster_blueprint_crop_and_transcription`/1.0 stamps; add review-state gate.
4. Attach `evidence_id` (doc, page, bbox, hash of page) to every edge and clause; Gate D must fail on edges without evidence.
5. Publish a single generated metrics file (`reports/metrics.json`) and make the docs quote only it; correct §2 numbers.
6. Clause-boundary QA: reject paragraph numbers out of the manual's known range/monotonic order (e.g. `PARA_5300`); reconcile detected-vs-kept per manual with a diff report.
7. OCR the 64 image-only pages (start with USFD 32) and record `extraction_method: ocr` with confidence.
8. Make CDP tests portable (env-driven Chrome path, headless flags, repo-relative artifacts) and add them to CI; run CI on all branches/PRs.
9. Repo hygiene: untrack `__pycache__`, `index.html.bak`, `scratch/`; stop committing regenerated PNGs.

**P1-R:**
10. Provision cards read from canonical text; show page number and offer source-page jump from every card.
11. Re-mark the P1 pilot checklist honestly and complete it for IRPWM before scaling to other manuals.

**New (needed for the product goal, currently missing):**
12. **Offline retrieval core (moves P5 earlier):** local SQLite FTS5/BM25 over clause text with identifier and synonym expansion; later add a small local embedding index and graph expansion, all served without network.
13. **Grounded QA:** replace the 13 hand-written answers with retrieve → rank → cite extractive answers; confidence computed from retrieval scores; refuse when evidence is weak; keep the 13 as regression questions, not as the engine.
14. **Cross-reference resolver (P2):** classify the ~640 IRPWM references first, then all manuals.
15. **Self-improvement loop (P7 pulled forward):** log queries locally, record thumbs/corrections, auto-queue zero-result/low-score queries and conflicting facts into `review_queue`, and turn every accepted review into a regression question run by `validate_all.py`.

### 37.6 Recommended next priority

One task: **P0-R.1 + P0-R.2**, unify canonical data and store full clause text, with gates for empty text, dangling requirement IDs and metric drift. Everything else in retrieval, QA and learning depends on that data being real.

### 37.7 Process note

The Gemini agent kept this document read-only and recorded status separately. Per §36, project status and audit results belong here. `docs/gemini/*` should be treated as **historical agent logs, not authoritative status**; where they conflict with §37, §37 governs.


### 37.8 Remediation progress

| Item | Status | Result (verified by re-run) |
|---|---|---|
| P0-R.1 single canonical source | **DONE (partial, see limits)** | `scripts/unify_manual_canonical.py` merges the two diverged stores (JSONL had name/status, compact JSON had provenance/hierarchy) into one node record; `rdso_manuals_knowledge.json` is now a *derived view* (content identical to the previous file); exports and `metrics.json` regenerate from it. |
| P0-R.2 full clause text | **DONE** | 1,838/1,838 clauses carry `text`, `page`, `document_id`, evidence id; requirements regenerated (2,199 rows, 0 empty, 0 dangling); 1,573 legacy dangling rows moved to `intermediate/quarantine_dangling_requirements.jsonl` (nothing deleted); 361 tolerance nodes and 667 evidence-linked `SPECIFIES` edges now in canonical. |
| Honest status | **DONE** | Extracted clauses/tolerances are `machine_extracted`; invented `mandatory/recommended` priority replaced by `unknown`. |
| P0-R.3 provenance re-baseline | **DONE** | `scripts/provenance_policy.py` (applied by `unify_manual_canonical.py`): all 6,830 nodes, 2,199 requirements and 1,875 evidence records were `verified` with no human review; they are now `machine_extracted` with confidence capped at 0.95. 8,270 facts stamped `raster_blueprint_crop_and_transcription`/`VERIFIED`/1.0 that were actually text-derived were relabelled `deterministic_text_extraction`/`MACHINE_EXTRACTED`. The only route to `reviewed` (1 reviewer) or `verified` (2 independent reviewers) is a record in `canonical/reviews.jsonl` (starts empty). |
| Gate M | **DONE** | `scripts/validate_provenance_policy.py`: statuses must equal what review records imply, no unreviewed confidence above 0.95, no text fact labelled raster transcription, review records well-formed and pointing at real ids. 5 tests incl. a negative test. |
| Gate L | **DONE** | `scripts/validate_manual_text_integrity.py` (in `validate_all.py`): empty text, dangling/duplicate/empty requirements, JSONL vs core divergence, derived-view and browser-bundle drift, stale metrics, short-clause ratchet. Negative test proves it fails on empty clause text. |
| Regression | **PASS** | 13/13 gates, 136 pytest (126 + 10 new), `verify_kg_manuals.js` 11/11 and `verify_knowledge_universes.js` pass in headless Chromium after the change. |

**Limits found while doing this (carry into the plan):**
1. **325 of 1,838 clauses (18%) have under 60 characters of text**: the extractor kept the heading, not the body (e.g. USFD 8.2 "Apparatus required:"). Gate L ratchets this at 325; it may only fall. Root cause: paragraph-boundary logic; fix in P0-R.6.
2. **Tolerance nodes are bare numbers** ("30 mm"): 783 mentions collapse to 361 ids with no subject/quantity/limit type. They are indexed but are not engineering facts. Needs a structured `Measurement` model (P2-facts below).
3. **Runtime merge still exists in `index.html`** (it reads `RDSO_MANUALS_KNOWLEDGE`). It is now a generated view so it cannot diverge (Gate L), but the frontend should read canonical directly (P1-R.10).
4. **Two edge vocabularies**: compact JSON keeps `CONTAINS_CHAPTER`, JSONL uses `HAS_SECTION`; Gate L compares them after normalisation. Retire `CONTAINS_CHAPTER` when gates F/J are ported.
5. `rdso_kg_data.js` is 24 MB (text now included twice: canonical + view). Acceptable now; shrink in the retrieval work (SQLite).
6. Some "clauses" are not clauses (e.g. title `CHAPTER – 4` for Para 145; `Annexure` headers); see P0-R.6.

### 37.9 Sprint A results (data truth) — 2026-09-30

| WP | Result (verified by re-run) |
|---|---|
| P0-R.4 evidence locations | `scripts/locate_evidence.py` locates each manual node's source text on its PDF page with PyMuPDF (pinned `pymupdf==1.28.2`). **6,663 of 6,663 text nodes located** (clauses, sections, subsections, tables, figures, tolerances); 83 chapters are page-level. Evidence now carries `page_number` (1-based PDF index; note printed page numbers differ, e.g. Para 429 is PDF page 195, printed 165), `region` and per-line `line_regions` in PDF points, `page_width/height`, `pdf_sha256`, `page_sha256` (hash of the page text as held in the raw layer) and `match_ratio`; crop evidence carries `file_sha256`. Visually checked on Para 429: rectangles enclose exactly the cited text. Evidence records: 1,875 to 6,783. |
| Edge evidence | 9,025 of 9,037 edges now cite evidence (structural edges cite the child heading/clause; drawing edges cite the crop of their source fact). The remaining **12 edges are ungrounded, hand-authored links** (greasing/lubrication, fish plate, keyman) added with the UI Q&A work; they are listed in `canonical/evidence_waivers.json`, may only shrink, and should be sourced or removed. |
| Gate N | `scripts/validate_evidence_locations.py`: every edge cites resolvable evidence or is waived (stale waivers fail); PDF hash in registry equals the file on disk; page exists; `page_sha256` equals the raw page text; region inside the page; quote actually occurs on the cited page; crop hashes match. 5 tests including tamper tests. |
| P0-R.5 metrics | `metrics.json` now includes per-manual short clauses, non-extractable pages, raw detected clauses, evidence pages/regions, edges without evidence; Gate L and CI (`--check-metrics`) fail when it is stale. |
| P0-R.8 browser tests | `tests/browser_env.js` (Chrome discovery on Windows/macOS/Linux, `CHROME_PATH`, headless flags, DevTools wait instead of fixed sleep, screenshots to a temp dir via `RDSO_ARTIFACT_DIR`) and `scripts/run_browser_tests.py`. **12/12 suites pass headless on Linux.** Found and fixed: two suites returned exit code 0 on error (false passes) and the Windows-only Chrome/artifact paths. `verify_semantic_intelligence.js` still needs a hand-started Chrome and a hard-coded `F:\` path; not automated. |
| P0-R.9 hygiene | `__pycache__`, `index.html.bak` and `scratch/` untracked and ignored. Old PNG screenshots remain in history/`artifacts/` but are no longer regenerated by test runs. |
| P0-R.10 bootstrap | `validate_all.py` checks dependencies first and prints the exact `pip install` (or `--install`). |
| CI | `ci.yml` now runs on every push and PR: `rebuild_all.py` (ingest, generate, unify, locate evidence, unify, bundle) then `git diff --exit-code -- data/` (**a rebuild from the source PDFs is byte-identical to the committed data**, proven locally), metrics freshness, Gates A to N, and a separate browser job. `manual-kg-continuous.yml` no longer auto-commits generated data to `main` (it previously could overwrite the unified canonical with an older generator's output). Chapter extraction timestamp made deterministic to allow the reproducibility check. |

**Sprint A findings for the plan:**
- The clause-quality problem is concentrated: **STMM has 240 of 396 clauses shorter than 60 characters**; USFD has 32 of 157 pages, FBW 13 of 69 without extractable text (metrics.json).
- `nodes.jsonl` grew to 16 MB and `rdso_kg_data.js` to 26 MB because text is now inline; move text to the SQLite retrieval store in P5.1 and slim the browser bundle then.
- Evidence text is the first 300 characters of each unit. Full-clause highlighting (whole paragraph span) is a P2.2 refinement.
- The 12 waived edges and their nodes (`act_*`, `defect_*`, `mat_*`, `role_keyman`) are unsourced knowledge; treat as untrusted until sourced.

### 37.10 Sprint B results (extraction quality) — 2026-09-30

**What was wrong (verified in §37.2 rows 1, 8, 10):** clauses were found by page-local regexes on flat text. That produced false paragraphs (page numbers, drawing dimensions, table values: `PARA_5300`, `PARA_1676 RUNNING TRACK`), cut every clause at page end and at 1,200 characters, ran on contents pages, and hid this behind gates that only checked shape.

**What was built:** `scripts/clause_parser.py`, a document-level layout parser. Heads are bold, left-margin rows starting with the manual's numbering; contents pages and running headers are removed; the numbering chain (longest strictly increasing sequence) rejects values that merely look like numbers; the chapter comes from the numbering itself; bodies run across pages until the next head or a stand-alone chapter/annexure banner; bare headings become sections, not clauses; deleted paragraphs are recorded as tombstones. `scripts/ocr_pages.py` OCRs the image-only pages (RapidOCR, offline).

| Manual | Clauses before | Clauses now | Short bodies (<60 chars) before, now | Image-only pages (OCR'd) | Old regex "detected" |
|---|---:|---:|---:|---:|---:|
| IRPWM | 673 | **421** (+2 deleted tombstones) | 22, **0** | 14 | 1,738 |
| TMM | 349 | **171** | 27, **0** | 4 | 1,062 |
| STMM | 396 | **258** | 240, **14** | 0 | 179 |
| USFD | 174 | **192** | ~14, **0** | 32 (6 weak) | 353 |
| AT Weld | 115 | **73** | 7, **0** | 1 | 163 |
| FBW | 131 | **57** | 15, **0** | 13 | 204 |
| **Total** | **1,838** | **1,172** | **325, 14** | **64** | 3,699 |

Interpretation: the earlier totals were inflated by false positives, not "more coverage". Evidence: in IRPWM, TMM and STMM the paragraph numbers now form a **contiguous run inside every chapter** (IRPWM 101 to 1515 with 517/518 explained as deleted; TMM 101 to 1216; STMM 101 to 2311), which the old set (numbers up to 8833) did not. Median IRPWM clause is 1,016 characters (old 437), Para 429 is complete (1,278 characters over its page; it previously stopped at an inline "Annexure" phrase in the old logic and at 1,200 characters).

| Store | Before Sprint B | After |
|---|---:|---:|
| Canonical nodes / edges | 6,830 / 9,037 | 4,894 / 6,415 |
| Requirements / evidence records | 2,199 / 6,783 | 1,632 / 4,847 |
| Tolerance nodes (bare values, see §37.8) | 361 | 460 (full text now yields more mentions) |
| Evidence regions located | 6,663 | 4,721 (all text nodes; 9 clause/section items are page-level only, ratcheted) |
| Edges without evidence | 12 (waived) | 12 (waived) |

**Other changes with reasons:**
- `generate_canonical_kg.py` no longer reads `rdso_manuals_knowledge.json`. That read was circular (the file was a view written from canonical) and was the original source of the empty-text clause nodes. Nodes and edges are now rebuilt without reading earlier canonical outputs, so stale records cannot survive; `rebuild_all.py` twice gives byte-identical files.
- **P1-R.1:** `index.html`, the bundle exporter and Gate L no longer use the legacy view; `data/rdso_manuals_knowledge.json` is deleted. Chapter ownership of clauses comes from the canonical id; provision cards read `text`, `page`, `roles`, `equipment`, `failure_modes`, `tolerance_texts` from the canonical node. Tests confirm nothing refers to the view (`test_frontend_single_source.py`); 12/12 browser suites pass; bundle 24 MB to 21 MB.
- **Gate O** (new): each of the 64 image-only manual pages has an OCR record tied to the current PDF hash; weak results (USFD: 6 pages with no text found or low confidence; a person should confirm they are figures or blank) are in `intermediate/review_queue.jsonl`. OCR is a committed artifact, not part of the byte-identical rebuild (model output can differ across runtimes).
- **Gate L** now also enforces numbering continuity for IRPWM, TMM and STMM (every number between a chapter's first and last is a clause, a bare heading or a deleted tombstone) and lowers the short-clause ratchet to 15. Gate I no longer fails decimal-manual clauses for sitting outside the *hand-written* registry page range (it warns, 85 warnings), because that registry is wrong for AT Weld (chapter 4 listed as pages 10 to 14, but its paragraphs run to page 17), FBW and parts of USFD.
- 16 new tests (parser unit tests, continuity, OCR tamper, frontend single source; 141 to 157); 157 pytest and 12 browser suites pass; 15 gates (A to O) pass.

**Known limits after Sprint B (honest):**
1. **Completeness for decimal manuals is not proven.** The continuity invariant exists only for the paragraph-numbered manuals. USFD, AT Weld and FBW (322 clauses) rely on the bold-head rule; FBW headings are not bold, so it uses margin plus sequence only. A sample review by a person is required (add to the review queue) before treating them as complete. 47 bare headings (USFD 17, AT Weld 19, FBW 11) were kept as sections, not clauses.
2. **Registry page ranges for AT Weld, FBW and USFD need a human correction** (numbering, not pages, currently owns the chapter). FBW pages 4 to 6 are an index and correction slips, not chapter text.
3. Body text keeps inline correction-slip markers such as "ACS - 2"; they should become structured amendment metadata (with the amendment date) in P2.3.
4. Clause bodies include tables and column text in reading order of the layout parser; table structure is not preserved. Table extraction is a separate work package (add to P2.3).
5. 14 STMM clauses are short (mostly "Nil." consumables and table-only troubleshooting entries); accepted, ratcheted.
6. There is no independent human gold set yet. All quality statements above rely on invariants (contiguity, coverage, gates) plus my inspection of sampled clauses.

**P1-R.2 pilot sign-off (Master §28) for IRPWM, criterion by criterion:**

| Criterion | Status | Evidence / gap |
|---|---|---|
| All pages registered | **MET** | 530/530 pages in `raw/extracted_pages.jsonl`, PDF SHA-256 in the registry (Gate N); 14 image-only pages OCR'd (Gate O). Per-page hashes are stored for every cited page. |
| Hierarchy represented | **MET** | 15 chapters, sections and subsections from source headings (Gates F, I, J, K). |
| Chapter order deterministic | **MET** | Numbering-derived; CI rebuild produces no diff. |
| Provisions preserved where detectable | **MET (IRPWM)** | 421 paragraphs plus 2 tombstones, contiguous 101 to 1515 (Gate L). Tables and annexures are not yet attached to their paragraphs (75% of page text lies inside clauses; the rest is annexures, tables and banners). |
| Source pages resolvable / source page opens | **MET** | Page numbers and rectangles verified on the PDF; viewer opens `#page=N` (browser suite). |
| Full-text search works | **PARTIAL** | In-page token search only; no BM25/identifier index (P5.1). |
| Natural-language queries retrieve evidence | **NOT MET** | Regex intents plus 13 canned answers (P5.1, P6.1). |
| Citations resolve | **PARTIAL** | Canonical evidence resolves and is hash-checked; the canned answers cite hard-coded paragraph lists. |
| Cross-references resolve or are classified | **NOT MET** | No resolver; 404 "Para NNN" and 236 "Annexure" mentions in IRPWM (P2.1). |
| Uncertain extraction is flagged | **PARTIAL** | Everything is `machine_extracted`; weak OCR queued; no per-clause uncertainty score yet. |
| No answer without retrieved evidence | **NOT MET** | Canned answers and substring fallback (P6.1). |
| Regression tests exist | **MET for data/extraction, NOT MET for retrieval** | 157 pytest, 12 browser suites; no retrieval/QA evaluation set yet (P7.1). |
| Rerun is deterministic | **MET** | `rebuild_all.py` twice and in CI: byte-identical (OCR excluded by design). |

Verdict: the **structural half of the pilot (PDF to registry to hierarchy to provisions to evidence to source page) is MET for IRPWM**. The **retrieval half (search, questions, cross-references, grounded answers) is NOT met**, and the pilot is therefore not complete. Do not scale to other manuals for retrieval until Sprint C.

### 37.11 Sprint C results (retrieval) — 2026-09-30

**Order followed:** measure first, then build, then tune only on the dev split.

**C1. Evaluation set (P7.1, started).** `eval/questions.jsonl`: 320 questions, built by `scripts/build_eval_set.py` from `eval/handwritten_questions.json`.

| Category | n | What it tests | Gold |
|---|---:|---|---|
| `nl` | 100 | natural-language questions written from sampled clauses across all six manuals | the clause that answers it |
| `ident` | 40 | "Para 429 IRPWM", "clause 710 of small track machines manual", "USFD 8.10" | that clause |
| `title_auto` | 120 | a unique clause title as the query (a lexical floor) | that clause |
| `kw_auto` | 40 | the `nl` questions reduced to bare keywords | that clause |
| `oos` | 20 | questions the manuals cannot answer (cooking, cricket, Python ...) | none: must refuse |

Each item has a deterministic dev/test split (hash of the question): 195 dev, 125 test. `eval/baseline.json` is committed; Gate P fails if Recall@5 or MRR of any category drops by more than 0.01 on either split, or if refusals regress.

**C2. Offline retrieval engine (P5.1).** `lib/rdso_search.js` is one engine for the browser and for Node, with no dependency and no network: BM25F over 3,190 passages (700 to 1,100 characters, cut at line boundaries; clause title and chapter weighted x3), Porter stemmer, unit and "1 in 12 / 1:12" normalisation, a railway abbreviation table (`data/search/synonyms.json`, expansions down-weighted), paragraph-number matching ("Para 429", "IRPWM 2024 225"), manual-name scoping (longest match, so "small track machines manual" does not also select TMM), a small topic prior (flash-butt words favour FBW, thermit words favour AT Weld ...), bigram re-ranking, and an **evidence-coverage score** (share of the question's term weight found in the best passage) used to refuse out-of-scope questions. Index: 10,193 terms, 4.7 MB (`data/search/search_index.js`), built deterministically by `scripts/build_search_index.py` inside `rebuild_all.py`. Speed: 0.7 ms per query warm, 2 ms cold, index load 2 ms in Node.

| Split | Category | n | R@1 | R@5 | R@10 | MRR |
|---|---|---:|---:|---:|---:|---:|
| dev | nl | 58 | 0.759 | 0.948 | 0.983 | 0.832 |
| dev | kw_auto | 23 | 0.652 | 0.913 | 0.957 | 0.772 |
| dev | ident | 29 | 1.000 | 1.000 | 1.000 | 1.000 |
| dev | title_auto | 73 | 0.904 | 0.986 | 0.986 | 0.943 |
| test | nl | 42 | 0.833 | 1.000 | 1.000 | 0.909 |
| test | kw_auto | 17 | 0.882 | 1.000 | 1.000 | 0.941 |
| test | ident | 11 | 1.000 | 1.000 | 1.000 | 1.000 |
| test | title_auto | 47 | 0.957 | 1.000 | 1.000 | 0.975 |

Refusal (threshold chosen on dev, coverage < 0.56 and no paragraph number resolved): dev 12/12 out-of-scope refused, 2 of 183 answerable wrongly refused; **test 6/8 out-of-scope refused**, 2 of 117 answerable wrongly refused. Two tuning steps were made on dev only (a longest-match manual detector that took `ident` from 0.93 to 1.0, and BM25 k1 1.2 to 1.0 with a topic prior and bigram weight 0.5); the test split was read once afterwards.

**How far to trust these numbers (important).**
1. The `nl` questions were written by the same author who was reading the clause, so they share vocabulary with the gold text; real users will paraphrase more. The numbers above are an upper bound.
2. An informal probe of 12 unlabelled, engineer-style questions ("what should a gangmate do if he finds a rail fracture", "rail flaw detection frequency for 60kg rails", "tamping cycle for concrete sleepers", "what is the gauge tolerance in track" ...) gave an acceptable first result for about 8, the right paragraph in the top three for one more, and clear misses for three (flaw-detection frequency returned USFD 7.1 rather than 6.6, tamping cycle and gauge tolerance returned neighbouring but wrong clauses). Treat top-1 accuracy on real questions as roughly 60 to 70% until an independent set exists.
3. `oos` has only 20 questions and the test half is 8, so the refusal figures carry wide error bars. Two test items ("How to repair a smartphone screen?", "speed limit for cars on national highways") share generic words with the manuals and are not refused.
4. Gold labels are `author_drafted_unreviewed`; a second person should check them (P7.1 completion).
5. Weak spots seen: USFD (and other decimal-numbered) clauses have poor titles (the label is the first sentence), which weakens the title field; queries about a value that lives in a table rank the surrounding prose.

**C3. Cross-references (P2.1).** `scripts/crossrefs.py` finds paragraph (with lists such as "Paras 619 and 620" and sub-clauses "(3)(a)"), annexure, table, figure, chapter and standard references in every clause, keeps the exact character span, types "(Back to Para N)" editorial back-links separately, follows "of the Indian Railway Code" style scopes to EXTERNAL, and resolves the rest against the canonical store. `canonical/crossrefs.jsonl` (1,572 records) and `reports/crossref_report.json`:

| Kind | Resolved | External | Not found | Notes |
|---|---:|---:|---:|---|
| paragraph | 548 | 9 | 9 | the 9 unresolved are listed in the report (e.g. IRPWM "Para 143", AT Weld "4.4.3.1", FBW "10.1.1") |
| annexure | 333 | 0 | 12 | |
| table | 79 | 0 | 11 | |
| figure | 197 | 0 | 107 | figures that were never extracted as nodes |
| chapter | 38 | 0 | 0 | |
| standard (IS, IRS, RDSO, RT ...) | 0 | 229 | 0 | external by definition |

1,676 `REFERENCES` edges were added (source clause to target; evidence = the source clause), taking the graph to 8,086 edges, all with evidence except the 12 waived ones. Gate Q recomputes the extraction and fails on stale data, wrong spans, missing targets or edges, and if unresolved paragraph references exceed 9.

**C4. Source highlighting (P2.2, partial).** `scripts/render_evidence.py` draws the stored per-line evidence regions on the PDF page and crops around them (verified visually on Para 429). The viewer modal shows this crop above the PDF when `artifacts/evidence/<id>.png` exists and otherwise behaves as before. Limits: only the first 300 characters of a clause are highlighted (the evidence quote), not the whole paragraph; crops are a git-ignored cache produced on demand (`--doc IRPWM` or `--all`) rather than shipped (about 1,200 images); an in-browser highlight would need pdf.js, which cannot read local PDFs from `file://` pages without browser flags, so it was not attempted.

**UI changes (index.html):**
- A question that no curated answer matches now gets an **extractive answer**: the best passage quoted (HTML-escaped) with manual, paragraph and page, an "Open source page" button, other relevant provisions, status `MACHINE_EXTRACTED` and confidence equal to evidence coverage. If evidence is thin the card says **"No sufficient evidence"** and lists nothing. The previous fallback substring search that declared any keyword hit "VERIFIED, 94%" was removed.
- **Bug found and fixed:** the curated-answer matcher returned the "bolt-hole star crack mitigation" card (status VERIFIED, 95%) for "How is casual renewal of a defective or fractured rail carried out?" because one keyword ("fractured") matched. Curated answers now need at least two of their own keywords.
- Provision cards list **References in this provision** and **Referenced by** as clickable chips coloured by status, and the clause text scrolls instead of stretching the panel.

**Test and gate state:** 17 gates (A to Q), 175 pytest, 13 browser suites, all passing; a rebuild from source is byte-identical (search index and cross-references included). New: `test_search_engine.py` (7), `test_crossrefs.py` (8), `test_render_evidence.py` (3), `verify_retrieval_ui.js` (5 checks). Browser tests now use a fresh Chrome profile per run (a crashed run had left a lock that failed the next one); the CI browser job installs PyMuPDF and Pillow.

**Pilot status after Sprint C (Master §28, IRPWM):** full-text search **MET** (BM25 with identifiers); natural-language retrieval **PARTIAL** (good on the authored set, ~60 to 70% top-1 on informal probes); cross-references **MET** (classified, with 9 unresolved paragraph references reported); citations resolve **MET** for retrieval answers; no answer without retrieved evidence **PARTIAL** (retrieval answers and refusals are evidence-gated; the 13 curated answers remain and still carry hard-coded "VERIFIED"); regression tests for retrieval **MET**.

### 37.12 Sprint D results (grounded answers and the feedback loop) — 2026-09-30

**D1. A blind evaluation set, and what it showed.** No real engineer questions were available, so 47 practitioner-style questions were written *before* reading any clause text (`eval/blind_questions.json`; 35 answerable, 12 railway-related but unanswerable from these manuals) and gold-labelled afterwards. Caveat that matters: the labeller looked at the engine's top results to find candidates, so the gold is biased towards what the engine can find; a second, independent labeller is still required. `build_eval_set.py` also accepts `eval/reviewed_feedback.json` (category `real`) for questions accepted from users.

| Blind set | n | R@1 | R@5 | MRR | Refusal of unanswerable |
|---|---:|---:|---:|---:|---|
| dev, before tuning | 20 | 0.650 | 1.000 | 0.800 | 20/20 (all out-of-scope items, threshold moved to 0.68 by the new railway-adjacent items) |
| dev, after | 20 | 0.750 | 1.000 | 0.850 | 20/20 |
| test, before | 15 | 0.667 | 0.933 | 0.767 | 10/12 |
| test, after | 15 | 0.667 | 0.933 | 0.789 | 10/12; 9 of 132 answerable test questions wrongly refused |

The only change kept from tuning on dev was a 1.15 authority prior for the Permanent Way Manual when the question names no manual and no topic (a clause aggregation variant was tried and rejected because it hurt paragraph-number queries). Unrefused test items: railway topics whose words appear in the manuals ("Rajdhani" appears in a speed clause, "coach ... cleaning" in a track-machine coach clause). Proximity-based coverage was tried as a better refusal signal and did not help. The blind numbers are much closer to the informal probe of Sprint C than the authored `nl` numbers are, so **expect roughly 65 to 75% first-result accuracy and about 93% in the top five on real questions**, with weakest results on railway-adjacent unanswerable questions.

**D2. The hand-written answers were unsafe, and are now retired or labelled.**
`scripts/audit_curated_answers.py` extracts the 13 curated answers from `index.html` and checks their numbers against the clauses they cite. Result: 1 supported, 5 with numbers absent from the cited clauses, 7 uncited (drawing knowledge that cannot be checked against manuals). The screening is coarse (number present anywhere in a cited clause passes), and a manual check found a worse case that it missed: the tongue-rail card stated **"maximum vertical wear 6.0 mm, lateral 8.0 mm per IRPWM Para 429 and IRS:T-10", status VERIFIED, 99% confidence. Para 429 gives 6 mm and 8 mm only as reconditioning limits for crossings and wing rails (and 10 mm / 8 mm for crossing wear); it gives no tongue-rail wear limits.** A safety limit attributed to the wrong component, presented as verified. Actions: the 6 manual-cited curated answers are `retired` and the questions are answered by retrieval; the remaining 7 keep working but are labelled **CURATED · UNREVIEWED** (no confidence percentage, status `CURATED_UNREVIEWED`); Gate P now fails if any curated answer claims `VERIFIED` or carries numbers its cited clauses lack. The `defect_*`, `act_*` and similar hand-made graph nodes behind them remain unsourced (12 waived edges).

**D3. Grounded answers (P6.1, partial).** `engine.answer()` returns either `no_evidence` or a cited answer: the sentences of the best passage that carry the question's terms (idf weighting, synonym and bigram credit, a bonus for sentences with a quantity when the question asks for a value), each as an exact slice of the passage (offsets are tested), a confidence tier (strong, probable, weak: from coverage and the margin over the next clause), the full passage on demand, and related provisions. The UI card shows the tier, the sentences with `[manual Para n · p.N]`, "Open source page" (with the highlighted crop when rendered) and thumbs up/down. Limits: a table-heavy passage (for example the level-crossing indicator clause 921) yields jumbled sentences because the parser flattens tables; the engine picks the best passage, not always the best clause; there is no per-claim contradiction or revision check yet, and the refusal threshold (coverage below 0.68, chosen on dev) both wrongly refuses about 5% of answerable questions and lets a few railway-adjacent questions through.

**D4. Feedback loop (P7.2, P7.3 partial).** The browser keeps a local log (queries with status, coverage and the clause shown; thumbs up/down) in `localStorage` (capped at 500 events) and exports it as JSONL on request; nothing leaves the machine. `scripts/ingest_feedback.py` merges exported logs into `data/feedback/feedback.jsonl` (git-ignored), rebuilds the `FB:*` items of `intermediate/review_queue.jsonl` (no-evidence questions, thumbs-down, low coverage), writes `reports/knowledge_gaps.json` (refused questions with counts) and `eval/candidates.jsonl` (thumbs-up pairs, `user_confirmed_unreviewed`). Candidates enter the evaluation set only after a person accepts them into `eval/reviewed_feedback.json`. Still missing from P7.3: applying reviewed synonyms automatically and the publish-blocking rebuild-and-evaluate step (today Gate P plays that role).

**Decision on embeddings (P5.2):** not justified yet. On the blind dev set the right clause is in the top five for every question; the errors are ordering (first versus second result), refusal of railway-adjacent questions, and table text, none of which a small embedding model is likely to fix reliably. Revisit if the independent real-question set shows top-five recall below about 90%.

**Not done this sprint (carried forward):** title repair for decimal-manual clauses, table-row indexing, per-claim revision/conflict flags, an independent second labeller for all `author_*` gold, and the automatic synonym loop. Test state: 17 gates, 180 pytest, 13 browser suites, all passing; 367 evaluation questions.

### 37.13 Sprint E results (tables and structured measurements) — 2026-09-30

**E1. Tables (P2.2).** `scripts/extract_tables.py` uses the PyMuPDF table finder over all six manuals and keeps only real data tables (at least two columns filled in half the rows, at least four filled cells, short cells); merged header cells are repeated, and a continuation table on the next page inherits the previous header. Result: 549 tables (TMM 152, IRPWM 204, STMM 139, USFD 24, AT_WELD 20, FBW 10) in `raw/tables.jsonl`, each with page, bounding box, rows, header rows, caption, the owning clause and the page hash. Gate R checks rectangular rows, header range, page hash against the raw text, that the owner clause exists, a floor of 540 tables, and that tables are in the search index. 526 tables reach the index as extra passages owned by their clause (`kind: table`, lines of the form "Header: value; ..."), so value queries ("versine for 4.5 degree curve") can hit a row. Limits: header detection is a heuristic; a scanned or ruled-line-free table can be missed or split; 23 tables are not indexed (no owner clause or no readable text).

Retrieval effect (dev tuning, then re-baselined; 12 new blind table questions): table questions dev R@1 0.78 to 0.89 and R@5 0.89 to 1.00; identifier queries unchanged (R@1 1.0); blind dev R@1 0.75, test R@1 0.60 (was 0.67, 15 questions, one question of difference) and blind table test 0.67 (3 questions, too few to conclude). Table passages initially displaced identifier queries (FBW 8.3 beat the requested paragraph); fixed with a 0.9 factor for table passages and an identifier second pass. Refusal threshold re-chosen on dev at 0.66: 20/20 dev and 10/12 test out-of-scope refused; 7/212 dev and 6/135 test answerable questions wrongly refused. 379 evaluation questions.

A side effect that is a quality loss: the tongue-rail wear question now answers from table rows of IRPWM Para 433 ("Switch 4; Distance between web to web of Tongue Rails"), tier "weak", where before it returned prose. The card says "rows copied from a table", which is honest, but the sentence extractor was built for prose and a row is a poor answer. Row-aware answer rendering (show the table with its header) is the next fix; the browser test now accepts both wordings.

**E2. Structured measurements (P2.3).** `scripts/measurements.py` + `extract_measurements.py` write `canonical/measurements.jsonl`: 5,778 values (3,345 from clause text, 2,433 from table cells), each with comparator (max, min, range, tolerance, value), numeric bounds, canonical unit (mm, m, kmph, kg, kn, degC, %, month ...), a quantity label where one could be assigned, the subject words, and the exact character span or table cell. Gate S re-reads the clause or cell and requires the span to reproduce the recorded text, canonical units, ordered bounds, and a count floor of 5,500. Conservative by design: paragraph, annexure, table and figure references, years, standards, implausible speeds (over 400 kmph) and percentages (over 100) are skipped; a quantity label is dropped when the unit cannot measure it (a "60 kg" is never a "height"). 4,070 values (70%) have no quantity label; that is deliberate, not a gap to paper over. Everything is `machine_extracted`.

Manual audit of 60 random labelled values: the number, unit and comparator were right in 59 of 60 (one truncated unit, `kg/cm2` read as `kg`, fixed and covered by a test). The quantity label was right in about 52 of 60 (roughly 87%); the wrong ones come from the nearest-keyword rule inside table-like paragraphs (for example a 3.6 m chord labelled "gauge", a temperature-table row labelled "length"). Treat the label as a search aid, not a fact. This audit is by the author of the extractor on a sample of 60; it is not independent.

A candidate report (`reports/measurements_report.json`) counts 20 groups where one manual gives different maxima or minima for the same quantity and unit. These are candidates for a person to look at (different components or speed classes will often explain them), not detected conflicts. The older bare `TOLERANCE` nodes stay because the UI depends on them; they are superseded by measurements and should be retired when the UI reads measurements.

**Not done this sprint (carried forward):** title repair for decimal-manual clauses (E3), registry page-range corrections for AT_WELD/FBW/USFD (E4, 85 warnings), row-aware answer rendering, measurement-to-graph edges, per-claim revision/conflict flags, independent second labeller and real engineer questions, automatic synonym loop. Test state: 19 gates (A to S), 191 pytest, 13 browser suites, all passing; rebuild is deterministic.

### 37.14 Sprint F results (titles, registry ranges, table answers) — 2026-09-30

**F1. Clause titles for numbered paragraphs without a heading (E3).** In the decimally numbered manuals a paragraph with no heading was given its first printed line as title, a wrapped fragment ("On Indian Railways Alumino-Thermic welding with short pre-heating process by using"). `clause_parser._repair_title` now replaces a fragment (55+ characters, no closing punctuation) with the first sentence of the paragraph, cut at a word boundary with an ellipsis at 100 characters. Real headings ("Shelf life of portion") are untouched. Limit: it cannot tell a heading from a first line by typography (bold is not carried through), so it works from length and punctuation; a few fragments under 55 characters remain (for example "Conventional A.T", cut at an abbreviation). The evaluation set is partly generated from titles, so it was regenerated and the baseline re-written deliberately: dev keyword and title recall@5 moved by one question each (0.913 to 0.88, 0.986 to 0.971), test unchanged in kind. Treat that as noise from a changed question set, not as a measured regression, but it is also not proof of no regression.

**F2. Registry page ranges (E4).** The hand-typed chapter page ranges for the alumino-thermic welding and flash-butt welding manuals disagreed with where the numbered paragraphs are (85 warnings, for example FBW chapter 5 registered at pages 9 to 13, paragraphs on pages 11 to 18). The ranges are now corrected from the parsed paragraph pages (USFD already agreed). The 85 warnings are gone; remaining warnings are the honest ones: chapters share boundary pages, and USFD chapters 12 and 15 have no numbered paragraph. The test that pinned the old FBW page was updated. Not independently checked against the printed manuals beyond the parser's own page assignment.

**F3. Table answers.** A question whose best passage is a table now answers with the matching whole rows (each cell prefixed with its column header) instead of sentence fragments, and merged cells that repeat their text are said once. The tongue-rail wear question of Sprint E (jumbled "Switch 4; Outer; Outer ...") is better but that particular table (IRPWM Para 433, a nested inspection proforma) is a poor data table and is still not a good answer; the fix for such tables is to exclude proformas from indexing, not done. Test state: 19 gates, 194 pytest, 13 browser suites, all passing.

**Not done (carried forward):** proforma tables excluded from the table index, measurement-to-graph edges, per-claim revision/conflict flags, independent second labeller and real engineer questions, automatic reviewed-synonym loop, drawings (P3/P4).

### 37.15 Sprint G results (form tables, conflict candidates) — 2026-09-30

**G1. Form-like tables demoted.** 142 table passages come from label-heavy tables (fewer than 35% of body cells contain a digit: inspection proformas, nested check-lists). They stay searchable but carry `form: true` and score at 0.7 of a data table (times the 0.9 table factor). Effect on the evaluation: none measurable (dev and test metrics identical with and without it); the visible effect is that "tongue rail wear limit" now answers from prose Para 429 instead of the Para 433 proforma. That is one probe, not a tested improvement; there is no form-specific evaluation question. The 0.35 cut-off was chosen by looking at the distribution, not tuned.

**G2. Conflict candidates from measurements.** `extract_measurements.py` now pairs bounds of the same manual, quantity, unit and comparator from different clauses with at least three shared subject words (`reports/measurement_conflict_candidates.json`). Result: 8 pairs, and on reading them none is a real contradiction (different speed bands, different components such as closure rail versus permanent closure, curve radius thresholds for different track classes). Without the earlier looser rule the list had 210 pairs of unrelated values. **Conclusion: regex measurements are good for value lookup, not for detecting conflicts between provisions; a conflict needs the condition each limit applies under (speed band, track class, component), which the extractor does not capture.** The list is kept as a review aid and no conflict flag is shown to users. Per-claim revision and conflict flags remain open, and need condition extraction first.

Test state: 19 gates, 195 pytest, 13 browser suites, all passing.

**Not done (carried forward):** condition extraction for measurements (speed band, track class, component), measurement-to-graph edges, independent second labeller and real engineer questions, automatic reviewed-synonym loop, drawings (P3/P4).

### 37.16 Sprint H results (intake for real questions, reviewed synonyms) — 2026-09-30

Sprint H builds the two human-in-the-loop pipelines that were missing. **It adds no new data and no measured improvement**: both need people to supply input, and none has been supplied.

**H1. Real engineer questions, double-labelled (P7.1).** `eval/real_questions_template.json` documents the format; `scripts/ingest_real_questions.py` reads `eval/real_questions.json` and accepts a question only when two different labellers each supplied a label. Gold is the clauses both share; both saying "no answer" makes an expected-refusal question (`real_oos`); anything else is a disagreement, reported for adjudication and not used. It reports exact-set agreement and Cohen's kappa on the answerable / no-answer decision (`reports/real_question_agreement.json`), rejects single-labeller items, unknown clause references and duplicates, and ignores `_example` items. `build_eval_set.py` reads the result as categories `real` and `real_oos`. Smoke-tested end to end with two invented items (both passed, then removed). Until a real file exists, the evaluation has no independent questions, and the blind-set numbers of §37.12 (which the author labelled while looking at the engine) remain the best estimate.

**H2. Reviewed synonyms (P7.3).** `scripts/apply_reviewed_synonyms.py` applies `eval/reviewed_synonyms.json` to `data/search/synonyms.json` only when each group has at least two phrases, a named reviewer, an existing evidence clause, at least one phrase found verbatim in the manuals, and is not a duplicate; a failing group blocks the whole batch. Accepted groups are recorded under `reviewed` with reviewer, reason and evidence. The regression check is the existing Gate P (`eval_retrieval.py --check` on the test split): a synonym that lowers retrieval fails the gate after the index is rebuilt. It is not automatic in the sense of learning from queries: `knowledge_gaps.json` still needs a person to propose the groups.

Test state: 19 gates, 199 pytest, 13 browser suites (browser suites not re-run this sprint, no browser code changed). 

**Next, and needs a person:** collect 50 to 100 real questions from engineers, have two people label them, run the intake, and then decide about embeddings (P5.2) from the resulting recall. Not done: condition extraction for measurements, measurement-to-graph edges, drawings (P3/P4).

### 37.17 Sprint I results (drawing identity and revision evidence, P3 start) — 2026-09-30

First drawing work, under the rule that the manuals are now proven enough to start. The 59 drawing PDFs are single-page raster scans with no text layer, so everything below rests on file names and OCR.

**I1. OCR of the sheets.** `scripts/ocr_drawings.py` (RapidOCR, page scaled to at most 3,000 pixels on the long side) writes `raw/drawing_ocr.jsonl` with every line, its confidence and its position (0 to 1 of the page), bound to the PDF hash. Like the manual OCR it is a committed artifact, not part of the byte-identical rebuild.

**I2. Registry.** `scripts/drawing_registry.py` writes `canonical/drawings_registry.jsonl`: per file, the drawing numbers stated in the file name (single, list or range endpoints, sub-sheets such as 6155/1, alteration marker ALT_n or ALT_NIL), the drawing numbers and dates read on the sheet, and checks that compare the two. Everything is `machine_extracted`. Results: 58 of 59 sheets show the number(s) stated in the file name (base number compared, so a wrong sub-sheet suffix would pass). The one that does not (`RDSO_T_3911 TO 3918`, a small sheet with a partial text layer) reads a different number (T-3002) and is left unconfirmed rather than forced. No file named ALT_NIL shows several dated revisions. Revision lineage: only T-6155 has several versions on disk (ALT_10, 12, 13); the newest by alteration number is also the one with the latest date read from the sheet (27-01-2025), so the two sources agree. Nothing else has more than one version, so the lineage feature is barely exercised.

**I3. Audit of the hand-made drawing catalogue (`data/rdso_drawing_catalog.json`).** 45 of 59 entries have a title that is just the file name ("RDSO Drawing Specification (file.pdf)"), so they carry no drawing information; 28 files cover several drawings (ranges or lists) but the catalogue gives each one number; the `key_highlights` free text has no source location and cannot be checked. The knowledge graph holds only 6 drawing nodes against 59 files. The catalogue should not be treated as evidence.

**I4. Gate T.** Every PDF has exactly one registry entry with the current hash, a parseable number, an OCR record for that hash, no ALT_NIL contradiction, and at least 55 sheets identity-confirmed. Tests: filename forms (ranges, lists, sub-sheets, the "RDSOT" typo, lower-case Alt), OCR zero-for-O tolerance, impossible dates, the two checks, and a negative test that removing an entry fails the gate. Test state: 20 gates (A to T), 205 pytest; browser suites not re-run (no browser code changed); rebuild deterministic.

**Not done (P3 remainder):** title-block fields (description, scale, rail section) are not extracted, because OCR returns the description block as jumbled fragments in non-reading order; notes, parts lists and dimensions with tolerances; highlighted evidence crops for drawings; revision comparison; turning the registry into graph nodes and linking drawings to manual clauses. Recommended next step for drawings: crop the title block by position and OCR it at higher resolution, then extract the alteration table row by row.

### 37.18 Sprint J results (title block and alteration table, P3.2 and P3.3) — 2026-09-30

`scripts/title_block.py` reads the fixed sheet layout from positioned OCR lines (page fractions, not reading order): the bottom row SPECIFICATION, SCALE, ALT:, DESCRIPTION, DATE and the drawing number; the alteration rows stacked above it (number, description, date); and the drawing description block above the number. It returns None for anything it cannot locate. The result sits in `title_block` of each registry record, all `machine_extracted`.

Measured on the 59 sheets (from `reports/drawing_registry_report.json`): a description was read for 58, a specification for 54, a scale for 46, and alteration rows for 23 sheets (28 rows). The 36 sheets without rows are mostly the older hand-lettered scans, where OCR reads handwriting poorly; that is a limit of the input, not something the code can fix.

**A real cross-check exists for alterations.** The highest alteration number read from the sheet's table must equal the ALT_n in the file name. It could be tested on 8 sheets (a legible number in the top row): 7 agree, 1 disagrees (`RDSO_T_6290_ALT_1`, where OCR read "80" from a hand-lettered scale, listed in the report for review). Small sample; it supports the file-name alteration numbers but does not prove them for the other 50 sheets.

**The hand-made catalogue disagrees with the sheets.** Of the 14 catalogue entries with a real title, the title read from the sheet matches the catalogue title closely (bigram overlap 0.9 or more) for 3, partly for 6 (paraphrase and OCR noise), and is different (below 0.6) for 5, for example a catalogue "Check Rail Arrangement and Chairs for 1 in 12 CMS Crossing" against a sheet reading "TIE PLATE FOR S.S.D FOR USE WITH (Zu-1-60) THICK-WEB SWITCH". Together with §37.17 (45 of 59 titles are file names) the catalogue should be considered unreliable and replaced by the registry.

Known weaknesses: the sheet description text keeps OCR damage (fused words such as "10125mmCURVEDSWITCHWITH", confusions such as 0 for O), so it is searchable evidence, not a clean title; a revision row whose number OCR missed has number None (a row between two read numbers that leave one free is not inferred, on purpose); some stamp text can leak into the description on unusual layouts. Sheets with several drawings (ranges) carry one title block, which describes only one of them.

Gate T now also requires 55 sheets with a description and 6 with a file-name/table alteration match. Tests use synthetic sheets (layout, missing anchors returning None, the alteration check). State: 20 gates, 208 pytest; browser suites not re-run (no browser code changed); rebuild deterministic.

**Not done (P3 remainder):** notes, parts lists and dimensions with tolerances; highlighted crops for drawing evidence; revision comparison (needs two versions of a sheet with legible tables: only T-6155 has them); graph nodes for drawings and links to manual clauses; replacing the hand-made catalogue and the 6 hand-made drawing nodes with registry-derived ones; a human transcription queue for the hand-lettered sheets.

### 37.19 Sprint K results (linking manual clauses to drawings, P3.6) — 2026-09-30

`scripts/drawing_links.py` finds drawing numbers cited in clause text (`RT-6154`, `RDSO/T-6155`, "drawing No. RDSO/T-1899") and marks each citation `SHEET_HELD` when a sheet in `drawings/` covers that number (a "6171 To 6173" file also covers 6172) or `NO_SHEET`. Output: `canonical/drawing_links.jsonl` (exact span per citation) and `reports/drawing_links_report.json`. Gate U checks every span against the clause text, every sheet against the registry, and status against coverage.

**Finding: the drawing collection barely overlaps what the manuals cite.** The manuals cite 103 distinct drawing numbers in 155 places; sheets exist for only 4 of them (6154, 6155, 6279, 6280, cited in IRPWM Paras 229 and 427), which involves 8 of the 59 sheet files. The other 51 sheets are cited by no manual clause, and 99 cited drawings are not in the collection (`cited_numbers_without_sheet`, a ready acquisition list). So a question that mixes a manual rule and a drawing can be answered for four drawings only; better drawing extraction will not change that, more drawings would.

Caveats: matching is by number only, and treating the `RT-` and `T-` prefixes as one series is an assumption not checked against an RDSO index; the citation pattern is tuned on this corpus (bare `T-nnnn` is accepted only outside reference-like contexts) and was not evaluated for recall; where several versions of a sheet exist (T-6155 has three) the link lists all of them and does not choose. The hand-made `data/rdso_drawing_catalog.json` is not used by the application (only by `scripts/analyze_rdso_drawing.py`, which produced it) and is superseded by the registry; it is kept for history and should not be cited. I did not replace the 6 hand-made drawing nodes in the graph: they feed the browser tests and the demo turnout scenes, and replacing them is a UI change of its own.

State: 21 gates (A to U), 213 pytest; browser suites not re-run (no browser code changed); rebuild deterministic.

**Next for drawings:** acquire the missing sheets (list above), notes and parts lists with dimensions, evidence crops on sheets, and registry-derived graph nodes once the UI can take them.

### 37.20 Sprint L results (surfacing the new data in the answer card) — 2026-09-30

Until now measurements (§37.13) and drawing links (§37.19) existed only as files. `scripts/build_clause_extras.py` writes a compact browser file `data/search/clause_extras.js` (490 clauses, 109 KB): up to 12 text-derived values per clause and the held drawing sheets cited by the clause. The answer card for a retrieved clause now shows, under the cited sentences, a collapsed "Values found in this provision (n, machine-extracted)" list (quantity label if one was assigned, comparator in words, value and unit, with the original wording quoted) and, when the provision cites a drawing we hold, links to the sheet PDF in `drawings/`. Table-derived values are not repeated there because their rows already reach the user as table rows.

What this does and does not give: only 490 of 1,172 clauses have any text value, and only 2 clauses (IRPWM Paras 229 and 427) link to drawings; the quantity label is right about 87% of the time (§37.13 audit) and 70% of values have none; the values are a reading aid next to the quoted sentences, not a replacement for them, which is why the original wording is always shown. Nothing in the answer text itself is generated from these values.

Checks: browser Test 7 (Para 522 shows values with the machine-extracted label; Para 229 shows working sheet links), and a pytest that every value in the browser file exists in `measurements.jsonl` with the same wording and unit and every linked file exists. `build_clause_extras.py` is in the rebuild chain. State: 21 gates, 214 pytest, 13 browser suites, all passing; rebuild deterministic.

**Still open:** condition extraction for measurements (so a value can say which speed band or component it applies to), measurement-to-graph edges, drawing notes and parts lists, registry-derived drawing nodes in the graph, real engineer questions with two labellers, embeddings decision.

### 37.21 Sprint M results (conditions attached to measurements) — 2026-09-30

`measurements.py` now records, for each value taken from clause text, the conditions named in the words around it (100 characters before, 60 after, never the value itself): rail section (52 kg, 60 kg, 60E1, 90/110 UTS), sleeper type, track geometry (straight, curve, turnout, crossing, switch, SEJ, bridge, tunnel, level crossing, running line ...), gauge, route class or zone, traffic, and, for a non-speed value, a speed value in the same sentence as `speed_band`. Fixed regular expressions, not understanding. 905 of 3,345 text values (27%) carry at least one condition; 2,440 carry none. Table cells carry no conditions yet (their row and column text would have to be parsed). Gate S checks the shape of the field; the browser card shows up to three of them as "near: ...".

Precision, by reading 30 random conditioned values (author-audited, not independent): about 25 of 30 carried conditions that are relevant to the value (for example "Curve" for a curve tolerance, "52 kg" and "PSC sleepers" for a formation depth, "bridges" for a refuge distance); errors are a verb read as a noun ("trains may approach" taken as track approach), a rail size taken as a condition when it was part of a table row unrelated to the value, and window spill in flattened tables. Missing conditions are more common than wrong ones: the qualifier often sits in a table column or an earlier sentence.

**Conflict candidates again, now with conditions:** pairs with the same manual, quantity, unit and comparator, and either the same non-empty condition set or overlapping subject words: 17 (9 by conditions, 8 by subject). Reading all 17: none is a real contradiction. The nine by conditions are curve-radius thresholds that belong to different purposes (track-recording tolerance bands in Para 520 to 525 versus pre-monsoon patrolling in Para 1112). **Conditions were not enough: what separates two limits is their purpose (what is being limited), which the extractor does not capture.** Consequence: no conflict flag is shown or planned from this data; a conflict feature needs a person reviewing pairs, and the candidate file is the queue for that.

State: 21 gates, 217 pytest, 13 browser suites, all passing; rebuild deterministic.

**Still open:** conditions for table cells, the purpose of a limit (needs a model or people), measurement-to-graph edges, drawing notes and parts lists, real engineer questions with two labellers, embeddings decision.

### 37.22 Sprint N results (human review workflow) — 2026-09-30

Every quality number in this document is still the author's own reading; nothing has ever been `reviewed` or `verified` by another person. Sprint N builds the way to change that with little effort from a reviewer.

**`scripts/make_review_packet.py`** writes one self-contained offline HTML file (images embedded, no server, no network): a seeded random sample of extracted items, shuffled, each shown with what was extracted, the exact span highlighted in the clause text, and the source page crop with the region drawn on it (table bounding box for tables). Kinds: clause (boundary and text), cross-reference, measurement, table, drawing link. The reviewer types a name, answers Correct, Wrong or Unsure (with a note), and downloads `decisions_<name>_s<seed>.json`. `--per-kind 10 --seed 1` gives 50 items (about 3 MB); the same seed given to two people lets their agreement be measured. A browser test (14th suite) checks the packet loads, shows images and highlights, and collects decisions.

**`scripts/ingest_reviews.py`** validates decision files (known target, matching kind, a named reviewer, no repeat by the same reviewer) and records them. Clause decisions go to `canonical/reviews.jsonl`, where the existing provenance policy (Gate M) applies: one approval gives `reviewed`, two distinct approvers give `verified`, any rejection gives `disputed`; the next rebuild applies it. Checked end to end with a throwaway decision (status changed to `reviewed`, Gate M passed), then removed. Decisions on other kinds go to `canonical/extractor_reviews.jsonl` and do not change any status. "Unsure" is counted, not recorded. `reports/review_accuracy.json` (rebuilt each time) gives, per kind, reviewed, correct, wrong, error rate with a 95% Wilson interval, and agreement between reviewers on items both saw. Because the sample is random, those error rates are honest estimates of each extractor, which the author-audited figures (measurement labels about 87%, conditions about 83%) are not.

Limits: decisions are trusted as typed (no identity check); a rejection of a clause marks the whole clause disputed without saying why beyond the note; extractor reviews measure accuracy but cannot yet correct data automatically. State: 21 gates, 222 pytest, 14 browser suites, all passing; the review report is empty because no packet has been reviewed yet.

**Action needed from people:** two engineers each complete a packet (50 items is about 30 to 60 minutes) and send back their decision files; `python scripts/ingest_reviews.py decisions_*.json` then `python scripts/rebuild_all.py`. This is the fastest route to independent accuracy numbers and to the first `reviewed` clauses.

---

## 38. Plan for Remaining Work (post P0-R.1/R.2)

**Ordering principle:** data truth first, then retrieval, then answers, then learning. Each work package (WP) is one small validated increment: it ends with a gate or test that fails before the change and passes after, a conventional commit, and an updated metrics file. Do not start a WP whose dependency is open.

### 38.1 Work packages

| WP | Title | Depends | Deliverable | Acceptance test (must fail today) |
|---|---|---|---|---|
| **P0-R.3 (DONE, §37.8)** | Provenance re-baseline | R.2 | Every non-drawing node/edge/evidence/requirement is `machine_extracted` unless a review record exists; remove false `raster_blueprint_crop_and_transcription`/confidence 1.0 stamps on text-derived facts; add `reviews.jsonl` (reviewer, date, decision) as the only path to `reviewed`/`verified`. | Gate M: no `verified` without a review record; no fact whose `extraction_method` contradicts its source type. |
| **P0-R.4 (DONE, §37.9)** | Evidence on every edge and clause | R.3 | Evidence record carries `page_number`, `bbox` (PyMuPDF word boxes), `page_sha256`, `source_pdf_sha256`; every edge lists `evidence_ids`. | Gate D extended: 0 edges without evidence (structural HAS_SECTION edges cite the heading evidence); every evidence page hash matches the PDF on disk. |
| **P0-R.5 (DONE, §37.9)** | Metrics as single truth | R.2 | `metrics.json` extended (short clauses, non-extractable pages, per-manual coverage); docs/UI read only it; a CI step diffs regenerated vs committed. | CI fails if committed metrics differ from regenerated. |
| **P0-R.6 (DONE, §37.10)** | Clause-boundary repair | R.2 | Extractor rewrite for paragraph bodies: numbering monotonic per chapter, reject values outside manual range (`PARA_5300`), drop header/annexure pseudo-clauses, join body until next valid paragraph; per-manual detected-vs-kept reconciliation report. Target: short clauses under 5%, IRPWM kept/detected above 90%. Benchmark against Docling result in `research/` before choosing the parser. | Gate L ratchet tightened stepwise; new gate for para-number monotonicity and range. |
| **P0-R.7 (DONE, §37.10)** | OCR for image-only pages | none | OCR (offline Tesseract or Docling) for the 64 pages without text; `extraction_method: ocr`, per-page confidence, low-confidence pages enter the review queue. | 0 pages with `is_extractable=false` and no OCR record. |
| **P0-R.8 (DONE, §37.9)** | Portable browser tests + CI | none | Env-driven Chrome path, headless flags, repo-relative artifacts; a `run_browser_tests.py`; CI job on all branches and PRs including browser tests; stop committing regenerated PNGs (upload as CI artifacts). | Fresh Linux CI runs the CDP suites green. |
| **P0-R.9 (DONE, §37.9)** | Repo hygiene | none | Untrack `__pycache__`, `index.html.bak`, `scratch/`; enforce conventional commits and one concern per commit; retire `docs/gemini/*` status claims (link to §37). | `git ls-files` contains none of those paths. |
| **P0-R.10 (DONE, §37.9)** | Bootstrap | none | `validate_all.py` checks/installs dependencies (or prints exact fix); dependency versions pinned. | Fresh clone: one command yields a green run. |
| **P1-R.1 (DONE, §37.10)** | Frontend reads canonical only | R.2 | Remove `RDSO_MANUALS_KNOWLEDGE` reads from `index.html`; provision cards use canonical `text`/`page`/`evidence_ids`; drop the derived legacy view once unused. | Test: card text equals canonical node text; grep gate for `RDSO_MANUALS_KNOWLEDGE` = 0. |
| **P1-R.2 (PARTIAL, §37.10)** | Honest P1 sign-off | R.6 | Tick the pilot checklist (§28) for IRPWM with evidence links; only then scale to other manuals. | Every checklist line has a reproducible command or test. |
| **P2.1 (DONE, §37.11)** | Cross-reference extraction and resolution | R.6 | Extract "Para N", "Annexure", "Chapter", "Rule", external IS/IRS/RDSO refs (~640 in IRPWM); classify `RESOLVED / AMBIGUOUS / EXTERNAL / NOT_FOUND`; edges `REFERENCES` with evidence; broken-reference report. | Every reference in the raw text is classified; 0 unclassified; resolved targets exist. |
| **P2.2 (PARTIAL, §37.11)** | Source highlighting | R.4 | Render page image with evidence `bbox` highlight (PyMuPDF, offline); UI opens the highlighted region, not just the page. | Test opens a clause and finds the highlighted rect over the quoted words. |
| **P2.3** | Measurement and requirement facts | R.6 | Structured `Measurement {subject, quantity, comparator, value, unit, applies_to, clause_id, evidence}` replacing bare tolerance nodes; requirement priority from modal verbs ("shall/should/may") with reviewed overrides. | Every tolerance has a subject and comparator; sample of 100 reviewed with at least 95% precision. |
| **P5.1 (DONE as BM25, §37.11)** | Offline retrieval core | R.6 | SQLite FTS5 (BM25) over clause text and headings in a single `.db` served with the app; identifier and para-number exact match; abbreviation/synonym dictionary (SSE/P.Way, CMS, USFD, ...); filters by manual/chapter/type/edition. | Retrieval eval set (below): Recall@5 at least 0.85 on keyword and identifier queries. |
| **P5.2** | Semantic layer | P5.1 | Small local embedding model (quantised, CPU) with an ANN index built offline; hybrid score = BM25 + vector + graph proximity; cross-encoder re-rank optional. Model file versioned and hashed. | Recall@5 at least 0.90 on natural-language set; no network calls (test blocks sockets). |
| **P6.1 (PARTIAL, §37.12)** | Grounded answers | P5.1 | Extractive answer builder: top evidence spans, quoted with citation (manual, para, page, evidence id); confidence from retrieval scores and agreement; explicit "insufficient evidence" refusal below threshold; conflict/applicability flags. Replace the 13 hand-written answers and their hard-coded confidences; keep them as regression questions. | 0 answers without a citation; refusal correct on the out-of-corpus set; every quoted span verifiable in the source text. |
| **P6.2** | Optional local LLM | P6.1 | Optional offline small LLM (llama.cpp class) only to rephrase extractive answers; output checked by a citation verifier that rejects any sentence not supported by retrieved spans. | Verifier rejects seeded hallucinations in tests. |
| **P7.1 (STARTED, §37.11)** | Evaluation harness | P5.1 | `eval/questions.jsonl` (start 150: 60 keyword, 40 natural-language, 20 identifier, 15 conflict/revision, 15 out-of-scope), each with gold clause ids and page; `scripts/eval_retrieval.py` prints Recall@k, MRR, refusal precision; results tracked per commit; regression gate. | Metrics file changes are diffed in CI; drops beyond tolerance fail the build. |
| **P7.2 (DONE, §37.12)** | Local feedback capture | P6.1 | Opt-in local log (IndexedDB/JSONL): query, results shown, clicked evidence, thumbs up/down, "wrong page" flag; never leaves the machine; exportable. | Log records round-trip; schema validated. |
| **P7.3 (PARTIAL, §37.12)** | Self-improvement loop | P7.1, P7.2 | Nightly/on-demand job: (a) zero-result and low-confidence queries into `review_queue`; (b) suggested synonyms/aliases from co-clicked queries, applied only after reviewer approval; (c) accepted corrections become new eval questions; (d) re-index and re-run eval, refusing to publish if metrics regress. Dashboard of knowledge gaps per manual/chapter. | An accepted correction changes the answer to that query, and the eval gate stays green. |
| **P7.4** | Learning content from evidence | P6.1 | Flashcards/quizzes generated only from cited clauses, stored with their clause ids; remove hand-authored quiz facts not traceable to a clause. | Every card links to a clause id and page. |
| **P3 / P4** | Drawings and engineering graph | P2.3 | As specified in §26; do not begin until manuals are proven. | Per §26 exit criteria. |
| **Scale** | Roll out to remaining manuals | P1-R.2, P2.1 | Apply pipeline to USFD, AT Weld, FBW, TMM, STMM one at a time using the IRPWM acceptance checklist. | Same checklist per manual. |

### 38.2 Recommended sequence and effort (relative)

1. **Sprint A, data truth:** R.3, R.4, R.5, R.10, R.9, R.8 (small each; R.4 is the largest).
2. **Sprint B, extraction quality:** R.6 (largest risk; benchmark Docling vs current parser first), R.7, P1-R.1, P1-R.2.
3. **Sprint C, retrieval:** P7.1 eval set first (so improvements are measurable), then P5.1, then P2.1 and P2.2 in parallel.
4. **Sprint D, answers:** P6.1, P2.3, then P5.2.
5. **Sprint E, self-improvement:** P7.2, P7.3, P7.4, then optional P6.2.
6. **Then** scale to the other five manuals, and only after that P3/P4.

### 38.3 Evaluation set design (needed before retrieval work)

- Source questions from real usage: senior engineers' typical queries (limits, intervals, who is responsible, procedure for X, difference between revisions), plus queries mined from the manuals' own headings.
- Each item: question, gold clause ids, acceptable pages, category, expected behaviour (`answer` or `refuse`).
- Keep the 13 existing hand-written Q&A items and the browser test questions as the first entries.
- Two-person review of gold labels; inter-reviewer disagreement is itself logged as a gap.

### 38.4 Risks and mitigations

| Risk | Mitigation |
|---|---|
| Extractor rewrite (R.6) changes clause ids, breaking links | Keep an id-alias map (`identity_aliases.json`); Gate B already audits references; migrate in one commit with the map. |
| Machine-extracted text is wrong on safety limits | Priority review queue for any clause containing numbers with units and "shall/mandatory"; answers show the extraction/review state. |
| OCR errors in scanned pages | Store confidence; show "OCR" badge; exclude low-confidence spans from extractive answers. |
| Offline embedding model size on low-end PCs | Ship BM25 only as the default; embeddings optional; measure on a low-spec machine. |
| Scope creep into an LLM before retrieval quality is proven | §34 guardrail: P6.2 is blocked until the P7.1 metrics meet target. |
| Agents overwrite each other's status docs | Status lives only in §37/§38 and `metrics.json`; other logs are non-authoritative. |

### 38.5 Definition of done for the product goal

An engineer can type a natural-language question offline and receive, in under 2 seconds on a modest laptop, an answer composed of quoted source spans with manual/paragraph/page citations that open on a highlighted region; weak or conflicting evidence is stated, not hidden; every wrong or missing answer reported by users becomes a reviewed correction and a permanent regression question; and all published metrics come from one generated file that CI recomputes.


### 38.6 Notes from P0-R.3

- The 13 hand-written QA answers and the UI still show hard-coded `VERIFIED`/0.99 badges (`CANONICAL_QA_DATABASE`). They are not canonical data, so Gate M cannot see them; they are replaced by computed confidence and review state in P6.1 and must not be presented as reviewed before then.
- Drawing-derived nodes (transcribed from crops) were downgraded too: no drawing fact has a human review record either. The review queue should start with safety-relevant numeric limits and the pilot drawings.
- `scripts/build_canonical_pipeline.py` is deprecated (it would re-stamp everything `verified`); `unify_manual_canonical.py` is the generator until the P0-R.6 extractor rewrite replaces its input.

### 38.7 Revised order after Sprint C

1. **Independent evaluation first (P7.1 completion).** Collect 100+ real questions from engineers (not derived from clause text), have a second reviewer label gold clauses, and report them as a separate `real` category. Decide on the semantic layer (P5.2) only after this set shows where BM25 fails; the informal probe suggests misses come from paraphrase, tables and poor titles.
2. **Retrieval quality fixes that need no model:** repair clause titles for decimal manuals (done, Sprint F1), ~~index table rows as structured records~~ (done, Sprint E1; row-aware answers Sprint F3, proforma tables still indexed), add reviewed synonyms from the misses. Re-measure on the independent set.
3. **Grounded answers (P6.1):** promote the extractive card to the only answer path, retire the 13 curated answers into regression questions (they still show hard-coded `VERIFIED`), add sentence-level extraction of the answering span with per-claim citation, conflict and revision flags, and a refusal rule tuned on the independent set.
4. **Feedback loop (P7.2, P7.3):** local log of queries, clicks and thumbs; zero-result and low-coverage queries into the review queue; accepted corrections become eval questions.
5. **Then** P5.2 (embeddings, only if step 1 justifies it), ~~table extraction, P2.3 measurements~~ (done, Sprint E), and rolling the remaining checks to drawings.
