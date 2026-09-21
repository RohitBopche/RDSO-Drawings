# Manuals Knowledge Graph v2 — Structural Isolation Blueprint

## Objective

Make the Manuals Knowledge Graph deterministic and document-first.

When a user selects a manual, the first expansion must be its authoritative chapter list:

Manual -> Chapter 1 ... Chapter N

Semantic clauses, topics, entities and extracted concepts are secondary content and must never replace the chapter hierarchy.

## Graph boundaries

### Manuals universe

- DOCUMENT
- CHAPTER
- SECTION / SUBSECTION
- CLAUSE / EVIDENCE
- TOPIC / CONCEPT
- MANUAL-SPECIFIC EQUIPMENT, LIMIT, ROLE and FAILURE information

### Drawings universe

- DRAWING
- REVISION
- NOTE
- COMPONENT
- DIMENSION / TOLERANCE
- DRAWING-SPECIFIC failure and engineering entities

No edge may cross these universes in the current release.

## Canonical structural contract

Every manual must have:

1. A stable document ID.
2. A deterministic ordered chapter registry.
3. One CHAPTER node per registered chapter.
4. One CONTAINS_CHAPTER edge from the manual to each chapter.
5. Stable chapter IDs in the form CHAPTER:<ALIAS>:CH_<NN>.
6. Page ranges and structure status.
7. A source-derived semantic layer attached below the structural hierarchy.
8. Every source-derived structural child carries machine-readable provenance: source document, source page, source section/reference, extraction method and parent chapter ownership.

## Expansion behavior

### Manual selected

Show only:

- selected manual
- direct chapter children

Do not show arbitrary concepts, drawing entities or extracted clauses as direct children.

### Chapter selected

Expand to the chapter's own sections/evidence/topics.

### Semantic exploration

Semantic nodes may be loaded on demand after the structural node is selected.

## Isolation rule

The canonical generator must reject/remove any edge where exactly one endpoint belongs to the manual domain.

Future relationships between manuals and drawings must be stored in a dedicated relationship layer with explicit evidence and provenance.

## Continuous loop

.github/workflows/manual-kg-continuous.yml:

1. Rebuild authoritative manual structure.
2. Rebuild canonical KG.
3. Validate manual structure and isolation.
4. Validate canonical chapter/content ownership and provenance.
5. Run the complete publication validation suite.
6. Detect generated-data drift.
7. Refresh generated artifacts on main when deterministic regeneration changes them.
8. Create a scheduled failure issue when the loop fails.

## Acceptance criteria

- Six authoritative manual roots.
- Every manual expands to exactly its registered N chapters.
- Chapter order is deterministic.
- No manual chapter is derived from drawing extraction.
- No manual-to-drawing or drawing-to-manual edge exists.
- Semantic extraction cannot create a new direct child of a manual root.
- Re-running ingestion produces the same structural hierarchy.
- All publication gates pass.

## Future integration

Do not connect manuals and drawings directly in the base KG.

Later add:

Manual Chapter -> relationship/evidence layer -> Drawing

Candidate predicates:

- REFERENCES
- APPLIES_TO
- ILLUSTRATED_BY
- DEFINED_IN
- SPECIFIED_BY
- RELATED_TO

Every future cross-domain relationship should carry source page/region, extraction method, confidence and validation status.


### Deterministic section/subsection layer

The current manual content pipeline now derives an explicit intermediate hierarchy from stable clause numbering:

```
Manual
  └── Chapter
       └── Section (derived from clause reference)
            └── Subsection (derived from clause reference)
                 └── Clause
```

These Section/Subsection nodes are marked `DERIVED_FROM_CLAUSE_NUMBERING` and retain source document, source page, source section/reference, source text, extraction method, confidence, and parent chapter provenance. They are not treated as authoritative table-of-contents headings. A future heading-aware extractor may replace or enrich this derived layer without changing chapter ownership.

Publication validation checks manual isolation, canonical IDs, single authoritative chapter ownership, source-page bounds, nested section/subsection ownership, and provenance completeness.


## Authoritative source-derived structural artifacts

The manual ingestion pipeline now materializes explicitly labeled source artifacts into the authoritative intermediate structure:

- `tables[]` → canonical `TABLE` nodes via `HAS_TABLE`
- `figures[]` → canonical `FIGURE` nodes via `HAS_FIGURE`
- `evidence[]` → canonical `EVIDENCE` nodes via `HAS_EVIDENCE`

Each artifact uses a deterministic chapter/page/ordinal/hash ID and carries `source_document`, `source_page`, `source_section`, `source_text`, `extraction_method`, `confidence`, and `parent_chapter_id`. Artifacts are direct Chapter children by default; the pipeline does not infer semantic Section/Subsection ownership for them. The canonical validator enforces ID shape, provenance completeness, confidence bounds, chapter page bounds, exactly one direct Chapter owner, structural relation parent types, and Manuals/Drawing isolation.

The extraction is deliberately label-driven. Unlabeled semantic mentions of tables, figures, or evidence do not become structural nodes. This keeps the Manual graph deterministic and prevents the earlier problem of random drawing-derived information appearing under Manuals.


## Source-heading enrichment (current phase)

Section/Subsection nodes now receive conservative source-heading evidence when a numbered heading can be detected deterministically on an owning chapter page. Heading enrichment includes the reference, title, page, source text, extraction method, and confidence. The existing numbering-derived hierarchy remains the fallback and still controls ownership. Heading detection intentionally rejects long procedural sentences and requirement-like lines; it does not use LLM inference and does not create cross-universe relationships.
