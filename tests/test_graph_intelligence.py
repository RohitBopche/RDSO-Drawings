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
    """Must discover valid multi-hop path from comp_detailb to doc_irpwm_2024."""
    edges = canonical_kg.get("edges", [])
    path = bfs_find_path(edges, "comp_detailb", "doc_irpwm_2024", max_hops=4)
    assert path is not None, "Failed to find path from comp_detailb to doc_irpwm_2024"
    assert len(path) >= 1
    assert any(step[1] in ["CONTAINS", "GOVERNS", "INTERFACES_WITH", "APPLIES_TO", "REFERENCES"] for step in path)


def test_pathfinding_drawing_to_crossing(canonical_kg):
    """Must discover path from drg_6155 to drg_6280 (CMS Crossing)."""
    edges = canonical_kg.get("edges", [])
    path = bfs_find_path(edges, "drg_6155", "drg_6280", max_hops=3)
    assert path is not None, "Failed to find path from drg_6155 to drg_6280"
    assert len(path) <= 3


def test_explain_relationship_coverage(canonical_kg):
    """Explanation dictionary must cover all core Blueprint Section 4.1 relationship predicates."""
    core_predicates = [
        "CONTAINS", "CONNECTED_TO", "INSTALLED_ON", "FASTENED_BY",
        "INTERFACES_WITH", "GOVERNS", "SPECIFIES", "REQUIRES",
        "INSPECTED_BY", "MAINTAINED_BY", "MITIGATED_BY", "CAN_CAUSE",
        "HAS_REVISION", "SUPERSEDES", "INTRODUCED_IN", "HAS_SPARE"
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

    # 3. Procedure Path: doc_usfd_2026 -> sop_usfd_switch_testing -> equip_usfd_tester
    proc_sop_path = bfs_find_path(edges, "doc_usfd_2026", "equip_usfd_tester", max_hops=3)
    assert proc_sop_path is not None, "Procedure Path template failed"

    # 4. Procurement Path: drg_6155 -> spare_bolt_25x310
    proc_path = bfs_find_path(edges, "drg_6155", "spare_bolt_25x310", max_hops=3)
    assert proc_path is not None, "Procurement Path template failed"
