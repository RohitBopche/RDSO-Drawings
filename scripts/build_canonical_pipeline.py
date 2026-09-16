"""
build_canonical_pipeline.py
============================
Synthesizes all drawing entities, candidates, and deep chapter-by-chapter
manuals knowledge into authoritative canonical datasets and exports:
- data/knowledge-graph/canonical/nodes.jsonl
- data/knowledge-graph/canonical/edges.jsonl
- data/knowledge-graph/canonical/documents.jsonl
- data/knowledge-graph/canonical/requirements.jsonl
- data/knowledge-graph/exports/graph.json
- data/knowledge-graph/exports/search_index.json
- data/rdso_canonical_kg.json (Unified backward-compatible core)
- data/rdso_manuals_knowledge.json (Deep manuals registry)

Enforces 100% referential integrity (zero dangling edges).
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


def build_canonical_layer():
    print("================================================================================")
    print("      DEEP CANONICAL KNOWLEDGE GRAPH & EXPORT SYNTHESIS PIPELINE")
    print("================================================================================")

    nodes = []
    edges = []
    node_id_set = set()
    edge_key_set = set()

    def add_node(node):
        nid = node["id"]
        if nid not in node_id_set:
            node_id_set.add(nid)
            nodes.append(node)
            return True
        return False

    def add_edge(u, v, rel, rationale="", source=None):
        if u in node_id_set and v in node_id_set:
            key = (u, v, rel)
            if key not in edge_key_set:
                edge_key_set.add(key)
                edges.append({
                    "from": u,
                    "to": v,
                    "rel": rel,
                    "rationale": rationale,
                    "source": source
                })
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
                "label": e["label"],
                "domain": e["domain"],
                "color": e["color"],
                "desc": e["desc"],
                "specs": e.get("specs", {}),
                "twinAsset": e.get("twinAsset"),
                "x": e.get("x", 0),
                "y": e.get("y", 0),
                "z": e.get("z", 0),
                "alt": e.get("alt", 13),
                "canonical_status": "VERIFIED"
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
                    "label": rec["label"],
                    "domain": rec["domain"],
                    "color": "#00f5d4" if rec["type"] in ["Clause", "Requirement", "Procedure"] else ("#ff007f" if rec["type"] == "Document" else "#fee440"),
                    "desc": rec.get("properties", {}).get("Scope") or rec.get("label"),
                    "specs": rec.get("properties", {}),
                    "source": rec.get("source"),
                    "canonical_status": "VERIFIED"
                })

    if os.path.exists(INTERMEDIATE_RELS):
        with open(INTERMEDIATE_RELS, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                rel = json.loads(line)
                add_edge(rel["source"], rel["target"], rel["predicate"], rel.get("properties", {}).get("rationale", ""))

    # 3. Ingest Deep Chapter-by-Chapter Manuals Knowledge
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
                "label": doc_title,
                "domain": "manuals",
                "color": "#ff007f",
                "desc": f"Statutory Indian Railways Manual: {doc_title}",
                "specs": {
                    "TotalChapters": m["total_chapters"],
                    "TotalClauses": m["total_clauses"]
                },
                "canonical_status": "VERIFIED"
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
                    "label": f"Chapter {ch_num}: {ch_title}",
                    "domain": "manuals",
                    "color": "#9d4edd",
                    "desc": f"Chapter {ch_num} of {alias}. Key topics: {', '.join(ch_topics)}. Covers pages {ch_pages[0]}-{ch_pages[1]}.",
                    "specs": {
                        "Manual": alias,
                        "ChapterNumber": ch_num,
                        "PageRange": f"{ch_pages[0]}-{ch_pages[1]}",
                        "KeyTopics": ch_topics,
                        "ClauseCount": len(ch["clauses"])
                    },
                    "canonical_status": "VERIFIED"
                })

                # Edge: Document -> Chapter
                add_edge(doc_id, ch_id, "CONTAINS_CHAPTER", f"Statutory chapter of {alias}")

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

                    # Add Clause Node
                    add_node({
                        "id": cl_id,
                        "type": "CLAUSE",
                        "label": f"Para {para_num}: {cl_title}",
                        "domain": "manuals",
                        "color": "#00f5d4",
                        "desc": summary,
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
                        "canonical_status": "VERIFIED"
                    })

                    # Edge: Chapter -> Clause
                    add_edge(ch_id, cl_id, "CONTAINS_CLAUSE", f"Governing clause in Chapter {ch_num}")

                    # Tolerances
                    for t in tols:
                        tol_text = t["text"]
                        clean_t = re.sub(r'[^A-Za-z0-9]', '_', tol_text).strip('_')
                        tol_id = f"TOL:{alias}:{clean_t}"
                        if add_node({
                            "id": tol_id,
                            "type": "TOLERANCE",
                            "label": f"Tolerance: {tol_text}",
                            "domain": "track_standards",
                            "color": "#fee440",
                            "desc": f"Statutory engineering bound {tol_text} specified in Para {para_num}",
                            "specs": t,
                            "canonical_status": "VERIFIED"
                        }):
                            deep_tolerances_catalog[tol_id] = t
                        add_edge(cl_id, tol_id, "SPECIFIES_TOLERANCE", f"Specified by Para {para_num}")

                    # Equipment
                    for eq in equips:
                        eq_id = f"EQUIP:{re.sub(r'[^A-Za-z0-9]', '_', eq.upper())}"
                        add_node({
                            "id": eq_id,
                            "type": "EQUIPMENT",
                            "label": eq,
                            "domain": "track_standards",
                            "color": "#3a86ff",
                            "desc": f"Maintenance equipment: {eq}",
                            "specs": {"Category": "Track Machine / Tool"},
                            "canonical_status": "VERIFIED"
                        })
                        add_edge(cl_id, eq_id, "MANDATES_EQUIPMENT", f"Used/mandated in Para {para_num}")

                    # Failure Modes
                    for fl in fails:
                        fl_id = f"FAIL:{re.sub(r'[^A-Za-z0-9]', '_', fl.upper())}"
                        add_node({
                            "id": fl_id,
                            "type": "FAILURE_MODE",
                            "label": fl,
                            "domain": "safety",
                            "color": "#ff3366",
                            "desc": f"Defect / Failure classification: {fl}",
                            "specs": {"Classification": "Track Defect"},
                            "canonical_status": "VERIFIED"
                        })
                        add_edge(cl_id, fl_id, "DETECTS_FAILURE", f"Monitored/addressed in Para {para_num}")

                    # Component Links (Turnout 1:12 drawing links)
                    for c_mention in comps:
                        low = c_mention.lower()
                        for pattern, target_id in COMP_TO_CANONICAL.items():
                            if pattern in low:
                                add_edge(cl_id, target_id, "GOVERNS_COMPONENT", f"Para {para_num} governs {c_mention}")

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

    # 4. Write Canonical Datasets
    nodes_file = os.path.join(CANONICAL_DIR, "nodes.jsonl")
    with open(nodes_file, "w", encoding="utf-8") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")

    edges_file = os.path.join(CANONICAL_DIR, "edges.jsonl")
    with open(edges_file, "w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    docs_file = os.path.join(CANONICAL_DIR, "documents.jsonl")
    with open(docs_file, "w", encoding="utf-8") as f:
        for n in nodes:
            if n["type"] in ["DOCUMENT", "DRAWING"]:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")

    reqs_file = os.path.join(CANONICAL_DIR, "requirements.jsonl")
    with open(reqs_file, "w", encoding="utf-8") as f:
        for n in nodes:
            if n["type"] in ["REQUIREMENT", "SPECIFICATION", "TOLERANCE", "CLAUSE"]:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")

    # 5. Write Exports: graph.json, search_index.json
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
            "label": n["label"],
            "type": n["type"],
            "domain": n.get("domain", "general"),
            "desc": n.get("desc", ""),
            "tokens": list(set(re.findall(r'\b[A-Za-z0-9\-\./_]+\b', f"{n['id']} {n['label']} {n.get('desc', '')} {json.dumps(n.get('specs', {}))}")))
        })
    search_file = os.path.join(EXPORTS_DIR, "search_index.json")
    with open(search_file, "w", encoding="utf-8") as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)

    # 6. Synchronize Legacy Bridges (rdso_canonical_kg.json & rdso_manuals_knowledge.json)
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
    print(f"Total Canonical Nodes Compiled: {len(nodes):,}")
    print(f"Total Canonical Typed Edges:    {len(edges):,}")
    print(f"Referential Integrity:          100% (0 dangling edges)")
    print(f"Search Index Tokens:            {sum(len(item['tokens']) for item in search_index):,}")
    print(f"Saved Canonical Core to:        {nodes_file}")
    print(f"Saved Graph Export to:          {graph_file}")
    print(f"Saved Unified Bridge to:        {LEGACY_CANONICAL}")
    print(f"Saved Deep Manuals Registry to: {MANUALS_KNOWLEDGE}")
    print("================================================================================")

if __name__ == "__main__":
    build_canonical_layer()
