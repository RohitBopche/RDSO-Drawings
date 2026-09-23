"""
export_kg_bundle.py
Generates data/rdso_kg_data.js to decouple massive JSON datasets from index.html.
Ensures 100% offline compatibility across file:/// and HTTP protocols.
"""

import json
import os


def main():
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(REPO_ROOT, "data")
    ext_path = os.path.join(data_dir, "rdso_extracted_knowledge.json")
    can_path = os.path.join(data_dir, "rdso_canonical_kg.json")
    man_path = os.path.join(data_dir, "rdso_manuals_knowledge.json")
    all_ch_path = os.path.join(data_dir, "knowledge-graph", "intermediate", "all_chapters_extracted.json")

    print("[*] Reading source JSON datasets...")
    with open(ext_path, "r", encoding="utf-8") as f:
        ext_data = json.load(f)

    with open(can_path, "r", encoding="utf-8") as f:
        can_data = json.load(f)

    # The canonical KG is the authoritative source and may contain a large Manuals
    # universe. The browser bootstrap must remain lightweight: manuals are built from
    # manual_structure.js + manual_content_index.js and are intentionally isolated.
    drawing_entities = [
        e for e in can_data.get("entities", [])
        if e.get("domain") != "manual" and e.get("universe") != "manuals"
    ]
    drawing_ids = {e.get("id") for e in drawing_entities}
    drawing_edges = [
        e for e in can_data.get("edges", [])
        if e.get("from") in drawing_ids and e.get("to") in drawing_ids
    ]
    drawing_facts = [
        fact for fact in can_data.get("facts", [])
        if fact.get("subject_id") in drawing_ids and fact.get("object_id") in drawing_ids
    ]
    drawing_data = {
        "metadata": {
            **can_data.get("metadata", {}),
            "universe": "drawings",
            "total_entities": len(drawing_entities),
            "total_edges": len(drawing_edges),
            "total_facts": len(drawing_facts),
        },
        "entities": drawing_entities,
        "edges": drawing_edges,
        "facts": drawing_facts,
    }

    man_data = {}
    if os.path.exists(man_path):
        with open(man_path, "r", encoding="utf-8") as f:
            man_data = json.load(f)

    compacted_tree = []
    if os.path.exists(all_ch_path):
        with open(all_ch_path, "r", encoding="utf-8") as f:
            all_ch = json.load(f)
        for m in all_ch.get("manuals", []):
            compacted_tree.append({
                "doc_id": m["document_id"],
                "alias": m["alias"],
                "title": m["title"],
                "total_chapters": m["total_chapters"],
                "total_clauses": m["total_clauses"],
                "chapters": [{
                    "id": ch["chapter_id"],
                    "num": ch["chapter_number"],
                    "title": ch["title"],
                    "pages": ch["page_range"],
                    "topics": ch["topics"],
                    "clauses": [{"id": cl["clause_id"], "para": cl["para_number"], "title": cl["title"], "page": cl["page_number"]} for cl in ch["clauses"]]
                } for ch in m["chapters"]]
            })

    output_js_path = os.path.join(data_dir, "rdso_kg_data.js")
    print(f"[*] Writing bundle to {output_js_path}...")

    with open(output_js_path, "w", encoding="utf-8") as f:
        f.write("// =========================================================================\n")
        f.write("// RDSO Track Infrastructure Knowledge Core - Decoupled Offline Data Bundle\n")
        f.write("// =========================================================================\n\n")
        f.write("const _root = (typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));\n\n")
        f.write("_root.RDSO_EXTRACTED_KNOWLEDGE = ")
        json.dump(ext_data, f, separators=(',', ':'))
        f.write(";\n\n_root.RDSO_CANONICAL_KG = ")
        json.dump(can_data, f, separators=(',', ':'))
        f.write(";\n\n_root.RDSO_MANUALS_KNOWLEDGE = ")
        json.dump(man_data, f, separators=(',', ':'))
        f.write(";\n\n_root.RDSO_COMPACTED_TREE = ")
        json.dump(compacted_tree, f, separators=(',', ':'))
        f.write(";\n")

    file_size = os.path.getsize(output_js_path)
    print(f"[+] Successfully exported data/rdso_kg_data.js ({file_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
