#!/usr/bin/env python3
"""Extract ruled data tables from the manuals with their structure (E1).

Writes data/knowledge-graph/raw/tables.jsonl, one record per data table:

    table_id  TBL:<alias>:P<page>:<k>      document_id, page, bbox [x0,y0,x1,y1] (PDF points)
    rows      list of rows of cell strings (whitespace normalised, merged cells repeated down/right)
    header_rows  number of leading header rows (heuristic: rows before the first row containing a number);
                 a table that continues on the next page inherits the previous header (header_inherited)
    caption   nearest "Table ..." line above the table on the same page, if any
    clause    canonical clause that owns the table (the last clause head above it in reading order)
    page_sha256  hash of the page text (same as evidence records), so the table can be re-verified

Boxes of running text (one column, or fewer than four filled cells) are not data tables and are skipped.
Deterministic for a given PDF and pinned PyMuPDF.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "raw" / "tables.jsonl"
CAPTION = re.compile(r"^\s*(table|tbl)\b[\s.\-–:]*[0-9A-Za-z][^\n]{0,80}", re.I)


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def clean(c) -> str:
    return " ".join(str(c).split()) if c is not None else ""


def fill_merged(rows: list[list[str]]) -> list[list[str]]:
    """PyMuPDF reports a merged cell once and None for the rest: repeat it across the merged header span."""
    out = []
    for r in rows:
        r = list(r)
        for j in range(1, len(r)):
            if r[j] == "" and r[j - 1] != "" and out == []:   # only in the first (header) row
                r[j] = r[j - 1]
        out.append(r)
    return out


def is_data_table(raw_rows: list[list[str]]) -> bool:
    """A grid with at least two columns that are each filled in at least half of the rows.
    Boxed running text (one wide column, other cells empty) is rejected."""
    if len(raw_rows) < 2:
        return False
    width = max(len(r) for r in raw_rows)
    full_cols = 0
    for j in range(width):
        col = [r[j] if j < len(r) else "" for r in raw_rows]
        if sum(1 for c in col if c) >= max(2, 0.5 * len(raw_rows)):
            full_cols += 1
    filled = [c for r in raw_rows for c in r if c]
    avg_len = sum(len(c) for c in filled) / max(1, len(filled))
    return full_cols >= 2 and len(filled) >= 4 and avg_len < 90


def header_row_count(rows: list[list[str]]) -> int:
    for i, r in enumerate(rows):
        if any(re.search(r"\d", c) and not re.fullmatch(r"(sl\.?|s\.?\s*n\.?|no\.?)\W*(no\.?)?", c.lower()) for c in r if c):
            # a first cell that is only a serial number still belongs to the body
            return min(i, 3)
    return 1


def main() -> int:
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    evidence = [e for e in read_jsonl(KG / "canonical" / "evidence.jsonl") if e["evidence_id"].startswith("ev:clause:") and e.get("region")]
    heads: dict[str, list] = {}
    for e in evidence:
        heads.setdefault(e["document_id"], []).append((e["page_number"], e["region"][1], e["evidence_id"][len("ev:clause:"):]))
    for v in heads.values():
        v.sort()
    records = []
    for doc_id in sorted(registry):
        if registry[doc_id].get("category") != "MANUAL" or doc_id not in heads:
            continue
        alias = doc_id.split(":")[1]
        pdf = pymupdf.open(ROOT / registry[doc_id]["file_path"])
        keys = [(p, y) for p, y, _ in heads[doc_id]]
        for pno, page in enumerate(pdf, 1):
            tabs = page.find_tables().tables
            if not tabs:
                continue
            text = page.get_text()
            page_hash = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
            lines = [(l["bbox"][1], "".join(s["text"] for s in l["spans"]).strip())
                     for b in page.get_text("dict")["blocks"] if b["type"] == 0 for l in b["lines"]]
            k = 0
            for t in sorted(tabs, key=lambda t: (t.bbox[1], t.bbox[0])):
                raw = [[clean(c) for c in r] for r in t.extract()]
                raw = [r for r in raw if any(r)]
                if not is_data_table(raw):
                    continue
                rows = fill_merged(raw)
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                above = [txt for y, txt in lines if y < t.bbox[1] and t.bbox[1] - y < 60 and CAPTION.match(txt)]
                idx = bisect.bisect_right(keys, (pno, t.bbox[1])) - 1
                owner = heads[doc_id][idx][2] if idx >= 0 else None
                k += 1
                hdr = header_row_count(rows)
                inherited = False
                prev = records[-1] if records else None
                if hdr == 0 and prev and prev["document_id"] == doc_id and prev["page"] == pno - 1 and prev["n_cols"] == width and prev["header_rows"]:
                    rows = prev["rows"][:prev["header_rows"]] + rows      # continuation of a table from the previous page
                    hdr, inherited = prev["header_rows"], True
                records.append({"table_id": f"TBL:{alias}:P{pno:04d}:{k:02d}", "document_id": doc_id, "page": pno,
                                "bbox": [round(v, 1) for v in t.bbox], "rows": rows, "n_rows": len(rows), "n_cols": width,
                                "header_rows": hdr, "header_inherited": inherited, "caption": clean(above[-1]) if above else "",
                                "clause": owner, "page_sha256": page_hash})
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    print(f"{len(records)} data tables on {len({(r['document_id'], r['page']) for r in records})} pages -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
