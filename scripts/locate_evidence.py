#!/usr/bin/env python3
"""Locate every manual node's source text on its PDF page (P0-R.4).

For each canonical manual node that carries `source_text` + `source_page` (and each
chapter, at its first page) write one record to
`data/knowledge-graph/raw/evidence_locations.jsonl`:

    evidence_id, node_id, document_id, page_number, region [x0,y0,x1,y1] (PDF points,
    top-left origin), line_regions, page_width, page_height, pdf_sha256, page_sha256,
    locator (word_sequence | page_only), match_ratio, quote

`page_sha256` is the SHA-256 of the page text as extracted (the stripped page text, identical to the raw layer's
`text_content`), so evidence can be re-verified against the PDF at any time.
Deterministic given the PDFs and the pinned PyMuPDF version.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "raw" / "evidence_locations.jsonl"
QUOTE_CHARS = 300
ANCHOR = 6
MIN_RATIO = 0.8


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_id_for(node: dict) -> str:
    return f"ev:clause:{node['id']}" if node["id"].startswith("CLAUSE:") else f"ev:src:{node['id']}"


FUSED_RE = re.compile(r"^(\d{3,4})([A-Z][a-z].*)$")


def split_fused(words: list) -> list:
    """Some manuals set the paragraph number and title without a space ("302Types"); the parser
    normalises that, so split the PDF word the same way (both halves keep the original box)."""
    out = []
    for w in words:
        m = FUSED_RE.match(w[4])
        if m:
            out.append((*w[:4], m.group(1), *w[5:]))
            out.append((*w[:4], m.group(2), *w[5:]))
        else:
            out.append(w)
    return out


def locate(words: list, quote: str):
    """Find `quote` in the page word list; returns (indices, ratio) or None."""
    q = quote.split()
    if len(quote) >= QUOTE_CHARS and len(q) > 1:
        q = q[:-1]  # the quote was cut mid-word
    if not q:
        return None
    toks = [w[4] for w in words]
    first_anchor = None
    for k in (min(ANCHOR, len(q)), min(3, len(q)), 1):
        for i in range(len(toks) - k + 1):
            if toks[i:i + k] == q[:k]:
                if first_anchor is None and k >= min(2, len(q)):
                    first_anchor = i
                seg = toks[i:i + len(q)]
                ratio = difflib.SequenceMatcher(None, seg, q, autojunk=False).ratio()
                if ratio >= MIN_RATIO:
                    return list(range(i, min(i + len(q), len(toks)))), ratio, "word_sequence"
    if first_anchor is not None:
        # Reading order of the layout parser differs from the PDF text order (tables, columns):
        # the full span cannot be matched, but the opening words can be located exactly.
        return list(range(first_anchor, min(first_anchor + 3 * ANCHOR, len(toks)))), 0.0, "anchor_only"
    return None


def rects(words: list, idx: list[int]):
    lines: dict[tuple, list] = {}
    for i in idx:
        w = words[i]
        lines.setdefault((w[5], w[6]), []).append(w)
    out = []
    for key in sorted(lines):
        ws = lines[key]
        out.append([round(min(w[0] for w in ws), 1), round(min(w[1] for w in ws), 1),
                    round(max(w[2] for w in ws), 1), round(max(w[3] for w in ws), 1)])
    union = [min(r[0] for r in out), min(r[1] for r in out), max(r[2] for r in out), max(r[3] for r in out)]
    return union, out


def main() -> int:
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    nodes = read_jsonl(KG / "canonical" / "nodes.jsonl")
    todo = []
    for n in nodes:
        if n.get("domain") != "manual":
            continue
        doc = n.get("source_document") or n.get("document_id") or (n.get("specs") or {}).get("Manual")
        if n.get("source_text") and str(n.get("source_page", "")).isdigit() and doc in registry:
            todo.append((n, doc, int(n["source_page"]), n["source_text"][:QUOTE_CHARS]))
        elif n["type"] == "CHAPTER":
            rng = (n.get("specs") or {}).get("Page Range") or (n.get("specs") or {}).get("PageRange")
            man = n["id"].split(":")[1]
            docs = [d for d in registry if d.startswith(f"DOC:{man}:") or d == f"DOC:{man}:2022" or d.split(":")[1] == man]
            if rng and docs:
                todo.append((n, docs[0], int(rng[0]), n["label"]))
    by_doc: dict[str, list] = {}
    for item in todo:
        by_doc.setdefault(item[1], []).append(item)

    records, misses = [], 0
    for doc_id in sorted(by_doc):
        reg = registry[doc_id]
        pdf = pymupdf.open(ROOT / reg["file_path"])
        pdf_hash = reg["sha256"]
        cache: dict[int, tuple] = {}
        for n, _, page_no, quote in by_doc[doc_id]:
            if not 1 <= page_no <= len(pdf):
                misses += 1
                continue
            if page_no not in cache:
                page = pdf[page_no - 1]
                cache[page_no] = (split_fused(page.get_text("words")), hashlib.sha256(page.get_text().strip().encode("utf-8")).hexdigest(),
                                  round(page.rect.width, 1), round(page.rect.height, 1))
            words, page_hash, w, h = cache[page_no]
            rec = {"evidence_id": evidence_id_for(n), "node_id": n["id"], "document_id": doc_id,
                   "page_number": page_no, "page_width": w, "page_height": h,
                   "pdf_sha256": pdf_hash, "page_sha256": page_hash, "quote": quote}
            hit = locate(words, quote) if n["type"] != "CHAPTER" else None
            if hit:
                union, lines = rects(words, hit[0])
                rec.update(region=union, line_regions=lines, locator=hit[2], match_ratio=round(hit[1], 3))
            else:
                rec.update(region=None, line_regions=[], locator="page_only", match_ratio=0.0)
            records.append(rec)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    located = sum(1 for r in records if r["region"])
    print(f"located {located}/{len(records)} evidence regions ({misses} out-of-range pages) -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
