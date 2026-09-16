# Railway Engineering Knowledge Graph Architecture

## RDSO Drawings — Manuals, Codes, Drawings, Letters and Circulars

**Status:** Proposed architecture  
**Repository:** `RohitBopche/RDSO-Drawings`

## 1. Purpose

Build a searchable, evidence-backed Railway Engineering Knowledge Graph (REKG) for:

- Railway manuals and handbooks
- Codes and specifications
- RDSO and standard drawings
- Drawing revisions and amendments
- Railway Board letters and circulars
- Zonal railway instructions
- Components, assemblies, materials and technical parameters
- Requirements, inspection and testing procedures

The system must answer engineering questions using exact source documents, pages, clauses, drawing sheets and revision status.

## 2. Architectural principle

Use a **hybrid architecture** rather than a graph-only system:

1. **Document registry** — authoritative metadata and version control.
2. **Knowledge graph** — typed entities and relationships.
3. **Evidence graph** — source page, clause, sheet, bounding box and extraction provenance.
4. **Vector search** — semantic retrieval.
5. **Full-text search** — exact identifiers, drawing numbers and clauses.
6. **Structured analytics** — requirements, dimensions, revisions and applicability.
7. **AI/RAG layer** — source-grounded explanations and learning experiences.

## 3. Graph layers

### 3.1 Document graph

Represents source artifacts:

- `Document`
- `Manual`
- `Code`
- `Specification`
- `Drawing`
- `DrawingSheet`
- `Letter`
- `Circular`
- `Amendment`
- `Revision`
- `Clause`
- `Section`

### 3.2 Engineering domain graph

Represents the subject matter:

- `EngineeringSystem`
- `Subsystem`
- `Component`
- `Assembly`
- `Part`
- `Material`
- `Parameter`
- `Requirement`
- `TestProcedure`
- `InspectionActivity`
- `Organization`
- `RailwayZone`
- `Division`
- `Project`
- `Topic`

### 3.3 Evidence and provenance graph

Every important fact or relationship should retain:

- Source document and version
- Page or drawing sheet
- Section or clause number
- Source text or image region
- Extraction method
- Model/version used
- Confidence score
- Verification status
- Reviewer and review date

## 4. Core relationships

### Document relationships

- `references`
- `referenced_by`
- `amends`
- `amended_by`
- `clarifies`
- `supersedes`
- `superseded_by`
- `revises`
- `has_revision`
- `has_sheet`
- `contains_clause`
- `related_to`

### Engineering relationships

- `describes`
- `applies_to`
- `specified_by`
- `governed_by`
- `illustrated_by`
- `contains_part`
- `uses_material`
- `has_parameter`
- `defines_requirement`
- `verified_by`
- `installed_by`
- `maintained_by`
- `tested_by`

### Applicability relationships

- `applicable_in`
- `applicable_for`
- `effective_from`
- `effective_until`
- `restricted_to`
- `issued_by`
- `addressed_to`

Relationships must be directional, typed and supported by evidence wherever possible.

## 5. Drawing intelligence

Drawings must be processed as engineering artifacts, not ordinary PDFs.

Extract and index:

- Drawing number and title
- Revision and issue date
- Sheet number and scale
- Units
- Title block fields
- Dimensions and tolerances
- Materials and grades
- Notes and callouts
- Bill of materials
- Part and assembly references
- Referenced drawings
- Approval and supersession information

Recommended techniques:

- PyMuPDF/pdfplumber for PDF structure
- OCR using PaddleOCR or Tesseract
- Regex and dictionaries for drawing identifiers
- Layout-aware extraction for title blocks and tables
- Computer vision for drawing similarity and revision comparison
- Human review for critical dimensions and requirements

Machine-extracted dimensions must be marked as unverified until reviewed.

## 6. Railway Board letters and zonal circulars

Letters and circulars are first-class knowledge entities. Store:

- Circular/letter number
- Subject
- Issuing organization
- Recipient organization
- Department
- Issue date
- Effective date
- Applicable zones/divisions
- Related drawings, manuals, codes and clauses
- Amendment or clarification relationship
- Supersession status
- Original source file and evidence

Do not infer that a later circular supersedes an earlier document unless the source explicitly establishes that relationship.

## 7. Ingestion pipeline

```text
Source files
  -> file validation and hashing
  -> document classification
  -> text, OCR and layout extraction
  -> metadata extraction
  -> entity extraction
  -> relationship extraction
  -> requirement and parameter extraction
  -> identifier/entity resolution
  -> confidence scoring
  -> human review queue
  -> graph, database and search indexes
```

Use deterministic rules first for:

- Drawing numbers
- Manual/specification numbers
- Dates
- Revision labels
- Clause references
- Circular numbers

Use ML/LLM extraction for ambiguous entities, concepts and relationships.

## 8. Retrieval architecture

Support five complementary retrieval modes:

1. **Exact search** — drawing numbers, document IDs, clauses and circular numbers.
2. **Full-text search** — OCR text, notes, tables and document content.
3. **Semantic search** — natural-language engineering questions.
4. **Graph traversal** — related manuals, drawings, specifications and circulars.
5. **Structured filtering** — department, zone, component, revision, date and status.

Recommended query flow:

```text
User question
  -> query understanding and entity resolution
  -> keyword + vector + graph + metadata retrieval
  -> result merging and ranking
  -> applicability and revision filtering
  -> evidence verification
  -> source-backed answer
```

## 9. Source-backed answer rules

For technical answers:

- Cite the exact source document.
- Include page, clause or drawing sheet where available.
- Show revision and status.
- Show applicability and effective dates.
- Distinguish authoritative facts from extracted or inferred facts.
- Surface conflicting evidence.
- Never invent dimensions, drawing numbers, standards or requirements.
- Link every important claim to evidence.

## 10. Recommended technology stack

### Initial low-cost architecture

- **Storage:** S3-compatible object storage or controlled local storage
- **Database:** PostgreSQL
- **Vector search:** pgvector
- **Full-text search:** PostgreSQL FTS; OpenSearch later if required
- **Graph:** Apache AGE initially or Neo4j when graph workload justifies it
- **OCR:** PaddleOCR/Tesseract
- **PDF processing:** PyMuPDF/pdfplumber
- **Backend:** FastAPI
- **ML/analytics:** Python, scikit-learn, PyTorch/Transformers, NetworkX
- **Frontend:** React/Next.js
- **Graph UI:** Cytoscape.js or React Flow
- **Workers:** Background job queue for OCR, embeddings and extraction

PostgreSQL should remain the authoritative metadata and evidence registry. Avoid premature multi-database complexity.

## 11. Suggested relational entities

Minimum tables:

- `documents`
- `document_versions`
- `document_sheets`
- `document_chunks`
- `entities`
- `entity_aliases`
- `relationships`
- `evidence`
- `requirements`
- `parameters`
- `applicability_rules`
- `extraction_jobs`
- `review_tasks`
- `embeddings`

Use stable UUIDs, content hashes, JSONB for extensible metadata, and unique constraints for document identity and revisions.

## 12. ML and analytics

### ML use cases

- Document classification
- OCR correction
- Named entity recognition
- Entity resolution and alias matching
- Relationship discovery
- Requirement extraction
- Semantic embeddings
- Query intent classification
- Search-result reranking
- Duplicate and near-duplicate detection
- Drawing similarity and revision comparison

### Graph/data analytics

- Document centrality
- Community detection
- Orphan document detection
- Unresolved reference detection
- Missing metadata analysis
- Revision frequency analysis
- Circular impact analysis
- Requirement coverage
- Source confidence distribution
- Knowledge-gap identification

ML-generated relationships should enter a review queue when confidence is low or when they affect technical applicability.

## 13. User interface modules

### Universal search

- Natural-language search
- Exact identifier search
- Filters for document type, system, department, zone, date, revision and status
- Search across manuals, drawings, codes, letters and circulars

### Graph explorer

- Progressive node expansion
- Typed relationship labels
- Relationship evidence preview
- Filters by entity type and confidence
- Revision timeline
- Saved graph views

### Document viewer

- Page and sheet navigation
- OCR text search
- Source highlighting
- Drawing zoom
- Extracted dimensions and metadata
- Linked documents
- Revision comparison

### Learning mode

- Topic maps
- Simple explanations
- Related drawings and manuals
- Flashcards
- Practice questions
- Learning paths generated from the authoritative graph

### Administration and quality

- Ingestion queue
- Human verification
- Failed extraction review
- Duplicate detection
- Orphan and unresolved reference reports
- Source quality metrics

## 14. Implementation roadmap

### Phase 1 — Foundation

- Stable document IDs
- File hashing and storage
- Metadata registry
- Version management
- OCR/text extraction
- Full-text search
- Basic document viewer

### Phase 2 — Core graph

- Ontology and controlled vocabularies
- Entity extraction
- Document references
- Drawing/manual/specification relationships
- Circular and letter relationships
- Evidence and provenance
- Graph explorer

### Phase 3 — Engineering intelligence

- Components and assemblies
- Materials and parameters
- Requirements and verification methods
- Drawing title-block extraction
- Structured dimensions
- Applicability and temporal reasoning
- Revision comparison

### Phase 4 — AI and learning

- Hybrid graph/vector RAG
- Query understanding
- Evidence-backed answers
- Learning paths
- Flashcards and practice questions
- User-specific views

### Phase 5 — Analytics and continuous improvement

- Knowledge-gap detection
- Graph quality metrics
- Revision and circular impact analytics
- Automated ingestion
- Human review workflows
- Search analytics and feedback loops

## 15. Quality gates

Before publishing extracted knowledge:

- Validate document identity.
- Validate source page/sheet.
- Check revision and status.
- Check relationship direction.
- Check entity resolution.
- Assign confidence.
- Require human review for critical technical facts.
- Preserve the original source.
- Maintain an audit trail.

## 16. Success criteria

The system should allow a user to:

1. Find a document by exact number or natural language.
2. Discover all relevant manuals, codes, drawings and circulars.
3. Trace a requirement to its exact source clause or drawing sheet.
4. Identify applicable and superseded revisions.
5. Explore component, assembly and drawing dependencies.
6. Compare revisions and identify changes.
7. Search by railway zone, department and applicability.
8. Receive explanations with evidence rather than unsupported summaries.
9. Learn a topic using connected documents and drawings.
10. Identify missing, conflicting or low-confidence knowledge.

## 17. Final architectural position

The RDSO Drawings project should evolve into a **Railway Engineering Knowledge Operating System**.

The graph is the relationship layer, not the entire system. The long-term value comes from combining:

- Authoritative documents
- Structured engineering entities
- Evidence and provenance
- Temporal applicability
- Hybrid retrieval
- ML-assisted extraction
- Human verification
- Learning and analytics

Every important piece of railway knowledge should be traceable from an engineering concept to the relevant document, exact evidence, applicable revision and related engineering entities.
