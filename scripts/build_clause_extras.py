#!/usr/bin/env python3
"""Compact per-clause extras for the browser: extracted measurements and held drawing sheets.

Writes data/search/clause_extras.js:  globalThis.RDSO_CLAUSE_EXTRAS = { "<clause id>": { v: [[comparator, lo, hi, unit, quantity, raw], ...],
                                                                                    d: [[number, "drawings/file.pdf"], ...] } }
Values are capped per clause (largest tables first would flood the card); every number here also exists, with its span, in
canonical/measurements.jsonl and canonical/drawing_links.jsonl. Deterministic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = ROOT / "data" / "search" / "clause_extras.js"
MAX_VALUES = 12
DECIMAL = ("AT_WELD", "FBW", "USFD")


def read(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    extras: dict[str, dict] = {}
    for m in read(KG / "canonical" / "measurements.jsonl"):
        if m["source"] != "text" or m.get("context") != "prose":
            continue             # table cells reach the user as table rows; values in flattened table/figure text lose their meaning
        e = extras.setdefault(m["clause"], {"v": []})
        if len(e["v"]) < MAX_VALUES:
            e["v"].append([m["comparator"], m["lo"], m["hi"], m["unit"], m["quantity"], " ".join(m["raw"].split()),
                           [f"{c['raw']}" for c in m.get("conditions", [])[:3]]])
    # decimal manuals: a paragraph such as 13.1 may be only the lead-in of 13.1.1, 13.1.2 ... which are clauses of their own
    clauses = [n for n in read(KG / "canonical" / "nodes.jsonl") if n["id"].startswith("CLAUSE:") and n["id"].split(":")[1] in DECIMAL]
    by_para = {(n["id"].split(":")[1], str(n["specs"]["Paragraph"])): n["id"] for n in clauses}
    for (alias, para), cid in sorted(by_para.items()):
        kids = [(p2, i2) for (a2, p2), i2 in by_para.items() if a2 == alias and p2.startswith(para + ".") and p2.count(".") == para.count(".") + 1]
        if kids:
            extras.setdefault(cid, {})["s"] = [[p2, i2] for p2, i2 in sorted(kids, key=lambda k: [int(x) if x.isdigit() else 0 for x in k[0].split(".")])][:12]
    files = {r["drawing_id"]: r["file"] for r in read(KG / "canonical" / "drawings_registry.jsonl")}
    for l in read(KG / "canonical" / "drawing_links.jsonl"):
        if l["status"] != "SHEET_HELD":
            continue
        e = extras.setdefault(l["clause"], {})
        d = e.setdefault("d", [])
        for s in l["sheets"]:
            item = [l["number"], files[s]]
            if item not in d:
                d.append(item)
    body = json.dumps(extras, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    OUT.write_text(f"globalThis.RDSO_CLAUSE_EXTRAS={body};\n", encoding="utf-8")
    print(f"clause extras: {len(extras)} clauses, {OUT.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
