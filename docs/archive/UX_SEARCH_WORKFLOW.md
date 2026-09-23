# Search → Drawing → Evidence → Graph

## Purpose

Define the first user-facing workflow for the RDSO Knowledge Graph so the graph supports engineering tasks instead of being the primary navigation surface.

## Primary workflow

```text
Search
  ↓
Results
  ↓
Entity detail
  ↓
Source / evidence
  ↓
Related knowledge
  ↓
Graph exploration
```

The workflow should work for drawing numbers, components, manuals, clauses, requirements, standards, revisions, procedures, defects, measurements, and ordinary engineering keywords.

## 1. Search

### Input

A single search box should accept:

- drawing number, e.g. `T-6155`
- drawing title or description
- component / part name
- material
- standard or specification
- manual / document name
- clause or requirement text
- revision identifier
- defect / failure mode
- procedure / inspection term
- measurement or tolerance
- general engineering keywords

### Behaviour

- Search should be available before the graph is loaded or manipulated.
- Exact identifiers should receive a strong match boost.
- Prefix and token matches should work for identifiers such as `T-6155`.
- Results should be grouped or clearly labelled by entity type.
- Empty, loading, and no-result states must be explicit.
- Keyboard navigation should be supported for the result list.
- Selecting a result must preserve the query and open the selected entity.

## 2. Search result card

Every result should expose enough information to choose the correct entity without opening several candidates.

Minimum fields:

| Field | Purpose |
| --- | --- |
| Entity type | Distinguish Drawing, Revision, Component, Document, Requirement, etc. |
| Display name | Human-readable identity |
| Canonical ID | Stable machine identity where useful |
| Revision / edition | Prevent selecting an obsolete version accidentally |
| Short description | Engineering context |
| Source indicator | Show whether supporting source/evidence exists |

For drawings, prefer showing drawing number and title together.

## 3. Entity detail

Selecting a result should open the existing intelligence surface in a focused state.

### Drawing detail minimum

1. Drawing identity
2. Current/applicable revision
3. Revision history
4. Components / assemblies
5. Key dimensions and measurements when available
6. Applicable standards / specifications
7. Related requirements
8. Related procedures / inspection criteria
9. Source document and page
10. Evidence available for important facts

The user should not need to understand graph physics, node IDs, or semantic modes to consume this information.

## 4. Evidence

Engineering claims should expose their provenance.

For each important fact, show:

- source document
- page / section / clause when available
- evidence quote or extracted value
- verification status
- confidence when available
- action to open the source

The UI should distinguish a directly evidenced fact from a graph-derived relationship.

## 5. Related knowledge

Use a compact relationship panel before exposing the full graph.

Useful sections:

- Used in
- Specified by
- Requires
- Inspected by
- Related drawings
- Related documents
- Revisions

Each item should be selectable without losing the current context.

## 6. Graph as a supporting surface

The Three.js graph remains useful for exploration, but it should answer follow-up questions such as:

> Show me how this drawing connects to its requirements and inspection procedure.

Required interactions:

- focus selected entity
- expand one-hop neighbourhood
- filter by entity type
- filter by relationship type
- highlight a path between two entities
- show why a connection exists
- open evidence from a graph relationship
- return to the previous entity without resetting the workspace

## 7. Context preservation

Navigation should preserve:

- current search query
- selected entity
- active semantic mode
- graph filters
- revision context

## 8. Accessibility and failure states

Minimum acceptance criteria:

- Search and result controls have accessible labels.
- Result focus is visible and keyboard usable.
- Information is not conveyed by colour alone.
- Text remains readable when browser zoom is increased.
- Source failures show an actionable error instead of an empty panel.
- Large result sets are bounded and remain responsive.

## 9. Acceptance criteria

The first implementation increment is complete when a user can:

1. Search `T-6155`.
2. See a clearly labelled drawing result.
3. Open the drawing without manually locating a graph node.
4. See revision and core metadata.
5. See at least one related source/evidence path when data exists.
6. Jump from the drawing into the graph with the drawing already focused.
7. Return to the search context without losing the query.

## Explicit non-goals

This increment should not:

- replace Three.js
- introduce a backend or database
- redesign the entire application
- migrate the canonical ID system
- add an LLM answer layer
- rebuild the graph dataset

Those changes should follow demonstrated user value from this workflow.

## Next implementation task

Implement only the search-result interaction needed to satisfy the acceptance criteria above, reusing the existing search index and entity-selection mechanisms. Keep the change local to the current application and add a focused regression check for the `T-6155` search flow.
