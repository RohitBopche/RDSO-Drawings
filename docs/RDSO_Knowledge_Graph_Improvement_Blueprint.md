# RDSO Drawings — Knowledge Graph Improvement Blueprint

## Purpose
Evolve RDSO-Drawings from a visual PDF/graph explorer into an offline-first, evidence-backed, revision-aware engineering knowledge system.

## Product goals
- Find the correct drawing and applicable revision.
- Understand components, dimensions, tolerances, notes, standards and BOMs.
- Compare revisions and explain what/why changed.
- Trace dependencies, interfaces, failure modes, inspections and maintenance.
- Open source evidence for every important fact.
- Power graph, search, 2D/3D, field, reporting, learning and AI from one knowledge core.

## Product pillars
1. Canonical engineering knowledge
2. Evidence and provenance
3. Graph intelligence
4. Engineering workflows
5. Learning and training
6. Visualization and digital twin

Priority: canonical knowledge → provenance → graph intelligence → workflows → learning/AI → advanced visualization.

## Target architecture
```text
Original PDFs/images/manuals
        ↓
Ingestion: PyMuPDF + OCR + table/title-block/region extraction
        ↓
Intermediate data: raw text, crops, facts, confidence, provenance
        ↓
Canonical Knowledge Core: entities, facts, edges, revisions, constraints
        ↓
Search/Retrieval + Graph Queries + Validation
        ↓
Application/API
        ├─ Knowledge Graph / Evidence Viewer
        ├─ Revision, inspection, procurement and failure workflows
        ├─ Learning system
        └─ 2D/3D digital twin and AI Copilot
```

## Technology direction
- Python for ingestion and validation.
- PyMuPDF for PDF processing; local OCR fallback.
- JSON Schema for contracts and validation.
- SQLite initially or PostgreSQL + JSONB for growth.
- pgvector for semantic retrieval when needed.
- Three.js for graph/digital-twin visualization.
- TypeScript/JavaScript modules for frontend modularization.
- JSON-LD/Cypher export for interoperability.
- Local filesystem/object storage for source files and crops.
- Introduce Neo4j only when graph traversal/algorithms become a demonstrated bottleneck.

## Canonical entity types
`DOCUMENT`, `DRAWING`, `REVISION`, `COMPONENT`, `SUBASSEMBLY`, `ASSEMBLY`, `RAIL`, `TONGUE_RAIL`, `STOCK_RAIL`, `SLEEPER`, `FASTENER`, `TIE_BAR`, `SLIDE_CHAIR`, `POINT_MACHINE`, `LOCKING_DEVICE`, `DIMENSION`, `TOLERANCE`, `MATERIAL`, `STANDARD`, `SPECIFICATION`, `NOTE`, `BOM_ITEM`, `SPARE_PART`, `INTERFACE`, `CONSTRAINT`, `FAILURE_MODE`, `HAZARD`, `INSPECTION`, `MAINTENANCE_ACTION`, `SOP`, `FIELD_OBSERVATION`, `LOCATION`, `EQUIPMENT`.

Entity types must be configuration-driven, not hard-coded in UI logic.

## Relationship vocabulary
`HAS_REVISION`, `SUPERSEDES`, `PRECEDES`, `REFERENCES`, `GOVERNS`, `SPECIFIES`, `CONTAINS`, `HAS_NOTE`, `HAS_DIMENSION`, `HAS_TOLERANCE`, `HAS_BOM_ITEM`, `HAS_SPARE`, `PART_OF`, `ASSEMBLED_FROM`, `INSTALLED_ON`, `FASTENED_BY`, `INTERFACES_WITH`, `CONNECTED_TO`, `OPERATED_BY`, `CONTROLLED_BY`, `REQUIRES`, `INSPECTED_BY`, `MAINTAINED_BY`, `HAS_FAILURE_MODE`, `CAN_CAUSE`, `MITIGATED_BY`, `APPLIES_TO`, `DERIVED_FROM`, `SUPPORTED_BY`, `CONFLICTS_WITH`, `VALID_DURING`, `MODIFIED_IN`, `INTRODUCED_IN`, `REMOVED_IN`.

## Engineering fact model
Important facts must be first-class, source-linked objects:

```json
{
  "id": "fact-example",
  "subject_id": "component-example",
  "predicate": "HAS_DIMENSION",
  "value": {"number": 222, "unit": "mm"},
  "source": {
    "drawing_id": "RDSO/T-6155",
    "revision": "ALT_12",
    "page": 1,
    "region": "DETAIL_B",
    "source_file": "drawing.pdf"
  },
  "confidence": 0.98,
  "status": "VERIFIED",
  "extraction_method": "manual_review",
  "created_at": "2025-01-01T00:00:00Z"
}
```

Supported statuses: `EXTRACTED`, `VERIFIED`, `DERIVED`, `INFERRED`, `CONFLICTING`, `REJECTED`, `UNKNOWN`.

Never present inferred or unverified facts as official requirements.

## Provenance and evidence
Every important fact should link to:
- source document and stable file hash;
- drawing number and revision;
- page and region/crop;
- extraction method and timestamp;
- confidence and verification status;
- reviewer and review history where applicable.

Provide an evidence viewer, source crop opening, evidence cards and citation links in UI/AI answers.

## Ingestion improvements
- Separate raw, intermediate and canonical data.
- Use configuration-driven drawing families.
- Extract title blocks, revision tables, notes, dimensions and BOMs.
- Use OCR only as a fallback and retain OCR confidence.
- Track source regions instead of relying only on fixed coordinates.
- Log extraction decisions and failures.
- Add a human review queue for uncertain or safety-relevant facts.

## Revision intelligence
Represent revision lineage explicitly with `HAS_REVISION`, `SUPERSEDES`, `VALID_DURING`, `MODIFIED_IN`, `INTRODUCED_IN` and `REMOVED_IN`.

Revision comparison should combine:
1. visual diff;
2. text diff;
3. structured engineering diff;
4. graph/dependency diff;
5. impact summary;
6. “Why was this changed?” evidence when available.

## Graph intelligence
Provide semantic modes rather than one graph view:
- Explore
- Revision impact
- Dependency trace
- Failure analysis
- Procurement/BOM
- Field inspection
- Learning

Add typed edges, hop expansion, filters, path queries, conflict detection, “Explain This Node” and “Question → Graph”.

## Engineering workflows
Build task-oriented flows for:
- Engineering Answer Cards
- drawing/revision lookup
- dependency and interface tracing
- BOM comparison and spare calculation
- failure-mode investigation
- inspection checklists
- maintenance actions
- field-oriented component identification
- engineering report export

Answer Cards should show summary, applicability, critical parameters, related components, risks/actions and source evidence.

## Search and AI
Use hybrid retrieval:
- keyword search;
- semantic embeddings;
- metadata filters;
- graph traversal;
- source/evidence ranking.

AI Copilot capabilities:
- Ask the Graph
- Explain This Node
- Why Was This Changed?
- source-backed summaries
- conflict-aware answers
- explicit uncertainty and citations

AI must retrieve from the canonical graph and original evidence; it must not invent engineering requirements.

## UI architecture
Replace the monolithic `index.html` with modular areas such as:
```text
src/
  app/
  graph/
  ontology/
  knowledge/
  evidence/
  revisions/
  workflows/
  learning/
  twin/
  ui/
```

Use a task-oriented home screen: Explore Drawing, Compare Revisions, Trace Component, Investigate Failure, Calculate Spares, Learn Component, Field Inspection.

Keep the immersive/cosmic graph as an optional mode. Add a technical mode with readable labels, engineering annotations and evidence-first panels. Make the right drawer contextual to the selected node/fact.

## Learning system
- Learn a Drawing
- Learn a Component
- concept graph
- lessons and explanations
- quizzes and flashcards
- spaced repetition
- weak-topic dashboard
- revision-aware practice

## Digital twin
Synchronize graph ↔ geometry ↔ drawing ↔ dimensions ↔ BOM ↔ failure/inspection. Add technical orthographic mode, exploded views, revision overlays and component-to-source navigation.

## Data quality and validation
Add:
- JSON Schema validation;
- stable IDs and controlled vocabularies;
- duplicate detection;
- broken-reference checks;
- unit and dimension validation;
- revision consistency checks;
- contradictory-fact/conflict detection;
- extraction regression fixtures;
- quality scoring and review queues.

## Security, reliability and offline-first
Offline functionality should include drawing browsing, search, graph navigation, source viewing, learning, revision comparison and local reports. Cloud sync, remote AI and collaboration remain optional. Preserve original files, use hashes, maintain audit logs and make uncertain/safety-relevant data require human review.

## Roadmap
### Phase 0 — Baseline
Inventory PDFs, drawing families, data sources, duplicates and current features. Freeze a known-good baseline and add reproducible setup/tests.

### Phase 1 — Knowledge Core v1
Define ontology, JSON Schema, entities, relationships, facts, provenance and revisions. Separate raw/intermediate/canonical data and build a validation CLI.

### Phase 2 — Ingestion v2
Refactor extraction, add title-block/OCR/table/region tracking, logs, confidence, statuses and review queues.

### Phase 3 — Evidence and Revision Intelligence
Build source viewer, crops, revision timeline, visual/text/structured/graph diff, conflict dashboard and evidence cards.

### Phase 4 — Graph Intelligence
Implement typed graph, semantic modes, filters, dependency trace, revision impact and question-to-graph.

### Phase 5 — Engineering Workflows
Add procurement, BOM comparison, spare calculation, failure analysis, inspection mode, field view and report export.

### Phase 6 — Learning
Add drawing/component lessons, quizzes, flashcards, spaced repetition and weak-topic analytics.

### Phase 7 — AI Copilot
Add graph-aware retrieval, source-grounded generation, citations, uncertainty and conflict-aware answers.

### Phase 8 — Digital Twin
Synchronize graph and 3D twin, add technical views, revision overlays, exploded views and performance optimization.

## First 30 days
### Week 1
Create architecture, ontology and data-model docs. Define entity/relationship/fact/provenance schemas. Select 5–10 representative drawings.

### Week 2
Create drawing inventory, raw/intermediate/canonical folders, canonical JSON output, schema validation and extraction tests.

### Week 3
Add source references, evidence panel, drawing/revision/page display, crop opening, revision model and verified/unverified badges.

### Week 4
Add typed graph nodes/edges, filters, dependency mode, revision impact mode, Explain This Node and basic question-to-graph.

## First 10 implementation priorities
1. Canonical engineering schema
2. Provenance for every fact
3. Latest revision and supersession tracking
4. Engineering Answer Cards
5. Revision comparison
6. Typed graph relationships
7. Dependency trace
8. Conflict detection
9. Explain This Node
10. Learn This Drawing/Component

## Definition of Done — Knowledge Core v1
- Every drawing has a stable ID.
- Every revision has a structured record.
- Important facts have provenance, status and confidence.
- Entities and relationships use controlled vocabularies.
- Canonical data passes validation.
- Source crops open from facts.
- Revision lineage is queryable.
- Conflicts can be recorded.
- Frontend does not own the canonical dataset.
- Ingestion is reproducible.
- Representative tests exist.
- Graph, search, learning and reports use the same knowledge core.

## Principles
1. Evidence before explanation.
2. Canonical data before visualization.
3. Source facts before AI inference.
4. Revision awareness everywhere.
5. Make uncertainty visible.
6. Engineering workflows over decorative complexity.
7. Offline-first by default.
8. Modular architecture over monolithic files.
9. Human review for uncertain or safety-relevant facts.
10. One knowledge core, many interfaces.

## Milestone
**Knowledge Core v1 = canonical schema + provenance + typed relationships + revision lineage + validation + evidence-backed queries.**

Build the reliable, traceable and reusable knowledge core first; then use it to power the Knowledge Graph, Search, AI Copilot, Revision Intelligence, Procurement, Failure Analysis, Field Inspection, Learning and Digital Twin.
