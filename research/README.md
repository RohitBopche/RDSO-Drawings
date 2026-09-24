# RDSO-Drawings Research Workspace

This directory is intentionally separate from docs/.

The research workspace contains external research papers, standards, datasets, methods, and research-to-implementation mappings that can inform RDSO-Drawings.

It is **not** the project architecture source of truth.

- Project architecture, roadmap, quality gates, and implementation decisions -> docs/PROJECT_MASTER.md
- Historical project documents -> docs/archive/
- External research and research-derived experiments -> research/

## Rules

1. Do not place product requirements or architecture decisions here without also updating docs/PROJECT_MASTER.md.
2. Do not treat a paper's proposed method as validated for RDSO data until it is benchmarked on representative RDSO manuals/drawings.
3. Prefer primary papers, publisher pages, arXiv, standards bodies, and official project repositories.
4. Record the research question and expected project impact, not only a citation.
5. Separate established evidence from hypotheses and proposed experiments.
6. Do not download or commit copyrighted papers unless their license permits redistribution.
7. Use this directory for reproducible research notes, benchmarks, paper metadata, and experiment plans.

## Current index

- RESEARCH_INDEX.md - curated research bibliography.
- RESEARCH_TO_ARCHITECTURE.md - mapping from research to RDSO modules and experiments.

## Initial research themes

1. Railway maintenance knowledge graphs
2. Engineering knowledge graphs and ontologies
3. PDF/document structure understanding
4. OCR-free and layout-aware document extraction
5. Engineering drawing understanding
6. Drawing revision/comparison
7. RAG and GraphRAG
8. Evidence/provenance and graph validation
9. Multimodal engineering knowledge graphs
10. Railway maintenance risk and decision support
