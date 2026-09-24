# Research -> RDSO Architecture Mapping

This is a research working document. It converts the bibliography into concrete engineering experiments.

## 1. Research-to-system map

| Research | RDSO layer | Candidate experiment | Success evidence |
|---|---|---|---|
| R-001 Railway manual KG | Manual ingestion/KG | Compare manual-first hierarchy + ontology extraction against current pipeline | Higher chapter/section/provision fidelity without fabricated nodes |
| R-002 Train maintenance KG | Canonical KG | Compare entity/relation taxonomy with our controlled vocabulary | Fewer ambiguous relation types; clear engineering semantics |
| R-003 Railway evidence GraphRAG | QA/retrieval | Build evidence-bounded multi-hop retrieval on representative railway questions | Higher citation coverage and lower unsupported-claim rate |
| R-004 Railway O&M risk KG | Analytics | Prototype failure/risk paths | Traceable risk paths with source evidence |
| R-005 Bridge maintenance KG | KG construction | Benchmark ontology-constrained extraction + rule-based relation creation | Auditable relations and improved precision |
| R-006 Human-in-loop KG | Review workflow | Confidence-driven review queue | Critical/uncertain facts routed for human verification |
| R-007 Docling | PDF ingestion | Run representative manuals through current parser and Docling | Heading/table/figure recall and processing cost |
| R-008 LayoutLM | Layout extraction | Benchmark layout-aware heading/table detection | Better structural extraction on difficult pages |
| R-009 Donut | Difficult visual docs | Benchmark OCR-free parsing on selected scanned pages | Accuracy vs OCR pipeline; hallucination/error profile |
| R-010 Drawing extraction | Drawing ingestion | Extract title blocks, dimensions, tolerances, notes and materials | Field-level precision/recall on labeled drawings |
| R-011 Drawing-Checker | Revision intelligence | Compare two drawing revisions at view/annotation level | Correct localization of changed engineering content |
| R-012 RAG | QA | Evidence-bounded retrieval + generation | Citation coverage, groundedness, answer completeness |
| R-013 GraphRAG | Graph retrieval | Compare lexical/vector retrieval vs graph-assisted retrieval | Multi-hop retrieval success without evidence dilution |
| R-014 SHACL | Validation | Encode graph shape constraints | Deterministic detection of invalid KG structures |
| R-015 PhyGeo-KG | Future multimodal KG | Explore geometry + procedural knowledge alignment | Physically plausible, source-grounded relations |

---

## 2. Immediate experiment sequence

### EXP-01 - PDF ingestion benchmark

**Question:** Can a structured PDF parser improve our manual extraction without damaging deterministic hierarchy?

Compare:

- current RDSO parser;
- Docling;
- current parser + Docling as secondary signal.

Measure:

- page registration accuracy;
- heading recall/precision;
- chapter boundary accuracy;
- section/subsection accuracy;
- table detection;
- figure detection;
- clause preservation;
- runtime;
- memory usage.

**Do not change production ingestion until the benchmark is complete.**

---

### EXP-02 - Manual hierarchy benchmark

Use one complete pilot manual.

Ground truth:

    MANUAL
      CHAPTER
        SECTION
          SUBSECTION
            CLAUSE

Measure:

- chapter recall;
- chapter ordering;
- section recall;
- clause recall;
- orphan rate;
- fabricated-node rate;
- page-range accuracy.

Critical acceptance condition:

**fabrication rate = 0 for authoritative structure.**

---

### EXP-03 - Evidence-grounded retrieval

Create a small curated question set covering:

- rule lookup;
- procedure lookup;
- authority lookup;
- exception lookup;
- source lookup;
- comparison;
- dependency lookup.

Compare:

1. keyword retrieval;
2. vector retrieval;
3. hybrid retrieval;
4. hybrid + graph traversal;
5. hybrid + graph + evidence reranking.

Measure:

- evidence recall;
- correct provision retrieval;
- citation resolution;
- unsupported claims;
- version/applicability errors.

---

### EXP-04 - Engineering drawing extraction

Create a manually verified benchmark set.

Required fields:

    drawing_number
    title
    revision
    sheet
    scale
    units
    material
    dimension
    tolerance
    note
    BOM_item
    reference
    approval

Measure field-level precision/recall and hallucination/error rates.

Do not evaluate only OCR accuracy. The required output is **structured engineering information**.

---

### EXP-05 - Drawing revision comparison

Select drawing revision pairs with known changes.

Expected output:

    REV-A -> REV-B

    Changed:
    - dimension
    - tolerance
    - material
    - note
    - BOM item

    Unchanged:
    - component
    - view
    - title block field

Every reported change must link back to a drawing region/sheet.

---

### EXP-06 - KG shape validation

Translate our current canonical contracts into machine-checkable constraints.

Initial constraints:

- every CHAPTER belongs to exactly one MANUAL;
- every CLAUSE has provenance;
- every evidence reference resolves;
- relationship type is controlled;
- relationship endpoints exist;
- Manual/Drawing isolation holds;
- revision relationships are valid;
- page/sheet references are in bounds.

SHACL can serve as conceptual reference even if the first implementation is JSON Schema/PostgreSQL validation.

---

## 3. Research-derived architectural rules

### Rule A - Ontology before unconstrained semantic graph generation

Railway and engineering maintenance KG work starts from domain concepts/constraints rather than an unrestricted LLM graph.

**RDSO implication:** controlled entity/relation vocabulary remains mandatory.

### Rule B - Evidence must remain attached to knowledge

Railway evidence-verifiable GraphRAG research supports the requirement that retrieved graph context be tied to verifiable source evidence.

**RDSO implication:** graph edges and facts should remain provenance-aware.

### Rule C - Document layout is part of meaning

LayoutLM and Docling demonstrate why text-only extraction is insufficient for complex documents.

**RDSO implication:** hierarchy extraction should preserve layout/page coordinates where useful.

### Rule D - Engineering drawings need specialized extraction

Recent engineering drawing research shows that generic OCR is inadequate for rotated annotations, symbols, GD&T and dense layouts.

**RDSO implication:** Drawing Universe extraction should be a separate pipeline from manual extraction.

### Rule E - AI is downstream of canonical knowledge

RAG/GraphRAG research supports external retrieval, but RDSO needs stronger provenance and revision controls than a generic corpus QA system.

**RDSO implication:** retrieval and graph traversal select bounded evidence; the LLM synthesizes only after applicability/conflict checks.

### Rule F - Human review is a feature, not a failure

Engineering KG research increasingly uses constrained relation construction and human-in-the-loop refinement.

**RDSO implication:** low-confidence and safety-critical facts should enter explicit review queues.

---

## 4. What not to copy

Research projects often optimize for benchmark performance rather than long-term engineering traceability.

Do not automatically copy:

- LLM-generated graph construction;
- vector-only retrieval;
- Neo4j-first architectures;
- end-to-end VLM extraction;
- graph community summarization as authoritative knowledge;
- model-generated relations without provenance;
- benchmark metrics that ignore source correctness.

For RDSO, the authoritative chain remains:

    SOURCE
      ->
    EVIDENCE
      ->
    CANONICAL FACT
      ->
    RELATIONSHIP
      ->
    RETRIEVAL
      ->
    GROUNDED ANSWER

---

## 5. Research backlog

### P0

- [ ] Benchmark Docling against current manual ingestion.
- [ ] Formalize pilot-manual hierarchy ground truth.
- [ ] Build evidence-grounded QA benchmark.
- [ ] Define KG shape constraints.
- [ ] Build drawing extraction benchmark.

### P1

- [ ] Benchmark layout-aware extraction.
- [ ] Evaluate graph-assisted retrieval.
- [ ] Build revision comparison benchmark.
- [ ] Add confidence-driven review workflow.

### P2

- [ ] Multimodal geometry/knowledge alignment.
- [ ] BIM/IFC integration research.
- [ ] Physics-aware engineering reasoning.
- [ ] Digital-twin research.

---

## 6. Relationship to PROJECT_MASTER.md

This file is a research working document.

When an experiment produces evidence that changes the architecture:

1. record the experiment and result here;
2. update docs/PROJECT_MASTER.md;
3. add/modify implementation;
4. add regression tests;
5. record the decision in normal project history.

Research never silently changes production architecture.
