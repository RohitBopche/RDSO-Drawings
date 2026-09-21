import pytest

from scripts.query_manual_kg import ManualKG


def make_kg():
    structure = {
        "manuals": [{
            "document_id": "DOC:M:1",
            "alias": "M",
            "title": "Test Manual",
            "chapters": [
                {"chapter_id": "CHAPTER:M:CH_01", "chapter_number": 1, "title": "First", "page_start": 1, "page_end": 10},
                {"chapter_id": "CHAPTER:M:CH_02", "chapter_number": 2, "title": "Second", "page_start": 11, "page_end": 20},
            ],
        }]
    }
    canonical = {
        "entities": [
            {"id": "DOC:M:1", "domain": "manual", "type": "DOCUMENT", "label": "Test Manual"},
            {"id": "CHAPTER:M:CH_01", "domain": "manual", "type": "CHAPTER", "label": "Chapter 1 — First", "specs": {"ChapterNumber": 1, "PageRange": "1–10"}},
            {"id": "CHAPTER:M:CH_02", "domain": "manual", "type": "CHAPTER", "label": "Chapter 2 — Second", "specs": {"ChapterNumber": 2, "PageRange": "11–20"}},
            {"id": "SECTION:M:CH_01:P1:01", "domain": "manual", "type": "SECTION", "label": "Overview", "page": 1},
            {"id": "drg_6155", "domain": "drawing", "type": "DRAWING", "label": "Drawing"},
        ],
        "edges": [
            {"from": "DOC:M:1", "to": "CHAPTER:M:CH_01", "rel": "HAS_CHAPTER"},
            {"from": "DOC:M:1", "to": "CHAPTER:M:CH_02", "rel": "HAS_CHAPTER"},
            {"from": "CHAPTER:M:CH_01", "to": "SECTION:M:CH_01:P1:01", "rel": "HAS_SECTION"},
            {"from": "CHAPTER:M:CH_01", "to": "drg_6155", "rel": "REFERENCES"},
        ],
    }
    return ManualKG(structure, canonical)


def test_manual_query_exposes_authoritative_chapters_only():
    result = make_kg().get_manual("DOC:M:1")
    assert [c["number"] for c in result["chapters"]] == [1, 2]
    assert [c["id"] for c in result["chapters"]] == [
        "CHAPTER:M:CH_01", "CHAPTER:M:CH_02"
    ]


def test_chapter_query_filters_to_structural_children():
    result = make_kg().chapter_children("CHAPTER:M:CH_01")
    assert [c["id"] for c in result] == ["SECTION:M:CH_01:P1:01"]


def test_search_cannot_return_drawing_nodes():
    result = make_kg().search("drawing")
    assert result == []
