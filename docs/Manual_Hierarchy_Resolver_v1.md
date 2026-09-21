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


### Ingestion contract

Manual ingestion now persists `headings[]` directly in each authoritative chapter record. Each heading carries its source document, source page, source reference/text, confidence, and deterministic extraction method. The ingestion stage deduplicates headings by `(reference, source_page, title)` and initializes structural artifact collections explicitly. This makes the resolver input complete and machine-readable rather than depending on a later enrichment pass.


### Coverage classification policy

Gate K classifies each chapter deterministically as `HEALTHY`, `SPARSE`, `NO_SOURCE_HEADINGS`, or `MALFORMED`. Sparse and missing-heading states are warnings because source PDFs may legitimately expose limited machine-readable heading structure; malformed references and out-of-range provenance remain hard failures. No missing source heading is synthesized. Chapters without authoritative headings therefore retain the resolver's existing fallback behavior until the real corpus audit demonstrates that a stronger extraction rule is justified.


## Machine-readable corpus audit

Gate K exposes a reusable `audit_manual_corpus(payload, canonical=None)` function and an optional JSON output mode:

```bash
python scripts/validate_manual_hierarchy.py --json-out data/knowledge-graph/reports/manual_hierarchy_audit.json
```

The report schema is `manual_hierarchy_audit_v1` and contains:

- `checked_chapters`: total chapters audited
- `class_counts`: counts for `HEALTHY`, `SPARSE`, `NO_SOURCE_HEADINGS`, and `MALFORMED`
- `manuals[]`: per-manual chapter/class counts
- `chapters[]`: one deterministic row per chapter, including page/headings/artifact metrics plus errors and warnings
- `error_count` / `warning_count` / `status`: aggregate audit outcome

This report is intended for the first real six-manual corpus audit. It makes the audit result machine-readable without requiring downstream tooling to parse console output. No corpus health result is assumed until the actual intermediate corpus is available.


## Extraction-gap preservation

Manual ingestion now preserves pages that fall outside the authoritative Chapter Boundary Registry as explicit `unmapped_pages` at the manual level and reports `total_unmapped_pages` at corpus level. Such pages are never silently assigned to the first or last chapter. This is an audit signal for registry/PDF alignment and is intentionally separate from chapter heading coverage.


## Manual corpus completeness matrix

The corpus audit now distinguishes four page states instead of treating extraction coverage as a single count:

- **registered/expected pages** — pages declared by the authoritative Chapter Boundary Registry.
- **observed pages** — pages actually assigned to the chapter by deterministic page ownership.
- **missing pages** — registered pages that were not observed in the chapter extraction.
- **unmapped pages** — extracted pages that could not be assigned to any registered chapter; these remain at manual scope.
- **pages with headings** — observed pages carrying at least one persisted source heading.
- **pages with clauses** — observed pages carrying at least one persisted clause.
- **content-empty pages** — observed chapter pages with no persisted heading, clause, table, figure, or evidence artifact.
- **coverage ratio** — observed chapter pages divided by registered expected pages.

The machine-readable manual_hierarchy_audit_v1 report includes these metrics in each chapters[] row, while manuals[] contains the corresponding per-manual aggregates. missing_pages, unmapped_pages, and content_empty_pages are emitted as explicit page lists so downstream QA can identify exact gaps rather than relying only on counts.

A page is considered non-empty only from persisted extraction provenance; arbitrary topic strings or semantic labels are not used to infer page coverage. This keeps completeness auditing independent from semantic enrichment.

The distinction is intentional:

missing != unmapped != content-empty

A missing page was expected but not observed; an unmapped page was observed but had no authoritative chapter owner; a content-empty page was observed and owned by a chapter but produced no persisted structural/content artifact.


## Manual-level ownership audit

Manual aggregates use the **union of registered chapter page ranges**, not the sum of chapter range lengths. This prevents shared chapter-boundary pages from inflating the expected-page denominator.

The audit also records `observed_pages_with_multiple_chapters`. A non-empty list means the extracted `pages_seen` data assigns the same physical page to more than one chapter and should be investigated against the authoritative boundary registry. `observed_page_owner_count` reports the number of distinct observed pages at manual scope.


## Observed-page ownership validation

The chapter-content validator now compares every persisted `pages_seen` value against the authoritative Manual Chapter Boundary Registry. Pages outside the registry are hard errors rather than being silently absorbed into a chapter. When a registry explicitly permits a shared one-page chapter boundary, observed ownership must match the registry owners exactly; unexpected multi-chapter ownership is rejected.


## Registry ownership in the corpus report

The machine-readable corpus audit now embeds `registry_page_audit` under each manual. It records registered and observed page counts, exact missing/unmapped page lists, multiply-owned pages, and explicit registry-vs-observed ownership mismatches. Ownership mismatches are hard audit errors; multiply-owned pages are retained as a diagnostic signal and are valid only when the authoritative registry assigns the same page to those chapters.
