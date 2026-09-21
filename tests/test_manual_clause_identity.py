from scripts.ingest_all_manual_chapters import extract_clauses_from_text, get_chapters_for_page


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
