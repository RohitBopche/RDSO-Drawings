# Phase P1: Manual Structure, Browsing & Pilot Strategy

**Reference:** [`docs/PROJECT_MASTER.md` Sections 26 (P1), 27 (Pilot Strategy), 28 (Pilot Criteria)](file:///f:/my%20git%20project/RDSO-Drawings/docs/PROJECT_MASTER.md#L1159-L1300)  
**Status:** Planned / Ready to Execute  
**Pilot Target Manual:** IRPWM 2024 (ACS 1–14) — 530 pages  
**Source Asset:** [`manuals/IRPWM 2024 Corrected Up To ACS - 14 (29-07-2026)-1.pdf`](file:///f:/my%20git%20project/RDSO-Drawings/manuals/IRPWM%202024%20Corrected%20Up%20To%20ACS%20-%2014%20(29-07-2026)-1.pdf)  

---

## 1. Objectives & Scope

Per Section 27 of `PROJECT_MASTER.md`, we do not semantically ingest all manuals simultaneously. Instead, we select one complete approximately 500-page manual (**IRPWM 2024**) and prove the complete canonical engineering loop:

```text
PDF
 ➔ source registry
 ➔ page segmentation
 ➔ hierarchy
 ➔ provisions
 ➔ evidence
 ➔ cross-references
 ➔ search
 ➔ question
 ➔ grounded answer
 ➔ citation
```

Once proven against the Pilot Acceptance Criteria (Section 28), the deterministic pipeline is scaled to the remaining 5 manuals.

---

## 2. P1 Roadmap Work Breakdown

| Step | Item | Requirement & Master Document Rule | Output Artifacts |
|---|---|---|---|
| **P1.1** | Complete Manual Hierarchy | Document ➔ Chapter ➔ Section ➔ Subsection ➔ Provision. Manuals universe entry shows only registered chapters. Direct Manual ↔ Drawing edges strictly prohibited. | `scripts/resolve_manual_hierarchy.py`, `data/manual_structure.js` |
| **P1.2** | Interactive Chapter Tree & TOC Navigator | Drawer tab for manuals shows ordered chapters with page ranges and clause counts. Real-time filtering by keyword or paragraph number. | `index.html` (Manuals TOC panel & search) |
| **P1.3** | Section / Subsection Navigation | Derived conservatively from source numbering when authoritative headings are absent, flagged as `DERIVED_FROM_CLAUSE_NUMBERING` with source page provenance. | `data/knowledge-graph/canonical/nodes.jsonl` |
| **P1.4** | Provision Detail & Answer Cards | Statutory provisions displayed with structured breakdown (condition, requirement, authority, inspection interval, tolerances) without altering source text. | UI Answer Card & Dossier |
| **P1.5** | Source Page Opening & Visual Evidence | Direct navigation from provision or fact to the exact page/crop in the PDF viewer without requiring manual document search. | Evidence viewer modal |
| **P1.6** | Search Result Cards with Provenance | Display entity type, display name, canonical ID, revision/edition, short description, and source indicator. | Search dropdown cards |
| **P1.7** | Context Preservation | Ensure search query, selected entity, universe mode, filters, and revision context are maintained across navigation. | Global application state |

---

## 3. Pilot Acceptance Checklist (Section 28)

- [ ] All 530 pages of IRPWM 2024 registered with content hashes.
- [ ] Deterministic chapter order (Chapters 1 through 15) preserved.
- [ ] Statutory provisions preserved with exact citation numbering.
- [ ] Source pages resolvable in the UI with single-click opening.
- [ ] Full-text lexical + identifier search indexes every provision.
- [ ] Natural language queries retrieve valid retrieved evidence.
- [ ] Cross-references classified (`RESOLVED`, `AMBIGUOUS`, `EXTERNAL`, `NOT_FOUND`).
- [ ] Uncertain or derived extraction explicitly flagged.
- [ ] Zero ungrounded claims generated.
- [ ] Automated regression tests pass and rerunning pipeline produces deterministic output.
