# Complete Manuals Knowledge Graph Plan

## 1. Objective

Build a complete, traceable, maintainable knowledge graph from every RDSO manual and drawing document in the repository. The graph must preserve the source meaning, engineering constraints, terminology, relationships, revisions, applicability, and evidence needed to answer technical questions without losing context.

## 2. Scope

Include all manuals, specifications, standards, instructions, drawings, annexures, tables, figures, notes, references, revision histories, and linked documents available in the repository.

The graph should cover:

- Document identity, title, number, revision, date, issuing authority, and status
- Sections, clauses, subclauses, paragraphs, notes, warnings, tables, figures, and annexures
- Components, assemblies, systems, materials, dimensions, tolerances, loads, forces, limits, grades, and units
- Installation, inspection, testing, maintenance, troubleshooting, acceptance, rejection, and safety procedures
- Design requirements, mandatory rules, recommendations, exceptions, dependencies, and applicability conditions
- Cross-document references and supersession relationships
- Drawing geometry, callouts, part numbers, bills of materials, dimensions, symbols, and tolerances
- Terminology, abbreviations, synonyms, identifiers, and domain concepts
- Provenance for every extracted fact

## 3. Guiding principles

1. **Source fidelity:** never paraphrase away a requirement, exception, qualifier, unit, or condition.
2. **Traceability:** every node and relationship must point to a document, page, section, table, figure, or drawing region.
3. **Revision awareness:** preserve historical versions and identify the currently applicable version only when supported by source evidence.
4. **Separation of fact and interpretation:** store extracted statements separately from derived classifications and engineering interpretations.
5. **No silent conflict resolution:** conflicting requirements must be represented, flagged, and reviewed.
6. **Deterministic rebuilds:** extraction and transformation should be repeatable from the source files.
7. **Human review for high-risk content:** safety, limits, tolerances, acceptance criteria, and legal/standards obligations require validation.
8. **Offline-first operation:** the repository should support local processing and querying without dependence on external services.

## 4. End-to-end workflow

### Phase A — Inventory and source registration

1. Enumerate every manual and drawing file recursively.
2. Compute a SHA-256 checksum for each source file.
3. Record file name, path, MIME type, size, checksum, detected language, and ingestion timestamp.
4. Detect duplicates and near-duplicates.
5. Identify document families, revisions, superseded files, and likely companion documents.
6. Create a source registry before extracting content.

**Deliverable:** `data/knowledge-graph/raw/source_registry.jsonl`

### Phase B — Document conversion and segmentation

1. Extract text from searchable PDFs.
2. OCR scanned pages at page level, retaining OCR confidence.
3. Extract page images for visual verification.
4. Detect headings, clauses, lists, notes, warnings, tables, figures, annexures, and references.
5. Preserve page numbers and source coordinates.
6. Segment content into stable addressable units:
   - document
   - revision
   - page
   - section
   - clause
   - paragraph
   - table
   - table row/cell
   - figure
   - drawing view
   - callout
   - annexure

**Deliverable:** normalized page and block records with provenance.

### Phase C — Structural and semantic extraction

Extract the following entities and attributes.

#### Document entities

- `Document`
- `DocumentRevision`
- `IssuingAuthority`
- `DocumentType`
- `RevisionEvent`
- `ApplicabilityScope`
- `ReferencedDocument`

#### Engineering entities

- `System`
- `Assembly`
- `Component`
- `Part`
- `Material`
- `Fastener`
- `Tool`
- `Equipment`
- `Geometry`
- `Dimension`
- `Tolerance`
- `Load`
- `Force`
- `Pressure`
- `Temperature`
- `Speed`
- `Clearance`
- `Grade`
- `SurfaceTreatment`
- `WeldingOrJoiningMethod`
- `InspectionCharacteristic`
- `Test`
- `AcceptanceCriterion`
- `FailureMode`
- `Hazard`
- `SafetyControl`

#### Knowledge entities

- `Requirement`
- `Procedure`
- `Step`
- `Condition`
- `Exception`
- `Recommendation`
- `Warning`
- `Note`
- `Definition`
- `Abbreviation`
- `Symbol`
- `Formula`
- `Unit`
- `StandardReference`
- `QuestionAnswerEvidence`

### Phase D — Relationship extraction

Capture explicit and carefully derived relationships, including:

- `CONTAINS`
- `HAS_REVISION`
- `SUPERSEDES`
- `REFERENCES`
- `APPLIES_TO`
- `PART_OF`
- `ASSEMBLES_WITH`
- `MADE_OF`
- `CONNECTED_TO`
- `HAS_DIMENSION`
- `HAS_TOLERANCE`
- `HAS_LIMIT`
- `REQUIRES`
- `PROHIBITS`
- `RECOMMENDS`
- `CONDITIONED_BY`
- `EXCEPTION_TO`
- `VERIFIED_BY`
- `INSPECTED_BY`
- `TESTED_BY`
- `ACCEPTED_IF`
- `REJECTED_IF`
- `FAILS_WHEN`
- `MITIGATED_BY`
- `DEFINED_AS`
- `SYNONYM_OF`
- `SYMBOLIZES`
- `DERIVED_FROM`
- `SUPPORTED_BY`
- `CONFLICTS_WITH`
- `UNCERTAIN_ABOUT`

Every relationship must include provenance, confidence, extraction method, and reviewer status.

### Phase E — Numeric, unit, and constraint normalization

1. Normalize units while preserving the original expression.
2. Store both raw and canonical numeric values.
3. Preserve inequality semantics: `<`, `≤`, `=`, `≥`, `>`, ranges, approximate values, and conditional limits.
4. Distinguish nominal dimensions from tolerances and inspection limits.
5. Detect inconsistent units and impossible conversions.
6. Preserve significant figures and stated precision.
7. Store formulas with variables, definitions, units, and source location.
8. Never merge values that differ by revision, applicability, component variant, or condition.

### Phase F — Drawing-specific extraction

For drawings, extract and link:

- Drawing number and revision
- Sheet and view identifiers
- Part numbers and item numbers
- Bill of materials rows
- Dimensions and tolerances
- Datum references
- Geometric tolerancing and surface-finish symbols
- Weld, bolt, thread, and joining callouts
- Material and treatment specifications
- Notes and manufacturing instructions
- Assembly hierarchy
- Cross-referenced drawings
- Visual regions supporting each extracted fact

Use image/OCR review for every low-confidence callout and for all safety-critical or manufacturing-critical values.

### Phase G — Canonical graph construction

Create a canonical graph in layers:

1. **Raw layer:** immutable source files, page images, OCR, and extracted blocks.
2. **Intermediate layer:** candidate entities, candidate relationships, normalized values, and extraction confidence.
3. **Canonical layer:** reviewed entities and relationships with stable IDs.
4. **Export layer:** graph formats for application use, search, analytics, and QA.

Recommended stable identifiers:

- `DOC:<document-number>:<revision>`
- `PAGE:<document-id>:<page-number>`
- `CLAUSE:<document-id>:<section-path>`
- `COMP:<normalized-name>:<variant>`
- `REQ:<document-id>:<clause-id>:<ordinal>`
- `REL:<source-id>:<predicate>:<target-id>`

Do not use display names as primary keys.

## 5. Required data model

Each node should support:

```json
{
  "id": "REQ:example",
  "type": "Requirement",
  "label": "Example requirement",
  "properties": {},
  "source": {
    "document_id": "DOC:example",
    "file_path": "manuals/example.pdf",
    "revision": "A",
    "page": 12,
    "section": "4.2",
    "region": null,
    "quote": "Exact source wording",
    "checksum": "sha256:..."
  },
  "confidence": 0.98,
  "review_status": "pending"
}
```

Each edge should support:

```json
{
  "id": "REL:source:predicate:target",
  "source": "COMP:one",
  "predicate": "HAS_TOLERANCE",
  "target": "TOL:one",
  "properties": {
    "condition": "when installed",
    "applicability": "variant A"
  },
  "source": {
    "document_id": "DOC:example",
    "page": 12,
    "section": "4.2"
  },
  "confidence": 0.95,
  "review_status": "pending"
}
```

## 6. Quality assurance gates

### Automated checks

- All source files are registered and checksummed.
- Every extracted fact has provenance.
- Every edge points to existing nodes.
- No duplicate canonical IDs.
- Units are recognized or explicitly flagged.
- Numeric constraints are parseable.
- Page and section references are valid.
- Revision relationships are internally consistent.
- No orphan requirements, components, or documents without a review status.
- Source text and canonical values remain linked.
- Re-running the pipeline produces deterministic output.

### Human review queues

Prioritize manual review for:

1. Safety warnings and prohibited actions
2. Load, force, pressure, temperature, speed, and clearance limits
3. Acceptance/rejection criteria
4. Tolerances and critical dimensions
5. OCR confidence below threshold
6. Conflicting requirements
7. Ambiguous references and supersession claims
8. Drawing callouts and symbols
9. Tables with merged cells or complex formatting
10. Any derived relationship not explicitly stated in the source

## 7. Search and application capabilities

The final graph should support:

- Exact phrase and full-text search
- Search by document number, component, part number, clause, revision, and drawing number
- “Where is this specified?” evidence lookup
- Requirement and constraint lookup with units and conditions
- Component-to-drawing and component-to-manual navigation
- Procedure step-by-step views
- Revision comparison and change impact analysis
- Cross-document dependency traversal
- Conflict and ambiguity reports
- Evidence-backed question answering
- Offline export for the existing web application

## 8. Recommended repository outputs

```text
data/knowledge-graph/
├── raw/
│   ├── source_registry.jsonl
│   ├── extracted_pages.jsonl
│   ├── ocr_blocks.jsonl
│   └── page_images/
├── intermediate/
│   ├── candidate_entities.jsonl
│   ├── candidate_relationships.jsonl
│   ├── normalized_measurements.jsonl
│   └── review_queue.jsonl
├── canonical/
│   ├── nodes.jsonl
│   ├── edges.jsonl
│   ├── documents.jsonl
│   ├── requirements.jsonl
│   ├── components.jsonl
│   └── procedures.jsonl
├── exports/
│   ├── graph.json
│   ├── graph.graphml
│   ├── search_index.json
│   └── application_dataset.json
└── schemas/
    ├── node.schema.json
    ├── edge.schema.json
    └── source.schema.json
```

## 9. Implementation sequence

1. Inventory all manuals and drawings.
2. Build source registry and duplicate detector.
3. Implement PDF text extraction and OCR fallback.
4. Implement page/block segmentation with provenance.
5. Implement table, figure, and drawing-region extraction.
6. Implement entity and relationship candidate extraction.
7. Implement unit, numeric, and constraint normalization.
8. Implement revision and cross-reference resolution.
9. Create canonical IDs and graph exports.
10. Add automated validation and review queues.
11. Run human review on high-risk facts.
12. Integrate graph search and evidence navigation into `index.html`.
13. Run offline regression tests.
14. Publish a versioned graph build manifest.

## 10. Definition of done

The knowledge graph is ready when:

- Every manual and drawing has a registered source record.
- Every page is text-extracted or OCR-processed with quality status.
- Every material engineering fact is represented or explicitly marked as not extractable.
- Every fact has document/page/section provenance.
- Requirements preserve conditions, exceptions, units, and limits.
- Drawings preserve callouts, dimensions, tolerances, and part relationships.
- Revisions and cross-references are represented.
- Automated validation passes with no unresolved critical errors.
- High-risk facts have human review status recorded.
- The graph can answer representative technical questions with source evidence.
- The build is reproducible and versioned.

## 11. Immediate next action

Start with a complete inventory of the newly added manuals. Do not begin canonical extraction until the inventory, checksums, document family grouping, and source registry are complete. This prevents duplicate facts, lost revisions, and untraceable knowledge from entering the graph.
