#!/usr/bin/env python3
"""Gate L: manual text integrity and single-source-of-truth checks.

Fails when canonical manual clauses lack real text, requirements are empty or
dangling, the JSONL store and the compact JSON core diverge, the derived legacy
manuals view or browser bundle drift from canonical, or metrics.json is stale.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "knowledge-graph" / "canonical"
METRICS = ROOT / "data" / "knowledge-graph" / "reports" / "metrics.json"
CORE_JSON = ROOT / "data" / "rdso_canonical_kg.json"
MANUALS_VIEW = ROOT / "data" / "rdso_manuals_knowledge.json"
BUNDLE = ROOT / "data" / "rdso_kg_data.js"
EXTRACTION = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"

RELATION_NORM = {"CONTAINS_CHAPTER": "HAS_SECTION", "CONTAINS_CLAUSE": "HAS_CLAUSE"}
EMPTY = {"", "...", "…"}
# Ratchet: clauses whose text is barely more than a heading (known extraction gap,
# tracked under P0-R.6). May only go down.
SHORT_CLAUSE_CHARS = 60
SHORT_CLAUSE_BASELINE = 325


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def bundle_object(name: str):
    text = BUNDLE.read_text(encoding="utf-8")
    marker = f"_root.{name} = "
    start = text.index(marker) + len(marker)
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def main() -> int:
    errors: list[str] = []
    nodes = read_jsonl(CANON / "nodes.jsonl")
    edges = read_jsonl(CANON / "edges.jsonl")
    reqs = read_jsonl(CANON / "requirements.jsonl")
    by_id = {n["id"]: n for n in nodes}
    clauses = [n for n in nodes if n["id"].startswith("CLAUSE:") and n["type"] == "SPECIFICATION"]

    # 1. clause text
    short = 0
    for n in clauses:
        t = (n.get("text") or "").strip()
        if t in EMPTY or len(t) < 3:
            errors.append(f"clause {n['id']}: empty text")
        elif len(t) < SHORT_CLAUSE_CHARS:
            short += 1
        if n.get("page") is None:
            errors.append(f"clause {n['id']}: missing page")
    if short > SHORT_CLAUSE_BASELINE:
        errors.append(f"short-clause ratchet exceeded: {short} > {SHORT_CLAUSE_BASELINE}")

    # 2. requirements
    seen: set[str] = set()
    for r in reqs:
        if r["id"] in seen:
            errors.append(f"requirement {r['id']}: duplicate id")
        seen.add(r["id"])
        if r["id"] not in by_id:
            errors.append(f"requirement {r['id']}: dangling (no node)")
        if r["statement"].strip() in EMPTY:
            errors.append(f"requirement {r['id']}: empty statement")
    missing = {n["id"] for n in clauses} - seen
    if missing:
        errors.append(f"{len(missing)} clauses have no requirement row")

    # 3. JSONL vs compact JSON core
    core = json.loads(CORE_JSON.read_text(encoding="utf-8"))
    core_nodes = {e["id"]: e for e in core["entities"]}
    if set(core_nodes) != set(by_id):
        errors.append(f"node id sets differ: jsonl={len(by_id)} core={len(core_nodes)}")
    else:
        for i, n in by_id.items():
            if core_nodes[i] != n:
                errors.append(f"node {i}: JSONL and core JSON records differ")
                break
    norm = lambda es: {(e["from"], e["to"], RELATION_NORM.get(e["rel"], e["rel"])) for e in es}
    if norm(core["edges"]) != norm(edges):
        errors.append("edge sets differ between JSONL and core JSON (after vocabulary normalisation)")

    # 4. derived legacy manuals view
    view = json.loads(MANUALS_VIEW.read_text(encoding="utf-8"))
    if set(view["clauses"]) != {n["id"] for n in clauses}:
        errors.append("manuals view clause ids differ from canonical")
    else:
        for n in clauses:
            if view["clauses"][n["id"]]["verbatim"] != n["text"]:
                errors.append(f"manuals view text differs from canonical for {n['id']}")
                break
    for tid in view["tolerances"]:
        if tid not in by_id:
            errors.append(f"manuals view tolerance {tid} not in canonical")

    # 5. extraction drift
    src = json.loads(EXTRACTION.read_text(encoding="utf-8"))
    src_ids = {cl["clause_id"] for m in src["manuals"] for c in m["chapters"] for cl in c["clauses"]}
    if src_ids != {n["id"] for n in clauses}:
        errors.append("canonical clause ids differ from deterministic extraction")

    # 6. metrics freshness
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    if (m["nodes"], m["edges"], m["requirements"]) != (len(nodes), len(edges), len(reqs)):
        errors.append("reports/metrics.json is stale; run scripts/unify_manual_canonical.py")

    # 7. browser bundle
    if BUNDLE.exists():
        b = bundle_object("RDSO_CANONICAL_KG")
        if len(b["entities"]) != len(nodes) or len(b["edges"]) != len(core["edges"]):
            errors.append("rdso_kg_data.js is stale; run scripts/export_kg_bundle.py")
        bm = bundle_object("RDSO_MANUALS_KNOWLEDGE")
        if len(bm["clauses"]) != len(view["clauses"]):
            errors.append("rdso_kg_data.js manuals view is stale")

    for e in errors[:50]:
        print(f"[ERROR] {e}")
    print(f"[SUMMARY] manual text integrity: {'FAIL' if errors else 'PASS'}; "
          f"clauses={len(clauses)} short(<{SHORT_CLAUSE_CHARS})={short}/{SHORT_CLAUSE_BASELINE} "
          f"requirements={len(reqs)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
