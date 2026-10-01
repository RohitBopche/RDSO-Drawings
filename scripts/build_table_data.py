#!/usr/bin/env python3
"""Browser file with the extracted tables, so the chat can show a matching row under its column headers.

data/search/tables.js:  globalThis.RDSO_TABLES = { "<table id>": { h: [header per column], r: [[cell,...],...], p: page, k: owner clause id, c: caption } }
Header cells of a multi-row header are already joined by extract_tables.py. Cells keep their newlines (wrapped records). Deterministic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = ROOT / "data" / "search" / "tables.js"
MAX_ROWS = 80


def main() -> int:
    out = {}
    for l in (KG / "raw" / "tables.jsonl").read_text(encoding="utf-8").splitlines():
        t = json.loads(l)
        if not t.get("clause") or not t["header_rows"]:
            continue
        hdr = [" ".join(" ".join(t["rows"][:t["header_rows"]][i][j] for i in range(t["header_rows"])).split()) for j in range(t["n_cols"])]
        body = t["rows"][t["header_rows"]:][:MAX_ROWS]
        out[t["table_id"]] = {"h": hdr, "r": body, "p": t["page"], "k": t["clause"], "c": t.get("caption", ""), "n": len(t["rows"]) - t["header_rows"]}
    OUT.write_text("globalThis.RDSO_TABLES=" + json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"table data: {len(out)} tables, {OUT.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
