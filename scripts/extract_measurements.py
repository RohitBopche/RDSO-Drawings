#!/usr/bin/env python3
"""Extract structured measurements (P2.3) into canonical/measurements.jsonl + a conflict-candidate report.

Reads clause text from canonical/nodes.jsonl and raw/tables.jsonl. Deterministic; does not modify nodes/edges.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import measurements as M  # noqa: E402

CAN = ROOT / "data" / "knowledge-graph" / "canonical"
OUT = CAN / "measurements.jsonl"
REPORT = ROOT / "data" / "knowledge-graph" / "reports" / "measurements_report.json"


def main() -> int:
    recs = []
    for line in (CAN / "nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if n["id"].startswith("CLAUSE:") and n.get("text"):
            recs += M.extract_from_text(n["id"], n["text"])
    for line in (ROOT / "data/knowledge-graph/raw/tables.jsonl").read_text(encoding="utf-8").splitlines():
        t = json.loads(line)
        if t.get("clause"):
            recs += M.extract_from_table(t)
    for i, r in enumerate(recs, 1):
        r["measurement_id"] = f"MEAS:{i:06d}"
        r["verification_status"] = "machine_extracted"
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in recs), encoding="utf-8")

    by_q, by_c, by_u = defaultdict(int), defaultdict(int), defaultdict(int)
    groups = defaultdict(list)
    for r in recs:
        by_q[r["quantity"] or "unclassified"] += 1
        by_c[r["comparator"]] += 1
        by_u[r["unit"]] += 1
        if r["quantity"] and r["comparator"] in ("max", "min"):
            groups[(r["clause"].split(":")[1], r["quantity"], r["unit"], r["comparator"])].append(r)
    cands = []
    for k, v in sorted(groups.items()):
        vals = sorted({(x["hi"] if x["comparator"] == "max" else x["lo"]) for x in v})
        if len(vals) > 1:
            cands.append({"manual": k[0], "quantity": k[1], "unit": k[2], "comparator": k[3], "values": vals,
                          "clauses": sorted({x["clause"] for x in v})[:8]})
    rep = {"total": len(recs), "text": sum(r["source"] == "text" for r in recs), "table": sum(r["source"] == "table" for r in recs),
           "by_quantity": dict(sorted(by_q.items())), "by_comparator": dict(sorted(by_c.items())), "by_unit": dict(sorted(by_u.items())),
           "conflict_candidates_note": "same manual+quantity+unit+comparator with different values: candidates for human review, NOT conflicts",
           "conflict_candidates": len(cands)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"measurements={len(recs)} text={rep['text']} table={rep['table']} candidates={len(cands)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
