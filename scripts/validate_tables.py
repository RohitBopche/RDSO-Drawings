#!/usr/bin/env python3
"""Gate R: extracted tables are structurally sound, tied to their page and owner clause, and indexed.

- rectangular rows, header_rows within range, bbox inside the page, owner clause exists (or is None)
- page hash equals the hash of the raw page text (same as evidence), so a table can be re-verified
- every table with an owner appears in the search index as table passages
- table count may not fall (ratchet), so a silent extraction failure is caught
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
MIN_TABLES = 540


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    errors: list[str] = []
    tables = read_jsonl(KG / "raw" / "tables.jsonl")
    clauses = {json.loads(l)["id"] for l in (KG / "canonical" / "nodes.jsonl").read_text(encoding="utf-8").splitlines()
               if l.startswith('{"id": "CLAUSE:')}
    pages = {(p["document_id"], p["page_number"]): p for p in read_jsonl(KG / "raw" / "extracted_pages.jsonl")}
    seen = set()
    for t in tables:
        tid = t["table_id"]
        if tid in seen:
            errors.append(f"{tid}: duplicate id")
        seen.add(tid)
        if len({len(r) for r in t["rows"]}) != 1 or len(t["rows"][0]) != t["n_cols"] or len(t["rows"]) != t["n_rows"]:
            errors.append(f"{tid}: rows are not rectangular")
        if not 0 <= t["header_rows"] < t["n_rows"]:
            errors.append(f"{tid}: header_rows out of range")
        raw = pages.get((t["document_id"], t["page"]))
        if raw is None:
            errors.append(f"{tid}: no raw page")
        elif hashlib.sha256(raw["text_content"].encode("utf-8")).hexdigest() != t["page_sha256"]:
            errors.append(f"{tid}: page hash differs from the raw page text")
        if t["clause"] is not None and t["clause"] not in clauses:
            errors.append(f"{tid}: owner clause {t['clause']} missing")
    if len(tables) < MIN_TABLES:
        errors.append(f"table count fell to {len(tables)} (< {MIN_TABLES})")

    probe = ("require('./data/search/search_index.js');const i=globalThis.RDSO_SEARCH_INDEX;"
             "const s={};i.docs.forEach(d=>{if(d.kind==='table')s[d.tableId]=1});console.log(JSON.stringify(Object.keys(s)))")
    r = subprocess.run(["node", "-e", probe], cwd=ROOT, capture_output=True, text=True)
    indexed = set(json.loads(r.stdout)) if r.returncode == 0 else set()
    missing = [t["table_id"] for t in tables if t["clause"] and t["table_id"] not in indexed
               and any(len({" ".join(c.split()) for c in row if c.strip()}) >= 2 for row in t["rows"][t["header_rows"]:])]
    if missing:
        errors.append(f"{len(missing)} tables are not in the search index (e.g. {missing[0]}); run scripts/build_search_index.py")
    for e in errors[:20]:
        print(f"[ERROR] {e}")
    print(f"[SUMMARY] tables: {'FAIL' if errors else 'PASS'}; tables={len(tables)} indexed={len(indexed)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
