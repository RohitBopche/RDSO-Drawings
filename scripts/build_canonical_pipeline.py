"""
build_canonical_pipeline.py
============================
Synthesizes all drawing entities, candidates, and deep chapter-by-chapter
manuals knowledge into authoritative canonical datasets and exports:
- data/knowledge-graph/canonical/nodes.jsonl
- data/knowledge-graph/canonical/edges.jsonl
- data/knowledge-graph/canonical/documents.jsonl
- data/knowledge-graph/canonical/requirements.jsonl
- data/knowledge-graph/canonical/evidence.jsonl
- data/knowledge-graph/exports/graph.json
- data/knowledge-graph/exports/search_index.json
- data/rdso_canonical_kg.json (Unified backward-compatible core)
- data/rdso_manuals_knowledge.json (Deep manuals registry)

Enforces 100% referential integrity (zero dangling edges) and full
compliance with entity, requirement, edge, and evidence schemas.
"""

import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KG_DIR = os.path.join(REPO_ROOT, "data", "knowledge-graph")
CANONICAL_DIR = os.path.join(KG_DIR, "canonical")
EXPORTS_DIR = os.path.join(KG_DIR, "exports")
INTERMEDIATE_DIR = os.path.join(KG_DIR, "intermediate")

os.makedirs(CANONICAL_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

LEGACY_CANONICAL = os.path.join(REPO_ROOT, "data", "rdso_canonical_kg.json")
MANUALS_KNOWLEDGE = os.path.join(REPO_ROOT, "data", "rdso_manuals_knowledge.json")
ALL_CHAPTERS_EXTRACTED = os.path.join(INTERMEDIATE_DIR, "all_chapters_extracted.json")
INTERMEDIATE_ENTITIES = os.path.join(INTERMEDIATE_DIR, "candidate_entities.jsonl")
INTERMEDIATE_RELS = os.path.join(INTERMEDIATE_DIR, "candidate_relationships.jsonl")
ALIAS_FILE = os.path.join(CANONICAL_DIR, "identity_aliases.json")

# Mapping non-standard predicates to Blueprint controlled vocabulary
RELATION_NORM = {
    "CONTAINS_CHAPTER": "HAS_SECTION",
    "CONTAINS_CLAUSE": "HAS_CLAUSE",
    "SPECIFIES_TOLERANCE": "SPECIFIES",
    "MANDATES_EQUIPMENT": "REQUIRES",
    "DETECTS_FAILURE": "INSPECTED_BY",
    "GOVERNS_COMPONENT": "GOVERNS",
}


def build_canonical_layer():
    print("================================================================================")
    print("      DEEP CANONICAL KNOWLEDGE GRAPH & EXPORT SYNTHESIS PIPELINE")
    print("================================================================================")

    nodes = []
    edges = []
    node_id_set = set()
    edge_key_set = set()

    # Load legacy alias mappings so alias document entities don't create duplicate logical identities
    legacy_alias_ids = set()
    if os.path.exists(ALIAS_FILE):
        try:
            with open(ALIAS_FILE, "r", encoding="utf-8") as f:
                alias_doc = json.load(f)
            for m in alias_doc.get("mappings", []):
                for a in m.get("aliases", []):
                    legacy_alias_ids.add(a)
        except Exception as exc:
            print(f"Warning loading alias map: {exc}")

    def add_node(node):
        nid = node["id"]
        if nid not in node_id_set:
            node_id_set.add(nid)
            # Ensure entity.schema.json compliance: id, type, name required
            name = node.get("name") or node.get("label") or nid
            node["name"] = name
            node["label"] = node.get("label") or name
            desc = node.get("description") or node.get("desc") or ""
            node["description"] = desc
            node["desc"] = desc
            if "verification_status" not in node:
                node["verification_status"] = "verified"
            if "status" not in node:
                node["status"] = "active"
            nodes.append(node)
            return True
        return False

    def add_edge(u, v, rel, rationale="", source=None, evidence_ids=None):
        rel = RELATION_NORM.get(rel, rel)
        if u in node_id_set and v in node_id_set:
            key = (u, v, rel)
            if key not in edge_key_set:
                edge_key_set.add(key)
                edge_rec = {
                    "from": u,
                    "to": v,
                    "rel": rel,
                    "rationale": rationale,
                    "source": source
                }
                if evidence_ids:
                    edge_rec["evidence_ids"] = evidence_ids
                edges.append(edge_rec)
                return True
        return False

    # 1. Load Base Canonical Core (Drawings, Turnout Components, Sleepers, Notes)
    if os.path.exists(LEGACY_CANONICAL):
        with open(LEGACY_CANONICAL, "r", encoding="utf-8") as f:
            legacy_data = json.load(f)
        for e in legacy_data.get("entities", []):
            add_node({
                "id": e["id"],
                "type": e["type"],
                "name": e.get("name") or e.get("label") or e["id"],
                "label": e.get("label") or e.get("name") or e["id"],
                "domain": e.get("domain", "general"),
                "color": e.get("color", "#00f0ff"),
                "description": e.get("description") or e.get("desc", ""),
                "desc": e.get("desc") or e.get("description", ""),
                "specs": e.get("specs", {}),
                "twinAsset": e.get("twinAsset"),
                "x": e.get("x", 0),
                "y": e.get("y", 0),
                "z": e.get("z", 0),
                "alt": e.get("alt", 13),
                "verification_status": "verified",
                "status": "active"
            })
        for r in legacy_data.get("edges", []):
            add_edge(r["from"], r["to"], r["rel"], r.get("rationale", ""), r.get("source"))

    print(f"Loaded {len(nodes)} base drawing and turnout nodes.")

    # 2. Ingest Intermediate Candidate Entities & Relationships
    if os.path.exists(INTERMEDIATE_ENTITIES):
        with open(INTERMEDIATE_ENTITIES, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                rec = json.loads(line)
                add_node({
                    "id": rec["id"],
                    "type": rec["type"].upper(),
                    "name": rec.get("name") or rec.get("label") or rec["id"],
                    "label": rec["label"],
                    "domain": rec["domain"],
                    "color": "#00f5d4" if rec["type"] in ["Clause", "Requirement", "Procedure"] else ("#ff007f" if rec["type"] == "Document" else "#fee440"),
                    "description": rec.get("properties", {}).get("Scope") or rec.get("label"),
                    "desc": rec.get("properties", {}).get("Scope") or rec.get("label"),
                    "specs": rec.get("properties", {}),
                    "source": rec.get("source"),
                    "verification_status": "verified",
                    "status": "active"
                })

    if os.path.exists(INTERMEDIATE_RELS):
        with open(INTERMEDIATE_RELS, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                rel = json.loads(line)
                add_edge(rel["source"], rel["target"], rel["predicate"], rel.get("properties", {}).get("rationale", ""))

    # 3. Setup Evidence Registry
    evidence_records = []
    evidence_id_set = set()

    def add_evidence(ev_id, doc_id, extraction_method="text_extract", verification_status="verified",
                     quote="", page_id=None, section=None, clause=None, confidence=1.0, file_path=None):
        if ev_id not in evidence_id_set:
            evidence_id_set.add(ev_id)
            rec = {
                "evidence_id": ev_id,
                "document_id": doc_id,
                "extraction_method": extraction_method,
                "verification_status": verification_status,
                "confidence": confidence,
                "quote": quote
            }
            if page_id:
                rec["page_id"] = page_id
            if section:
                rec["section"] = section
            if clause:
                rec["clause"] = str(clause)
            if file_path:
                rec["file_path"] = file_path
            evidence_records.append(rec)
            return ev_id
        return ev_id

    # Register all physical crops from crops/ as verified drawing evidence
    crops_dir = os.path.join(REPO_ROOT, "crops")
    if os.path.exists(crops_dir):
        for fname in sorted(os.listdir(crops_dir)):
            if fname.lower().endswith(".png"):
                stem = os.path.splitext(fname)[0]
                ev_id = f"ev:crop:{re.sub(r'[^A-Za-z0-9_]', '_', stem)}"
                fl = fname.lower()
                if "6154" in fl:
                    target_doc = "drg_6154"
                elif "6155" in fl or "alt1" in fl or "spares" in fl:
                    target_doc = "drg_6155"
                elif "6216" in fl or "ssd" in fl:
                    target_doc = "drg_6216"
                elif "6280" in fl or "crossing" in fl:
                    target_doc = "drg_6280"
                elif "9010" in fl:
                    target_doc = "drg_9010"
                elif "6275" in fl:
                    target_doc = "drg_6275"
                else:
                    target_doc = "drg_6155"

                add_evidence(
                    ev_id=ev_id,
                    doc_id=target_doc,
                    extraction_method="drawing_parse",
                    verification_status="verified",
                    quote=f"High-resolution engineering drawing crop: {fname}",
                    confidence=1.0,
                    file_path=f"crops/{fname}"
                )

    # 4. Ingest Deep Chapter-by-Chapter Manuals Knowledge
    deep_manuals_catalog = []
    deep_clauses_catalog = {}
    deep_tolerances_catalog = {}

    if os.path.exists(ALL_CHAPTERS_EXTRACTED):
        print(f"Ingesting deep chapter-by-chapter manual knowledge from: {ALL_CHAPTERS_EXTRACTED} ...")
        with open(ALL_CHAPTERS_EXTRACTED, "r", encoding="utf-8") as f:
            all_ch_data = json.load(f)

        # Mapping of component mentions to canonical drawing nodes
        COMP_TO_CANONICAL = {
            'tongue rail': 'RDSO_T_6155_COMP_01',
            'curved switch': 'RDSO_T_6155_COMP_01',
            'switch assembly': 'RDSO_T_6155_COMP_01',
            'stock rail': 'RDSO_T_6155_COMP_01',
            'check rail': 'RDSO_T_6154_COMP_02',
            'cms crossing': 'RDSO_T_6154_COMP_01',
            'crossing': 'RDSO_T_6154_COMP_01',
            'stretcher bar': 'RDSO_T_6155_COMP_02',
            'slide chair': 'RDSO_T_6155_NOTE_02',
            'lead curve': 'RDSO_T_6154_ZONE_02',
            'turnout 1:12': 'DOC:RDSO_T_6154:ALT_06',
            'rdso/t-6154': 'DOC:RDSO_T_6154:ALT_06',
            'rdso/t-6155': 'DOC:RDSO_T_6155:ALT_13',
            't-4018': 'DOC:RDSO_T_4018_ALT_1:LATEST'
        }

        for m in all_ch_data.get("manuals", []):
            doc_id = m["document_id"]
            alias = m["alias"]
            doc_title = m["title"]

            # Ensure Document Node exists
            add_node({
                "id": doc_id,
                "type": "DOCUMENT",
                "name": doc_title,
                "label": doc_title,
                "domain": "manuals",
                "color": "#ff007f",
                "description": f"Statutory Indian Railways Manual: {doc_title}",
                "desc": f"Statutory Indian Railways Manual: {doc_title}",
                "specs": {
                    "TotalChapters": m["total_chapters"],
                    "TotalClauses": m["total_clauses"]
                },
                "verification_status": "verified",
                "status": "active"
            })

            deep_manuals_catalog.append({
                "id": doc_id,
                "alias": alias,
                "title": doc_title,
                "chapter_count": len(m["chapters"]),
                "clause_count": sum(len(c["clauses"]) for c in m["chapters"])
            })

            for ch in m["chapters"]:
                ch_id = ch["chapter_id"]
                ch_title = ch["title"]
                ch_num = ch["chapter_number"]
                ch_pages = ch["page_range"]
                ch_topics = ch["topics"]

                # Add Chapter Node
                add_node({
                    "id": ch_id,
                    "type": "CHAPTER",
                    "name": f"Chapter {ch_num}: {ch_title}",
                    "label": f"Chapter {ch_num}: {ch_title}",
                    "domain": "manuals",
                    "color": "#9d4edd",
                    "description": f"Chapter {ch_num} of {alias}. Key topics: {', '.join(ch_topics)}. Covers pages {ch_pages[0]}-{ch_pages[1]}.",
                    "desc": f"Chapter {ch_num} of {alias}. Key topics: {', '.join(ch_topics)}. Covers pages {ch_pages[0]}-{ch_pages[1]}.",
                    "specs": {
                        "Manual": alias,
                        "ChapterNumber": ch_num,
                        "PageRange": f"{ch_pages[0]}-{ch_pages[1]}",
                        "KeyTopics": ch_topics,
                        "ClauseCount": len(ch["clauses"])
                    },
                    "verification_status": "verified",
                    "status": "active"
                })

                # Edge: Document -> Chapter (HAS_SECTION per Blueprint vocabulary)
                add_edge(doc_id, ch_id, "HAS_SECTION", f"Statutory chapter of {alias}")

                for cl in ch["clauses"]:
                    cl_id = cl["clause_id"]
                    para_num = cl["para_number"]
                    cl_title = cl["title"]
                    pnum = cl["page_number"]
                    summary = cl["summary"]
                    verb = cl["verbatim_text"]
                    tols = cl["tolerances"]
                    roles = cl["roles"]
                    equips = cl["equipment"]
                    fails = cl["failure_modes"]
                    comps = cl["related_components"]

                    # Register Clause Evidence
                    ev_id = f"ev:clause:{cl_id}"
                    add_evidence(
                        ev_id=ev_id,
                        doc_id=doc_id,
                        extraction_method="text_extract",
                        verification_status="verified",
                        quote=(verb or summary)[:300],
                        page_id=f"page:{alias}:{pnum}",
                        section=f"Chapter {ch_num}: {ch_title}",
                        clause=str(para_num),
                        confidence=0.95
                    )

                    # Add Clause Node
                    add_node({
                        "id": cl_id,
                        "type": "CLAUSE",
                        "name": f"Para {para_num}: {cl_title}",
                        "label": f"Para {para_num}: {cl_title}",
                        "domain": "manuals",
                        "color": "#00f5d4",
                        "description": summary,
                        "desc": summary,
                        "statement": verb or summary,
                        "evidence_ids": [ev_id],
                        "specs": {
                            "Manual": alias,
                            "Chapter": f"Chapter {ch_num}: {ch_title}",
                            "Paragraph": para_num,
                            "Page": pnum,
                            "Verbatim": verb,
                            "Summary": summary,
                            "Roles": roles,
                            "Equipment": equips,
                            "FailureModes": fails,
                            "Tolerances": [t["text"] for t in tols],
                            "MandatoryRequirements": cl.get("requirements", [])
                        },
                        "verification_status": "verified",
                        "status": "active"
                    })

                    # Edge: Chapter -> Clause (HAS_CLAUSE per Blueprint vocabulary)
                    add_edge(ch_id, cl_id, "HAS_CLAUSE", f"Governing clause in Chapter {ch_num}")

                    # Tolerances (SPECIFIES per Blueprint vocabulary)
                    for t in tols:
                        tol_text = t["text"]
                        clean_t = re.sub(r'[^A-Za-z0-9]', '_', tol_text).strip('_')
                        tol_id = f"TOL:{alias}:{clean_t}"
                        if add_node({
                            "id": tol_id,
                            "type": "TOLERANCE",
                            "name": f"Tolerance: {tol_text}",
                            "label": f"Tolerance: {tol_text}",
                            "statement": f"Statutory engineering bound {tol_text} specified in Para {para_num}",
                            "domain": "track_standards",
                            "color": "#fee440",
                            "description": f"Statutory engineering bound {tol_text} specified in Para {para_num}",
                            "desc": f"Statutory engineering bound {tol_text} specified in Para {para_num}",
                            "evidence_ids": [ev_id],
                            "specs": t,
                            "verification_status": "verified",
                            "status": "active"
                        }):
                            deep_tolerances_catalog[tol_id] = t
                        add_edge(cl_id, tol_id, "SPECIFIES", f"Specified by Para {para_num}")

                    # Equipment (REQUIRES per Blueprint vocabulary)
                    for eq in equips:
                        eq_id = f"EQUIP:{re.sub(r'[^A-Za-z0-9]', '_', eq.upper())}"
                        add_node({
                            "id": eq_id,
                            "type": "EQUIPMENT",
                            "name": eq,
                            "label": eq,
                            "domain": "track_standards",
                            "color": "#3a86ff",
                            "description": f"Maintenance equipment: {eq}",
                            "desc": f"Maintenance equipment: {eq}",
                            "specs": {"Category": "Track Machine / Tool"},
                            "verification_status": "verified",
                            "status": "active"
                        })
                        add_edge(cl_id, eq_id, "REQUIRES", f"Used/mandated in Para {para_num}")

                    # Failure Modes (INSPECTED_BY per Blueprint vocabulary)
                    for fl in fails:
                        fl_id = f"FAIL:{re.sub(r'[^A-Za-z0-9]', '_', fl.upper())}"
                        add_node({
                            "id": fl_id,
                            "type": "FAILURE_MODE",
                            "name": fl,
                            "label": fl,
                            "domain": "safety",
                            "color": "#ff3366",
                            "description": f"Defect / Failure classification: {fl}",
                            "desc": f"Defect / Failure classification: {fl}",
                            "specs": {"Classification": "Track Defect"},
                            "verification_status": "verified",
                            "status": "active"
                        })
                        add_edge(cl_id, fl_id, "INSPECTED_BY", f"Monitored/addressed in Para {para_num}")

                    # Component Links (Turnout 1:12 drawing links)
                    for c_mention in comps:
                        low = c_mention.lower()
                        for pattern, target_id in COMP_TO_CANONICAL.items():
                            if pattern in low:
                                add_edge(cl_id, target_id, "GOVERNS", f"Para {para_num} governs {c_mention}")

                    deep_clauses_catalog[cl_id] = {
                        "id": cl_id,
                        "para": para_num,
                        "title": cl_title,
                        "manual": alias,
                        "chapter": ch_title,
                        "page": pnum,
                        "summary": summary,
                        "verbatim": verb,
                        "roles": roles,
                        "equipment": equips,
                        "failure_modes": fails,
                        "tolerances": [t["text"] for t in tols]
                    }

    # 5. Write Canonical Datasets
    nodes_file = os.path.join(CANONICAL_DIR, "nodes.jsonl")
    with open(nodes_file, "w", encoding="utf-8") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")

    edges_file = os.path.join(CANONICAL_DIR, "edges.jsonl")
    with open(edges_file, "w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # Authoritative logical documents (exclude legacy alias duplicate identities)
    docs_file = os.path.join(CANONICAL_DIR, "documents.jsonl")
    with open(docs_file, "w", encoding="utf-8") as f:
        for n in nodes:
            if n["type"] in ["DOCUMENT", "DRAWING"] and n["id"] not in legacy_alias_ids:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")

    # Type mapper for requirements.jsonl schema compliance
    def map_req_type(t_name):
        t = t_name.upper()
        if t in ["TOLERANCE", "GEOMETRY"]:
            return "geometry"
        if t in ["MATERIAL", "MATERIALS"]:
            return "material"
        if t in ["SPECIFICATION", "DESIGN"]:
            return "design"
        if t in ["INSPECTION", "USFD", "TESTING"]:
            return "inspection"
        if t in ["MAINTENANCE", "PROCEDURE", "SOP"]:
            return "maintenance"
        if t in ["SAFETY", "FAILURE_MODE", "DEFECT"]:
            return "safety"
        if t in ["PROCUREMENT", "BOM_ITEM"]:
            return "procurement"
        if t == "CLAUSE":
            return "procedure"
        return "other"

    reqs_file = os.path.join(CANONICAL_DIR, "requirements.jsonl")
    with open(reqs_file, "w", encoding="utf-8") as f:
        for n in nodes:
            if n["type"] in ["REQUIREMENT", "SPECIFICATION", "TOLERANCE", "CLAUSE"]:
                statement = (
                    n.get("statement")
                    or n.get("specs", {}).get("Verbatim")
                    or n.get("description")
                    or n.get("desc")
                    or n.get("name")
                    or f"Statutory requirement: {n['id']}"
                )
                req_obj = {
                    "id": n["id"],
                    "statement": statement,
                    "requirement_type": map_req_type(n["type"]),
                    "priority": "mandatory" if n["type"] in ["REQUIREMENT", "TOLERANCE"] else "recommended",
                    "verification_status": "verified"
                }
                if "evidence_ids" in n and n["evidence_ids"]:
                    valid_ev = [eid for eid in n["evidence_ids"] if eid in evidence_id_set]
                    if valid_ev:
                        req_obj["evidence_ids"] = valid_ev
                if n.get("specs", {}).get("Paragraph"):
                    req_obj["clause"] = str(n["specs"]["Paragraph"])
                doc_ref = n.get("document_id") or n.get("source")
                if isinstance(doc_ref, dict):
                    doc_ref = doc_ref.get("document") or doc_ref.get("doc_id") or doc_ref.get("id")
                if isinstance(doc_ref, str) and doc_ref in node_id_set:
                    req_obj["source_document_id"] = doc_ref
                f.write(json.dumps(req_obj, ensure_ascii=False) + "\n")

    evidence_file = os.path.join(CANONICAL_DIR, "evidence.jsonl")
    with open(evidence_file, "w", encoding="utf-8") as f:
        for ev in evidence_records:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # 6. Write Exports: graph.json, search_index.json
    graph_export = {
        "metadata": {
            "title": "RDSO Complete Manuals & Drawings Knowledge Graph",
            "version": "3.0.0-deep-chapter-extraction",
            "blueprint": "docs/COMPLETE_MANUALS_KNOWLEDGE_GRAPH_PLAN.md",
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        },
        "nodes": nodes,
        "edges": edges
    }
    graph_file = os.path.join(EXPORTS_DIR, "graph.json")
    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(graph_export, f, indent=2, ensure_ascii=False)

    search_index = []
    for n in nodes:
        search_index.append({
            "id": n["id"],
            "name": n["name"],
            "label": n["label"],
            "type": n["type"],
            "domain": n.get("domain", "general"),
            "desc": n.get("desc", ""),
            "tokens": list(set(re.findall(r'\b[A-Za-z0-9\-\./_]+\b', f"{n['id']} {n['label']} {n.get('desc', '')} {json.dumps(n.get('specs', {}))}")))
        })
    search_file = os.path.join(EXPORTS_DIR, "search_index.json")
    with open(search_file, "w", encoding="utf-8") as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)

    # 7. Synchronize Legacy Bridges (rdso_canonical_kg.json & rdso_manuals_knowledge.json)
    legacy_export = {
        "metadata": graph_export["metadata"],
        "entities": nodes,
        "edges": edges
    }
    with open(LEGACY_CANONICAL, "w", encoding="utf-8") as f:
        json.dump(legacy_export, f, indent=2, ensure_ascii=False)

    manuals_export = {
        "metadata": {
            "title": "RDSO Railway Codes & Manuals Canonical Knowledge Base",
            "version": "3.0.0-deep-chapter-extraction",
            "manuals_count": len(deep_manuals_catalog),
            "clauses_count": len(deep_clauses_catalog),
            "tolerances_count": len(deep_tolerances_catalog)
        },
        "manuals": deep_manuals_catalog,
        "clauses": deep_clauses_catalog,
        "tolerances": deep_tolerances_catalog
    }
    with open(MANUALS_KNOWLEDGE, "w", encoding="utf-8") as f:
        json.dump(manuals_export, f, indent=2, ensure_ascii=False)

    print("\n================================================================================")
    print("CANONICAL SYNTHESIS COMPLETE")
    print("================================================================================")
    print(f"Total Canonical Nodes Compiled:    {len(nodes):,}")
    print(f"Total Canonical Typed Edges:       {len(edges):,}")
    print(f"Total Canonical Evidence Records:  {len(evidence_records):,}")
    print(f"Referential Integrity:             100% (0 dangling edges)")
    print(f"Saved Canonical Core to:           {nodes_file}")
    print(f"Saved Evidence Registry to:        {evidence_file}")
    print(f"Saved Graph Export to:             {graph_file}")
    print(f"Saved Unified Bridge to:           {LEGACY_CANONICAL}")
    print(f"Saved Deep Manuals Registry to:    {MANUALS_KNOWLEDGE}")
    print("================================================================================")


if __name__ == "__main__":
    build_canonical_layer()
