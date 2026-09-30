#!/usr/bin/env python3
"""Gate U: drawing citations reproduce the clause text and point at real registry sheets (P3.6)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import drawing_links as L  # noqa: E402

KG = ROOT / "data" / "knowledge-graph"
MIN_CITATIONS = 130


def main() -> int:
    errors = []
    texts = {}
    for line in (KG / "canonical" / "nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if n["id"].startswith("CLAUSE:"):
            texts[n["id"]] = n.get("text", "")
    registry = [json.loads(l) for l in (KG / "canonical" / "drawings_registry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = {r["drawing_id"] for r in registry}
    cov = L.sheet_coverage(registry)
    recs = [json.loads(l) for l in (KG / "canonical" / "drawing_links.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in recs:
        t = texts.get(r["clause"])
        if t is None or t[r["start"]:r["end"]] != r["raw"]:
            errors.append(f"{r['link_id']}: span does not reproduce clause text")
        if any(s not in ids for s in r["sheets"]):
            errors.append(f"{r['link_id']}: unknown sheet")
        if r["sheets"] != cov.get(r["number"], []):
            errors.append(f"{r['link_id']}: sheets disagree with registry coverage of {r['number']}")
        if (r["status"] == "SHEET_HELD") != bool(r["sheets"]):
            errors.append(f"{r['link_id']}: status inconsistent with sheets")
    if len(recs) < MIN_CITATIONS:
        errors.append(f"only {len(recs)} drawing citations (< {MIN_CITATIONS})")
    for e in errors[:30]:
        print("[ERROR]", e)
    print(f"[SUMMARY] drawing links: {'FAIL' if errors else 'PASS'}; citations={len(recs)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
