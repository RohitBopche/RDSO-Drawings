import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from resolve_manual_hierarchy import heading_kind, numeric_parent, resolve_heading_sequence


def test_heading_depth_and_kind():
    assert heading_kind("2") == ("SECTION", 1)
    assert heading_kind("2.1") == ("SUBSECTION", 2)
    assert heading_kind("2.1.1") == ("SUBSECTION", 3)
    assert heading_kind("ANNEXURE-II") == ("ANNEXURE", 1)


def test_numeric_parent():
    assert numeric_parent("2.1") == "2"
    assert numeric_parent("2.1.1") == "2.1"
    assert numeric_parent("2") is None


def test_valid_nested_heading_sequence():
    headings, errors = resolve_heading_sequence([
        {"reference": "2", "title": "Track Structure", "source_page": 10},
        {"reference": "2.1", "title": "Rails", "source_page": 11},
        {"reference": "2.1.1", "title": "Rail Selection", "source_page": 11},
        {"reference": "2.2", "title": "Sleepers", "source_page": 12},
        {"reference": "ANNEXURE-I", "title": "Inspection Form", "source_page": 13},
    ], [10, 20])
    assert not errors
    assert headings[2]["parent_heading_ref"] == "2.1"
    assert headings[4]["heading_kind"] == "ANNEXURE"


def test_reject_missing_parent_and_depth_jump():
    _, errors = resolve_heading_sequence([
        {"reference": "2", "title": "Track Structure", "source_page": 10},
        {"reference": "2.1.1", "title": "Rail Selection", "source_page": 11},
    ], [10, 20])
    assert any("missing parent heading 2.1" in e for e in errors)


def test_reject_duplicate_and_out_of_range_heading():
    _, errors = resolve_heading_sequence([
        {"reference": "2", "title": "Track Structure", "source_page": 10},
        {"reference": "2", "title": "Duplicate", "source_page": 11},
        {"reference": "3", "title": "Outside", "source_page": 21},
    ], [10, 20])
    assert any("duplicate heading reference: 2" in e for e in errors)
    assert any("outside chapter range" in e for e in errors)


def test_canonical_graph_materializes_authoritative_nested_headings_and_deepest_clause_owner():
    from resolve_manual_hierarchy import resolve_canonical_graph

    chapter_id = "CHAPTER:TEST:CH_02"
    clause_id = "CLAUSE:TEST:PARA_2_1_1"
    canonical = {
        "entities": [
            {"id": chapter_id, "type": "CHAPTER", "domain": "manual", "universe": "manuals"},
            {"id": clause_id, "type": "CLAUSE", "domain": "manual", "universe": "manuals"},
        ],
        "edges": [
            {"from": chapter_id, "to": clause_id, "rel": "HAS_CLAUSE"},
        ],
        "facts": [],
        "metadata": {},
    }
    intermediate = {
        "manuals": [{
            "document_id": "DOC:TEST:2026",
            "alias": "TEST",
            "chapters": [{
                "chapter_id": chapter_id,
                "title": "Test Chapter",
                "page_range": [10, 20],
                "headings": [
                    {"reference": "2", "title": "Track Structure", "source_page": 10},
                    {"reference": "2.1", "title": "Rails", "source_page": 11},
                    {"reference": "2.1.1", "title": "Rail Selection", "source_page": 12},
                ],
                "clauses": [{
                    "clause_id": clause_id,
                    "para_number": "2.1.1",
                    "source_page": 12,
                }],
            }],
        }],
    }
    result, errors = resolve_canonical_graph(intermediate, canonical)
    assert not errors
    entities = {e["id"]: e for e in result["entities"]}
    assert entities["SECTION:TEST:CHAPTER_TEST_CH_02:SEC_2"]["heading_kind"] == "SECTION"
    assert entities["SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1_1"]["heading_kind"] == "SUBSECTION"
    assert any(e["from"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1" and e["to"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1_1" and e["rel"] == "HAS_SECTION" for e in result["edges"])
    assert any(e["from"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1_1" and e["to"] == clause_id and e["rel"] == "HAS_CLAUSE" for e in result["edges"])
    assert not any(e["from"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1" and e["to"] == clause_id and e["rel"] == "HAS_CLAUSE" for e in result["edges"])
    assert result["metadata"]["manual_hierarchy_resolved_headings"] == 3


def test_coverage_audit_flags_sparse_chapters_as_warnings():
    from validate_manual_hierarchy import _coverage_audit
    errors, warnings, metrics = _coverage_audit({
        "chapter_id": "CHAPTER:TEST:CH_01",
        "page_range": [10, 12],
        "pages_seen": [10],
        "headings": [{"reference": "2.1", "source_page": 10, "title": "Heading"}],
        "clauses": [],
        "tables": [],
        "figures": [],
        "evidence": [],
    })
    assert errors == []
    assert metrics["pages_expected"] == 3
    assert metrics["pages_seen"] == 1
    assert metrics["headings"] == 1
    assert any("not observed" in warning for warning in warnings)


def test_coverage_audit_rejects_malformed_heading_references():
    from validate_manual_hierarchy import _coverage_audit
    errors, warnings, metrics = _coverage_audit({
        "chapter_id": "CHAPTER:TEST:CH_01",
        "page_range": [10, 10],
        "pages_seen": [10],
        "headings": [{"reference": "not-a-reference", "source_page": 10, "title": "Bad"}],
    })
    assert any("malformed heading reference" in error for error in errors)


def test_coverage_audit_classifies_health_states():
    from validate_manual_hierarchy import _coverage_audit

    base = {
        "chapter_id": "CHAPTER:TEST:CH_01",
        "page_range": [10, 10],
        "pages_seen": [10],
        "clauses": [],
    }
    errors, warnings, metrics = _coverage_audit({**base, "headings": []})
    assert not errors
    assert metrics["coverage_class"] == "NO_SOURCE_HEADINGS"

    errors, warnings, metrics = _coverage_audit({
        **base,
        "headings": [
            {"reference": "2", "source_page": 10, "title": "Section"},
            {"reference": "2.1", "source_page": 10, "title": "Subsection"},
        ],
    })
    assert not errors
    assert metrics["coverage_class"] == "HEALTHY"

    errors, warnings, metrics = _coverage_audit({
        **base,
        "headings": [{"reference": "2", "source_page": 10, "title": "Section"}],
    })
    assert not errors
    assert metrics["coverage_class"] == "SPARSE"

    errors, warnings, metrics = _coverage_audit({
        **base,
        "headings": [{"reference": "bad", "source_page": 10, "title": "Bad"}],
    })
    assert errors
    assert metrics["coverage_class"] == "MALFORMED"
