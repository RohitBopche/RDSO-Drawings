from scripts.ingest_all_manual_chapters import MANUAL_CHAPTER_REGISTRY, get_chapters_for_page


def test_overlapping_manual_boundary_pages_are_preserved_for_all_owners():
    at_weld = get_chapters_for_page("DOC:AT_WELD:2022", 7)
    assert [chapter["num"] for chapter in at_weld] == [1, 2]

    fbw = get_chapters_for_page("DOC:FBW:2022:CS5", 4)
    assert [chapter["num"] for chapter in fbw] == [1, 2]


def test_non_overlapping_page_has_single_authoritative_owner():
    chapters = get_chapters_for_page("DOC:AT_WELD:2022", 8)
    assert [chapter["num"] for chapter in chapters] == [3]


def test_unknown_page_has_no_authoritative_owner():
    assert get_chapters_for_page("DOC:AT_WELD:2022", 6) == []
