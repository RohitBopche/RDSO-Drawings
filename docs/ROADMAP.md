# RDSO Manuals Knowledge Base — Project Roadmap

**Status:** **The only live project document.** Goal, current state, architecture, rules, data contracts, roadmap, metrics, research and workflow all live here.
**Everything else** is history in [`docs/archive/`](archive/). Do not plan from archived docs, and do not create new plan docs: change this file.
**Last updated:** 2026-09-28

## Contents

1. [Goal](#1-goal)
2. [Scope decisions](#2-scope-decisions-final)
3. [Where we are today](#3-where-we-are-today-audit-2026-09-28)
4. [Target architecture](#4-target-architecture)
5. [Data contracts](#5-data-contracts) (incl. letters & amendments)
6. [Answer contract & AI guardrails](#6-answer-contract--ai-guardrails)
7. [Roadmap phases](#7-roadmap-phases)
   - [Corpus register](#75-corpus-register)
8. [Timeline](#8-timeline-indicative)
9. [Metrics](#9-metrics-tracked-in-ci-from-phase-2)
10. [Research & experiments](#10-research--experiments)
11. [Repository, pipeline & commands](#11-repository-pipeline--commands)
12. [How we work](#12-how-we-work)
13. [Non-negotiable rules](#13-non-negotiable-rules)
14. [Immediate next tasks](#14-immediate-next-tasks)

---

## 1. Goal

> Ask any question about Indian Railways **manuals (20+) and letters/circulars (100+, growing)** in plain language, and get a correct, AI-quality answer that **cites the exact manual para or letter, with page**, and says whether a later letter or correction slip modifies it.
> The system runs **fully offline** on an office PC.
> It **gets better with use** without ever inventing rules.

### What "done" looks like (v1)

The engineer types *"What is the permissible gap in SEJ for LWR on girder bridge?"* and gets:

1. a 2–6 sentence answer;
2. the limits/values, quoted from the source;
3. citations such as `IRPWM 2024 ACS-14 · Para <n> · p. <n>`;
4. clicking a citation opens the PDF at that page with the text highlighted;
5. an **"as modified by"** line when an in-force letter or ACS changes that para (e.g. `modified by RB letter No. … dt …`);
6. related provisions (referenced paras, same table, related letters);
7. 👍 / 👎 / "correct para is…" feedback.

If the manuals don't cover the question, the answer says so and shows the closest provisions.

---

## 2. Scope decisions (final)

| Decision | Choice | Reason |
|---|---|---|
| Primary product | **Manuals + letters Q&A and search** | This is the stated goal. |
| Corpus | **20+ manuals, 100+ letters/circulars/correction slips**, then more over time | Volume estimate: ~8–10k pages, ~60–120k chunks. SQLite, CPU embedding and local LLM all handle this comfortably. |
| Onboarding | **Config and catalogue driven, no code change per document.** Target: a new manual in ≤ 1 hour of human effort, a new letter in ≤ 5 minutes. | 6 hand-coded manuals don't scale to 120+ documents. |
| Source files | PDFs live **outside git** in `corpus/` (shared drive or Git LFS); git tracks only `corpus/catalogue.csv` with metadata and SHA-256 | 120+ PDFs would make the repo unusable. |
| Drawings / 3D digital twin | **Frozen.** Keep working, no new features until v1 ships (Phase 9). | The work stays and nothing is deleted. |
| 3D knowledge graph | "Explore" tab, not the home screen | Engineers need answers first and graphs second. |
| Manual ↔ Drawing links | None in the base KG; only evidence-backed `REFERENCES` later | Keeps manual chapters free of drawing noise. |
| Storage | **SQLite** — FTS5 (BM25) + `sqlite-vec` + plain tables | One file, no server, copies to any PC. PostgreSQL only if a multi-user central deployment is ever needed; Neo4j only if graph workloads prove it. |
| Runtime | Local Python service (FastAPI) on `127.0.0.1` + existing web UI | Needed for LLM and reranker. Browser-only BM25 search stays as a fallback. |
| LLM | Local via `llama.cpp` / Ollama. Default Qwen2.5-7B-Instruct Q4_K_M, alternative Llama-3.1-8B-Instruct. Configurable. | CPU with 16 GB RAM; GPU optional. |
| Embeddings | `bge-m3` (multilingual) or `bge-small-en-v1.5` (fast) | Local, strong retrieval. |
| Reranker | `bge-reranker-v2-m3` | Largest precision gain per effort. |
| Truth policy | LLM answers **only from retrieved chunks**. Numbers are verified against the source. Everything is `EXTRACTED` until a human sets `VERIFIED`. | Safety-critical domain. |
| Pilot manual | **IRPWM 2024 (ACS-14)** proves the pipeline, then every other manual goes through the same pipeline in batches. | Largest, most-used manual. |
| Letters before AI answers | The letters/amendments layer ships **before** v1 LLM answers | An answer that ignores a later letter can quote a superseded rule. That is a safety issue. |

---

## 3. Where we are today (audit 2026-09-28)

All numbers were regenerated from the repo at `104e189`. The full audit is archived at [`archive/AUDIT_2026-09_KNOWLEDGE_BASE.md`](archive/AUDIT_2026-09_KNOWLEDGE_BASE.md).

### 3.1 Scorecard

| Area | State |
|---|---|
| Sources | 6 manuals (IRPWM 2024, USFD, AT Weld 2022, FBW 2022, Track Machine Manual, Small Track Machines Manual), 1,485 pages, SHA-256 registry ✅ |
| Corpus coverage | **6 of 20+ manuals; 0 of 100+ letters** ❌ |
| Onboarding | Chapter registries, page ranges and topics are hand-typed per manual in `ingest_all_manual_chapters.py` ❌ |
| Letters / amendments | No letter, circular or correction-slip model; ACS only in the edition name ❌ |
| Page text | Full text kept in `data/knowledge-graph/raw/extracted_pages.jsonl` (2.6 M chars) ✅ |
| Hierarchy | 83 chapters, deterministic ✅; 257/673 IRPWM clauses mis-numbered/mis-parented ❌ |
| Clause text in KG | `desc: "..."` on all 1,838 clauses; text capped at 1,200 chars, evidence at 500; 1,561/3,772 requirements `"..."` ❌ |
| Tables | 178 pages with tables → 57 labels, 0 rows ❌ |
| Scanned pages | 75 near-empty pages, no OCR ❌ |
| Search | Substring match over titles (`index.html` `rankSearchResults`); the built `exports/search_index.json` is never loaded ❌ |
| "Semantic" | 29 hand-written synonyms ❌ |
| Q&A | 13 hand-written answers (`CANONICAL_QA_DATABASE`) ❌ |
| Verification flags | 100 % `"verified"`, hardcoded, none reviewed ❌ |
| Self-improvement | None. The "Learning" tab is user flashcards. ❌ |
| Tests / CI | 126 pytest + gates A–K pass, but they check structure only; some tests re-implement app logic ❌ |
| Reproducibility | Pipeline rebuild is deterministic ✅ |
| Offline | ✅ |

### 3.2 Key defects and where they live

| # | Defect | Location | Fixed in |
|---|---|---|---|
| D1 | Text caps `[:1200]`, `[:500]`, `[:280]+"..."` | `scripts/ingest_all_manual_chapters.py:484-488`, `scripts/generate_canonical_kg.py:614,846,876,953-963,991,1038` | 1.1 |
| D2 | Headers, footers and page numbers merged into para numbers (e.g. STMM `PARA_1616`, `"1012 Functional Requirements \n97"`) | clause regex in `ingest_all_manual_chapters.py` | 1.2, 1.3 |
| D3 | Tables not extracted as rows | — | 1.4 |
| D4 | No OCR | — | 1.5 |
| D5 | `"verified"` hardcoded in 12 places | `scripts/build_canonical_pipeline.py` | 1.6 |
| D6 | Substring search; 29-entry synonym map | `index.html:9938-10866` | 2.x |
| D7 | Canned QA + regex intent | `index.html:7954-8460` | 6.7 |
| D8 | No retrieval/answer evaluation | `tests/` | 2.4, 6.6 |
| D9 | 497 KB `index.html` built by a 417 KB Python templater *and* patched by `scratch/*.py`; literal `\n` at line 2843; 22 MB bundle loaded at startup | `scripts/build_updated_app.py`, `index.html` | 0.4, 2.6 |
| D10 | Repo hygiene: 200 MB git pack; tracked `.bak`, `node_modules`, `__pycache__`, `scratch/`; the same data held in 5 overlapping files | root, `data/` | 0.2, 0.3 |
| D11 | EXP-01 benchmarked a different USFD file (147 pp) than the pipeline (157 pp) | `research/benchmarks/` | 1.9 |
| D12 | Hand-coded per-manual chapter registries (page ranges, topics) | `ingest_all_manual_chapters.py:31-200` | 1.10, 3.x |
| D13 | No document-type model for letters, circulars or correction slips, and no amendment links | schemas | 1.11, 4.x |
| D14 | 22 MB app bundle for 6 manuals, so 20+ manuals + letters would reach ~100 MB+; the whole-corpus 3D graph won't render | `data/rdso_kg_data.js`, `index.html` | 2.5, 5.5 |

### 3.3 Documentation audit (resolved by this file)

There were 12 plan/architecture docs (~7,800 lines) with 5 different phase numberings. They drifted between a turnout digital twin and a manuals Q&A system, and they gave conflicting database advice (SQLite vs PostgreSQL). Their status claims were not measured: "100 % verified", and "real-time autocomplete" from an index the app never loads. None defined a self-improvement loop or a measurable definition of done. All of them are now archived. What was worth keeping is merged below.

---

## 4. Target architecture

```text
 corpus/manuals/*.pdf   corpus/letters/*.pdf   corpus/acs/*.pdf      + corpus/catalogue.csv
      │
 ⓪ INTAKE ── SHA-256 dedup ─ doc type (MANUAL | LETTER | CIRCULAR | ACS) ─ metadata from catalogue
      │       + auto-extracted (letter no., date, issuer, subject) ─ only new/changed files reprocessed
      ▼
 ① INGEST ── validate ─ PyMuPDF text+layout ─ OCR (Tesseract eng+hin) on empty/scanned pages
      │       table extraction ─ header/footer strip ─ per-manual numbering profile
      ▼
 ② STRUCTURE ── Manual → Chapter → Section → Para → Sub-para  (+ Table, Figure, Annexure)
      │          Letter  → Subject → Para;  ACS → amended paras
      │          TOC auto-detected (PDF outline / contents page); profile YAML only for overrides
      │          full text, page, bbox, edition, status=EXTRACTED, computed confidence
      │          per-document QUALITY REPORT → publish only if it passes
      ▼
 ③ CHUNKS  data/kb/chunks.jsonl   (para | sub-para | table-row | figure caption | definition)
      ▼
 ④ INDEXES  data/kb/kb.sqlite
      ├─ FTS5 (BM25)           exact words, para numbers, values
      ├─ sqlite-vec            meaning (embeddings)
      ├─ graph tables          HAS_*, REFERENCES, AMENDS/SUPERSEDES/CLARIFIES, DEFINES
      └─ feedback / logs       queries, clicks, votes, corrections
      ▼
 ⑤ QUERY  normalise (abbrev, units, para forms) → BM25 ∪ vector (RRF)
          → graph expand (parent, referenced paras, table siblings, in-force amending letters)
          → rerank → top-8 → applicability / in-force check → conflict check
      ▼
 ⑥ ANSWER  local LLM, cite-only prompt → citation + number verifier → answer | "not found"
      ▼
 ⑦ UI  Ask box · answer card · citations → PDF.js page viewer · related · Explore graph
      ▼
 ⑧ LEARN  nightly: failed queries → review · synonym mining · gold-set growth · tuning
```

**Ownership rule:** no frontend feature owns engineering truth. The canonical data and evidence layer owns it, and every interface consumes it.

**Retrieval priority:** exact identifier/para → exact title → lexical relevance → metadata → semantic similarity → graph context. Vector search never replaces lexical search.

---

## 5. Data contracts

### 5.1 Identity

- Every entity has a stable, machine-safe ID, type, name, aliases, status, provenance and verification state. IDs are never filenames or display labels.
- The logical document (e.g. `DOC:IRPWM:2024:ACS14`) is separate from the physical source file, which keeps its SHA-256.
- Hierarchy: `DOCUMENT_FAMILY → DOCUMENT → EDITION/REVISION → SOURCE_FILE → PAGE → CHAPTER/SECTION/CLAUSE/TABLE/FIGURE`.
- Para IDs follow one pattern per manual: `CLAUSE:<MANUAL>:CH_<nn>:PARA_<number>`. Mixed patterns (`CLAUSE:TMM:PARA_421`) are migrated.

### 5.2 Manual structure

- `MANUAL → CHAPTER → SECTION → SUBSECTION → CLAUSE`. Selecting a manual first shows only its registered chapters, in order, with page ranges.
- Sections derived from clause numbering are marked `DERIVED_FROM_CLAUSE_NUMBERING`.
- **Orphan headings:** preserve the heading, attach it to its chapter, and record the missing parent. Never invent the parent.
- TABLE, FIGURE and EVIDENCE become structural nodes only when label-driven and evidence-backed.
- Para numbers must be monotonic within a chapter and carry the chapter prefix where the manual uses one. Violations go to review.

### 5.3 Chunk (retrieval unit)

```jsonc
{ "id": "...", "manual": "DOC:IRPWM:2024:ACS14", "edition": "ACS-14",
  "chapter": "CHAPTER:IRPWM:CH_02", "para": "228", "parent": "...",
  "type": "para|subpara|table_row|figure_caption|definition",
  "text": "<full, untruncated source text>", "page": 81, "bbox": [x0,y0,x1,y1],
  "extraction_method": "text|ocr|table", "confidence": 0.0-1.0,
  "status": "EXTRACTED", "text_sha256": "..." }
```

### 5.4 Evidence & verification

- Evidence carries: document, edition, page, chapter/para, full quote, bbox, extraction method, timestamp, confidence, status, and reviewer/date where applicable.
- **Status vocabulary:** `EXTRACTED` (default) · `VERIFIED` (human only, with reviewer id and date) · `DERIVED` · `INFERRED` · `CONFLICTING` · `REJECTED` · `UNKNOWN`.
- Confidence is **computed** from extraction method, OCR quality and numbering consistency. It is never hardcoded.
- Required path: **Answer → Provision/Fact → Evidence → Source page**. The user never has to hunt for the source.

### 5.5 Engineering facts

- Numeric values carry: value, unit, nominal/min/max, fact type, applicability, evidence and status.
- Each value is marked specified, measured, derived or inferred. An inferred value is never shown as an official requirement.
- A rule may be decomposed as `CONDITION → REQUIREMENT → ACTION → AUTHORITY → DOCUMENTATION → INSPECTION → EXCEPTION`. The decomposition never replaces the original text.

### 5.6 Cross-references & versions

- References ("Para 630", "Annexure-8/6", "Chapter IV", "as per USFD Manual") are first-class edges. Each stores source para, target, reference text and resolution state: `RESOLVED` · `AMBIGUOUS` · `BROKEN` · `EXTERNAL` · `NOT_FOUND`.
- Version edges: `HAS_EDITION`, `HAS_REVISION`, `SUPERSEDES`, `AMENDS`/`AMENDED_BY`, `CORRECTS`, `VALID_DURING`, `WITHDRAWN_BY`.
- Never infer supersession from dates alone. The source must say it.

### 5.7 Letters, circulars & correction slips

**Document types:**
- `MANUAL`
- `CORRECTION_SLIP` (ACS/CS)
- `LETTER` (Railway Board, RDSO directorate)
- `CIRCULAR` (zonal/divisional)
- `SPECIFICATION`/`CODE` (IRS, IS)
- `DRAWING`

**Letter record** (catalogue + auto-extraction, human-confirmed):

```jsonc
{ "id": "LETTER:RB:2019_TRACK-III_TK_xx:2023-05-12", "type": "LETTER",
  "letter_no": "…", "date": "2023-05-12", "issuer": "Railway Board | RDSO/<Dte> | <Zone> HQ",
  "subject": "…", "addressees": ["…"], "file_no": "…", "language": "en|hi|bilingual",
  "category": "policy|technical_instruction|clarification|correction_slip|procedure",
  "references": ["LETTER:…"],                         // earlier letters cited
  "effects": [ { "action": "AMENDS|SUPERSEDES|CLARIFIES|ADDS|WITHDRAWS",
                 "target": "CLAUSE:IRPWM:CH_02:PARA_228 | LETTER:…",
                 "evidence": "<quoted sentence>", "status": "EXTRACTED|VERIFIED" } ],
  "effective_from": "…", "in_force": true, "sha256": "…" }
```

**Extraction:**
- Letter number, date, issuer and subject are extracted by regex from the letterhead block.
- Effect phrases are detected: "in supersession of", "in partial modification of", "Para … of IRPWM stands amended/substituted/deleted", "the following shall be added".
- Each target resolves like a cross-reference (§5.6).

**Rules:**
- An `AMENDS`/`SUPERSEDES`/`WITHDRAWS` link affects answers only after a human sets `VERIFIED`. Until then the answer shows "possibly modified by … (unverified)".
- A letter superseded by a later letter is `in_force: false` and stays searchable, with a banner.
- Each para has a **timeline**: original manual text → ACS → letters, newest first.
- Letters are chunked per paragraph. Short letters (< 1 page) are one chunk plus the subject line.

### 5.8 Relationship vocabulary

- The controlled list lives in `data/knowledge-graph/schemas/vocabularies/relationship-types.json`, which is authoritative and covers all types in use.
- Direction is meaningful, and both endpoints must exist.
- A new type needs a vocabulary update, a fixture and a test before use.
- Core manual edges: `HAS_SECTION`, `HAS_CLAUSE`, `HAS_TABLE`, `HAS_FIGURE`, `HAS_EVIDENCE`, `REFERENCES`, `DEFINES`, `APPLIES_TO`, `REQUIRES`, `PROHIBITS`, `EXCEPTION_TO`.
- Amendment edges (letters/ACS → para/letter): `AMENDS`, `SUPERSEDES`, `CLARIFIES`, `ADDS`, `WITHDRAWS`, `CITES`.

### 5.9 Raw → intermediate → canonical

- `raw/` is direct extraction and is never edited by hand.
- `intermediate/` holds normalised candidates and review queues.
- `canonical/` holds validated output.
- Raw source text is never overwritten by normalised output. Only validated canonical data feeds search and answers.

---

## 6. Answer contract & AI guardrails

### 6.1 Answer structure

1. Direct answer.
2. Applicable rule/requirement.
3. Procedure steps (in source order).
4. Authority/responsibility.
5. Exceptions.
6. Citations: manual · edition · chapter · para · page, plus the quoted excerpt.
7. Related provisions.
8. **Amendment status:** "as modified by …", "superseded by …", or "no known amendment as of <catalogue date>".
9. Status badge (`EXTRACTED`/`VERIFIED`) and confidence.
10. Conflict or edition warning where applicable.

### 6.2 Conflicts

- Never resolve conflicts silently. Show both provisions with version, scope, date and evidence.
- If precedence isn't documented, show **"Conflict/ambiguity detected — manual verification required."**
- Never pick a provision just because it ranked higher.
- A later letter overrides a manual para **only** through a `VERIFIED` `AMENDS`/`SUPERSEDES` link. A newer date alone is not enough. Otherwise show both, with a conflict warning.
- Never answer from a superseded or withdrawn letter without saying so.

### 6.3 Guardrails

The AI layer must never invent a rule, para number, page, dimension or standard. It must never change source meaning, present inference as official text, or ignore version conflicts.

The LLM gets only a bounded, numbered evidence set, never the whole corpus.

A verifier checks every cited `[n]` and every number/unit/para against the cited chunk. Anything unverified is redacted and flagged.

If no evidence clears the threshold, the answer is **"Not found in the loaded manuals"**, followed by the nearest provisions.

---

## 7. Roadmap phases

Each phase ends with a **gate** that CI checks. Durations assume one developer.

**Two tracks run in parallel from Phase 3:**
- *Engineering* (Phases 5–7) builds retrieval and answers.
- *Content* (Phases 3–4) onboards manuals and letters with the Phase 1 pipeline. It is mostly catalogue and review work, and a domain assistant can do it.

### Phase 0 — Clean the ground (≈ 3 days)

| # | Task | Output |
|---|---|---|
| 0.1 | Freeze drawings/twin features | README status line ✅ (done) |
| 0.2 | Remove tracked junk: `index.html.bak`, `node_modules/`, `__pycache__/`, `scratch/`, and the committed `package-lock.json` that is ignored | cleaner repo |
| 0.3 | **Move source PDFs out of git:** `corpus/{manuals,letters,circulars,acs,specs}/` (gitignored; shared drive or Git LFS). Git tracks `corpus/catalogue.csv` (id, type, title, edition/letter no., date, issuer, file, SHA-256, status). Existing `manuals/`, `drawings/` and `crops/` move there. | repo < 50 MB, catalogue |
| 0.4 | Fix `index.html:2843` literal `\n`; fix the broken Blueprint path in `rdso_canonical_kg.json` metadata | — |
| 0.5 | Consolidate docs into this file | ✅ (done) |
| 0.6 | `Makefile` / `run.ps1` targets: `intake`, `ingest`, `index`, `serve`, `eval`, `report`, `test` | one-command workflow |

**Gate 0:** fresh clone + corpus folder → `make test` passes on Windows and Linux.

### Phase 1 — Stop losing knowledge, generic pipeline (≈ 3 weeks) — *highest priority*

| # | Task | Files |
|---|---|---|
| 1.1 | Remove every text cap. Canonical para gets full `text`; `summary` is optional and separate. | `ingest_all_manual_chapters.py`, `generate_canonical_kg.py` |
| 1.2 | Header/footer/page-number stripping via layout bands (`get_text("dict")`, y-position + repetition across pages) | `scripts/kb/layout.py` |
| 1.3 | Numbering detectors (`NNN(n)(a)`, `N.N.N`, `N.N`, Roman chapters) auto-selected per document. Enforce prefix and monotonic order; violations go to a review file. | `scripts/kb/numbering.py` |
| 1.4 | Table extraction (`page.find_tables()`; Docling if EXP-01 wins). Rows + caption; one chunk per row. | `scripts/kb/tables.py` |
| 1.5 | OCR pages with < 50 chars (Tesseract `eng+hin`); `extraction_method=ocr`, lower confidence. Needed heavily for scanned letters. | `scripts/kb/ocr.py` |
| 1.6 | Honest status: default `EXTRACTED`, computed confidence | `build_canonical_pipeline.py` |
| 1.7 | Emit `data/kb/chunks.jsonl` per §5.3, including bbox | new |
| 1.8 | Migrate mixed para-ID patterns to §5.1 | migration script |
| 1.9 | Redo EXP-01 on the registry's USFD file; record Docling vs PyMuPDF | `research/benchmarks/` |
| 1.10 | **Replace hand-coded chapter registries:** auto-detect the TOC from the PDF outline, else parse the "Contents" page, else use heading cues. `corpus/profiles/<doc>.yaml` only for overrides (page offset, chapter list fixes). Re-derive the existing 6 manuals and diff against the current registry. | `scripts/kb/toc.py` |
| 1.11 | Document-type model (§5.7) in schemas + catalogue; intake step with SHA-256 dedup and incremental processing (unchanged files skipped) | `scripts/kb/intake.py`, schemas |
| 1.12 | **Per-document quality report**: pages covered, OCR %, numbering consistency, tables, unresolved refs, TOC match. A document is published to the index only if it passes. | `scripts/kb/report.py` → `data/kb/reports/` |

**Gate 1:**
- 0 chunks with `"..."`, truncated or empty text;
- ≥ 98 % of pages covered per document;
- ≥ 99 % para-number consistency;
- tables present as rows;
- 0 `VERIFIED` without a reviewer;
- a 50-para hand-checked IRPWM fixture matches exactly;
- the 6 existing manuals re-ingest with **no hand-coded registry**, and their chapters match the old registry.

### Phase 2 — Real search (≈ 2 weeks)

| # | Task |
|---|---|
| 2.1 | `data/kb/kb.sqlite` with FTS5 (porter + unicode61); weights: para title/letter subject > text > chapter. Filters: document type, manual, issuer, year, in-force only. |
| 2.2 | Domain lexicon `data/kb/lexicon.yaml`: abbreviations (LWR, SEJ, USFD, ADEN, SSE/P.Way, CMS, TWS, GRSP, ERC, AT, FBW, RB, CE, PCE…), unit forms (`60kg`/`60 kg`, `1:12`/`1 in 12`), para forms (`Para 262`, `P-262`, `262(3)`), letter-number forms. Phase 7 appends to it. |
| 2.3 | **Gold set** `eval/questions.jsonl`: start with 150 questions (100 IRPWM, 10 per other manual) with expected para/page/value, including 15 "not in corpus" negatives. Grows with every onboarded document (§7.5). A domain expert reviews. |
| 2.4 | `scripts/kb/eval_retrieval.py`: Recall@5/10, MRR, zero-result rate, **reported per document**. Runs in CI and fails on regression. |
| 2.5 | Browser fallback: BM25 index **sharded per document** and loaded lazily (MiniSearch), so size stays flat as the corpus grows. Retire the monolithic 22 MB bundle. |
| 2.6 | UI: results show title, highlighted snippet, and manual · para · page or letter no. · date. Click → bundled **PDF.js** viewer at the page with the bbox highlighted. Search stays keyboard-accessible, with explicit empty, loading and error states. |
| 2.7 | Delete `rankSearchResults`, `rankHybridSearchResults` and `SEMANTIC_SYNONYM_REGISTRY`. |

**Gate 2:** BM25 Recall@10 ≥ 0.75; search p95 < 300 ms at the full-corpus size (tested with a synthetic 100k-chunk index).

### Phase 3 — Manuals scale-out: 6 → 20+ (content track, ≈ 1–2 days per manual, parallel)

| # | Task |
|---|---|
| 3.1 | Owner fills the **corpus register** (§7.5) with every target manual: title, edition, latest ACS, file, priority. |
| 3.2 | Onboard in batches of 3–5, highest-use first. Per document: `make intake ingest report` → fix profile overrides → quality report passes → add ≥ 10 gold questions → `make index eval`. |
| 3.3 | Treat ACS/correction slips as separate `CORRECTION_SLIP` documents linked to their manual. Keep the incorporated edition as the base text. |
| 3.4 | Cross-manual references ("as per USFD Manual para …") resolve across documents. |
| 3.5 | Track onboarding effort per manual. If it's > 1 hour of human work, improve the generic pipeline before adding more profile overrides. |

**Gate 3 (per manual):**
- quality report passes;
- ≥ 10 gold questions;
- per-document Recall@5 ≥ 0.8;
- no regression on the other documents.

### Phase 4 — Letters, circulars & amendments (content + engineering, ≈ 3 weeks, then continuous)

| # | Task |
|---|---|
| 4.1 | Letter intake: catalogue row (can be pre-filled from the letterhead by `intake.py`, then confirmed); OCR where scanned; bilingual handling. |
| 4.2 | Letterhead parser: letter no., date, issuer, subject, file no., addressees, references. |
| 4.3 | Effect extractor: "supersession / partial modification / stands amended / substituted / deleted / added" → `effects[]` with target resolution (§5.7). |
| 4.4 | **Amendment review queue:** every extracted `AMENDS`/`SUPERSEDES`/`WITHDRAWS` link needs a human decision before it affects answers. |
| 4.5 | Para timeline view: original text → ACS → letters (in-force first); superseded letters shown with a banner. |
| 4.6 | Letter-to-letter chains: supersession and "reference" graph, and the in-force status computed from it. |
| 4.7 | Search filters and ranking: in-force letters rank above superseded ones; "latest instruction on X" queries sort by date. |
| 4.8 | Gold set: ≥ 50 letter/amendment questions ("what is the latest instruction on…", "has Para X been modified?", "which letter superseded …?"). |
| 4.9 | Bulk-load the first 100+ letters; after that, a new letter takes ≤ 5 minutes to onboard. |

**Gate 4:**
- 100 % of letters have number, date, issuer and subject;
- ≥ 95 % of detected effects resolved to a target or marked `EXTERNAL`/`NOT_FOUND`;
- 0 unreviewed amendment links applied to answers;
- amendment-question Recall@5 ≥ 0.85.

### Phase 5 — Semantic retrieval + graph (engineering track, ≈ 2 weeks)

| # | Task |
|---|---|
| 5.1 | Embed chunks → `sqlite-vec`, incrementally, keyed by `text_sha256`. At ~100k chunks, use int8 quantisation or 384-d `bge-small`, which keeps vectors ≲ 200 MB. A full re-embed takes ~1–3 h on CPU and runs nightly only for changed chunks. |
| 5.2 | Hybrid: BM25 top-50 ∪ vector top-50 → Reciprocal Rank Fusion. |
| 5.3 | Cross-reference parser → `REFERENCES` edges with resolution state (§5.6), plus a broken/ambiguous reference report. |
| 5.4 | Definitions/glossary → `DEFINES` edges, used in query expansion. |
| 5.5 | Query-time graph expansion (parent, referenced paras, table siblings, **verified in-force amendments**; ≤ 10). The Explore graph loads neighbourhoods on demand and never the whole corpus. |
| 5.6 | Cross-encoder rerank → top 8. |
| 5.7 | Run EXP-03 and record the result. |

**Gate 5:** Recall@5 ≥ 0.85, MRR ≥ 0.70 over the whole gold set. Any stage that doesn't help on eval is removed.

### Phase 6 — Offline AI answers (≈ 3 weeks)

| # | Task |
|---|---|
| 6.1 | `serve/` FastAPI: `/search`, `/ask` (streaming), `/chunk/{id}`, `/pdf/{doc}/{page}`, `/timeline/{para}`, `/feedback`. Binds `127.0.0.1` only. `start.bat` / `start.sh`. |
| 6.2 | LLM adapter (llama.cpp / Ollama, `config.yaml`). A model-free mode still returns ranked evidence. |
| 6.3 | Cite-only prompt that produces the §6.1 structure, including the amendment status. |
| 6.4 | Verifier + conflict/edition/in-force check per §6.2–6.3. |
| 6.5 | Answer UI: streaming card, citation chips → PDF viewer, evidence drawer, "as modified by" chips → letter, related provisions, status badges. |
| 6.6 | Answer eval: faithfulness, citation precision, negative-refusal rate, **amendment-awareness** (the answer cites the in-force letter when one exists). |
| 6.7 | Delete `CANONICAL_QA_DATABASE`, `detectQuestionIntent`, `answerEngineeringQuestion`. |

**Gate 6:**
- 100 % of answers cited;
- 100 % of numbers verified or redacted;
- amendment-awareness ≥ 0.95;
- negative refusal ≥ 0.9;
- answer p95 < 20 s on a 16 GB CPU PC;
- works with the network unplugged.

**→ Release v1.0: offline Q&A over all onboarded manuals + letters.**

### Phase 7 — Self-improvement loop (≈ 2 weeks, then continuous)

| # | Task |
|---|---|
| 7.1 | Log every query locally: text, normalised form, filters, retrieved ids, answer, citations, clicks, latency. |
| 7.2 | Feedback UI: 👍/👎, "correct para/letter is …" picker, "wrong number" flag, "this is outdated — see letter …". |
| 7.3 | **Admin review page:** zero-result queries, 👎 answers, extraction issues hit by users, low-confidence chunks shown in answers, pending amendment links, documents failing the quality report. Actions: fix text, mark `VERIFIED`, confirm/reject amendment, add synonym, add to gold set. Each decision keeps the candidate, reviewer, timestamp and notes. |
| 7.4 | Nightly `scripts/kb/improve.py`: mine reformulations and clicks into lexicon candidates; turn confirmed (query → para/letter) pairs into gold-set additions; grid-tune BM25 weights, RRF k and rerank cut-off; optional embedding fine-tune once there are ≥ 500 confirmed pairs. |
| 7.5 | **Promotion rule:** promote only when eval does not regress, otherwise auto-rollback. Versions live in `data/kb/config_history/`. |
| 7.6 | "Corpus gap" signal: frequent queries with no good source → suggest which manual or letter is missing from the corpus. |
| 7.7 | Review-debt metrics: % of cited chunks `VERIFIED`, pending amendment links, queue age. |

**Gate 7:** each weekly cycle shows the gold set growing and Recall@5 / 👍-rate flat or rising.

### Phase 8 — Wider sources & language (continuous)

| # | Task |
|---|---|
| 8.1 | IRS specifications (T-10, T-29, T-12…), IRSOD BG, relevant IS codes (IS 2062, IS 1030, IS 12994). Same pipeline, `SPECIFICATION`/`CODE` types. |
| 8.2 | Zonal/divisional circulars with jurisdiction metadata; answers show the jurisdiction. |
| 8.3 | Hindi queries and Hindi-only letters (bge-m3 + Hindi abbreviation lexicon). |
| 8.4 | New-edition handling: when a new manual edition arrives, run a clause-level diff against the old one, mark letters incorporated into the new edition, and re-point amendment links. |

### Phase 9 — Reconnect drawings (after v1)

- Unfreeze the drawings universe and reuse the chunk/index/answer stack for drawing numbers, titles, revisions, title blocks, notes, BOM, dimensions and tolerances (EXP-04).
- Add revision comparison, with each change linked to its sheet/region (EXP-05).
- Machine-extracted dimensions stay unverified until reviewed.
- Manual ↔ Drawing links are allowed only as evidence-backed `REFERENCES`.
- The 3D twin becomes the viewer for a cited drawing.

### 7.5 Corpus register

The **source list itself lives in `corpus/catalogue.csv`** (one row per document), and this table tracks progress. **Action for project owner:** list all 20+ manuals and the letter sets (issuer, year range, count) so batches can be planned.

| Group | Documents | Pages (approx.) | Status |
|---|---|---|---|
| Manuals — ingested (need Phase 1 re-ingest) | IRPWM 2024 (ACS-14), USFD 2026, AT Weld 2022, FBW 2022 (CS-5), Track Machine Manual 2020 (ACS-10), Small Track Machines Manual 2024 | 1,485 | 🟡 re-ingest |
| Manuals — to add | 14+ more (owner to list) | ~5–7k | ⬜ Phase 3 |
| Correction slips (ACS/CS) | per manual | small | ⬜ Phase 3.3 |
| Railway Board / RDSO letters | 100+ (owner to list by issuer/year) | ~500–1,000, many scanned | ⬜ Phase 4 |
| Zonal / divisional circulars | TBD | TBD | ⬜ Phase 8.2 |
| IRS / IS specifications, IRSOD | TBD | TBD | ⬜ Phase 8.1 |
| RDSO drawings | 59 | — | ❄️ frozen (Phase 9) |

Batch order: IRPWM pilot → the 5 already-ingested manuals → remaining manuals by usage → letters, newest first (newest letters are most likely in force).

---

## 8. Timeline (indicative)

```text
             ENGINEERING TRACK                         CONTENT TRACK
Week  1      Phase 0  clean, corpus/ + catalogue
Weeks 2–4    Phase 1  full text, generic pipeline,
                      OCR, tables, quality report     owner lists 20+ manuals + letters
Weeks 5–6    Phase 2  BM25 search + gold set + PDF    Phase 3 batch 1 (re-ingest 6 + 3 new)
Weeks 7–8    Phase 5  hybrid + graph + rerank         Phase 3 batches 2–3 (→ 20+ manuals)
Weeks 9–11   Phase 4  letters parser + amendments     letters bulk load + amendment review
Weeks 12–14  Phase 6  local LLM answers  →  v1.0
Weeks 15–16  Phase 7  feedback + nightly learning
Then         Phase 8/9 specs, circulars, Hindi, new editions, drawings
```

---

## 9. Metrics (tracked in CI from Phase 2)

| Metric | v1 target |
|---|---|
| Documents catalogued → published (passing quality report) | 20+ manuals, 100+ letters, 100 % of catalogued |
| Pages covered by chunks (per document) | ≥ 98 % |
| Paras with full text | 100 % |
| Para numbering consistency | ≥ 99 % |
| Letters with no./date/issuer/subject | 100 % |
| Amendment effects resolved | ≥ 95 % |
| Unreviewed amendment links used in answers | 0 |
| Retrieval Recall@5 / MRR (overall and worst document) | ≥ 0.85 / ≥ 0.70 overall; worst document ≥ 0.75 |
| Zero-result rate (real queries) | < 5 % |
| Answers with valid citation | 100 % |
| Numbers verified in cited source | 100 % |
| Amendment-awareness | ≥ 95 % |
| Correct "not found" on negatives | ≥ 90 % |
| 👍 rate (after Phase 7) | ≥ 80 % and rising |
| Cited chunks human-`VERIFIED` | rising monthly |
| Human effort per new manual / letter | ≤ 1 h / ≤ 5 min |
| Search p95 / Answer p95 (full corpus) | < 300 ms / < 20 s |

Node counts, edge counts, embedding counts and graph visuals are **not** success metrics.

---

## 10. Research & experiments

Research informs the phases but never changes production silently. Each experiment is recorded under `research/benchmarks/`, and this file is updated with the outcome.

| Exp | Question | Phase | Status |
|---|---|---|---|
| EXP-01 | Docling vs PyMuPDF for headings, tables, figures, runtime | 1.9 | Baseline only; redo on the correct file |
| EXP-02 | Pilot-manual hierarchy ground truth (fabrication rate must be 0) | 1.3, 1.10 | Not started |
| EXP-03 | Keyword vs vector vs hybrid vs +graph vs +rerank | 5.7 | Not started — **most important** |
| EXP-04 | Drawing field extraction precision/recall | 9 | Not started |
| EXP-05 | Drawing revision comparison | 9 | Not started |
| EXP-06 | KG shape constraints (SHACL-style, as JSON Schema/pytest) | Gates | Partly covered by gates A–K |

**Reference papers:**
- R-001/002 — railway maintenance KG: [Huddersfield](https://pure.hud.ac.uk/en/publications/ontology-guided-knowledge-graph-construction-to-support-schedulin/), [Tongji](https://umt1998.tongji.edu.cn/en/article/doi/10.16037/j.1007-869x.2024.09.035)
- R-003 — evidence-verifiable railway defect KG: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0957417426014508)
- R-006 — human-in-the-loop KG: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1474034626007263)
- R-007 — Docling: [arXiv](https://arxiv.org/abs/2408.09869)
- R-008 — LayoutLM: [arXiv](https://arxiv.org/abs/1912.13318)
- R-010 — drawing parsing: [arXiv](https://arxiv.org/abs/2506.17374)
- R-011 — Drawing-Checker: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2212827126008085)
- R-012 — RAG: [arXiv](https://arxiv.org/abs/2005.11401)
- R-013 — GraphRAG: [arXiv](https://arxiv.org/abs/2404.16130)
- R-014 — SHACL: [W3C](https://www.w3.org/TR/shacl/)

The full annotated index is in `archive/research/RESEARCH_INDEX.md`.

**What not to copy from research:** LLM-generated graphs, vector-only retrieval, Neo4j-first designs, end-to-end VLM extraction, community summaries treated as authoritative, relations without provenance, and metrics that ignore source correctness.

---

## 11. Repository, pipeline & commands

```text
RDSO-Drawings/
├── README.md                 pointer to this file
├── docs/ROADMAP.md           ← this file (only live doc)
├── docs/archive/             history only
├── corpus/                   (Phase 0.3+, gitignored) manuals/ letters/ circulars/ acs/ specs/ drawings/
│   ├── catalogue.csv         tracked: one row per document (id, type, no., date, issuer, file, SHA-256)
│   └── profiles/             tracked: per-document overrides (only when auto-detection needs help)
├── manuals/, drawings/, crops/  current locations, moving to corpus/ in 0.3
├── data/knowledge-graph/     raw/ intermediate/ canonical/ exports/ schemas/ reports/
├── data/kb/                  (Phase 1+) chunks.jsonl, kb.sqlite, lexicon.yaml, reports/, config_history/
├── eval/                     (Phase 2+) gold questions + results
├── scripts/                  ingestion, KG build, validation (scripts/kb/ for new pipeline)
├── serve/                    (Phase 6+) local API
├── research/benchmarks/      experiment outputs
├── tests/                    pytest + browser checks
├── lib/                      offline Three.js
└── index.html                offline app
```

**Current pipeline** (run from repo root, Python 3.11, `pip install -r requirements-dev.txt`):

```bash
python scripts/build_source_registry.py        # hash + register PDFs
python scripts/ingest_all_manual_chapters.py   # chapters/clauses → intermediate/
python scripts/generate_canonical_kg.py        # → data/rdso_canonical_kg.json
python scripts/export_kg_bundle.py             # → data/rdso_kg_data.js (app bundle)
python scripts/validate_all.py                 # gates A–K
python -m pytest -q                            # unit tests
```

Open `index.html` directly in a browser for the offline app. From Phase 0.6, `make ingest | index | serve | eval | test` replaces the commands above.

**Adding a document (target workflow from Phase 1):**
1. Drop the PDF into `corpus/<type>/`.
2. Add a row to `corpus/catalogue.csv`, or run `make intake`, which pre-fills letter no./date/issuer/subject for you to confirm.
3. Run `make ingest report`. Fix `corpus/profiles/<id>.yaml` only if the quality report fails.
4. Add gold questions to `eval/questions.jsonl`.
5. Run `make index eval`.

Identity always comes from the catalogue (ID, title, edition/letter no., SHA-256), never from the filename.

**CI:**
- `.github/workflows/ci.yml` runs gates A–K.
- `manual-kg-continuous.yml` rebuilds and validates every 6 h and commits deterministic drift on `main`.
- From Phase 2, CI also runs the eval gate.

---

## 12. How we work

1. Before a change, check HEAD, recent commits, open PRs and the exact files involved. Never overwrite active work.
2. Pick **one** task from §14 or the current phase, and make the smallest safe change.
3. Run focused tests → `validate_all.py` → full pytest → (from Phase 2) eval. Look at the real data/UI output.
4. Commit only validated work, using conventional commits: `feat(search):`, `fix(kb):`, `test(eval):`, `docs(roadmap):`.
5. Update this file when a task completes or a decision changes: tick the task, update §3 numbers, record experiment results.
6. Regenerate metrics before claiming them. Numbers in old session notes are not evidence.
7. Don't do prematurely:
   - rewrite the whole frontend;
   - add Neo4j/PostgreSQL/OpenSearch for fashion;
   - build LLM features before Gates 4 and 5;
   - delete legacy data without a reference audit;
   - optimise graph looks over answers.

---

## 13. Non-negotiable rules

1. No answer without retrieved evidence. Nothing invented: no para, page, number or rule.
2. Raw source text is never truncated or overwritten.
3. `VERIFIED` only by a human, with reviewer id and date.
4. Every retrieval or answer change passes the eval gate. The gold set only grows.
5. Everything runs offline. No telemetry leaves the machine.
6. **One doc:** this file. Don't create new plan docs.

---

## 14. Immediate next tasks

1. **Owner:** list the 20+ manuals and 100+ letters (issuer, year range) for the corpus register (§7.5).
2. **1.1** — remove text caps and regenerate the KG with full clause text.
3. **1.6** — default status `EXTRACTED`; computed confidence.
4. Add Gate 1 content checks to `scripts/validate_all.py`.
5. **1.10/1.11** — auto-TOC + catalogue/doc-type model, so onboarding needs no code change.
6. **1.2/1.3** — header/footer strip + numbering detectors, with a 50-para IRPWM fixture.
7. **2.3** — draft the first 50 IRPWM gold questions (a domain expert reviews them).
