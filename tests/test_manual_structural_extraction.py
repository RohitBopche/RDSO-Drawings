import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ingest_all_manual_chapters import extract_structural_content


def test_explicit_table_figure_evidence_are_extracted_with_stable_ids():
    text = """Table 1 - Acceptance Limits
Column A | Column B
Figure 2 - Weld profile
Evidence: inspection record
"""
    first = extract_structural_content("DOC:AT_WELD:2022", 7, 21, text)
    second = extract_structural_content("DOC:AT_WELD:2022", 7, 21, text)

    assert len(first["tables"]) == 1
    assert len(first["figures"]) == 1
    assert len(first["evidence"]) == 1
    assert first == second
    assert first["tables"][0]["id"].startswith("TABLE:AT_WELD:CH_07:P0021:")
    assert first["figures"][0]["id"].startswith("FIGURE:AT_WELD:CH_07:P0021:")
    assert first["evidence"][0]["id"].startswith("EVIDENCE:AT_WELD:CH_07:P0021:")
    for item in first["tables"] + first["figures"] + first["evidence"]:
        assert item["source_document"] == "DOC:AT_WELD:2022"
        assert item["source_page"] == 21
        assert item["source_text"]
        assert item["extraction_method"] == "deterministic_explicit_source_label"
        assert item["confidence"] == 0.90


def test_unlabeled_semantic_text_does_not_create_structural_artifacts():
    result = extract_structural_content(
        "DOC:AT_WELD:2022",
        7,
        21,
        "This paragraph mentions a table and figure but has no explicit source label."
    )
    assert result == {"tables": [], "figures": [], "evidence": []}


def test_numbered_source_heading_extraction_is_conservative():
    from ingest_all_manual_chapters import extract_source_headings
    result = extract_source_headings("DOC:AT_WELD:2022", 12, "2.1 Rail Selection Criteria\nRails shall be inspected before welding.\n2.2 Equipment Storage")
    assert [h["reference"] for h in result] == ["2.1", "2.2"]
    assert result[0]["title"] == "Rail Selection Criteria"
    assert result[0]["extraction_method"] == "deterministic_numbered_source_heading"


def test_source_heading_extraction_rejects_requirement_prose_and_long_lines():
    from ingest_all_manual_chapters import extract_source_headings

    result = extract_source_headings(
        "DOC:AT_WELD:2022",
        12,
        "2.1 Rail Selection Criteria\n"
        "Rails shall be inspected before welding.\n"
        "2.2 This is a very long heading that contains more than twenty words "
        "and should therefore not be treated as a structural source heading.\n"
        "2.3 Equipment Storage"
    )
    assert [h["reference"] for h in result] == ["2.1", "2.3"]


def test_source_heading_extraction_preserves_page_and_document_provenance():
    from ingest_all_manual_chapters import extract_source_headings

    result = extract_source_headings(
        "DOC:FBW:2022:CS5",
        9,
        "4.1 Welding Procedure"
    )
    assert result[0]["source_document"] == "DOC:FBW:2022:CS5"
    assert result[0]["source_page"] == 9
    assert result[0]["source_section"] == "4.1"


def test_authoritative_registry_boundaries_are_valid():
    from validate_manual_chapter_content import validate_registry_boundaries
    errors, warnings = validate_registry_boundaries()
    assert not errors
    assert isinstance(warnings, list)
