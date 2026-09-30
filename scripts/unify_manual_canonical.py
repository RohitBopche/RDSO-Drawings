#!/usr/bin/env python3
"""Make the canonical store the single source for manual clause content (P0-R.1/R.2).

Reads the authoritative deterministic extraction
(`data/knowledge-graph/intermediate/all_chapters_extracted.json`) and updates,
idempotently:

- canonical clause nodes: full verbatim `text`, page, paragraph, summary `desc`
- TOLERANCE nodes + clause -[SPECIFIES]-> tolerance edges (machine_extracted)
- requirements.jsonl: one row per clause/tolerance with real statements;
  rows whose id matches no node are moved to
  `intermediate/quarantine_dangling_requirements.jsonl` (nothing is lost)
- data/rdso_canonical_kg.json, exports/graph.json, exports/search_index.json
- data/rdso_manuals_knowledge.json, regenerated as a *derived view* of canonical
- reports/metrics.json, the only place project metrics should be quoted from

Extraction output is labelled `machine_extracted`, never `verified`.
Run `python scripts/export_kg_bundle.py` afterwards to refresh the browser bundle.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import provenance_policy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
CANON = KG / "canonical"
INTER = KG / "intermediate"
EXPORTS = KG / "exports"
REPORTS = KG / "reports"
SRC = INTER / "all_chapters_extracted.json"
LEGACY_JSON = ROOT / "data" / "rdso_canonical_kg.json"
MANUALS_VIEW = ROOT / "data" / "rdso_manuals_knowledge.json"
QUARANTINE = INTER / "quarantine_dangling_requirements.jsonl"
METRICS = REPORTS / "metrics.json"

MACHINE = "machine_extracted"
RELATION_NORM = {"CONTAINS_CHAPTER": "HAS_SECTION", "CONTAINS_CLAUSE": "HAS_CLAUSE"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def tol_id(alias: str, text: str) -> str:
    return f"TOL:{alias}:{re.sub(r'[^A-Za-z0-9]', '_', text).strip('_')}"


def to_int(v):
    try:
        return int(str(v))
    except (TypeError, ValueError):
        return None


def build() -> dict:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    legacy = json.loads(LEGACY_JSON.read_text(encoding="utf-8"))
    jsonl_nodes = {n["id"]: n for n in read_jsonl(CANON / "nodes.jsonl")}
    # The two stores diverged: the compact JSON carries provenance/hierarchy fields,
    # the JSONL carries name/status fields. Merge them into one node record.
    nodes = []
    for e in legacy["entities"]:
        merged = dict(e)
        for k, v in jsonl_nodes.get(e["id"], {}).items():
            merged.setdefault(k, v)
        nodes.append(merged)
    edges = read_jsonl(CANON / "edges.jsonl")
    json_edges = list(legacy["edges"])
    reqs = read_jsonl(CANON / "requirements.jsonl")
    evidence_ids = {e["evidence_id"] for e in read_jsonl(CANON / "evidence.jsonl")}
    by_id = {n["id"]: n for n in nodes}
    edge_keys = {(e["from"], e["to"], e["rel"]) for e in edges}

    clause_rows: dict[str, dict] = {}
    tol_nodes: dict[str, dict] = {}
    tol_edges: list[dict] = []
    manual_catalog = []

    for man in src["manuals"]:
        alias, doc_id = man["alias"], man["document_id"]
        manual_catalog.append({
            "id": doc_id, "alias": alias, "title": man["title"],
            "chapter_count": len(man["chapters"]),
            "clause_count": sum(len(c["clauses"]) for c in man["chapters"]),
        })
        for ch in man["chapters"]:
            for cl in ch["clauses"]:
                cid = cl["clause_id"]
                node = by_id.get(cid)
                if node is None:
                    raise SystemExit(f"extraction clause {cid} has no canonical node")
                text = cl.get("verbatim_text") or cl.get("source_text") or ""
                page = to_int(cl.get("page_number"))
                node["text"] = text
                node["desc"] = node["description"] = cl.get("summary") or text[:280]
                node["page"] = page
                node["document_id"] = doc_id
                node["extraction_method"] = cl.get("extraction_method", "deterministic_manual_clause_numbering")
                node["verification_status"] = MACHINE
                specs = node.setdefault("specs", {})
                specs["Manual Ref"] = str(cl["para_number"])
                specs["Paragraph"] = str(cl["para_number"])
                specs["Page"] = page
                specs["Manual"] = doc_id
                ev_id = f"ev:clause:{cid}"
                if ev_id in evidence_ids:
                    node["evidence_ids"] = [ev_id]
                clause_rows[cid] = {
                    "cl": cl, "alias": alias, "doc_id": doc_id, "chapter": ch,
                    "page": page, "text": text,
                }
                for t in cl.get("tolerances", []):
                    tid = tol_id(alias, t["text"])
                    if tid not in tol_nodes and tid not in by_id:
                        tol_nodes[tid] = {
                            "id": tid, "type": "TOLERANCE",
                            "name": f"Tolerance: {t['text'].strip()}",
                            "label": f"Tolerance: {t['text'].strip()}",
                            "domain": "manual", "universe": "manuals", "color": "#fee440",
                            "description": f"Bound {t['text'].strip()} first specified in Para {cl['para_number']}",
                            "desc": f"Bound {t['text'].strip()} first specified in Para {cl['para_number']}",
                            "specs": dict(t), "document_id": doc_id,
                            "source_document": doc_id, "source_page": page,
                            "source_section": str(cl["para_number"]),
                            "source_text": text[:300], "confidence": 0.8,
                            "extraction_method": "deterministic_tolerance_regex",
                            "parent_chapter_id": ch["chapter_id"],
                            "provenance": {"source_document": doc_id, "source_page": page,
                                           "source_section": str(cl["para_number"]),
                                           "confidence": 0.8,
                                           "extraction_method": "deterministic_tolerance_regex",
                                           "chapter_id": ch["chapter_id"]},
                            "verification_status": MACHINE, "status": "active",
                        }
                    key = (cid, tid, "SPECIFIES")
                    if key not in edge_keys:
                        edge_keys.add(key)
                        rec = {"from": cid, "to": tid, "rel": "SPECIFIES",
                               "rationale": f"Specified by Para {cl['para_number']}", "source": None}
                        if f"ev:clause:{cid}" in evidence_ids:
                            rec["evidence_ids"] = [f"ev:clause:{cid}"]
                        tol_edges.append(rec)

    for tid, tn in tol_nodes.items():
        by_id[tid] = tn
        nodes.append(tn)
    edges.extend(tol_edges)
    # Rebuild-safe: make sure the compact core carries every canonical edge (vocabulary-normalised).
    norm = lambda e: (e["from"], e["to"], RELATION_NORM.get(e["rel"], e["rel"]))
    have = {norm(e) for e in json_edges}
    json_edges.extend(e for e in edges if norm(e) not in have)

    # --- requirements: regenerate manual rows, quarantine dangling rows ---
    kept, quarantined = [], []
    manual_req_ids = set(clause_rows) | {n["id"] for n in nodes if n["type"] == "TOLERANCE"}
    for r in reqs:
        if r["id"] in manual_req_ids:
            continue  # regenerated below
        (kept if r["id"] in by_id else quarantined).append(r)
    new_rows = []
    for cid, info in clause_rows.items():
        cl = info["cl"]
        row = {
            "id": cid, "statement": info["text"], "requirement_type": "procedure",
            "priority": "unknown", "confidence": 0.95, "verification_status": MACHINE,
            "clause": str(cl["para_number"]), "source_document_id": info["doc_id"],
        }
        if f"ev:clause:{cid}" in evidence_ids:
            row["evidence_ids"] = [f"ev:clause:{cid}"]
        new_rows.append(row)
    for n in nodes:
        if n["type"] == "TOLERANCE" and n["id"] in by_id:
            new_rows.append({
                "id": n["id"], "statement": n["description"], "requirement_type": "geometry",
                "priority": "unknown", "confidence": 0.8, "verification_status": MACHINE,
            })
    reqs = kept + new_rows
    if quarantined:
        write_jsonl(QUARANTINE, quarantined)


    # --- unified core json (keep facts; add facts for new edges) ---
    facts = legacy.get("facts", [])
    have = {(f["subject_id"], f["object_id"], f["predicate"]) for f in facts}
    for e in json_edges:
        if e["rel"] != "SPECIFIES" or e["from"] not in clause_rows:
            continue
        if (e["from"], e["to"], e["rel"]) in have:
            continue
        facts.append({
            "id": f"fact_{len(facts) + 1:04d}", "subject_id": e["from"], "predicate": e["rel"],
            "object_id": e["to"],
            "source": {"drawing_id": clause_rows[e["from"]]["doc_id"], "revision": "STRUCTURE",
                       "region": str(clause_rows[e["from"]]["cl"]["para_number"]), "crop": ""},
            "confidence": 0.8, "status": "MACHINE_EXTRACTED",
            "extraction_method": "deterministic_text_extraction",
            "evidence_text": e["rationale"],
        })
    evidence = read_jsonl(CANON / "evidence.jsonl")
    reviews_path = CANON / "reviews.jsonl"
    reviews = read_jsonl(reviews_path) if reviews_path.exists() else []
    provenance_policy.apply(nodes, reqs, evidence, facts, reviews)
    write_jsonl(CANON / "nodes.jsonl", nodes)
    write_jsonl(CANON / "edges.jsonl", edges)
    write_jsonl(CANON / "requirements.jsonl", reqs)
    write_jsonl(CANON / "evidence.jsonl", evidence)

    meta = legacy.get("metadata", {})
    meta.update(total_entities=len(nodes), total_edges=len(edges), total_facts=len(facts))
    legacy = {"metadata": meta, "entities": nodes, "edges": json_edges, "facts": facts}
    LEGACY_JSON.write_text(json.dumps(legacy, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- exports ---
    (EXPORTS / "graph.json").write_text(json.dumps({
        "metadata": {**meta, "total_nodes": len(nodes)}, "nodes": nodes, "edges": edges,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    index = []
    for n in nodes:
        blob = f"{n['id']} {n.get('label', '')} {n.get('desc', '')} {n.get('text', '')} {json.dumps(n.get('specs', {}))}"
        index.append({"id": n["id"], "name": n["name"], "label": n.get("label", n["name"]),
                      "type": n["type"], "domain": n.get("domain", "general"),
                      "desc": n.get("desc", ""), "tokens": sorted(set(re.findall(r"\b[A-Za-z0-9\-\./_]+\b", blob)))})
    (EXPORTS / "search_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- derived legacy manuals view ---
    clauses = {}
    for cid, info in clause_rows.items():
        cl = info["cl"]
        clauses[cid] = {
            "id": cid, "para": cl["para_number"], "title": cl["title"], "manual": info["alias"],
            "chapter": info["chapter"]["title"], "page": cl["page_number"],
            "summary": cl["summary"], "verbatim": info["text"], "roles": cl["roles"],
            "equipment": cl["equipment"], "failure_modes": cl["failure_modes"],
            "tolerances": [t["text"] for t in cl["tolerances"]],
        }
    tolerances = {n["id"]: n["specs"] for n in nodes
                  if n["type"] == "TOLERANCE" and n["id"].startswith("TOL:")}
    MANUALS_VIEW.write_text(json.dumps({
        "metadata": {"title": "RDSO Railway Codes & Manuals Canonical Knowledge Base",
                     "version": "3.0.0-deep-chapter-extraction", "manuals_count": len(manual_catalog),
                     "clauses_count": len(clauses), "tolerances_count": len(tolerances),
                     "derived_from": "data/knowledge-graph/canonical (do not edit)"},
        "manuals": manual_catalog, "clauses": clauses, "tolerances": tolerances,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    return write_metrics()


SHORT_CLAUSE_CHARS = 60
RAW_PAGES = KG / "raw" / "extracted_pages.jsonl"


def compute_metrics() -> dict:
    """Deterministic metrics from committed files only; the single quotable source."""
    nodes = read_jsonl(CANON / "nodes.jsonl")
    edges = read_jsonl(CANON / "edges.jsonl")
    reqs = read_jsonl(CANON / "requirements.jsonl")
    evid = read_jsonl(CANON / "evidence.jsonl")
    reviews = read_jsonl(CANON / "reviews.jsonl") if (CANON / "reviews.jsonl").exists() else []
    per_manual: dict[str, dict] = {}
    for n in nodes:
        if n["type"] == "SPECIFICATION" and n["id"].startswith("CLAUSE:"):
            m = per_manual.setdefault(n.get("document_id") or n["specs"].get("Manual", "?"),
                                      {"clauses": 0, "clauses_with_text": 0, "short_clauses": 0})
            text = (n.get("text") or "").strip()
            m["clauses"] += 1
            m["clauses_with_text"] += 1 if len(text) > 3 else 0
            m["short_clauses"] += 1 if len(text) < SHORT_CLAUSE_CHARS else 0
    pages: dict[str, dict] = {}
    if RAW_PAGES.exists():
        for p in read_jsonl(RAW_PAGES):
            doc = p["document_id"]
            if doc in per_manual:
                d = pages.setdefault(doc, {"pages": 0, "non_extractable_pages": 0, "raw_detected_clauses": 0})
                d["pages"] += 1
                d["non_extractable_pages"] += 0 if p.get("is_extractable") else 1
                d["raw_detected_clauses"] += len(p.get("detected_clauses", []))
    for doc, d in pages.items():
        per_manual[doc].update(d)
    types: dict[str, int] = {}
    for n in nodes:
        types[n["type"]] = types.get(n["type"], 0) + 1

    def statuses(rows):
        out: dict[str, int] = {}
        for r in rows:
            out[r.get("verification_status", "?")] = out.get(r.get("verification_status", "?"), 0) + 1
        return dict(sorted(out.items()))

    return {
        "generated_by": "scripts/unify_manual_canonical.py",
        "nodes": len(nodes), "edges": len(edges), "requirements": len(reqs), "evidence": len(evid),
        "reviews": len(reviews),
        "edges_with_evidence": sum(1 for e in edges if e.get("evidence_ids")),
        "evidence_with_page": sum(1 for e in evid if e.get("page_number")),
        "evidence_with_bbox": sum(1 for e in evid if e.get("bbox")),
        "node_types": dict(sorted(types.items())),
        "verification_status": statuses(nodes),
        "evidence_status": statuses(evid),
        "manual_clauses": dict(sorted(per_manual.items())),
    }


def write_metrics() -> dict:
    metrics = compute_metrics()
    REPORTS.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def main() -> int:
    if "--check-metrics" in sys.argv:
        stored = json.loads(METRICS.read_text(encoding="utf-8"))
        if stored != compute_metrics():
            print("reports/metrics.json is stale; run scripts/unify_manual_canonical.py")
            return 1
        print("metrics.json is current")
        return 0
    metrics = build()
    print(json.dumps({k: metrics[k] for k in ("nodes", "edges", "requirements", "evidence")}, indent=2))
    print(f"wrote {METRICS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
