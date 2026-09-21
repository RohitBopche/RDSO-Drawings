"""Validate the Manuals Knowledge Graph structural contract.

The validator intentionally treats the manual hierarchy as authoritative:
Manual -> Chapter. Semantic clauses/topics are secondary and may not replace
chapter nodes. The Drawing KG is a separate universe.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERMEDIATE = os.path.join(ROOT, "data", "knowledge-graph", "intermediate", "all_chapters_extracted.json")
CANONICAL = os.path.join(ROOT, "data", "rdso_canonical_kg.json")

EXPECTED_MANUALS = {
    "DOC:IRPWM:2024:ACS14",
    "DOC:USFD:2026:ACS4",
    "DOC:AT_WELD:2022",
    "DOC:FBW:2022:CS5",
    "DOC:TMM:2020:ACS10",
    "DOC:STMM:2024",
}


def fail(msg):
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


def main():
    if not os.path.exists(INTERMEDIATE):
        fail(f"Missing authoritative manual structure: {INTERMEDIATE}")
    if not os.path.exists(CANONICAL):
        fail(f"Missing canonical KG: {CANONICAL}")

    with open(INTERMEDIATE, "r", encoding="utf-8") as f:
        structured = json.load(f)
    with open(CANONICAL, "r", encoding="utf-8") as f:
        canonical = json.load(f)

    manuals = structured.get("manuals", [])
    actual_manuals = {m.get("document_id") for m in manuals}
    if actual_manuals != EXPECTED_MANUALS:
        fail(f"Manual registry mismatch: expected {sorted(EXPECTED_MANUALS)}, got {sorted(actual_manuals)}")

    entities = {e.get("id"): e for e in canonical.get("entities", [])}
    edges = canonical.get("edges", [])

    # 1. Every manual has an explicit root and every registered chapter has an
    #    explicit CHAPTER node.
    expected_chapters = set()
    for manual in manuals:
        mid = manual["document_id"]
        if mid not in entities:
            fail(f"Missing manual root node: {mid}")
        if entities[mid].get("domain") != "manual":
            fail(f"Manual root is not in manual domain: {mid}")

        chapters = manual.get("chapters", [])
        if manual.get("total_chapters") != len(chapters):
            fail(f"{mid}: total_chapters does not match chapter list")

        orders = []
        for ch in chapters:
            cid = ch.get("chapter_id")
            expected_chapters.add(cid)
            if cid not in entities:
                fail(f"{mid}: missing chapter node {cid}")
            node = entities[cid]
            if node.get("type") != "CHAPTER" or node.get("domain") != "manual":
                fail(f"{cid}: chapter node has wrong type/domain")
            orders.append(ch.get("order", ch.get("chapter_number")))
        if orders != sorted(orders) or len(set(orders)) != len(orders):
            fail(f"{mid}: chapter ordering is not deterministic")

    # 2. Exactly one parent edge per chapter, and it must be the owning manual.
    parent_edges = [e for e in edges if e.get("rel") == "CONTAINS_CHAPTER"]
    parent_map = {}
    for e in parent_edges:
        child = e.get("to")
        parent_map.setdefault(child, []).append(e.get("from"))

    for manual in manuals:
        mid = manual["document_id"]
        for ch in manual.get("chapters", []):
            cid = ch["chapter_id"]
            parents = parent_map.get(cid, [])
            if parents != [mid]:
                fail(f"{cid}: expected exactly one parent {mid}, got {parents}")

    # 3. Isolation: any edge touching a manual-domain node must remain inside
    #    the manual domain. Drawing nodes may reference each other freely.
    for e in edges:
        a = entities.get(e.get("from"))
        b = entities.get(e.get("to"))
        if not a or not b:
            fail(f"Dangling edge: {e}")
        if (a.get("domain") == "manual") != (b.get("domain") == "manual"):
            fail(f"Cross-universe edge detected: {e.get('from')} -> {e.get('to')}")

    # 4. No legacy manual IDs should masquerade as graph roots.
    legacy = {"doc_irpwm_2024", "doc_usfd_2026", "doc_atweld_2022", "doc_fbw_2022", "doc_tmm_2020", "doc_stmm_2024"}
    legacy_manual_nodes = [eid for eid in legacy if eid in entities]
    if legacy_manual_nodes:
        print(f"[WARN] Legacy manual IDs remain in canonical data: {legacy_manual_nodes}")
        # They are acceptable only if they are not connected to drawing nodes.
        for eid in legacy_manual_nodes:
            if entities[eid].get("domain") != "manual":
                fail(f"Legacy manual ID has non-manual domain: {eid}")

    print("[PASS] Manuals KG structural contract is valid.")
    print(f"       Manuals: {len(manuals)}")
    print(f"       Chapters: {len(expected_chapters)}")
    print(f"       Manual roots with explicit chapter edges: {len(parent_map)}")
    print("       Manual/Drawing graph isolation: PASS")


if __name__ == "__main__":
    main()
