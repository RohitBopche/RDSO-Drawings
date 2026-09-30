import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.ingest_all_manual_chapters import build_clause_record, get_chapters_for_page  # noqa: E402
from scripts.validate_manual_canonical_content import validate_child_provenance  # noqa: E402


def test_manual_clause_identity_is_chapter_scoped():
    body = "1.0 Scope and General Requirements\nThe applicable requirement shall be followed."

    one = build_clause_record("DOC:AT_WELD:2022", "AT_WELD", 1, "1.0", "Scope", 7, 7, body)
    two = build_clause_record("DOC:AT_WELD:2022", "AT_WELD", 2, "1.0", "Scope", 7, 7, body)

    assert one["clause_id"] == "CLAUSE:AT_WELD:CH_01:PARA_1_0"
    assert two["clause_id"] == "CLAUSE:AT_WELD:CH_02:PARA_1_0"
    assert one["clause_id"] != two["clause_id"]


def test_clause_record_keeps_full_text_beyond_old_1200_char_limit():
    body = "429 Long clause\n" + ("The gauge shall be checked daily. " * 100)
    rec = build_clause_record("DOC:IRPWM:2024:ACS14", "IRPWM", 4, "429", "Long clause", 195, 196, body)

    assert rec["verbatim_text"] == body and len(rec["verbatim_text"]) > 1200
    assert rec["page_number"] == 195 and rec["page_end"] == 196


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
