#!/usr/bin/env python3
"""Gate Q: cross-references are extracted, classified and resolvable (Master §14, P2.1).

- crossrefs.jsonl equals a fresh extraction from the canonical clause text (no stale data)
- each record's span reproduces its raw text inside the source clause
- every status is one of RESOLVED / DELETED / EXTERNAL / AMBIGUOUS / NOT_FOUND and RESOLVED targets exist
- every resolved reference has a REFERENCES edge (with evidence) from the source to each target
- unresolved paragraph references may only go down (ratchet)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import crossrefs  # noqa: E402

CANON = ROOT / "data" / "knowledge-graph" / "canonical"
STATUSES = {"RESOLVED", "DELETED", "EXTERNAL", "AMBIGUOUS", "NOT_FOUND"}
MAX_UNRESOLVED_PARAS = 9


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    errors: list[str] = []
    nodes = read_jsonl(CANON / "nodes.jsonl")
    by_id = {n["id"]: n for n in nodes}
    edges = read_jsonl(CANON / "edges.jsonl")
    refs = read_jsonl(CANON / "crossrefs.jsonl")
    src = json.loads((ROOT / "data/knowledge-graph/intermediate/all_chapters_extracted.json").read_text(encoding="utf-8"))
    deleted = {m["alias"]: src["clause_parse_stats"][m["document_id"]]["deleted_paras"] for m in src["manuals"]}

    if crossrefs.extract(nodes, deleted) != refs:
        errors.append("crossrefs.jsonl differs from a fresh extraction; run scripts/rebuild_all.py")

    ref_edges = {(e["from"], e["to"]): e for e in edges if e["rel"] == "REFERENCES"}
    unresolved_paras = 0
    for r in refs:
        node = by_id.get(r["source"])
        if node is None:
            errors.append(f"{r['ref_id']}: source clause missing")
            continue
        if node["text"][r["start"]:r["end"]] != r["raw"]:
            errors.append(f"{r['ref_id']}: span does not reproduce raw text")
        if r["status"] not in STATUSES:
            errors.append(f"{r['ref_id']}: bad status {r['status']}")
        if r["status"] == "RESOLVED":
            if not r["targets"]:
                errors.append(f"{r['ref_id']}: RESOLVED without targets")
            for t in r["targets"]:
                if t not in by_id:
                    errors.append(f"{r['ref_id']}: target {t} does not exist")
                elif t != r["source"] and (r["source"], t) not in ref_edges:
                    errors.append(f"{r['ref_id']}: no REFERENCES edge {r['source']} -> {t}")
        elif r["targets"]:
            errors.append(f"{r['ref_id']}: {r['status']} must not have targets")
        if r["target_kind"] == "para" and r["status"] == "NOT_FOUND":
            unresolved_paras += 1
    for (a, b), e in ref_edges.items():
        if not e.get("evidence_ids"):
            errors.append(f"REFERENCES {a} -> {b}: no evidence")
    if unresolved_paras > MAX_UNRESOLVED_PARAS:
        errors.append(f"unresolved paragraph references {unresolved_paras} > ratchet {MAX_UNRESOLVED_PARAS}")

    for e in errors[:25]:
        print(f"[ERROR] {e}")
    s = crossrefs.summarize(refs)
    print(f"[SUMMARY] cross-references: {'FAIL' if errors else 'PASS'}; total={s['total']} {s['by_status']} "
          f"unresolved_paras={unresolved_paras} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
