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
