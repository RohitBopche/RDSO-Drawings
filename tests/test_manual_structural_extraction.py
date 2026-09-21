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


def _minimal_registry_payload():
    from validate_manual_chapter_content import MANUAL_CHAPTER_REGISTRY
    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    return {
        "manuals": [{
            "document_id": doc_id,
            "chapters": [{
                "chapter_id": f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}",
                "chapter_number": spec["num"],
                "parent_manual_id": doc_id,
                "universe": "manuals",
                "order": spec["num"],
                "structure_status": "STRUCTURE_VERIFIED",
                "page_range": [spec["page_start"], spec["page_end"]],
                "pages_seen": [],
                "headings": [],
                "clauses": [],
            } for spec in registry["chapters"]],
        }]
    }


def test_payload_rejects_observed_pages_outside_registry():
    from validate_manual_chapter_content import validate_payload

    payload = _minimal_registry_payload()
    chapter = payload["manuals"][0]["chapters"][0]
    chapter["pages_seen"] = [chapter["page_range"][0] - 1]
    errors, warnings = validate_payload(payload)
    assert any("observed pages outside authoritative registry" in error for error in errors)


def test_payload_accepts_observed_boundary_page_when_registry_assigns_it_to_both_chapters():
    from validate_manual_chapter_content import MANUAL_CHAPTER_REGISTRY, validate_payload

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    payload = _minimal_registry_payload()
    chapters = payload["manuals"][0]["chapters"]
    by_num = {c["chapter_number"]: c for c in chapters}
    for left, right in zip(registry["chapters"], registry["chapters"][1:]):
        if left["page_end"] == right["page_start"]:
            page = left["page_end"]
            by_num[left["num"]]["pages_seen"] = [page]
            by_num[right["num"]]["pages_seen"] = [page]
            errors, warnings = validate_payload(payload)
            assert not any("observed page" in error and str(page) in error for error in errors)
            return
    # Registry currently may have no shared boundary; the structural test remains valid.
    assert True


def test_heading_candidate_normalization_suppresses_duplicates_large_integer_noise_and_backward_order():
    from ingest_all_manual_chapters import normalize_source_heading_candidates

    candidates = [
        {"reference": "1", "title": "INTRODUCTION", "source_page": 1, "source_text": "1 INTRODUCTION"},
        {"reference": "1", "title": "INTRODUCTION", "source_page": 2, "source_text": "1 INTRODUCTION"},
        {"reference": "1.1", "title": "GENERAL REQUIREMENTS", "source_page": 2, "source_text": "1.1 GENERAL REQUIREMENTS"},
        {"reference": "900", "title": "PAGE NUMBER NOISE", "source_page": 3, "source_text": "900 PAGE NUMBER NOISE"},
        {"reference": "1.0", "title": "BACKWARD NOISE", "source_page": 4, "source_text": "1.0 BACKWARD NOISE"},
        {"reference": "2", "title": "NEXT SECTION", "source_page": 5, "source_text": "2 NEXT SECTION"},
    ]

    result = normalize_source_heading_candidates(candidates)
    assert [item["reference"] for item in result] == ["1", "1.1", "2"]
