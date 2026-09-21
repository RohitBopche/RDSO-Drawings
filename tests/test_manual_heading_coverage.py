from scripts.validate_manual_hierarchy import _coverage_audit


def test_heading_gap_pages_are_diagnostic_only():
    chapter = {
        "page_range": [10, 12],
        "pages_seen": [10, 11, 12],
        "headings": [
            {"reference": "1", "title": "Scope", "source_page": 10},
        ],
        "clauses": [
            {"source_page": 10},
            {"source_page": 11},
        ],
        "tables": [],
        "figures": [],
        "evidence": [],
    }
    errors, warnings, metrics = _coverage_audit(chapter)
    assert not errors
    assert metrics["heading_gap_pages"] == [11]
    assert metrics["heading_coverage_ratio"] == 0.5
    assert metrics["heading_gap_class"] == "PARTIAL_SOURCE_HEADING_COVERAGE"
    assert metrics["coverage_class"] == "SPARSE"


def test_no_heading_evidence_is_distinguished_from_empty_content():
    chapter = {
        "page_range": [20, 21],
        "pages_seen": [20, 21],
        "headings": [],
        "clauses": [{"source_page": 20}],
        "tables": [],
        "figures": [],
        "evidence": [],
    }
    errors, warnings, metrics = _coverage_audit(chapter)
    assert not errors
    assert metrics["heading_gap_pages"] == [20]
    assert metrics["heading_coverage_ratio"] == 0.0
    assert metrics["heading_gap_class"] == "NO_SOURCE_HEADING_EVIDENCE"
    assert metrics["content_empty_pages"] == [21]
