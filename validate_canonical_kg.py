"""
validate_canonical_kg.py
Validates the Canonical Knowledge Core against schema constraints, controlled vocabularies,
and referential integrity specified in docs/RDSO_Knowledge_Graph_Improvement_Blueprint.md.
"""

import json
import sys

# Controlled Entity Vocabularies from Blueprint Section 5
CONTROLLED_ENTITY_TYPES = {
    "DOCUMENT", "DRAWING", "REVISION", "COMPONENT", "SUBASSEMBLY", "ASSEMBLY",
    "RAIL", "TONGUE_RAIL", "STOCK_RAIL", "SLEEPER", "FASTENER", "TIE_BAR",
    "SLIDE_CHAIR", "POINT_MACHINE", "LOCKING_DEVICE", "DIMENSION", "TOLERANCE",
    "MATERIAL", "STANDARD", "SPECIFICATION", "NOTE", "BOM_ITEM", "SPARE_PART",
    "INTERFACE", "CONSTRAINT", "FAILURE_MODE", "HAZARD", "INSPECTION",
    "MAINTENANCE_ACTION", "SOP", "FIELD_OBSERVATION", "LOCATION", "EQUIPMENT", "ZONE"
}

# Controlled Relationship Vocabularies from Blueprint Section 6
CONTROLLED_PREDICATES = {
    "HAS_REVISION", "SUPERSEDES", "PRECEDES", "REFERENCES", "GOVERNS", "SPECIFIES",
    "CONTAINS", "HAS_NOTE", "HAS_DIMENSION", "HAS_TOLERANCE", "HAS_BOM_ITEM",
    "HAS_SPARE", "PART_OF", "ASSEMBLED_FROM", "INSTALLED_ON", "FASTENED_BY",
    "INTERFACES_WITH", "CONNECTED_TO", "OPERATED_BY", "CONTROLLED_BY", "REQUIRES",
    "INSPECTED_BY", "MAINTAINED_BY", "HAS_FAILURE_MODE", "CAN_CAUSE", "MITIGATED_BY",
    "APPLIES_TO", "DERIVED_FROM", "SUPPORTED_BY", "CONFLICTS_WITH", "VALID_DURING",
    "MODIFIED_IN", "INTRODUCED_IN", "REMOVED_IN", "CONTAINS_SLEEPER"
}

def validate():
    print("================================================================================")
    print("RDSO CANONICAL KNOWLEDGE CORE SCHEMA & INTEGRITY AUDITOR")
    print("================================================================================")

    try:
        with open("rdso_canonical_kg.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[FATAL] Failed to read rdso_canonical_kg.json: {e}")
        sys.exit(1)

    entities = data.get("entities", [])
    edges = data.get("edges", [])
    facts = data.get("facts", [])

    errors = []
    warnings = []

    # 1. Entity Validation
    entity_ids = set()
    for e in entities:
        eid = e.get("id")
        if not eid:
            errors.append(f"Entity missing 'id': {e}")
            continue
        if eid in entity_ids:
            errors.append(f"Duplicate entity ID: {eid}")
        entity_ids.add(eid)

        etype = e.get("type")
        if not etype or etype not in CONTROLLED_ENTITY_TYPES:
            errors.append(f"Entity '{eid}' has uncontrolled type '{etype}'")

        if not e.get("label"):
            warnings.append(f"Entity '{eid}' has no human-readable label")

    # 2. Edge & Referential Integrity Validation
    for i, edge in enumerate(edges):
        from_id = edge.get("from")
        to_id = edge.get("to")
        rel = edge.get("rel")

        if not from_id or from_id not in entity_ids:
            errors.append(f"Edge #{i} 'from' reference '{from_id}' does not exist in entities")
        if not to_id or to_id not in entity_ids:
            errors.append(f"Edge #{i} 'to' reference '{to_id}' does not exist in entities")

        if not rel or rel not in CONTROLLED_PREDICATES:
            errors.append(f"Edge #{i} ({from_id} -> {to_id}) uses uncontrolled predicate '{rel}'")

    # 3. Fact Provenance Validation
    for f in facts:
        fid = f.get("id")
        sub = f.get("subject_id")
        obj = f.get("object_id")
        src = f.get("source", {})

        if sub not in entity_ids:
            errors.append(f"Fact '{fid}' subject '{sub}' does not exist in entities")
        if obj not in entity_ids:
            errors.append(f"Fact '{fid}' object '{obj}' does not exist in entities")

        if not src.get("drawing_id"):
            warnings.append(f"Fact '{fid}' missing source drawing_id")
        if not src.get("crop"):
            warnings.append(f"Fact '{fid}' missing source blueprint crop link")

    # Print Summary
    print(f"\n[METRICS]")
    print(f"  • Total Entities:        {len(entities)}")
    print(f"  • Total Typed Edges:     {len(edges)}")
    print(f"  • Total Provenance Facts:{len(facts)}")
    print(f"  • Graph Density:         {len(edges) / max(1, len(entities)):.2f} edges/node")

    # Domain Breakdown
    domains = {}
    for e in entities:
        d = e.get("domain", "other")
        domains[d] = domains.get(d, 0) + 1
    print("\n[ENTITY DOMAIN DISTRIBUTION]")
    for d, count in sorted(domains.items()):
        print(f"  • {d.upper():<20}: {count} entities")

    # Predicate Breakdown
    predicates = {}
    for edge in edges:
        p = edge.get("rel", "other")
        predicates[p] = predicates.get(p, 0) + 1
    print("\n[PREDICATE FREQUENCY]")
    for p, count in sorted(predicates.items(), key=lambda x: -x[1]):
        print(f"  • {p:<20}: {count} edges")

    print("\n================================================================================")
    if errors:
        print(f"[FAIL] Found {len(errors)} critical validation errors:")
        for err in errors[:10]:
            print(f"  ❌ {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        sys.exit(1)
    else:
        print(f"[PASS] 0 Schema Errors! Knowledge Core is 100% compliant with Blueprint standards.")
        if warnings:
            print(f"       ({len(warnings)} non-fatal provenance warnings logged)")
    print("================================================================================\n")

if __name__ == "__main__":
    validate()
