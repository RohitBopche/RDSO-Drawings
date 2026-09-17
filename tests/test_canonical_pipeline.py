"""
Regression tests for Canonical Knowledge Graph Pipeline (Task P0.3).
Validates schema contracts, vocabulary compliance, referential integrity,
and evidence resolution against canonical JSONL datasets.
"""

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "knowledge-graph" / "canonical"
VOCABULARY_FILE = ROOT / "data" / "knowledge-graph" / "schemas" / "vocabularies" / "relationship-types.json"


@pytest.fixture(scope="module")
def nodes():
    path = CANONICAL / "nodes.jsonl"
    assert path.exists(), "nodes.jsonl missing"
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def edges():
    path = CANONICAL / "edges.jsonl"
    assert path.exists(), "edges.jsonl missing"
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def requirements():
    path = CANONICAL / "requirements.jsonl"
    assert path.exists(), "requirements.jsonl missing"
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def evidence():
    path = CANONICAL / "evidence.jsonl"
    assert path.exists(), "evidence.jsonl missing"
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def allowed_relationships():
    assert VOCABULARY_FILE.exists(), "relationship-types.json missing"
    with VOCABULARY_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return set(data["items"]["enum"])


def test_canonical_nodes_have_required_fields(nodes):
    """Every node must satisfy entity.schema.json: id, type, and name."""
    assert len(nodes) > 100
    seen_ids = set()
    for n in nodes:
        assert "id" in n and isinstance(n["id"], str) and n["id"], f"Invalid ID in node: {n}"
        assert n["id"] not in seen_ids, f"Duplicate node ID: {n['id']}"
        seen_ids.add(n["id"])
        assert "type" in n and isinstance(n["type"], str) and n["type"], f"Missing type in {n['id']}"
        assert "name" in n and isinstance(n["name"], str) and n["name"], f"Missing name in {n['id']}"
        assert n.get("verification_status") in [
            "unverified", "machine_extracted", "reviewed", "verified", "disputed"
        ], f"Invalid verification_status in {n['id']}"


def test_canonical_edges_use_controlled_vocabulary(edges, allowed_relationships, nodes):
    """Every edge must have a valid rel from the controlled vocabulary and zero dangling endpoints."""
    node_ids = {n["id"] for n in nodes}
    assert len(edges) > 100
    for idx, e in enumerate(edges):
        rel = e.get("rel")
        assert rel in allowed_relationships, f"Invalid relationship '{rel}' in edge {idx}"
        assert e.get("from") in node_ids, f"Dangling edge from: {e.get('from')}"
        assert e.get("to") in node_ids, f"Dangling edge to: {e.get('to')}"


def test_canonical_requirements_have_statement(requirements, nodes):
    """Every requirement must satisfy requirement.schema.json: id and statement."""
    assert len(requirements) > 100
    node_ids = {n["id"] for n in nodes}
    for r in requirements:
        assert "id" in r and r["id"], f"Requirement missing ID: {r}"
        assert "statement" in r and isinstance(r["statement"], str) and r["statement"].strip(), (
            f"Requirement {r['id']} missing statement"
        )
        if r.get("source_document_id"):
            assert r["source_document_id"] in node_ids, (
                f"Requirement {r['id']} has invalid source_document_id: {r['source_document_id']}"
            )


def test_evidence_integrity_and_crops_on_disk(evidence, nodes):
    """All evidence records must reference known documents and existing physical files."""
    assert len(evidence) > 50
    node_ids = {n["id"] for n in nodes}
    seen_ev_ids = set()

    for ev in evidence:
        eid = ev.get("evidence_id")
        assert eid and isinstance(eid, str), f"Invalid evidence_id in {ev}"
        assert eid not in seen_ev_ids, f"Duplicate evidence_id: {eid}"
        seen_ev_ids.add(eid)

        assert ev.get("document_id") in node_ids, f"Evidence {eid} references unknown document_id: {ev.get('document_id')}"
        assert ev.get("extraction_method") in [
            "manual", "text_extract", "ocr", "table_extract", "drawing_parse", "derived"
        ], f"Invalid extraction_method in {eid}"
        assert ev.get("verification_status") in [
            "unverified", "machine_extracted", "reviewed", "verified", "disputed"
        ], f"Invalid verification_status in {eid}"

        file_path = ev.get("file_path")
        if file_path:
            full_path = ROOT / file_path
            assert full_path.exists(), f"Physical evidence file does not exist: {file_path}"
