# RDSO Drawings — Manuals Knowledge Graph Separation & Chapter-First Architecture

## 1. Problem

The Manuals graph currently allows extracted drawing-oriented entities, clauses, topics, equipment, components, and other derived information to become the visible children of a manual.

That is the wrong hierarchy.

A manual is a document with a deterministic table-of-contents hierarchy. If a manual contains **N chapters**, selecting that manual must reveal **exactly those N chapter nodes** as its first-level children.

Example:

```
Manual
├── Chapter 1
├── Chapter 2
├── Chapter 3
├── ...
└── Chapter N
```

The current graph should not infer the manual's first-level children from whatever knowledge was extracted from its pages.

## 2. Architectural decision

For the current phase, maintain **two independent knowledge universes**:

```
DRAWINGS UNIVERSE
    Drawing
      ├── Revision
      ├── Note
      ├── Component
      ├── Dimension
      ├── Requirement
      └── Drawing relationships

MANUALS UNIVERSE
    Manual
      ├── Chapter
      │    ├── Section / Clause
      │    ├── Table
      │    ├── Figure
      │    └── Evidence
      └── ...
```

There must be **no automatic cross-universe edges** during this phase.

Later, a controlled bridge layer can connect them:

```
Manual Chapter / Clause
        │
        └── APPLIES_TO / REFERENCES / SPECIFIES
                         │
                         ▼
                    Drawing Entity
```

These bridges must be evidence-backed and explicitly typed.

## 3. Non-negotiable hierarchy

### Manuals

```
DOCUMENT
  └── CHAPTER
       └── CLAUSE / SECTION / TABLE / FIGURE
            └── EVIDENCE
```

The graph renderer must respect this hierarchy.

When a manual is expanded:

- reveal all registered chapters;
- preserve chapter number/order;
- do not replace chapters with extracted concepts;
- do not sort chapters by relevance;
- do not generate chapter names from page text when an authoritative registry exists;
- do not attach drawing components as direct children.

### Drawings

Keep the existing drawing knowledge model independent:

```
DRAWING
 ├── REVISION
 ├── NOTE
 ├── COMPONENT
 ├── MEASUREMENT
 ├── REQUIREMENT
 └── RELATED DRAWING
```

## 4. Source of truth for manual structure

The existing `MANUAL_CHAPTER_REGISTRY` in `scripts/ingest_all_manual_chapters.py` should become the authoritative structural registry.

It contains:

- manual ID;
- alias;
- title;
- chapter number;
- chapter title;
- page start;
- page end;
- topic hints.

The registry is **structural metadata**, not extracted knowledge.

Extraction may populate chapter content, but extraction must never determine whether a chapter exists.

## 5. Canonical manual model

Each manual should publish a deterministic document record:

```json
{
  "id": "DOC:IRPWM:2024:ACS14",
  "type": "MANUAL",
  "universe": "manuals",
  "title": "Indian Railways Permanent Way Manual 2024",
  "edition": "2024",
  "chapters": [
    {
      "id": "CHAPTER:IRPWM:CH_01",
      "number": 1,
      "title": "Duties of Permanent Way Officials",
      "page_range": [31, 60]
    }
  ]
}
```

Every chapter must have:

- stable chapter ID;
- parent manual ID;
- chapter number;
- canonical title;
- page range;
- ordinal/order;
- extraction status;
- child content references.

## 6. Separate structure from extracted knowledge

Do not model this as:

```
Manual → whatever extraction found
```

Model it as:

```
Manual
  └── STRUCTURAL_CHILD
       └── Chapter
            └── extracted knowledge
```

The chapter exists even when extraction finds zero clauses.

This is important because a chapter with no successfully extracted clauses is still a real chapter.

Recommended states:

- `STRUCTURE_VERIFIED`
- `CONTENT_PARTIAL`
- `CONTENT_VERIFIED`
- `EXTRACTION_FAILED`

## 7. Graph node classes

Introduce explicit universe/type metadata.

### Manual nodes

- `MANUAL`
- `CHAPTER`
- `SECTION`
- `CLAUSE`
- `TABLE`
- `FIGURE`
- `EVIDENCE`

### Drawing nodes

- `DRAWING`
- `REVISION`
- `NOTE`
- `COMPONENT`
- `MEASUREMENT`
- `REQUIREMENT`
- `STANDARD`

Every node must contain:

```json
{
  "id": "...",
  "type": "...",
  "universe": "manuals | drawings",
  "parent_id": "...",
  "order": 1
}
```

`universe` must never be inferred from the display label.

## 8. First-level expansion contract

Implement one deterministic operation:

```
getChildren(nodeId)
```

For a manual:

```
getChildren(MANUAL)
→ ordered Chapter[] only
```

For a chapter:

```
getChildren(CHAPTER)
→ SECTION / CLAUSE / TABLE / FIGURE nodes
```

For a drawing:

```
getChildren(DRAWING)
→ its drawing-domain children
```

The graph UI should not construct child relationships by searching the entire node list for semantic similarity.

## 9. Expansion algorithm

Use explicit parent-child relationships.

Pseudo-flow:

```
select manual
    ↓
ensure manual universe is active
    ↓
load manual's registered chapters
    ↓
sort by chapter number
    ↓
create/reveal chapter nodes
    ↓
connect:
MANUAL --HAS_CHAPTER--> CHAPTER
    ↓
render
```

No content extraction or drawing graph query should run during this operation.

## 10. Chapter positioning

When chapters are expanded, arrange them as a structured tree rather than a force-directed random cloud.

Recommended layout:

```
                 MANUAL
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
  Chapter 1      Chapter 2      Chapter 3 ... Chapter N
```

For large manuals, use:

- horizontal/vertical ordered rows;
- chapter-number labels;
- consistent spacing;
- lazy rendering of deep descendants.

The graph physics engine may animate the transition, but it must not determine semantic hierarchy.

## 11. Manual card / graph interaction

Manual node/card should display:

- manual title;
- edition/year;
- amendment/correction status;
- chapter count;
- extraction status;
- source availability.

When clicked:

```
Manual
  ↓
[N] Chapters
```

The UI should explicitly say:

```
15 Chapters
```

or equivalent.

This provides immediate confirmation that the graph represents the actual manual structure.

## 12. Chapter node information

A chapter node/card should show:

- Chapter number;
- canonical chapter title;
- page range;
- clause/section count;
- extraction status;
- source page availability.

Example:

```
CHAPTER 4
Curves & Turnouts
Pages 175–292
118 clauses
```

The clause count is content metadata and must not replace the chapter itself.

## 13. Clause extraction correction

The existing extraction code currently assigns extracted clauses to chapters based primarily on page ranges.

Keep that mechanism, but make it subordinate to the structural registry.

Required behavior:

1. Create every registered chapter first.
2. Process source pages.
3. Assign extracted clauses to the chapter covering the page.
4. Preserve source page.
5. Preserve evidence.
6. Deduplicate within the chapter.
7. Never delete an empty chapter.

If a page falls outside the registered range:

- mark it as `UNMAPPED_PAGE`;
- do not silently attach it to the first/last chapter.

The current fallback behavior of assigning out-of-range pages to the first/last chapter should be removed or changed to an explicit review bucket.

## 14. Important extraction issue

The current clause regex approach is useful for candidate extraction but should not be treated as the chapter structure.

There are two different operations:

### Structural extraction

Answers:

> What chapters exist?

Source:

- authoritative chapter registry;
- table of contents;
- verified document metadata.

### Content extraction

Answers:

> What clauses, tables, figures and facts exist inside each chapter?

Source:

- source pages;
- OCR/text extraction;
- table extraction;
- evidence regions.

These pipelines must remain separate.

## 15. Manual graph data package

Create a dedicated export:

```
data/knowledge-graph/exports/manuals_graph.json
```

Recommended shape:

```json
{
  "schema_version": "manuals-kg-v1",
  "universe": "manuals",
  "manuals": [],
  "chapters": [],
  "sections": [],
  "clauses": [],
  "tables": [],
  "figures": [],
  "evidence": [],
  "edges": []
}
```

Do not mix this package with the drawing graph export.

Recommended drawing package:

```
data/knowledge-graph/exports/drawings_graph.json
```

Later:

```
combined_graph.json
```

can be generated as a derived product.

## 16. Separate runtime graph stores

The application should load:

```
manuals_graph.json
drawings_graph.json
```

independently.

Runtime state:

```
window.manualKnowledgeGraph
window.drawingKnowledgeGraph
```

Avoid a single mutable array where manual and drawing nodes are indistinguishable.

A combined view, when eventually enabled, should be a derived projection:

```
drawings_graph + manuals_graph + verified_bridge_edges
```

## 17. No accidental cross-linking

Until the bridge layer is implemented:

- manual nodes cannot have drawing parents;
- drawing nodes cannot have manual parents;
- drawing-derived components cannot appear as chapter children;
- manual topics cannot become drawing children;
- semantic search must respect the active universe by default.

If a user searches within Manuals, drawing-only entities must not become structural children.

## 18. Future bridge architecture

Do not delete the possibility of interlinking.

Introduce a future bridge namespace:

```
BRIDGE:<source>:<relationship>:<target>
```

Examples:

```
CHAPTER:IRPWM:CH_04
    └── APPLIES_TO
        └── drg_6155
```

or:

```
CLAUSE:IRPWM:PARA_429
    └── SPECIFIES
        └── drg_6275
```

Every bridge must have:

- relationship type;
- evidence;
- source document;
- page/clause;
- confidence;
- verification status.

No inferred bridge should be rendered as authoritative.

## 19. UI modes

The graph should expose three conceptual modes:

### Drawings

Shows only drawing universe.

### Manuals

Shows only manual universe.

### Combined

Shows both universes plus explicitly verified bridge relationships.

Current default should remain **Drawings** if that is the existing product behavior.

Switching to Manuals should clear/hide drawing nodes rather than merely filtering them visually.

## 20. Search behavior

Search should respect universe.

Manual search:

```
query
 → manuals
 → manual
 → chapter
 → clause/evidence
```

Drawing search:

```
query
 → drawings
 → drawing
 → revision/component/note
```

Combined search may search both, but results must visibly identify their universe.

## 21. Validation requirements

Add structural validators.

### Manual completeness

For every registered manual:

```
actual_chapter_count == registry_chapter_count
```

### Chapter identity

Every chapter must have:

- unique ID;
- exactly one manual parent;
- valid chapter number;
- canonical title;
- page range.

### Ordering

Chapter numbers must be strictly ordered.

### Parent integrity

No chapter may belong to another manual.

### Universe isolation

```
manual_nodes ∩ drawing_children = ∅
```

and vice versa.

### Empty chapter preservation

A chapter with zero extracted clauses must still exist.

### Evidence integrity

Every clause/fact evidence reference must resolve.

## 22. Automated regression tests

Add tests for every manual.

Minimum test:

```
for manual in MANUAL_CHAPTER_REGISTRY:
    expand(manual)
    assert visible_children == registered_chapters
    assert order == chapter_number_order
    assert every(child.universe == "manuals")
```

Specific examples:

- IRPWM → 15 chapters;
- USFD → 15 registered chapter entries;
- AT Weld → 9;
- FBW → 9;
- TMM → 12;
- STMM → 23.

Do not assert only that chapter count is greater than zero.

## 23. UI regression tests

Required scenarios:

### Test A — Manual isolation

1. Start Drawings universe.
2. Switch to Manuals.
3. Assert zero visible drawing nodes.
4. Assert manual roots visible.

### Test B — Manual expansion

1. Select IRPWM.
2. Expand.
3. Assert exactly 15 direct chapter children.
4. Assert chapter numbers 1–15.
5. Assert no drawing components among direct children.

### Test C — Chapter expansion

1. Expand Chapter 4.
2. Assert chapter remains visible.
3. Assert clauses/sections appear below Chapter 4.
4. Assert clauses belong to Chapter 4.
5. Assert no drawing-domain node appears.

### Test D — Collapse

1. Collapse manual.
2. Assert chapter descendants are hidden.
3. Manual root remains.

### Test E — Switch universe

1. Expand a manual.
2. Switch to Drawings.
3. Assert manual nodes are hidden.
4. Assert drawing graph is unaffected.

## 24. Performance

Do not render all clause/evidence descendants when a manual is first opened.

Use progressive expansion:

```
Manual click
  → chapters only

Chapter click
  → immediate sections/clauses

Clause click
  → evidence/facts
```

This keeps the graph readable and reduces force simulation load.

## 25. Visual language

Use distinct visual grammar.

### Manual

Document/book icon.

### Chapter

Numbered document section icon.

### Clause

Paragraph/section icon.

### Evidence

Source/page icon.

### Drawing

Engineering drawing icon.

### Revision

Revision/alteration icon.

The user should understand the difference without reading metadata.

## 26. Recommended implementation sequence

### P0 — Correct the structural model

1. Extract manual registry into a dedicated machine-readable structure.
2. Build deterministic manual nodes.
3. Build deterministic chapter nodes.
4. Add explicit `HAS_CHAPTER` edges.
5. Remove content-derived first-level manual children.
6. Remove drawing-derived children from Manuals universe.

### P1 — Correct ingestion

7. Make chapter registry authoritative.
8. Remove silent page-range fallback.
9. Add unmapped-page review bucket.
10. Preserve empty chapters.
11. Add extraction status.

### P2 — Correct runtime graph

12. Separate `manualKnowledgeGraph` and `drawingKnowledgeGraph`.
13. Make `getChildren()` hierarchy-aware.
14. Make manual expansion chapter-first.
15. Make chapter expansion content-first.
16. Preserve chapter ordering.

### P3 — Correct UI

17. Manual chapter count badges.
18. Chapter labels and page ranges.
19. Structured chapter layout.
20. Manual-specific node panel.
21. Universe-specific search.

### P4 — Validation

22. Manual structure validator.
23. Per-manual regression tests.
24. Browser expansion tests.
25. Universe isolation tests.
26. CI gate.

### P5 — Future bridge

27. Define bridge ontology.
28. Add evidence-backed bridge records.
29. Build combined projection.
30. Add explainable cross-universe navigation.

## 27. Definition of Done

This upgrade is complete when:

- selecting any manual reveals its actual registered chapters;
- the number of direct children equals the manual's chapter count;
- chapters appear in canonical order;
- chapter titles are authoritative;
- page ranges are preserved;
- chapter nodes exist even if extraction produced no clauses;
- clauses/sections are descendants of chapters;
- drawing knowledge does not contaminate manual hierarchy;
- drawing and manual graph data are separately loadable;
- switching universes is deterministic;
- tests cover every manual;
- no cross-universe relationship exists without explicit bridge evidence.

## 28. Product principle

The graph must represent the **structure of the source document first**, and the **knowledge extracted from the source second**.

Therefore:

```
Manual
  ↓
Actual Chapters
  ↓
Actual Sections / Clauses / Tables / Figures
  ↓
Evidence-backed Knowledge
```

not:

```
Manual
  ↓
Randomly selected extracted concepts
  ↓
Unclear relationships
```

This distinction is the foundation for making the Manuals knowledge graph reliable, navigable, searchable, and suitable for future evidence-backed connections to the Drawings knowledge graph.
