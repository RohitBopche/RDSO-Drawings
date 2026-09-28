# RDSO Manuals Knowledge Base — Final Roadmap

**Status:** Single source of truth for *what we build next and in what order*.
**Supersedes:** PROJECT_MASTER §26–28, every roadmap/phase list in `docs/archive/`, and the README feature list.
**Still authoritative alongside this doc:** PROJECT_MASTER for data contracts (§5–14), the answer contract (§17), conflict handling (§18) and AI guardrails (§29).
**Evidence base:** [`AUDIT_2026-09_KNOWLEDGE_BASE.md`](AUDIT_2026-09_KNOWLEDGE_BASE.md).
**Last updated:** 2026-09-28

---

## 1. Goal

> Ask any question about the Indian Railways manuals in plain language, and get a correct, AI-quality answer that **cites the exact manual, para and page**.
> The system runs **fully offline** on an office PC.
> It **gets better with use** without ever inventing rules.

### What "done" looks like (v1)

The engineer types *"What is the permissible gap in SEJ for LWR on girder bridge?"* and gets:

1. a 2–6 sentence answer;
2. the limits/values, quoted from the source;
3. citations like `IRPWM 2024 ACS-14 · Para <n> · p. <n>` (format only);
4. clicking a citation opens the PDF at that page with the text highlighted;
5. related provisions (the referenced paras, the amending ACS, the same table);
6. 👍 / 👎 / "correct para is…" feedback.

If the manuals don't cover the question, the answer says so and shows the closest provisions.

### Scope decisions (final)

| Decision | Choice | Reason |
|---|---|---|
| Primary product | **Manuals Q&A + search** | This is the stated goal. |
| Drawings / 3D digital twin | **Frozen.** Keep working, no new features until v1 ships. | The work stays and nothing is deleted. |
| 3D knowledge graph | Kept as an "Explore" tab, not the home screen | Engineers need answers first and graphs second. |
| Storage | **SQLite** (FTS5 + `sqlite-vec` + plain tables) | One file, no server, copies to any PC. PostgreSQL only if a multi-user central deployment is ever needed. |
| Runtime | Local Python service (FastAPI) on `127.0.0.1` + existing web UI | Needed for LLM and reranker. Browser-only search stays as a fallback. |
| LLM | Local via `llama.cpp` / Ollama. Default Qwen2.5-7B-Instruct Q4_K_M; Llama-3.1-8B-Instruct as alternative. Configurable. | Runs on CPU with 16 GB RAM; GPU optional. |
| Embeddings | `bge-m3` (multilingual) or `bge-small-en-v1.5` (fast) | Local, strong retrieval. |
| Reranker | `bge-reranker-v2-m3` | Largest precision gain per effort. |
| Truth policy | LLM answers **only from retrieved chunks**. Numbers are verified against the source. Everything is `EXTRACTED` until a human marks it `VERIFIED`. | Safety-critical domain. |
| Pilot manual | **IRPWM 2024 (ACS-14)** for the gold set. Pipeline fixes apply to all 6 manuals. | Largest, most-used manual. |

---

## 2. Where we are today (measured 2026-09-28)

| Area | State |
|---|---|
| Sources | 6 manuals, 1,485 pages, SHA-256 registry ✅ |
| Page text | Full text kept in `raw/extracted_pages.jsonl` ✅ |
| Hierarchy | 83 chapters ✅; 257/673 IRPWM clauses mis-numbered/mis-parented ❌ |
| Clause text in KG | `desc: "..."` for all 1,838 clauses; text capped at 1,200 chars ❌ |
| Tables | 178 pages with tables → 57 labels, 0 rows ❌ |
| Scanned pages | 75 near-empty pages, no OCR ❌ |
| Search | Substring match over titles; prebuilt index unused ❌ |
| Q&A | 13 hand-written answers ❌ |
| Verification flags | 100 % "verified", none reviewed ❌ |
| Self-improvement | None ❌ |
| Tests | 126 pass, but structural only; no retrieval/answer metrics ❌ |
| Offline | ✅ |

---

## 3. Target architecture

```text
 manuals/*.pdf  (+ ACS slips, circulars later)
      │
 ① INGEST ── PyMuPDF text+layout ─ OCR(Tesseract) on empty pages ─ table extraction
      │       header/footer strip ─ per-manual numbering profile
      ▼
 ② STRUCTURE ── Manual → Chapter → Section → Para → Sub-para  (+ Table, Figure, Annexure)
      │          full text, page, bbox, ACS/edition, status=EXTRACTED, computed confidence
      ▼
 ③ CHUNKS  data/kb/chunks.jsonl   (para | sub-para | table-row | figure caption | definition)
      ▼
 ④ INDEXES  data/kb/kb.sqlite
      ├─ FTS5 (BM25)           exact words, para numbers, values
      ├─ sqlite-vec            meaning (embeddings)
      ├─ graph tables          HAS_*, REFERENCES (Para 630, Annexure 8/6), AMENDED_BY, DEFINES
      └─ feedback / logs       queries, clicks, votes, corrections
      ▼
 ⑤ QUERY  normalise (abbrev, units) → BM25 ∪ vector (RRF) → graph expand → rerank → top-k
      ▼
 ⑥ ANSWER  local LLM, cite-only prompt → citation + number verifier → answer or "not found"
      ▼
 ⑦ UI  Ask box · answer card · citations → PDF.js page viewer · related · Explore graph
      ▼
 ⑧ LEARN  nightly: failed queries → review · synonym mining · gold-set growth · weight tuning
```

---

## 4. Phases

Each phase ends with a **gate** that CI checks. Do not start the next phase's UI work before the previous gate is green. Durations assume one developer.

### Phase 0 — Clean the ground (≈ 3 days)

| # | Task | Output |
|---|---|---|
| 0.1 | Freeze drawings/twin features; add a note in README | README "Status" block |
| 0.2 | Remove tracked junk: `index.html.bak`, `node_modules/`, `__pycache__/`, `scratch/`, and the committed `package-lock.json` that is ignored | cleaner repo |
| 0.3 | Move large binaries (`manuals/`, `drawings/`, `crops/`) to Git LFS, or keep them outside git and pin by SHA-256 | repo < 50 MB |
| 0.4 | Fix `index.html:2843` literal `\n`; fix broken metadata path to the Blueprint | — |
| 0.5 | Rewrite README around the goal (what, how to run offline, where the roadmap is) | README |
| 0.6 | Add `pytest` and a `Makefile`/`run.ps1` with `ingest`, `index`, `serve`, `eval`, `test` | one-command workflow |

**Gate 0:** fresh clone → `make test` passes, and a README quick-start works on Windows and Linux.

### Phase 1 — Stop losing knowledge (≈ 2 weeks) — *highest priority*

| # | Task | Files |
|---|---|---|
| 1.1 | Remove every text cap (`[:1200]`, `[:500]`, `[:280]+"..."`). Canonical para gets full `text`; `summary` is optional and separate. | `ingest_all_manual_chapters.py`, `generate_canonical_kg.py` |
| 1.2 | Header/footer/page-number stripping via layout bands (`get_text("dict")`, y-position + repetition across pages) | new `scripts/kb/layout.py` |
| 1.3 | Per-manual numbering profile (IRPWM `NNN(n)(a)`, USFD `N.N.N`, STMM, TMM, FBW, AT-Weld). Enforce chapter prefix + monotonic order, and route violations to a review file | `scripts/kb/profiles/*.yaml` |
| 1.4 | Table extraction (`page.find_tables()`, with Docling as a candidate per EXP-01). Store rows plus caption; each row becomes a chunk | `scripts/kb/tables.py` |
| 1.5 | OCR pages with < 50 chars (Tesseract, `eng+hin`). `extraction_method=ocr`, lower confidence | `scripts/kb/ocr.py` |
| 1.6 | Honest status: default `EXTRACTED`; computed `confidence` (method, OCR, numbering consistency). Only a human sets `VERIFIED`. | `build_canonical_pipeline.py` |
| 1.7 | Emit `data/kb/chunks.jsonl`: `{id, manual, edition, chapter, para, parent, type, text, page, bbox, status, confidence}` | new |
| 1.8 | Store bounding boxes so the UI can highlight | — |
| 1.9 | Redo EXP-01 on the *same* USFD file as the registry, and record the Docling vs PyMuPDF result | `research/benchmarks/` |

**Gate 1 (new CI checks):**
- 0 chunks with `"..."`, truncated or empty text;
- ≥ 98 % of pages covered by ≥ 1 chunk;
- ≥ 99 % para-number consistency;
- tables present as rows;
- 0 objects `VERIFIED` without a reviewer id;
- a 50-para hand-checked IRPWM fixture matches exactly.

### Phase 2 — Real search (≈ 2 weeks)

| # | Task |
|---|---|
| 2.1 | Build `data/kb/kb.sqlite` with FTS5 (porter + unicode61), columns weighted: para title > text > chapter. |
| 2.2 | Domain normaliser: abbreviation dictionary (LWR, SEJ, USFD, ADEN, SSE/P.Way, CMS, TWS, GRSP, ERC, AT, FBW, DFW…), unit forms (`60kg`/`60 kg`/`60 kg/m`, `1:12`/`1 in 12`), para forms (`Para 262`, `P-262`, `262(3)`). Kept in `data/kb/lexicon.yaml`, which Phase 5 learning appends to. |
| 2.3 | **Gold question set** `eval/questions.jsonl`: 150 questions (100 IRPWM, 10 per other manual) with expected para/page and expected value. Include 15 "not in manuals" negatives. Seed from the 13 canned answers plus a domain expert. |
| 2.4 | `scripts/kb/eval_retrieval.py`: Recall@5/10, MRR, zero-result rate. Runs in CI and fails on regression. |
| 2.5 | Browser fallback: export a compact BM25 index (MiniSearch) so search works from `file://` without the service. |
| 2.6 | UI: search results show para title, snippet with highlights, manual · para · page. Click → **PDF.js viewer** (bundled offline) opens at the page with the bbox highlighted. |
| 2.7 | Delete `rankSearchResults`, `rankHybridSearchResults` and `SEMANTIC_SYNONYM_REGISTRY` (moved to the lexicon). |

**Gate 2:** BM25-only Recall@10 ≥ 0.75 on the gold set; search p95 < 300 ms.

### Phase 3 — Semantic retrieval + graph (≈ 2 weeks)

| # | Task |
|---|---|
| 3.1 | Embed all chunks with `bge-m3` (or `bge-small-en`) → `sqlite-vec`. Rebuild incrementally, keyed by the chunk text hash. |
| 3.2 | Hybrid retrieval: BM25 top-50 ∪ vector top-50 → Reciprocal Rank Fusion. |
| 3.3 | Cross-reference parser: "Para 630", "Annexure-8/6", "Chapter IV", "as per USFD Manual…" → `REFERENCES` edges with resolution state (RESOLVED/AMBIGUOUS/EXTERNAL/NOT_FOUND). |
| 3.4 | Definitions → `DEFINES` edges (glossary chapters) and their use in query expansion. |
| 3.5 | Graph expansion at query time: add parent para, referenced paras and table siblings as candidates (bounded, ≤ 10). |
| 3.6 | Cross-encoder reranker `bge-reranker-v2-m3` → top 8. |
| 3.7 | Run research EXP-03 (keyword vs vector vs hybrid vs hybrid + graph vs hybrid + graph + rerank) and record it. |

**Gate 3:** Recall@5 ≥ 0.85, MRR ≥ 0.70; each added stage must prove ≥ 0 gain on eval, or it is removed.

### Phase 4 — Offline AI answers (≈ 3 weeks)

| # | Task |
|---|---|
| 4.1 | `serve/` FastAPI app: `/search`, `/ask` (streaming), `/chunk/{id}`, `/pdf/{doc}/{page}`, `/feedback`. Binds `127.0.0.1` only. `start.bat` / `start.sh`. |
| 4.2 | LLM adapter (llama.cpp server or Ollama; model path in `config.yaml`). A model-free mode still returns ranked evidence. |
| 4.3 | Prompt contract: answer **only** from numbered chunks; every sentence cites `[n]`; if evidence is insufficient, reply "Not found in loaded manuals". The answer follows the PROJECT_MASTER §17 structure (direct answer → rule → procedure → authority → exceptions → citations). |
| 4.4 | **Verifier:** each cited `[n]` exists; every number/unit/para in the answer appears in the cited chunk; otherwise redact the claim and flag it. Detect conflicts and edition mismatches and show both (PROJECT_MASTER §18). |
| 4.5 | Answer UI: streaming answer card, citation chips → PDF viewer, "evidence used" drawer, related provisions, confidence and status badges (`EXTRACTED` vs `VERIFIED`). |
| 4.6 | Answer eval: faithfulness (numbers verified), citation precision, negative-question refusal rate. Optional LLM-as-judge run locally. |
| 4.7 | Delete `CANONICAL_QA_DATABASE`, `detectQuestionIntent` regexes, `answerEngineeringQuestion`. |

**Gate 4:**
- 100 % of answers carry ≥ 1 valid citation;
- 100 % of numbers are verified or redacted;
- negative refusal ≥ 0.9;
- answer p95 < 20 s on a 16 GB CPU PC;
- works with the network unplugged.

**→ Release v1.0 (offline Q&A) after Gate 4.**

### Phase 5 — Self-improvement loop (≈ 2 weeks, then continuous)

| # | Task |
|---|---|
| 5.1 | Log every query: text, normalised form, retrieved ids, answer, citations, clicks, latency (local SQLite, no network). |
| 5.2 | Feedback UI: 👍/👎, "correct para is …" picker, "wrong number" flag. |
| 5.3 | **Admin review page:** zero-result queries, 👎 answers, extraction issues hit by users, and low-confidence chunks shown in answers. Actions: fix text, mark `VERIFIED`, add synonym, add to gold set. |
| 5.4 | Nightly `scripts/kb/improve.py`: (a) mine reformulation pairs and click-throughs into candidate lexicon entries; (b) turn confirmed (query → para) pairs into gold-set additions; (c) grid-tune BM25 weights, RRF k and rerank cut-off on the gold set; (d) optional hard-negative fine-tune of embeddings once there are ≥ 500 confirmed pairs. |
| 5.5 | **Promotion rule:** a new config/lexicon/model is promoted only if the eval does not regress; otherwise it is rolled back automatically. Every promotion is versioned in `data/kb/config_history/`. |
| 5.6 | Review-debt metrics: % of cited chunks that are `VERIFIED`, and queue age. |

**Gate 5:** each weekly cycle shows the gold set growing, and Recall@5 / 👍-rate trending flat-or-up. Nothing reaches production without passing eval.

### Phase 6 — Coverage & versions (continuous)

| # | Task |
|---|---|
| 6.1 | Drop-in ingestion: add a PDF to `manuals/` → `make ingest` → registry, chunks, index, eval. |
| 6.2 | Add sources: LWR Manual, IRSOD BG, IRS T-specs (T-10, T-29, T-12), relevant IS codes, then Railway Board letters and zonal circulars (per the Railway Engineering KG Architecture doc). |
| 6.3 | ACS / correction-slip handling: clause-level diff between editions → `AMENDED_BY`/`SUPERSEDES` with effective dates. Answers default to the latest edition and flag amended text. |
| 6.4 | Hindi query support (bge-m3 plus a Hindi abbreviation lexicon). |

### Phase 7 — Reconnect drawings (after v1)

Unfreeze the drawings universe, and reuse the same chunk/index/answer stack for drawing notes, BOM and title blocks (research EXP-04/05). Manual↔Drawing links are allowed only as evidence-backed `REFERENCES` (PROJECT_MASTER §3.3). The 3D twin becomes a viewer for the cited drawing.

---

## 5. Timeline (indicative)

```text
Week  1      Phase 0   clean ground
Weeks 2–3    Phase 1   full text, tables, OCR, honest status        ← biggest value
Weeks 4–5    Phase 2   BM25 search + gold set + PDF viewer          ← usable product
Weeks 6–7    Phase 3   hybrid + graph + rerank
Weeks 8–10   Phase 4   local LLM answers  →  v1.0 release
Weeks 11–12  Phase 5   feedback + nightly learning
Then         Phase 6/7 coverage, ACS versions, drawings
```

---

## 6. Metrics dashboard (tracked in CI from Phase 2)

| Metric | v1 target |
|---|---|
| Pages covered by chunks | ≥ 98 % |
| Paras with full text | 100 % |
| Para numbering consistency | ≥ 99 % |
| Retrieval Recall@5 / MRR | ≥ 0.85 / ≥ 0.70 |
| Zero-result rate (real queries) | < 5 % |
| Answers with valid citation | 100 % |
| Numbers verified in cited source | 100 % |
| Correct "not found" on negatives | ≥ 90 % |
| 👍 rate (after Phase 5) | ≥ 80 % and rising |
| Cited chunks that are human-`VERIFIED` | rising each month |
| Search p95 / Answer p95 | < 300 ms / < 20 s |

Node counts, edge counts and graph visuals are **not** success metrics.

---

## 7. Non-negotiable rules

1. No answer without retrieved evidence. No invented para, page, number or rule (PROJECT_MASTER §29).
2. Raw source text is never truncated or overwritten.
3. `VERIFIED` only by a human, with reviewer id and date.
4. Every retrieval or answer change must pass the eval gate. The gold set only grows.
5. Everything runs offline. No telemetry leaves the machine.
6. One roadmap: change this file, and don't create new plan docs.

---

## 8. Documentation map (after consolidation)

| Doc | Role |
|---|---|
| `docs/ROADMAP.md` | **What to build, in what order, and how we measure it** (this file) |
| `docs/PROJECT_MASTER.md` | Contracts: identity, hierarchy, evidence, answer format, guardrails |
| `docs/AUDIT_2026-09_KNOWLEDGE_BASE.md` | Baseline audit that justifies this roadmap |
| `data/knowledge-graph/schemas/ONTOLOGY.md` + `vocabularies/` | Entity and relationship vocabulary |
| `research/` | Papers and experiments (EXP-01…06), feeding phases 1–4 and 7 |
| `docs/archive/` | History only. Do not plan from these. |

## 9. Immediate next 5 tasks

1. Phase 1.1 — remove text caps, and regenerate the KG with full clause text.
2. Phase 1.6 — switch the default status to `EXTRACTED`.
3. Add Gate 1 content checks to `scripts/validate_all.py`.
4. Phase 1.2/1.3 — header/footer strip + IRPWM numbering profile, with a 50-para fixture.
5. Phase 2.3 — draft the first 50 IRPWM gold questions (needs a domain expert's review).
