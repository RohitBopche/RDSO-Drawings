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
4. Run the complete publication validation suite.
5. Detect generated-data drift.
6. Refresh generated artifacts on main when deterministic regeneration changes them.
7. Create a scheduled failure issue when the loop fails.

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
