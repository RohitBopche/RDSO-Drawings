# Railway Manuals Knowledge Base & Evidence-Grounded Question Answering Architecture

**Project:** RDSO-Drawings  
**Status:** Strategic architecture and implementation specification  
**Scope:** Railway technical manuals, codes, specifications, procedures, rules, and departmental working practices

## 1. Purpose

The project should evolve into a Railway Technical Knowledge System that allows an engineer to ask:

- Which rule governs this work?
- What procedure should be followed?
- Which manual/chapter/paragraph specifies the requirement?
- What approval or authority is required?
- What inspection or acceptance criteria apply?
- Are there exceptions?
- Which other provisions are referenced?
- Which edition/revision is applicable?
- Why did the system reach this answer?

The manuals and their evidence remain the source of truth. The LLM is a reasoning and synthesis layer.

## 2. Problem Definition

Expected corpus:

- 15–20 manuals
- approximately 500 pages per manual
- approximately 7,500–10,000 pages total

The target workflow is:

~~~text
Question
  -> question understanding
  -> hybrid retrieval
  -> hierarchy + graph traversal
  -> evidence ranking
  -> applicable provision(s)
  -> answer synthesis
  -> citation/source verification
~~~

This is not simply a PDF chatbot and not simply a visual knowledge graph.

## 3. Product Definition

The target product is:

> A hierarchical, version-aware, provenance-preserving Railway Technical Knowledge Base with hybrid retrieval, semantic knowledge graph capabilities, and evidence-grounded question answering.

### 3.1 Universe Explorer

The manual hierarchy must represent the actual documents:

~~~text
Railway Knowledge
|
+-- Department
|   |
|   +-- Manual A
|   |   +-- Chapter 1
|   |   |   +-- Section 1.1
|   |   |   +-- Section 1.2
|   |   +-- Chapter 2
|   |
|   +-- Manual B
|
+-- Other Departments
~~~

The graph UI must not substitute random extracted concepts for the manual/chapter/section hierarchy.

### 3.2 Ask the Knowledge Base

Natural-language questions should return:

- direct answer;
- applicable rule/procedure;
- ordered steps where relevant;
- authority/responsibility;
- exceptions;
- related provisions;
- exact manual/chapter/section/paragraph;
- page/source reference;
- evidence excerpt;
- applicability/version;
- uncertainty/conflict indicator.

## 4. Architectural Model

~~~text
USER INTERFACE
  Universe | Search | Q&A | Source Viewer
                |
                v
QUERY ENGINE
  Intent | Entities | Filters | Expansion | Ranking
                |
                v
RETRIEVAL / KNOWLEDGE
  Full Text | Vector | Hierarchy | Graph | Cross-Refs
                |
                v
CANONICAL KNOWLEDGE CORE
  Manuals | Chapters | Provisions | Rules | Procedures
  Entities | Facts | Relationships | Versions
                |
                v
EVIDENCE / PROVENANCE
  PDF | Page | Region | Paragraph | Hash | Edition
                |
                v
SOURCE LAYER
  Original manuals / PDFs / OCR / extracted source
~~~

## 5. Three Complementary Knowledge Representations

### Structural knowledge

~~~text
Manual
  -> Chapter
      -> Section
          -> Subsection
              -> Paragraph / Provision
~~~

### Semantic knowledge

~~~text
Provision
  +-- REQUIRES -> Approval
  +-- APPLIES_TO -> Work Type
  +-- PERFORMED_BY -> Authority
  +-- REFERENCES -> Other Provision
  +-- HAS_EXCEPTION -> Special Case
~~~

### Retrieval knowledge

Combines exact identifier search, full-text search, metadata filtering, semantic/vector search, hierarchy filtering, graph traversal, and cross-reference expansion.

All three representations must be connected through stable IDs and provenance.

## 6. Canonical Document Model

~~~text
DOCUMENT_FAMILY
    |
    +-- MANUAL
          |
          +-- EDITION / REVISION
                |
                +-- SOURCE_FILE
                      |
                      +-- PAGE
                            |
                            +-- CHAPTER
                                  |
                                  +-- SECTION
                                        |
                                        +-- SUBSECTION
                                              |
                                              +-- PROVISION / PARAGRAPH
~~~

Core fields should include:

~~~text
manual_id
title
department
issuing_authority
edition
revision
effective_date
status
source_file_id
page_number
printed_page_number
chapter_number
chapter_title
section_number
section_title
paragraph_number
paragraph_text
~~~

The physical PDF and logical manual are different objects. Never use filenames as canonical identity.

## 7. Version and Amendment Model

~~~text
Manual A
|
+-- Edition 2018
|   +-- Amendment 1
|   +-- Amendment 2
|
+-- Edition 2022
|
+-- Edition 2025
    +-- Amendment 1
~~~

Represent AMENDS, SUPERSEDES, MODIFIES, CORRECTS, VALID_DURING, and WITHDRAWN_BY.

The QA engine must not return a superseded provision as if it were current. If applicability cannot be established, the answer must say so.

## 8. Provision Model

A provision is more than text. Recommended representation:

~~~json
{
  "provision_id": "prov:manual_a:5.3.2",
  "manual_id": "manual:a",
  "edition_id": "edition:a:2025",
  "chapter": "5",
  "section": "5.3",
  "paragraph": "5.3.2",
  "type": "REQUIREMENT",
  "text": "...",
  "page": 183,
  "status": "CURRENT",
  "evidence_ids": ["ev:manual_a:page:183:p5.3.2"]
}
~~~

Controlled types:

- DEFINITION
- REQUIREMENT
- PROCEDURE
- RESPONSIBILITY
- AUTHORITY
- INSPECTION_CRITERION
- ACCEPTANCE_CRITERION
- PROHIBITION
- EXCEPTION
- NOTE
- REFERENCE
- STANDARD
- SPECIFICATION

## 9. Rule and Procedure Model

Important operational knowledge should be decomposed into:

~~~text
CONDITION
  -> REQUIREMENT
      -> ACTION / PROCEDURE
          -> AUTHORITY
              -> DOCUMENTATION
                  -> INSPECTION / ACCEPTANCE
                      -> EXCEPTION
~~~

For ordered procedures:

~~~text
Procedure X
  -> Step 1
  -> Step 2
  -> Step 3
  -> Inspection
  -> Documentation
~~~

The original source text must always be retained alongside the structured interpretation.

## 10. Cross-Reference Model

Cross-references are first-class knowledge.

~~~text
Provision A
  -- REFERENCES --> Provision B
~~~

Reference records should preserve:

~~~text
source_provision_id
target_manual_id
target_edition_id
target_chapter
target_section
target_paragraph
reference_text
resolution_status
evidence_id
~~~

Resolution states:

- RESOLVED
- AMBIGUOUS
- BROKEN
- EXTERNAL
- NOT_FOUND

## 11. Evidence and Provenance

Every important claim must be traceable.

~~~json
{
  "evidence_id": "ev:manual_a:page:183:p5.3.2",
  "source_file_id": "src:manual_a:2025",
  "page_number": 183,
  "printed_page": "171",
  "chapter": "5",
  "section": "5.3",
  "paragraph": "5.3.2",
  "quote": "...",
  "extraction_method": "pdf_text",
  "confidence": 0.98,
  "verification_status": "VERIFIED"
}
~~~

Evidence states:

- EXTRACTED
- VERIFIED
- DERIVED
- INFERRED
- CONFLICTING
- REJECTED
- UNKNOWN

The system must distinguish official statements from derived and inferred information.

## 12. Ingestion Pipeline

~~~text
PDF
 -> register source
 -> calculate file hash
 -> page extraction
 -> text extraction
 -> OCR fallback if necessary
 -> document metadata
 -> chapter detection
 -> section detection
 -> provision detection
 -> table/note extraction
 -> reference extraction
 -> candidate entities
 -> candidate rules/procedures
 -> normalization
 -> validation
 -> human review where required
 -> canonical publication
 -> search indexes
 -> graph exports
~~~

Maintain separate raw, intermediate, canonical, evidence, and index layers. Never overwrite raw extraction.

### OCR

Preferred order:

1. Native PDF text extraction.
2. Validate text quality.
3. OCR only pages requiring it.
4. Preserve OCR provenance.
5. Flag uncertain OCR for review.

OCR confidence must not automatically become factual confidence.

## 13. Chunking Strategy

Do not use arbitrary fixed-size chunks as the primary knowledge representation.

Preferred:

~~~text
Manual
 -> Chapter
    -> Section
       -> Paragraph
          -> Sentence
~~~

Retrieval chunks can be generated from this hierarchy while preserving manual, edition, chapter, section, paragraph, neighboring provisions, page, source, and provision type.

## 14. Search Architecture

Use hybrid retrieval:

~~~text
Question
  |
  +-- Exact / identifier search
  +-- Full-text search
  +-- Metadata filtering
  +-- Semantic/vector search
  +-- Graph/cross-reference traversal
              |
              v
       Candidate evidence
              |
              v
          Re-ranking
              |
              v
       Final evidence set
~~~

Ranking should generally prioritize:

~~~text
Exact provision/identifier
  > exact title/name
  > keyword relevance
  > metadata relevance
  > semantic similarity
  > graph/context relevance
~~~

Do not begin with vector search alone.

## 15. Query Understanding

Classify questions before retrieval.

Examples:

- RULE_LOOKUP — Which rule applies?
- PROCEDURE_LOOKUP — What is the procedure?
- AUTHORITY_LOOKUP — Who can approve?
- SOURCE_LOOKUP — Where is this specified?
- EXCEPTION_LOOKUP — Are there exceptions?
- COMPARISON — What differs between procedures?
- DEPENDENCY_LOOKUP — What other rules apply?

Extract where possible:

- activity/work;
- department;
- equipment/component;
- context/location;
- rule type;
- authority;
- time/version;
- named manual;
- paragraph/drawing identifiers.

## 16. Question Answering Pipeline

~~~text
User Question
  -> Intent Detection
  -> Entity / Context Extraction
  -> Hierarchy Filtering
  -> Hybrid Retrieval
  -> Cross-reference Expansion
  -> Graph Traversal
  -> Evidence Re-ranking
  -> Applicability / Version Check
  -> Conflict Check
  -> LLM Synthesis
  -> Citation Verification
  -> Answer
~~~

The LLM should only receive a bounded, evidence-ranked context.

## 17. Answer Contract

A standard answer should contain:

~~~text
Answer
  [direct answer]

Applicable requirement
  [rule/procedure]

Procedure
  1. ...
  2. ...
  3. ...

Authority / responsibility
  [...]

Exceptions
  [...]

Related provisions
  [...]

Source
  Manual:
  Edition:
  Chapter:
  Section:
  Paragraph:
  Page:

Evidence
  [source passage]

Applicability / confidence
  [...]
~~~

## 18. Citation Requirements

Minimum:

~~~text
Manual
Chapter
Section
Paragraph
Page
~~~

Preferred:

~~~text
Manual
Edition
Chapter
Section
Paragraph
Printed page
PDF page
Evidence excerpt
Source file
~~~

Provide an Open Source action whenever possible.

## 19. Conflict Handling

Conflicts must not be silently resolved.

If two provisions appear contradictory, show:

- both provisions;
- versions;
- scope/applicability;
- dates;
- documented precedence if available;
- evidence.

If precedence cannot be established:

> Conflict/ambiguity detected — manual verification required.

Do not choose a winner merely because one provision scored higher in retrieval.

## 20. Knowledge Graph Design

### Structural

~~~text
Manual
  -> CONTAINS -> Chapter
  -> CONTAINS -> Section
  -> CONTAINS -> Provision
~~~

### Semantic

~~~text
Provision
  +-- REQUIRES -> Requirement
  +-- APPLIES_TO -> Work
  +-- PERFORMED_BY -> Authority
  +-- REFERENCES -> Provision
  +-- EXCEPTION_TO -> Rule
  +-- SUPERSEDES -> Older Provision
~~~

The graph UI is a navigation/explanation tool, not the canonical data store.

## 21. Controlled Relationship Vocabulary

~~~text
CONTAINS
HAS_CHAPTER
HAS_SECTION
HAS_PROVISION
HAS_EDITION
HAS_REVISION
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
PERFORMED_BY
APPROVED_BY
INSPECTED_BY
ACCEPTED_BY
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
~~~

New relationship types must be documented and validated before broad use.

## 22. Database Strategy

Recommended starting point:

| Area | Technology |
|---|---|
| Application/data processing | Python |
| PDF extraction | PyMuPDF |
| OCR | OCRmyPDF/Tesseract where required |
| Database | PostgreSQL |
| Vector search | pgvector |
| Full-text search | PostgreSQL FTS |
| Initial graph model | PostgreSQL relational graph |
| API | FastAPI |
| Frontend | Existing RDSO web application, modularized incrementally |
| Local AI | Configurable local inference layer |
| Cloud AI | Provider abstraction |
| Validation | JSON Schema + Python tests |
| Testing | pytest + browser/E2E |

A dedicated graph database such as Neo4j should only be introduced if actual graph workloads justify it.

## 23. Suggested Core Data Model

~~~text
manuals
manual_editions
source_files
pages
chapters
sections
provisions
provision_references
entities
facts
relationships
evidence
procedures
requirements
authorities
applicability
review_queue
ingestion_runs
~~~

Search structures:

~~~text
provision_fts
entity_fts
provision_embeddings
entity_embeddings
~~~

## 24. First-Class Facts

Important facts must not exist only inside free text.

Examples:

- measurements;
- time limits;
- authorities;
- thresholds;
- quantities;
- tolerances;
- required documents;
- inspection intervals;
- approvals;
- responsibilities.

## 25. Human Review

Automation should produce candidate knowledge, not blindly publish uncertain facts.

~~~text
Candidate fact
  -> confidence/rule checks
  -> low confidence OR safety-relevant
  -> review queue
  -> accept / edit / reject / conflict
  -> canonical publication
~~~

Review records should preserve candidate, source, reviewer, timestamp, decision, notes, and resulting canonical record.

## 26. Validation Gates

### Structural

- schema valid;
- required fields present;
- controlled types valid.

### Identity

- unique IDs;
- no accidental duplicates;
- aliases explicit.

### Hierarchy

- chapter belongs to manual;
- section belongs to chapter;
- provision belongs to section;
- page/source references resolve.

### Relationships

- endpoints exist;
- relationship type is valid;
- direction is valid;
- revision chains are valid.

### Evidence

- every evidence reference resolves;
- source/page exists;
- source hash is recorded where available.

### Semantics

- units valid;
- numeric bounds coherent;
- applicability represented;
- conflicts not silently discarded.

## 27. Security and Reliability

Support local/offline deployment, access control for central deployments, audit logs, source integrity hashes, immutable raw sources, explicit model/provider configuration, and safe document handling.

Never silently replace a source document.

## 28. Offline-First Requirement

The knowledge core should support offline:

- manual browsing;
- hierarchy navigation;
- full-text search;
- source viewing;
- evidence inspection;
- graph exploration;
- rule/procedure lookup;
- local question answering where a local model is configured;
- exports/reports.

Cloud AI should be optional, not a hard dependency.

## 29. Repository Architecture

Manual knowledge should remain logically separate from drawing knowledge while sharing evidence, search, graph, identity, and version infrastructure.

Target direction:

~~~text
RDSO-Drawings/
|
+-- drawings/
+-- manuals/
|
+-- data/
|   +-- drawings/
|   +-- manuals/
|   |   +-- raw/
|   |   +-- intermediate/
|   |   +-- canonical/
|   |   +-- evidence/
|   |   +-- indexes/
|   +-- shared/
|
+-- scripts/
|   +-- drawings/
|   +-- manuals/
|   +-- ingestion/
|   +-- validation/
|   +-- search/
|
+-- src/
|   +-- knowledge/
|   +-- manuals/
|   +-- evidence/
|   +-- search/
|   +-- graph/
|   +-- qa/
|
+-- tests/
|   +-- manuals/
|   +-- knowledge/
|   +-- search/
|   +-- qa/
|
+-- docs/
    +-- RDSO_Knowledge_Graph_Improvement_Blueprint.md
    +-- RAILWAY_MANUALS_KNOWLEDGE_BASE_ARCHITECTURE.md
~~~

This is a target architecture, not a requirement to create every directory immediately.

## 30. Manual/Drawing Separation

~~~text
                 SHARED KNOWLEDGE CORE
                         |
           +-------------+-------------+
           |                           |
     MANUAL KNOWLEDGE            DRAWING KNOWLEDGE
           |                           |
     rules/procedures             drawings/components
     requirements                 dimensions
     authorities                  assemblies
     inspections                  revisions
     departmental practice        BOM
           |                           |
           +-------------+-------------+
                         |
                  Cross-domain links
~~~

Do not mix manual chapters with drawing-derived nodes merely because they are related. A manual chapter remains a manual chapter; a drawing remains a drawing. Relationships connect them.

## 31. Example Question Flow

For "What approval is required before starting work X?":

~~~text
AUTHORITY / APPROVAL LOOKUP
  -> identify Work X
  -> retrieve requirements
  -> retrieve approval provisions
  -> follow relevant cross-references
  -> check edition/applicability
  -> check conflicts
  -> rank evidence
  -> answer with source
~~~

## 32. Example "Which Rule Applies?" Flow

~~~text
Activity X
  -> entity normalization
  -> candidate provisions
  -> APPLIES_TO / GOVERNS relationships
  -> department/manual filtering
  -> version/applicability check
  -> evidence ranking
  -> applicable provision set
~~~

If multiple provisions apply, return the set and explain scope instead of forcing one answer.

## 33. Example Procedure Flow

~~~text
Procedure
  -> prerequisites
  -> approval
  -> ordered steps
  -> inspection
  -> documentation
  -> exception
~~~

Preserve source-defined ordering.

## 34. Explainability Flow

~~~text
Question
  -> retrieved provision
  -> cross-reference
  -> applicability/version
  -> evidence
  -> answer statement
~~~

The UI should expose this chain.

## 35. Knowledge Graph UI Rules

Support manual hierarchy, chapter/section expansion, provision opening, semantic relationships, evidence opening, focused neighborhoods, filtering, "why connected?", and path exploration.

Default interaction:

~~~text
Manual
  -> Chapter
     -> Section
        -> Provision
           -> Related knowledge
~~~

Only expand semantic neighborhoods on demand.

## 36. Search UI Rules

Search results should show manual, chapter, section, paragraph, provision type, short text, edition/revision, source page, and verification status.

## 37. Source Viewer

Provide page navigation, search within source, highlighted evidence, paragraph location, printed/PDF page mapping, source metadata, and related provisions.

Required navigation:

~~~text
Answer -> Provision -> Evidence -> PDF page
~~~

## 38. Metrics

Measure outcomes rather than graph size.

### Retrieval

- exact-query success;
- zero-result rate;
- relevant-result rate;
- time to useful provision.

### Evidence

- percentage of important facts with evidence;
- evidence resolution rate;
- verification coverage.

### Answering

- citation coverage;
- unsupported-claim rate;
- conflict detection rate;
- human validation rate.

### Data

- unresolved references;
- broken cross-references;
- duplicate provisions;
- stale editions;
- review queue size.

Do not optimize for node count, edge count, visual complexity, or number of embeddings.

## 39. Implementation Roadmap

### M0 — Manual foundation

1. Register all manuals.
2. Identify editions/revisions.
3. Store source files and hashes.
4. Build manual/chapter/section/paragraph hierarchy.
5. Preserve page mapping.
6. Validate hierarchy.

**Exit:** one complete manual can be browsed structurally without semantic extraction.

### M1 — Search

1. Full-text search.
2. Identifier search.
3. Metadata filtering.
4. Search result cards.
5. Source opening.

**Exit:** user can locate a provision faster than manual PDF searching.

### M2 — Cross-references

1. Detect references.
2. Resolve references.
3. Build reference graph.
4. Validate broken/ambiguous references.

**Exit:** multi-manual references can be followed automatically.

### M3 — Semantic extraction

1. Rules.
2. Procedures.
3. Authorities.
4. Requirements.
5. Exceptions.
6. Inspection criteria.
7. Facts/measurements.

**Exit:** important operational knowledge exists as structured records linked to source text.

### M4 — Knowledge graph

1. Structural hierarchy graph.
2. Semantic graph.
3. Controlled relationships.
4. Focused graph UI.
5. Evidence-linked edges.

**Exit:** graph answers useful navigation and relationship questions.

### M5 — Hybrid retrieval

1. Full text.
2. Metadata.
3. Vector search.
4. Graph traversal.
5. Re-ranking.

**Exit:** natural-language questions retrieve a relevant evidence set.

### M6 — Evidence-grounded QA

1. Question intent.
2. Retrieval.
3. Evidence ranking.
4. Applicability.
5. Conflict detection.
6. Answer synthesis.
7. Citation verification.

**Exit:** questions produce source-backed answers.

### M7 — Reliability

1. Regression questions.
2. Answer evaluation.
3. Citation validation.
4. Hallucination checks.
5. Review workflows.

**Exit:** suitable as an engineering research assistant, with normal human verification for safety-critical decisions.

## 40. First Manual Pilot

Do not ingest all 15–20 manuals into the semantic system at once.

Select one complete ~500-page manual and prove:

~~~text
PDF
 -> hierarchy
 -> provision extraction
 -> cross-reference extraction
 -> evidence
 -> search
 -> question
 -> answer
 -> citation
~~~

Only after the pipeline works end-to-end should it be scaled to the remaining manuals.

## 41. Pilot Acceptance Criteria

For one complete manual:

- all pages registered;
- chapter hierarchy represented;
- sections represented;
- provision locations preserved where detectable;
- source pages resolvable;
- full-text search works;
- representative natural-language queries work;
- answers cite exact provisions;
- source page can be opened;
- cross-references are represented;
- uncertain extraction is flagged;
- no answer is generated without retrieved evidence;
- regression tests cover representative questions.

## 42. AI Guardrails

The AI layer must:

1. never invent a rule;
2. never invent a paragraph number;
3. never invent a source page;
4. never silently change source meaning;
5. never present inference as an official requirement;
6. never ignore version conflict;
7. never hide uncertainty;
8. prefer primary source evidence;
9. preserve citations;
10. require human verification for unresolved or safety-critical conflicts.

## 43. Long-Term Capabilities

Once mature, the same knowledge core can support engineering Q&A, procedure assistance, compliance checking, inspection guidance, authority lookup, revision analysis, cross-manual impact analysis, structured learning, field assistance, engineering reports, evidence packages, and an AI copilot grounded in verified knowledge.

## 44. Strategic Architecture Decision

Do not build:

~~~text
PDF -> embeddings -> chatbot
~~~

Build:

~~~text
SOURCE DOCUMENTS
       |
STRUCTURED DOCUMENT MODEL
       |
EVIDENCE / PROVENANCE
       |
CANONICAL KNOWLEDGE
       |
HIERARCHICAL + SEMANTIC GRAPH
       |
HYBRID RETRIEVAL
       |
EVIDENCE-RANKED CONTEXT
       |
GROUNDED ANSWER
       |
CITATION / VALIDATION
~~~

This provides maintainability, auditability, version awareness, extensibility, and evidence traceability.

## 45. Relationship to Existing RDSO Blueprint

The existing RDSO Knowledge Graph Improvement Blueprint defines the broader drawing knowledge platform. This document specializes that architecture for manual/code/procedure knowledge.

The two domains should remain logically separate while sharing:

- evidence;
- provenance;
- identity;
- search;
- graph infrastructure;
- versioning;
- QA;
- future AI retrieval.

## 46. Immediate Implementation Order

~~~text
1. Inspect current manual ingestion state
2. Select one pilot manual
3. Establish canonical manual hierarchy
4. Establish page/provision provenance
5. Build structural browsing
6. Build full-text search
7. Build cross-reference extraction
8. Add evidence records
9. Add structured rule/procedure extraction
10. Add semantic relationships
11. Add hybrid retrieval
12. Add evidence-grounded QA
13. Add citation verification
14. Add regression question suite
15. Scale to all manuals
~~~

Do not start with a complete graph rewrite, Neo4j migration, a large LLM pipeline, vector search without structural extraction, or semantic extraction across every manual before the pilot works.

## 47. Definition of Done — Manual Knowledge Base v1

Version 1 is complete when:

- pilot manual pages are registered;
- hierarchy is preserved;
- provisions have stable IDs;
- source pages are resolvable;
- evidence is first-class;
- cross-references are represented;
- important rules/procedures can be structured;
- version context is preserved;
- full-text retrieval works;
- semantic retrieval can be added without replacing structural search;
- graph relationships are controlled;
- question answering is evidence-grounded;
- citations resolve;
- conflicts are surfaced;
- regression questions exist;
- raw source data remains immutable;
- UI consumes canonical knowledge rather than storing its own truth.

## 48. Final Target State

~~~text
              RAILWAY TECHNICAL KNOWLEDGE SYSTEM

Manuals / Codes / Specifications
              |
              v
       Document Structure
              |
              v
      Evidence + Provenance
              |
              v
      Canonical Knowledge Core
         |       |       |
         v       v       v
      Search   Graph   Versions
         |       |       |
         +-------+-------+
                 |
                 v
          Hybrid Retrieval
                 |
                 v
          Evidence Ranking
                 |
                 v
          Question Answering
                 |
        +--------+--------+
        |        |        |
        v        v        v
      Rule   Procedure  Authority
      Lookup Lookup     Lookup
        |        |        |
        +--------+--------+
                 |
                 v
        Source-backed answer
                 |
                 v
          Original evidence
~~~

**Strategic objective:** Reduce the time required to move from an engineering question to the correct, applicable, source-verifiable provision in the railway manuals without sacrificing provenance, version awareness, or human oversight.
