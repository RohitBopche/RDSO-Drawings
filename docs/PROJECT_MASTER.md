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
| **P2.1** | Cross-reference extraction and resolution | R.6 | Extract "Para N", "Annexure", "Chapter", "Rule", external IS/IRS/RDSO refs (~640 in IRPWM); classify `RESOLVED / AMBIGUOUS / EXTERNAL / NOT_FOUND`; edges `REFERENCES` with evidence; broken-reference report. | Every reference in the raw text is classified; 0 unclassified; resolved targets exist. |
| **P2.2** | Source highlighting | R.4 | Render page image with evidence `bbox` highlight (PyMuPDF, offline); UI opens the highlighted region, not just the page. | Test opens a clause and finds the highlighted rect over the quoted words. |
| **P2.3** | Measurement and requirement facts | R.6 | Structured `Measurement {subject, quantity, comparator, value, unit, applies_to, clause_id, evidence}` replacing bare tolerance nodes; requirement priority from modal verbs ("shall/should/may") with reviewed overrides. | Every tolerance has a subject and comparator; sample of 100 reviewed with at least 95% precision. |
| **P5.1** | Offline retrieval core | R.6 | SQLite FTS5 (BM25) over clause text and headings in a single `.db` served with the app; identifier and para-number exact match; abbreviation/synonym dictionary (SSE/P.Way, CMS, USFD, ...); filters by manual/chapter/type/edition. | Retrieval eval set (below): Recall@5 at least 0.85 on keyword and identifier queries. |
| **P5.2** | Semantic layer | P5.1 | Small local embedding model (quantised, CPU) with an ANN index built offline; hybrid score = BM25 + vector + graph proximity; cross-encoder re-rank optional. Model file versioned and hashed. | Recall@5 at least 0.90 on natural-language set; no network calls (test blocks sockets). |
| **P6.1** | Grounded answers | P5.1 | Extractive answer builder: top evidence spans, quoted with citation (manual, para, page, evidence id); confidence from retrieval scores and agreement; explicit "insufficient evidence" refusal below threshold; conflict/applicability flags. Replace the 13 hand-written answers and their hard-coded confidences; keep them as regression questions. | 0 answers without a citation; refusal correct on the out-of-corpus set; every quoted span verifiable in the source text. |
| **P6.2** | Optional local LLM | P6.1 | Optional offline small LLM (llama.cpp class) only to rephrase extractive answers; output checked by a citation verifier that rejects any sentence not supported by retrieved spans. | Verifier rejects seeded hallucinations in tests. |
| **P7.1** | Evaluation harness | P5.1 | `eval/questions.jsonl` (start 150: 60 keyword, 40 natural-language, 20 identifier, 15 conflict/revision, 15 out-of-scope), each with gold clause ids and page; `scripts/eval_retrieval.py` prints Recall@k, MRR, refusal precision; results tracked per commit; regression gate. | Metrics file changes are diffed in CI; drops beyond tolerance fail the build. |
| **P7.2** | Local feedback capture | P6.1 | Opt-in local log (IndexedDB/JSONL): query, results shown, clicked evidence, thumbs up/down, "wrong page" flag; never leaves the machine; exportable. | Log records round-trip; schema validated. |
| **P7.3** | Self-improvement loop | P7.1, P7.2 | Nightly/on-demand job: (a) zero-result and low-confidence queries into `review_queue`; (b) suggested synonyms/aliases from co-clicked queries, applied only after reviewer approval; (c) accepted corrections become new eval questions; (d) re-index and re-run eval, refusing to publish if metrics regress. Dashboard of knowledge gaps per manual/chapter. | An accepted correction changes the answer to that query, and the eval gate stays green. |
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
