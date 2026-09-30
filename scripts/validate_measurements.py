#!/usr/bin/env python3
"""Gate S: measurements are traceable and canonical (P2.3)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import measurements as M  # noqa: E402

MIN_MEASUREMENTS = 5500
CANON_UNITS = set(M.UNIT_MAP.values())


def main() -> int:
    errors = []
    texts = {}
    for line in (ROOT / "data/knowledge-graph/canonical/nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if n["id"].startswith("CLAUSE:"):
            texts[n["id"]] = n.get("text", "")
    tables = {}
    for line in (ROOT / "data/knowledge-graph/raw/tables.jsonl").read_text(encoding="utf-8").splitlines():
        t = json.loads(line)
        tables[t["table_id"]] = t
    recs = [json.loads(l) for l in (ROOT / "data/knowledge-graph/canonical/measurements.jsonl").read_text(encoding="utf-8").splitlines()]
    seen = set()
    for r in recs:
        mid = r["measurement_id"]
        if mid in seen:
            errors.append(f"{mid}: duplicate id")
        seen.add(mid)
        if r["unit"] not in CANON_UNITS:
            errors.append(f"{mid}: non-canonical unit {r['unit']}")
        if r["lo"] is None and r["hi"] is None:
            errors.append(f"{mid}: no numeric bound")
        if r["lo"] is not None and r["hi"] is not None and r["lo"] > r["hi"]:
            errors.append(f"{mid}: lo > hi")
        if r["verification_status"] != "machine_extracted":
            errors.append(f"{mid}: unexpected status {r['verification_status']}")
        if r["source"] == "text":
            t = texts.get(r["clause"])
            if t is None or t[r["start"]:r["end"]].strip() != r["raw"]:
                errors.append(f"{mid}: span does not reproduce clause text")
        else:
            t = tables.get(r["table_id"])
            if t is None or t["rows"][r["row"]][r["col"]].strip() != r["raw"]:
                errors.append(f"{mid}: cell does not reproduce table text")
    if len(recs) < MIN_MEASUREMENTS:
        errors.append(f"only {len(recs)} measurements (< {MIN_MEASUREMENTS})")
    for e in errors[:30]:
        print("[ERROR]", e)
    print(f"[SUMMARY] measurements: {'PASS' if not errors else 'FAIL'}; measurements={len(recs)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
