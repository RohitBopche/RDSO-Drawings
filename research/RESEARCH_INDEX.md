# RDSO-Drawings - Research Index

**Status:** Initial curated research set  
**Scope:** External research that can directly inform the Railway Engineering Knowledge System  
**Last reviewed:** 2026-09-24

## How to use this index

Priority is based on expected architectural relevance, not paper quality ranking.

- **P0** - should directly inform current implementation or near-term experiments.
- **P1** - relevant to the next engineering layers.
- **P2** - future capability / research direction.

No paper is treated as an implementation mandate.

---

## A. Railway knowledge graphs

### R-001 - Ontology-guided Knowledge Graph Construction to Support Scheduling in a Train Maintenance Depot
- Authors: Emmanuel Papadakis, Lee McCluskey, Hassna Louadah, Gareth Tucker
- Year: 2023
- Priority: **P0**
- Relevance: Semi-structured railway maintenance manuals -> knowledge acquisition pipeline -> domain ontology -> knowledge graph.
- RDSO use: Validate our manual-first hierarchy, ontology, extraction and canonical KG approach.
- Source: https://pure.hud.ac.uk/en/publications/ontology-guided-knowledge-graph-construction-to-support-schedulin/

### R-002 - Construction and Application of Knowledge Graph for Train Maintenance Field
- Authors: Junjie Zhang, Shijun Jiang, Weidong Liu
- Year: 2024
- Priority: **P0**
- Relevance: Railway/train maintenance KG covering ontology design, information extraction, knowledge mapping, storage and fusion.
- RDSO use: Compare our architecture with an independently described railway maintenance KG lifecycle.
- DOI: 10.16037/j.1007-869x.2024.09.035
- Source: https://umt1998.tongji.edu.cn/en/article/doi/10.16037/j.1007-869x.2024.09.035

### R-003 - Evidence-verifiable intelligent interaction system and defect knowledge graph for operation-and-maintenance diagnosis of high-speed railway infrastructure
- Authors: Zhihui Zhu et al.
- Year: 2026
- Priority: **P0**
- Relevance: Railway O&M defect KG + entity anchoring + GraphRAG + evidence-verifiable QA.
- RDSO use: Inform grounded QA, evidence retrieval, graph traversal and citation verification.
- DOI: 10.1016/j.eswa.2026.132537
- Source: https://www.sciencedirect.com/science/article/abs/pii/S0957417426014508

### R-004 - Knowledge graph-based operation and maintenance risk analysis and early warning approach for railway traction power supply systems
- Year: 2026
- Priority: **P1**
- Relevance: Railway O&M KG applied to risk analysis and early warning.
- RDSO use: Future failure/risk reasoning and maintenance analytics.
- DOI: 10.1016/j.engappai.2025.113564
- Source: https://www.sciencedirect.com/science/article/pii/S095219762503595X

---

## B. Engineering maintenance knowledge graphs

### R-005 - Construction of Bridge Maintenance Knowledge Graph Based on Deep Learning
- Authors: Yiming Zhang, Hongshuai Gao
- Year: 2026
- Priority: **P0**
- Relevance: Standards-aligned ontology, annotated engineering reports, entity extraction, interpretable rule-based relation construction.
- RDSO use: Reference for ontology constraints, human-reviewed extraction and engineering-constrained graph construction.
- DOI: 10.3390/app16041985
- Source: https://www.mdpi.com/2076-3417/16/4/1985

### R-006 - A human-in-the-loop automated framework for high-precision bridge maintenance knowledge graphs: from construction to refinement with LLMs and GNNs
- Year: 2026
- Priority: **P1**
- Relevance: Human-in-the-loop KG construction/refinement.
- RDSO use: Future review queues, confidence-driven correction and controlled AI refinement.
- DOI: 10.1016/j.aei.2026.105034
- Source: https://www.sciencedirect.com/science/article/abs/pii/S1474034626007263

---

## C. Document/PDF understanding

### R-007 - Docling Technical Report
- Authors: Christoph Auer et al.
- Year: 2024
- Priority: **P0**
- Relevance: Open-source PDF conversion with layout analysis and table structure recognition; designed to run on commodity hardware.
- RDSO use: Benchmark against current PDF/manual ingestion for hierarchy, tables and figures.
- Source: https://arxiv.org/abs/2408.09869
- Official project: https://docling-project.github.io/docling/

### R-008 - LayoutLM: Pre-training of Text and Layout for Document Image Understanding
- Authors: Yiheng Xu et al.
- Year: 2020
- Priority: **P1**
- Relevance: Joint modeling of document text and spatial layout.
- RDSO use: Heading, table, note and structural extraction where plain text loses positional context.
- Source: https://arxiv.org/abs/1912.13318

### R-009 - OCR-free Document Understanding Transformer (Donut)
- Authors: Geewook Kim et al.
- Year: 2022
- Priority: **P1**
- Relevance: OCR-free visual document understanding and structured document parsing.
- RDSO use: Benchmark for difficult scanned/manual pages and drawing annotations; not a replacement for deterministic extraction.
- Source: https://arxiv.org/abs/2111.15664
- Official implementation: https://github.com/clovaai/donut

---

## D. Engineering drawing understanding

### R-010 - From drawings to decisions: A hybrid vision-language framework for parsing 2D engineering drawings into structured manufacturing knowledge
- Authors: Muhammad Tayyab Khan et al.
- Year: 2026 journal publication; arXiv preprint 2025
- Priority: **P0**
- Relevance: Rotation-aware detection + VLM parsing of engineering drawing annotations such as GD&T, tolerances, measures, materials, notes and title blocks.
- RDSO use: Direct benchmark/reference for Drawing Universe extraction.
- DOI: 10.1016/j.rcim.2025.103186
- arXiv: https://arxiv.org/abs/2506.17374
- Publisher: https://www.sciencedirect.com/science/article/pii/S0736584525002406

### R-011 - Drawing-Checker: A Vision RAG Framework for Automated Comparison of Engineering Drawings
- Authors: Zhou Jiwei, Jorge D. Camba, Pedro Company, et al.
- Year: 2026
- Priority: **P1**
- Relevance: View-level drawing comparison using detection, retrieval and multimodal reasoning.
- RDSO use: Future drawing revision comparison and localized change detection.
- DOI: 10.1016/j.procir.2026.05.235
- Source: https://www.sciencedirect.com/science/article/pii/S2212827126008085

---

## E. RAG and GraphRAG

### R-012 - Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- Authors: Patrick Lewis et al.
- Year: 2020
- Priority: **P0**
- Relevance: External evidence retrieval combined with generation; explicitly addresses provenance/update limitations of parametric-only models.
- RDSO use: Foundation for evidence-bounded QA.
- Source: https://arxiv.org/abs/2005.11401

### R-013 - From Local to Global: A Graph RAG Approach to Query-Focused Summarization
- Authors: Darren Edge et al.
- Year: 2024
- Priority: **P1**
- Relevance: Graph-based retrieval/summarization over large private corpora.
- RDSO use: Inform graph-assisted retrieval and corpus-level questions, while preserving our stricter source/evidence model.
- Source: https://arxiv.org/abs/2404.16130

---

## F. Graph validation / standards

### R-014 - Shapes Constraint Language (SHACL)
- Organization: W3C
- Status: Recommendation
- Priority: **P0**
- Relevance: Formal constraints for validating RDF graph structures, cardinalities, datatypes and relationships.
- RDSO use: Inspiration for machine-checkable KG shape validation even if our first graph implementation remains relational/PostgreSQL.
- Source: https://www.w3.org/TR/shacl/

---

## G. Multimodal engineering / digital twins

### R-015 - PhyGeo-KG: Physics-Regularized Distant Supervision for Multimodal Geometric Knowledge Graph Construction in Catenary Maintenance
- Year: 2026
- Priority: **P2**
- Relevance: Railway catenary maintenance; combines semantic, geometric, physical and procedural knowledge with BIM/IFC grounding.
- RDSO use: Long-term multimodal KG/digital-twin direction; physics-aware validation is particularly relevant to future engineering reasoning.
- Source: https://www.mdpi.com/1424-8220/26/7/2155

---

## Immediate reading / experiment set

1. R-001 - railway manual KG
2. R-002 - train maintenance KG
3. R-003 - evidence-verifiable railway GraphRAG
4. R-007 - Docling
5. R-010 - engineering drawing extraction
6. R-012 - RAG
7. R-014 - SHACL

## Next wave

8. R-004 - railway O&M risk
9. R-005 - engineering maintenance KG
10. R-008 - LayoutLM
11. R-009 - Donut
12. R-011 - Drawing-Checker
13. R-013 - GraphRAG

## Future research

14. R-006 - human-in-the-loop KG refinement
15. R-015 - multimodal railway/digital twin KG

## Interpretation rule

The research corpus should answer:

- Which methods are suitable for RDSO documents?
- Which methods should be benchmarked?
- Which architectural decisions have external support?
- Which approaches fail on our document types?
- What new experiments are justified?

It must not be used to justify adding technology without an observed project need.
