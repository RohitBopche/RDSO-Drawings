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
