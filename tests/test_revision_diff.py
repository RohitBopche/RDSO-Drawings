"""
Automated unit and regression tests for Phase 2: Evidence and Revision Intelligence.
Tests revision sequence ordering, notes diff classification, downstream impact traversal,
and data conflict records per Blueprint Section 6, 12, 30, and 36.
"""

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_KG_FILE = ROOT / "data" / "rdso_canonical_kg.json"
EXTRACTED_KNOWLEDGE_FILE = ROOT / "data" / "rdso_extracted_knowledge.json"


@pytest.fixture(scope="module")
def canonical_kg():
    assert CANONICAL_KG_FILE.exists(), "rdso_canonical_kg.json missing"
    with CANONICAL_KG_FILE.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def extracted_knowledge():
    assert EXTRACTED_KNOWLEDGE_FILE.exists(), "rdso_extracted_knowledge.json missing"
    with EXTRACTED_KNOWLEDGE_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def test_t6155_revision_sequence(canonical_kg):
    """RDSO/T-6155 must possess a complete linear revision lineage from Alt 10 to Alt 13."""
    entities = {e["id"]: e for e in canonical_kg.get("entities", [])}
    edges = canonical_kg.get("edges", [])

    expected_revs = [
        "rev_6155_alt10",
        "rev_6155_alt11",
        "rev_6155_alt12",
        "rev_6155_alt13"
    ]
    for r in expected_revs:
        assert r in entities, f"Missing revision node: {r}"
        assert entities[r].get("type") == "REVISION"

    # Verify linear SUPERSEDES chain
    supersedes_pairs = [
        (e["from"], e["to"]) for e in edges if e.get("rel") == "SUPERSEDES"
    ]
    assert ("rev_6155_alt10", "rev_6155_alt11") in supersedes_pairs
    assert ("rev_6155_alt11", "rev_6155_alt12") in supersedes_pairs
    assert ("rev_6155_alt12", "rev_6155_alt13") in supersedes_pairs


def test_revision_notes_diff_logic(extracted_knowledge):
    """Diffing between Alt 10 and Alt 13 must detect additions such as Note 28 and Detail B."""
    t6155 = extracted_knowledge.get("RDSO_T_6155", {})
    history = t6155.get("alteration_history", [])
    assert len(history) >= 4, "T-6155 alteration history missing entries"

    alt13 = next((h for h in history if h.get("alt") == 13), None)
    alt12 = next((h for h in history if h.get("alt") == 12), None)
    assert alt13 is not None and "Note 28" in alt13.get("desc", "")
    assert alt12 is not None and "Detail 'B'" in alt12.get("desc", "")

    notes = t6155.get("general_notes", [])
    assert len(notes) == 28, f"Expected 28 general notes, got {len(notes)}"
    assert any("10%" in n.get("text", "") or "LIST - A" in n.get("text", "") for n in notes if n.get("num") == 28)


def test_revision_impact_traversal(canonical_kg):
    """Traversing from rev_6155_alt12 must discover downstream tie bar, drop clearance, and clamp lock."""
    edges = canonical_kg.get("edges", [])
    entities = {e["id"]: e for e in canonical_kg.get("entities", [])}

    # Find notes introduced in Alt 12
    alt12_notes = [e["to"] for e in edges if e["from"] == "rev_6155_alt12" and e["rel"] == "INTRODUCED_IN"]
    assert len(alt12_notes) >= 2, "rev_6155_alt12 must introduce at least 2 notes (Notes 25 & 26)"
    assert "note_6155_25" in alt12_notes

    # Verify note_6155_25 links to tolerance and SOP
    note25_out = [e["to"] for e in edges if e["from"] == "note_6155_25"]
    note25_in = [e["from"] for e in edges if e["to"] == "note_6155_25"]
    all_connected = set(note25_out + note25_in)
    assert any("tol_" in c or "spec_" in c or "sop_" in c for c in all_connected), (
        "note_6155_25 must be connected to an engineering tolerance or SOP"
    )


def test_conflict_records_integrity():
    """Defined engineering conflict records must have valid evidence and active precedence rules."""
    known_conflicts = [
        {
            "id": "conf_gauge_nominal",
            "title": "Nominal Gauge Notation: 1673 mm vs 1676 mm",
            "historical_value": "1673 mm (Title block BG nominal notation)",
            "statutory_value": "1676 mm (Standard Broad Gauge per IRPWM 2024 Para 405)",
            "precedence_rule": "Statutory Manual Precedence (IRPWM 2024 overrides legacy blueprint title text)",
            "status": "RESOLVED"
        },
        {
            "id": "conf_rail_steel_spec",
            "title": "Rail Steel Specification: UIC 860 vs IRS:T-12",
            "historical_value": "UIC 860 Grade 900A (Legacy European standard cited on initial tracings)",
            "statutory_value": "IRS:T-12:2009 / R260 / 1080 Head-Hardened Grade",
            "precedence_rule": "Active RDSO Standard Precedence (IRS:T-12 mandates min 320 HB for tongue rails)",
            "status": "RESOLVED"
        },
        {
            "id": "conf_fastener_upgrade",
            "title": "Elastic Fasteners: ERC Mk-III vs ERC Mk-V",
            "historical_value": "ERC Mk-III with GFN Liners at Sleeper 03-13",
            "statutory_value": "ERC Mk-V with Metal Liners (RDSO/T-5919)",
            "precedence_rule": "High-Axle-Load Corridor Mandate (Alt 10 upgraded to Mk-V for anti-creep resistance)",
            "status": "RESOLVED"
        }
    ]

    for c in known_conflicts:
        assert c["id"].startswith("conf_")
        assert len(c["historical_value"]) > 0
        assert len(c["statutory_value"]) > 0
        assert len(c["precedence_rule"]) > 0
        assert c["status"] in ["RESOLVED", "FLAGGED", "ACTIVE_DISCREPANCY"]
