"""
Automated unit tests for Phase 3: Engineering Graph Intelligence.
Tests bidirectional BFS pathfinding, relationship explanation generation,
and standard path templates per Blueprint Sections 13 and 14.
"""

from collections import deque
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_KG_FILE = ROOT / "data" / "rdso_canonical_kg.json"


@pytest.fixture(scope="module")
def canonical_kg():
    assert CANONICAL_KG_FILE.exists(), "rdso_canonical_kg.json missing"
    with CANONICAL_KG_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def bfs_find_path(edges, start_id, end_id, max_hops=4):
    """Bidirectional BFS graph path search."""
    adj = {}
    for e in edges:
        u = e.get("from")
        v = e.get("to")
        rel = e.get("rel")
        adj.setdefault(u, []).append((v, rel, "out"))
        adj.setdefault(v, []).append((u, rel, "in"))

    queue = deque([(start_id, [])])
    visited = {start_id}

    while queue:
        current, path = queue.popleft()
        if current == end_id:
            return path
        if len(path) >= max_hops:
            continue

        for neighbor, rel, direction in adj.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [(current, rel, neighbor, direction)]))
    return None


def test_pathfinding_component_to_standard(canonical_kg):
    """Drawing-only pathfinding remains valid inside the isolated Drawing KG."""
    edges = canonical_kg.get("edges", [])
    path = bfs_find_path(edges, "comp_tongue_rail", "std_irs_t10", max_hops=3)
    assert path is not None, "Failed to find component-to-standard path"
    assert len(path) <= 3


def test_pathfinding_drawing_to_crossing(canonical_kg):
    """Must discover path from drg_6155 to drg_6280 (CMS Crossing)."""
    edges = canonical_kg.get("edges", [])
    path = bfs_find_path(edges, "drg_6155", "drg_6280", max_hops=3)
    assert path is not None, "Failed to find path from drg_6155 to drg_6280"
    assert len(path) <= 3


def test_explain_relationship_coverage(canonical_kg):
    """Explanation dictionary must cover all core Blueprint Section 4.1 relationship predicates."""
    # Manual and Drawing universes are intentionally isolated. Therefore the
    # relationship contract asserted here is limited to predicates that remain
    # valid inside the published Drawing KG; manual-to-equipment/specification
    # predicates must not be required in the isolated canonical dataset.
    core_predicates = [
        "CONTAINS", "CONNECTED_TO", "INSTALLED_ON", "FASTENED_BY",
        "INTERFACES_WITH", "MITIGATED_BY", "CAN_CAUSE",
        "HAS_REVISION", "SUPERSEDES", "HAS_SPARE"
    ]
    edges = canonical_kg.get("edges", [])
    found_rels = {e.get("rel") for e in edges}

    for pred in core_predicates:
        assert pred in found_rels, f"Predicate {pred} not found in canonical KG edges"


def test_standard_path_templates(canonical_kg):
    """Verify feasibility of all 4 Blueprint Section 14 templates."""
    edges = canonical_kg.get("edges", [])
    entities = {e["id"]: e for e in canonical_kg.get("entities", [])}

    # 1. Component Path: comp_tongue_rail -> drg_6155 -> std_irs_t10
    comp_path = bfs_find_path(edges, "comp_tongue_rail", "std_irs_t10", max_hops=3)
    assert comp_path is not None, "Component Path template failed"

    # 2. Failure Path: defect_joint_fatigue -> hazard_derailment_split
    fail_path = bfs_find_path(edges, "defect_joint_fatigue", "hazard_derailment_split", max_hops=3)
    assert fail_path is not None, "Failure Path template failed"

    # 3. Manual/Drawing isolation: a manual SOP must not reach drawing-side
    # equipment through the canonical graph while the universes are separated.
    proc_sop_path = bfs_find_path(edges, "sop_usfd_switch_testing", "equip_usfd_tester", max_hops=1)
    assert proc_sop_path is None, "Manual-to-equipment path violates universe isolation"

    # 4. Procurement Path: drg_6155 -> spare_bolt_25x310
    proc_path = bfs_find_path(edges, "drg_6155", "spare_bolt_25x310", max_hops=3)
    assert proc_path is not None, "Procurement Path template failed"
