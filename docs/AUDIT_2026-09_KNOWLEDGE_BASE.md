# Audit — Offline Railway Manuals Knowledge Base & Knowledge Graph

**Date:** 2026-09-28
**Branch audited:** `claude/epic-cannon-f9menl` @ `104e189`
**Goal audited against:** *Ask any question about the railway manuals, get an intelligent, AI-like, source-cited answer — fully offline — and have the system improve itself over time.*

All numbers below were regenerated from the repository during the audit (not copied from older session reports).

---

## 0. Verdict (TL;DR)

| Capability required by goal | Status | Why |
|---|---|---|
| Manuals ingested | 🟡 Partial | 6 PDFs, 1,485 pages read by PyMuPDF. Text is there in `raw/extracted_pages.jsonl`. |
| Full clause text searchable | 🔴 Broken | All 1,838 clause nodes have `desc: "..."`. Clause text is truncated to 1,200 chars (425 clauses hit the cap) and evidence to 500 chars. 1,561 of 3,772 requirements have `statement: "..."`. |
| Correct hierarchy | 🟡 Partial | 83 chapters OK. But 257/673 IRPWM clauses sit under a chapter whose number does not match the para number; STMM IDs like `PARA_1616` / `PARA_1012` come from page numbers and titles glued together. |
| Tables (tolerances, limits) | 🔴 Missing | 178 pages contain tables; only 57 TABLE nodes, stored as labels, no rows/cells. Most engineering answers live in tables. |
| Scanned / image pages | 🔴 Missing | 75 manual pages have < 50 chars of text (USFD 32, IRPWM 23, FBW 13…). No OCR step. |
| Search | 🔴 Weak | `rankSearchResults` / `rankHybridSearchResults` in `index.html` do substring `includes()` over label + `desc` (which is `"..."`) + JSON-stringified specs. No tokenisation, stemming, BM25, phrase or number handling. Clause body text is effectively not searched. |
| "Semantic" search | 🔴 Cosmetic | `SEMANTIC_SYNONYM_REGISTRY` = 29 hand-written keys, mostly drawing/turnout terms. No embeddings, no vector index. |
| AI-like answers | 🔴 Canned | `answerEngineeringQuestion` matches the query against `CANONICAL_QA_DATABASE` — **13 hand-written answers**. Everything else falls back to a keyword filter over clause titles. No retrieval-augmented generation, no local LLM. |
| Citations to source page | 🟡 Partial | Clause nodes carry `provenance.source_page`, but the UI can't show the full provision text, and there's no page viewer that jumps to the PDF page. |
| Self-improving | 🔴 Absent | The "Learning" module is a training academy (flashcards, quizzes) for *users*. The system itself never logs queries, collects feedback, mines synonyms, or grows an evaluation set. `review_queue.jsonl` has 826 bytes. |
| Trustworthiness flags | 🔴 Misleading | **Every** node (6,469), evidence (1,875) and requirement (3,772) has `verification_status: "verified"`, and every evidence item has hardcoded confidence 0.95/1.0. Nothing was reviewed by a person. `scripts/build_canonical_pipeline.py` hardcodes `"verified"` in 12 places. |
| Offline | 🟢 Yes | Static `index.html` + local JS bundles, works from `file://`. |
| Tests / CI | 🟡 Green but hollow | 126 pytest pass, gates A–K pass — while the defects above exist. E.g. `tests/test_question_interface.py` re-implements a QA bank in Python and tests *that*, not the app. No test checks retrieval quality. |
| Reproducibility | 🟢 Good | Re-running `ingest_all_manual_chapters.py` + `generate_canonical_kg.py` reproduces the artifacts (timestamp is the only diff). |

**Bottom line:** the project has a good *skeleton* (source registry with SHA-256, deterministic manual → chapter hierarchy, provenance fields, schemas, validation gates, offline shell). The *intelligence layer* the goal asks for — full-text retrieval, semantic retrieval, grounded answer generation, and a feedback loop — does not exist yet. What the UI shows as "semantic" and "AI answers" is hand-authored content. Also, the text needed to power it is thrown away between the raw layer and the canonical layer.

---

## 1. What exists (inventory)

| Area | Files | Notes |
|---|---|---|
| Source PDFs | `manuals/*.pdf` (6, 47 MB), `drawings/` (59), `crops/` (37) | Committed to git. Pack size is 200 MB. |
| Source registry | `data/knowledge-graph/raw/source_registry.jsonl` | SHA-256, page count, family. Good. |
| Page text | `data/knowledge-graph/raw/extracted_pages.jsonl` (1,544 pages, 2.6 M chars for manuals) | **The best asset in the repo.** Full page text is kept here. |
| Chapter extraction | `scripts/ingest_all_manual_chapters.py` → `intermediate/all_chapters_extracted.json` | Hardcoded chapter registry per manual, regex clause split, 1,200-char cap. |
| Canonical KG | `scripts/generate_canonical_kg.py` (92 KB) → `data/rdso_canonical_kg.json` (24 MB) + `canonical/*.jsonl` | 6,469 nodes, 8,370 edges; 92 % of edges are `HAS_SECTION`/`HAS_CLAUSE`; ~99 % are structural. Only ~120 semantic edges, almost all drawing-side. |
| Frontend bundle | `scripts/export_kg_bundle.py` → `data/rdso_kg_data.js` (22 MB) | Loaded on page open. |
| App | `index.html` (497 KB, 138 functions, Three.js graph) | Built by `scripts/build_updated_app.py` (417 KB Python holding HTML strings), and also patched directly by `scratch/*.py`. |
| Validation | `scripts/validate_*.py`, `validate_all.py`, 2 GitHub workflows | Structural checks only. |
| Research | `research/`, EXP-01 Docling benchmark | Docling not actually run. |
| Docs | `docs/PROJECT_MASTER.md` + 10 archived docs | Heavy spec; implementation lags far behind. |

---

## 2. Findings in detail

### F1 — Clause text lost between raw and canonical (Critical)

- `scripts/ingest_all_manual_chapters.py:484-488` caps `source_text`/`verbatim_text` at `[:1200]`.
- `scripts/generate_canonical_kg.py:614` sets desc to `text[:280] + "..."`, but in practice the stored `desc` is literally `"..."` for all 1,838 clauses (median length 3).
- Evidence quotes are cut to `[:500]` (`generate_canonical_kg.py:846, 876, 953-963, 991, 1038`).
- 1,561 requirement `statement`s are `"..."`; others end mid-sentence ("Contractors and their Agents may ").

**Impact:** you can't search, quote or answer from text you have deleted. This is the single biggest blocker.

**Fix:** store full clause text as the canonical `text` field (no cap). Make `desc`/`summary` a separate optional field. Evidence gets a full quote plus `page` and `bbox`.

### F2 — Clause segmentation & numbering errors (High)

- 257/673 IRPWM clause IDs don't match their chapter (IRPWM paras are chapter-prefixed: Ch 4 → 4xx).
- STMM: `PARA_1616 "Troubleshooting"`, `PARA_1012 "Functional Requirements \n97"` — the page number / running header got merged into the para number.
- TMM has 349 clauses for 458 pages; mixed ID styles (`CLAUSE:TMM:PARA_421` vs `CLAUSE:TMM:CH_03:PARA_123`).
- Headers, footers and page numbers aren't stripped before segmentation.

**Fix:** a per-manual layout profile (header/footer bands, numbering regex, font-size/bold heading cues from PyMuPDF `get_text("dict")`). Validate that para numbers are monotonic and chapter-prefixed. Add a gold file with ~50 hand-checked clauses per manual, and gate on it.

### F3 — Tables and figures not extracted as content (High)

178 pages have tables. Railway manuals put most limits, tolerances and frequencies in tables (e.g. IRPWM tolerances, USFD defect classes). Today only 57 table *labels* exist.

**Fix:** `page.find_tables()` (PyMuPDF ≥ 1.23) or Docling/Camelot for tables. Store each table as rows plus a caption, and index each row as a retrievable chunk ("<table caption> | <col>: <val> …").

### F4 — No OCR for image pages (Medium)

75 manual pages have under 50 characters of text. They're probably scanned annexures, diagrams or forms.

**Fix:** Tesseract (offline) or PaddleOCR on pages whose text is under N chars. Mark the output `extraction_method: ocr` with lower confidence.

### F5 — Search is substring matching over titles (Critical)

`index.html:10866 rankSearchResults` and `:9997 rankHybridSearchResults`:
- score = `id.includes(q)`, `label.includes(q)`, plus +80 per token found anywhere in `id+label+desc+JSON(specs)`;
- no stemming ("inspections" ≠ "inspection"), no stop-words, no IDF (so "rail" weighs the same as "destressing"), no phrase proximity, no unit/number normalisation ("1 in 12", "1:12", "60 kg", "60kg");
- `desc` is `"..."`, so clause bodies are not searched at all;
- it loops over every node on each keystroke.

**Fix:** a real inverted index with BM25 over chunk text (details in §3).

### F6 — "Semantic" and "AI answer" layers are hand-written (Critical)

- `SEMANTIC_SYNONYM_REGISTRY` (`index.html:9938`): 29 keys, turnout/drawing-oriented.
- `CANONICAL_QA_DATABASE` (`index.html:7954`): 13 authored answers with hardcoded paras and values. Nothing checks them against source text, so if the manual has an ACS correction, the answer silently goes stale.
- `detectQuestionIntent` uses keyword regexes and returns confidence 0.95–0.98 whatever the evidence.

**Fix:** replace this with retrieval + a local LLM that is constrained to cite retrieved chunks (§3). Keep the 13 authored answers only as *evaluation questions* whose expected citations are checked.

### F7 — Verification status is meaningless (High, safety)

Every object is `"verified"`. For a safety-critical domain this is the most dangerous defect: the UI can't tell a human-checked limit from a regex guess.

**Fix:** the default is `EXTRACTED`, which already exists in the PROJECT_MASTER vocabulary. Only a human review action sets `VERIFIED`. Confidence should be computed (from extraction method, OCR quality, and numbering consistency), not hardcoded.

### F8 — No self-improvement loop (Critical to the goal)

Nothing records what users ask, what they clicked, or whether the answer was right.

**Fix:** see §4.

### F9 — Tests prove structure, not usefulness (High)

- 126 tests plus 11 gates pass while F1–F8 exist.
- Several Python tests re-implement the frontend logic and test the copy, not the app (`tests/test_question_interface.py`, `test_semantic_intelligence.py`).
- There are no retrieval metrics.

**Fix:**
- Build a gold QA set, `eval/questions.jsonl`: question → expected manual/para/page, and expected value where applicable. Start with 100 questions and grow it from user feedback.
- Add a CI gate on Recall@5 and MRR, and later on answer faithfulness.
- Add content gates: no `"..."` text, no truncated text, and para numbers monotonic within a chapter.

### F10 — Frontend architecture is fragile (Medium)

- One 497 KB `index.html` is generated by a 417 KB Python file of string templates, *and* patched by `scratch/*.py`. The generator and its output can drift.
- A literal `\n` sits between script tags (`index.html:2843`).
- A 22 MB JS bundle is parsed at startup.
- The 3D graph is the centrepiece, but for Q&A the answer panel matters more.

**Fix:**
- Split into `app/` ES modules (search, answer, graph, viewer) and stop generating HTML from Python.
- Load the search index lazily as a binary/JSON shard.
- Make the main screen a search/answer page, with the graph as a secondary view.

### F11 — Repo hygiene (Low–Medium)

- `index.html.bak` is tracked even though `*.bak` is in `.gitignore`.
- Tracked files that should not be: `node_modules/`, `__pycache__`, and `package-lock.json`, which is ignored yet committed.
- `scratch/` is committed.
- 156 PDF/PNG binaries are in git history (200 MB pack). Use Git LFS or keep sources outside git and pin them by SHA-256 in `source_registry.jsonl`.
- Datasets are duplicated: `rdso_canonical_kg.json`, `canonical/*.jsonl`, `exports/graph.json`, `rdso_kg_data.js`, and `rdso_manuals_knowledge.json` are five copies of overlapping truth.
- The EXP-01 USFD benchmark reports 147 pages and 0 empty, but the registry says USFD has 157 pages and 32 near-empty. The benchmark and the pipeline used different files.

### F12 — Coverage of the corpus (Medium)

- 6 manuals are in the KB.
- `manuals/README.md` lists LWR manual, IRSOD, IRS T-specs, IS codes, and there are no correction slips/circulars layer.
- ACS (correction slip) handling is by edition name only. There's no clause-level "amended by ACS-n".

---

## 3. Target architecture for "AI-like, offline" answers

Keep what's good: raw → intermediate → canonical, provenance, and the manual hierarchy. Add a **retrieval + generation** layer that runs completely on a local machine.

```text
PDF ─► PyMuPDF (+OCR on empty pages, +table extraction)
     ─► layout-aware segmentation (header/footer strip, numbering profile)
     ─► CHUNKS  (clause | sub-clause | table-row | figure caption)
            id, manual, edition/ACS, chapter, para, page, bbox, full text
     ─► INDEXES
          • BM25 / FTS5          (exact terms, para numbers, values)
          • dense vectors         (meaning; local embedding model)
          • KG                    (hierarchy, cross-refs "see Para 630", defined-terms, ACS amendments)
     ─► QUERY PIPELINE
          normalise (units, abbreviations: SEJ, LWR, USFD, ADEN, SSE/P.Way…)
          → hybrid retrieve (BM25 ∪ vector, RRF fusion, top 50)
          → graph expand (parent para, referenced paras, amending ACS, same table)
          → rerank (local cross-encoder, top 8)
          → local LLM: answer ONLY from given chunks, cite [manual para page]
          → verifier: every number/limit in answer must appear in a cited chunk
     ─► UI: answer + clickable citations → PDF page viewer at the exact page/bbox
```

### Recommended offline stack

| Layer | Recommended | Why |
|---|---|---|
| Runtime | Small local Python service (FastAPI) on `localhost`, with the existing HTML as client | Browser-only works for search but is too weak for LLM plus reranking. One `start.bat`/`start.sh` keeps it offline. |
| Store | **SQLite**: FTS5 for BM25 + `sqlite-vec` for vectors + tables for KG/feedback | One file, zero server, easy to copy to field offices. |
| Embeddings | `BAAI/bge-small-en-v1.5` or `bge-m3` (handles Hindi terms), via `sentence-transformers`/ONNX | CPU-friendly, strong retrieval. |
| Reranker | `BAAI/bge-reranker-base` (or `-v2-m3`) | Big precision gain on top-50 → top-8. |
| LLM | `llama.cpp` / Ollama with Qwen2.5-7B-Instruct or Llama-3.1-8B-Instruct (Q4_K_M, ~5 GB, 8–16 GB RAM) | Good instruction following and citation discipline. It runs on an office PC CPU; a GPU makes it faster. |
| Browser-only fallback | Precomputed BM25 JSON + MiniSearch/FlexSearch, optional `transformers.js` embeddings | Search keeps working when the service is not running. |
| Tables/layout | PyMuPDF `find_tables`; Docling as a benchmark candidate (EXP-01) | |
| OCR | Tesseract 5 (offline) | |

**Rule:** the LLM never answers from its own memory. If retrieval returns nothing above threshold, it says "Not found in the loaded manuals", and shows the closest provisions.

---

## 4. Self-improvement loop (what "self improving" should mean)

The system must not rewrite rules by itself. Safe self-improvement means it gets better at **finding and presenting** source text, from logged usage plus human confirmation.

```text
every query ─► log (query, retrieved ids, answer, citations, latency)   [local SQLite]
user action ─► 👍/👎, "correct source is Para X", clicked citation, reformulated query
nightly job ─►
   1. zero-result & 👎 queries        → review list for admin
   2. reformulation pairs (q1→q2 click) → candidate synonyms/abbrev map
   3. confirmed (query → para) pairs   → added to eval/questions.jsonl (gold set grows)
   4. gold set                         → fine-tune/adjust: BM25 field weights, RRF k,
                                         reranker threshold; optional LoRA on embeddings
   5. low-confidence extractions hit by users → review queue → human VERIFIED
   6. re-run eval; promote new config only if Recall@5 / faithfulness do not regress
new manual / ACS dropped in manuals/ ─► ingest → diff vs previous edition → "amended" links
```

This is measurable, reversible (config versioned), and keeps humans in control of safety facts.

---

## 5. Prioritised roadmap

### Phase 1 — Stop losing knowledge (1–2 weeks)

1. Remove all text caps (`[:1200]`, `[:500]`, `[:280]+"..."`). Canonical clause gets a full `text`.
2. Strip headers, footers and page numbers. Fix para-number parsing. Add a monotonic/chapter-prefix gate.
3. Set `verification_status` default to `EXTRACTED` and compute confidence.
4. Extract tables as rows, and OCR near-empty pages.
5. New `data/kb/chunks.jsonl`: one row per clause, sub-clause, table row or figure caption, with page and bbox.
6. Content gates in `validate_all.py`: no `"..."`, no truncation, ≥ 95 % pages covered by some chunk.

### Phase 2 — Real search (1–2 weeks)

7. Build SQLite FTS5 index + domain normaliser (abbreviation list, units, "1 in 12" ↔ "1:12").
8. Build the gold eval set (100 questions across 6 manuals) and add `scripts/eval_retrieval.py` with Recall@k and MRR in CI.
9. Replace `rankSearchResults` with index-backed search. Show the snippet plus manual/para/page. Clicking opens the PDF at that page (pdf.js, offline).

### Phase 3 — AI answers offline (2–3 weeks)

10. Embeddings + `sqlite-vec`, hybrid RRF, reranker.
11. Graph expansion: parse cross-refs ("Para 630", "Annexure 8/6", "Chapter IV") into `REFERENCES` edges, then resolve them.
12. Local LLM answer endpoint with strict citation prompt + numeric verifier. Stream to UI.
13. Convert the 13 canned answers into eval questions and delete `CANONICAL_QA_DATABASE`.

### Phase 4 — Self-improvement (ongoing)

14. Query/feedback logging, admin review page, nightly improvement job (§4).
15. Manual/ACS versioning: a clause-level diff between editions, with `AMENDED_BY` edges.

### Phase 5 — Coverage & hygiene

16. Add the LWR manual, IRSOD, IRS T-specs, IS codes and circulars.
17. Git LFS or external sources, and delete the duplicate datasets, `index.html.bak`, `node_modules`, `__pycache__` and `scratch/`.
18. Modularise the frontend, and demote the 3D graph to an "explore" tab.

---

## 6. Acceptance metrics (define "done")

| Metric | Target v1 |
|---|---|
| Manual pages with ≥ 1 chunk | ≥ 98 % |
| Clauses with full, untruncated text | 100 % |
| Para-number / chapter consistency | ≥ 99 % |
| Retrieval Recall@5 on gold set | ≥ 0.85 |
| MRR on gold set | ≥ 0.70 |
| Answers with ≥ 1 valid citation | 100 % |
| Numbers in answer found verbatim in cited chunk | 100 % (else answer blocked) |
| "Not found" when the answer is absent (negative questions) | ≥ 0.9 |
| p95 latency, search / LLM answer (CPU) | < 300 ms / < 20 s |
| Works with network cable unplugged | yes |
