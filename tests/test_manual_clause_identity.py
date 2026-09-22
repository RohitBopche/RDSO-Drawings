from scripts.ingest_all_manual_chapters import extract_clauses_from_text, get_chapters_for_page
from scripts.validate_manual_canonical_content import validate_child_provenance


def test_manual_clause_identity_is_chapter_scoped():
    text = "1.0 Scope and General Requirements\nThe applicable requirement shall be followed."

    chapter_one = extract_clauses_from_text("DOC:AT_WELD:2022", 7, text, 1)
    chapter_two = extract_clauses_from_text("DOC:AT_WELD:2022", 7, text, 2)

    assert chapter_one
    assert chapter_two
    assert chapter_one[0]["clause_id"] == "CLAUSE:AT_WELD:CH_01:PARA_1_0"
    assert chapter_two[0]["clause_id"] == "CLAUSE:AT_WELD:CH_02:PARA_1_0"
    assert chapter_one[0]["clause_id"] != chapter_two[0]["clause_id"]


def test_boundary_page_reports_all_authoritative_chapters():
    chapters = get_chapters_for_page("DOC:AT_WELD:2022", 7)

    assert [chapter["num"] for chapter in chapters] == [1, 2]


def test_manual_child_provenance_requires_reference_and_confidence():
    errors = []
    validate_child_provenance(
        "CLAUSE:M:CH_01:PARA_1_0",
        {
            "source_document": "Manual.pdf",
            "source_text": "Requirement text",
            "source_page": 12,
            "extraction_method": "deterministic",
            "confidence": 0.95,
            "source_reference": "1.0",
        },
        errors,
    )
    assert errors == []


def test_manual_child_provenance_rejects_missing_reference_and_confidence():
    errors = []
    validate_child_provenance(
        "CLAUSE:M:CH_01:PARA_1_0",
        {
            "source_document": "Manual.pdf",
            "source_text": "Requirement text",
            "source_page": 12,
            "extraction_method": "deterministic",
        },
        errors,
    )
    assert "CLAUSE:M:CH_01:PARA_1_0: invalid confidence provenance" in errors
    assert "CLAUSE:M:CH_01:PARA_1_0: missing source_section/source_reference provenance" in errors
