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


## Consolidated Manual readiness status

Each chapter audit row now exposes a deterministic `status`:

- `HEALTHY` — no chapter-level errors or warnings.
- `ATTENTION` — structurally valid but has coverage/extraction warnings that should be reviewed.
- `BLOCKED` — one or more hard validation errors prevent treating the chapter as structurally trustworthy.

Each manual receives the same status based on its chapter rows plus manual-level registry ownership errors/warnings. This is a readiness signal, not a semantic quality score: it identifies where extraction or ownership requires attention without hiding the underlying evidence lists and metrics.


## Readiness field contract

The machine-readable chapter row exposes both the legacy `status` field and explicit readiness fields:

- `readiness_status`: `HEALTHY`, `ATTENTION`, or `BLOCKED`.
- `readiness_reasons`: deterministic reason codes such as `complete_structural_coverage`, `no_source_headings`, `sparse`, `missing_pages`, `content_empty_pages`, or `structural_or_ownership_error`.
- `ownership_status`: `CLEAN` or `BLOCKED`.
- `ownership_issue_pages`: exact pages with registry ownership mismatches.

These fields are intended for downstream QA/UI consumption without requiring consumers to reinterpret free-form warnings. Chapter `ownership_issue_pages` is derived from the same registry mismatch records used by the corpus audit, so a page-level ownership failure is attributed to every affected observed/expected chapter and contributes to that chapter's `ownership_status`, `readiness_status`, and `errors`. The classification remains evidence-based and does not infer semantic completeness from chapter topics.

## Corpus audit summary

The audit report also exposes a dashboard-ready `summary` object containing total Manuals/Chapters, readiness counts, IDs requiring attention or blocked, coverage-class counts, aggregate page gaps (`missing`, `unmapped`, `content_empty`), and validation error/warning totals. The summary is derived from the detailed Manual and Chapter rows and does not replace their evidence.

## Manual readiness aggregation contract

Manual-level readiness is derived from an explicit `manual_chapter_rows` collection for the current Manual; it does not depend on global chapter-row ordering. The precedence is:

1. `BLOCKED` if the Manual has registry ownership errors or any chapter is `BLOCKED`.
2. `ATTENTION` if there are manual-scope ownership warnings, any chapter is `ATTENTION`, or `unmapped_pages` exist.
3. `HEALTHY` otherwise.

The report also exposes `manuals[].chapter_status_counts` so consumers can distinguish a Manual blocked by one chapter from a Manual whose chapters are only in attention.

Page-gap signals remain separate:

- `missing_pages`: expected registry pages not observed in chapter extraction.
- `unmapped_pages`: observed/extracted pages without an authoritative chapter owner; manual scope.
- `content_empty_pages`: owned observed pages with no persisted structural/content artifact.
- ownership mismatch: observed chapter ownership differs from the authoritative registry and is a hard validation failure.

These signals are not collapsed into ownership state. A Manual may therefore have a `HEALTHY` chapter while the Manual itself is `ATTENTION` because of manual-scope unmapped pages.

## Readiness reason aggregation

`readiness_reasons` is an ordered set of all applicable deterministic signals, not a first-match classification. A chapter may therefore expose `no_source_headings` together with `missing_pages`, or a hard `structural_or_ownership_error` together with coverage gaps. `readiness_status` still uses severity precedence: `BLOCKED` for hard errors, `ATTENTION` for non-error signals, and `HEALTHY` only when no attention signal applies. This preserves diagnostic evidence instead of hiding secondary extraction gaps.


## Manual readiness reason aggregation

The `manuals[]` rows now expose the same explicit readiness contract at Manual scope:

- `readiness_status`: `HEALTHY`, `ATTENTION`, or `BLOCKED`.
- `readiness_reasons`: ordered deterministic Manual-level signals.
- `status`: retained as a compatibility alias of `readiness_status`.

Manual reason codes are:

- `complete_manual_readiness` — no Manual-level or chapter-level readiness signal applies.
- `chapter_blocked` — at least one chapter is `BLOCKED`.
- `chapter_attention` — at least one chapter is `ATTENTION`.
- `registry_ownership_error` — the Manual registry ownership audit has hard errors.
- `registry_ownership_warning` — the Manual registry ownership audit has warnings.
- `unmapped_pages` — extracted pages exist outside the authoritative chapter registry.

All applicable signals are retained in deterministic order; they are not mutually exclusive. `readiness_status` still follows severity precedence: `BLOCKED` when a hard signal applies, `ATTENTION` for non-error signals, and `HEALTHY` only when no signal applies. Exact page evidence remains in `registry_page_audit`, `missing_pages`, `unmapped_pages`, and chapter-level readiness rows. These fields are QA metadata only and never participate in hierarchy construction.


## Corpus artifact preflight

The Gate K validator now explicitly treats an empty or invalid `all_chapters_extracted.json` as an external corpus-readiness blocker. It exits with status `2` and reports the artifact condition instead of raising an unhandled JSON error or implying that zero chapters constitute a valid audit. This keeps the distinction clear between a valid corpus audit result and an unavailable corpus artifact.


### Corpus schema preflight

Before Gate K performs chapter-level auditing, the validator verifies that the corpus artifact is valid JSON, is an object, contains a `manuals` list, and contains at least one Manual. Empty, malformed, or structurally invalid artifacts are reported as `BLOCKED` external corpus-readiness conditions rather than being interpreted as a valid zero-manual audit.

## Overlapping chapter-boundary policy

The authoritative chapter registry may intentionally assign the same source page to adjacent chapters, for example where a chapter boundary shares a page. Ingestion must preserve every registry owner rather than selecting the first matching chapter.

The ingestion contract is therefore:

- get_chapters_for_page() returns all authoritative owners for a page.
- Shared boundary pages are extracted into every owning chapter.
- Chapter pages_seen remains chapter-scoped and deterministic.
- The ownership audit compares observed owners with the full registry owner set.
- A shared page is not treated as an ownership error when the observed owner set exactly matches the registry.
- get_chapter_for_page() remains only as a backward-compatible single-owner helper; new ingestion logic must use the multi-owner function.

This prevents false extraction-gap warnings while preserving the authoritative registry as the source of chapter identity.

## Orphan source-heading policy

A source heading may reference a numeric parent that is not present in the extracted source-heading sequence. This is treated as an extraction/completeness signal, not as a structural contradiction.

The resolver preserves the observed heading as authoritative and records:

- `parent_heading_ref`: the parent reference stated/implied by its numeric structure.
- `parent_available_in_source: false`.
- `parent_resolution: CHAPTER_FALLBACK`.
- `Structure Status: AUTHORITATIVE_SOURCE_HEADING_ORPHAN`.

The canonical graph attaches such a heading directly to its authoritative Chapter with `HAS_SECTION`. The resolver never invents a missing parent node. If the missing parent is recovered in a later extraction, the next canonical generation deterministically reparents the existing heading.

This policy prevents incomplete source extraction from suppressing an otherwise valid chapter hierarchy while keeping the missing structural evidence explicit and auditable.
\n