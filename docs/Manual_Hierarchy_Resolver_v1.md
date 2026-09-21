# Manual Structural Hierarchy Resolver v1

## Purpose

The Manual Knowledge Graph now has a deterministic hierarchy-resolution stage between source extraction and canonical graph consumption.

The resolver is intentionally non-LLM. It treats the authoritative chapter registry as the boundary contract and source-numbered headings as the next structural authority.

## Resolution contract

For each authoritative Manual Chapter:

`Manual → Chapter → Section → Subsection → Clause`

- `2` → `SECTION`, depth 1
- `2.1` → `SUBSECTION`, depth 2
- `2.1.1` → `SUBSECTION`, depth 3, retaining explicit depth metadata
- `ANNEXURE-I`, `APPENDIX-A`, `SCHEDULE-1` → explicit structural heading with `heading_kind`
- source order is preserved
- source page must remain inside the owning Chapter page range
- numeric child headings require their immediate numeric parent
- hierarchy depth may not jump by more than one level
- duplicate references are rejected
- backward numeric ordering is rejected

## Ownership

Every resolved heading carries:

- `chapter_id`
- `parent_heading_ref`
- `heading_kind`
- `depth`
- `order`
- source document/page/section/text
- extraction confidence and method

Clauses retain their direct Chapter ownership. The resolver additionally creates the deepest evidence-backed `HAS_CLAUSE` relationship whose heading reference prefixes the clause reference.

## Annexures and appendices

Annexures/appendices are structural children, not semantic topics. They are represented as explicit heading nodes and retain their source labels and provenance.

No Drawing node is introduced into this hierarchy.

## Publication

Run:

```bash
python scripts/resolve_manual_hierarchy.py
python scripts/validate_manual_hierarchy.py
```

The unified publication validator now includes **Gate K — Manuals Source-Heading Hierarchy**.

If a heading sequence is structurally invalid, the resolver does not partially materialize that chapter's source-heading hierarchy. Existing clause-derived hierarchy remains fallback evidence until the source structure is corrected.

## Next iteration

After this resolver is validated against all current manual source headings, the next step is to make the frontend consume the resolved source-heading tree directly, replacing clause-number-derived hierarchy as the primary Chapter → Section → Subsection source while preserving deterministic fallbacks and provenance.


## Publication pipeline integration

The deterministic resolver is now a shared in-memory publication primitive. The normal
`scripts/generate_canonical_kg.py` pipeline invokes `resolve_canonical_graph()` before
the final Manuals/Drawing isolation gate, so authoritative source-heading nodes and
nested `HAS_SECTION` relationships are produced during ordinary canonical generation.

The standalone `scripts/resolve_manual_hierarchy.py` command remains available for
diagnostics and repair workflows, but it no longer owns a separate implementation.

For valid source-heading sequences, clause ownership is refined to the deepest matching
numeric heading. Direct Chapter → Clause ownership remains intact for canonical
ownership/audit purposes. Invalid heading sequences do not replace the clause-derived
fallback structure.

Gate K now checks both the intermediate heading sequence and, when the canonical output
exists, the presence and authoritative status of the generated source-heading nodes and
their `HAS_SECTION` edges.
