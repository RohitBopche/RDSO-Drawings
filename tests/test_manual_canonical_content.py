import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_manual_canonical_content import validate


def base():
    structure = {
        "manuals": [{
            "document_id": "DOC:M:1",
            "chapters": [{
                "chapter_id": "CHAPTER:M:CH_01",
                "chapter_number": 1,
                "page_range": [10, 20],
                "clauses": [{
                    "clause_id": "CLAUSE:M:PARA_1",
                    "page_number": 12,
                }],
            }],
        }]
    }
    canonical = {
        "entities": [
            {"id": "DOC:M:1", "domain": "manual", "universe": "manuals", "type": "DOCUMENT"},
            {"id": "CHAPTER:M:CH_01", "domain": "manual", "universe": "manuals", "type": "CHAPTER",
             "specs": {"PageRange": [10, 20]}},
            {"id": "CLAUSE:M:PARA_1", "domain": "manual", "universe": "manuals", "type": "CLAUSE",
             "source_document": "DOC:M:1", "source_page": 12,
             "extraction_method": "test", "parent_chapter_id": "CHAPTER:M:CH_01"},
        ],
        "edges": [{
            "from": "CHAPTER:M:CH_01", "to": "CLAUSE:M:PARA_1", "rel": "HAS_CLAUSE"
        }],
    }
    return structure, canonical


def test_authoritative_clause_ownership_passes():
    structure, canonical = base()
    errors, _ = validate(structure, canonical)
    assert errors == []


def test_child_page_must_stay_inside_chapter():
    structure, canonical = base()
    canonical["entities"][2]["source_page"] = 99
    errors, _ = validate(structure, canonical)
    assert any("outside chapter" in e for e in errors)


def test_child_cannot_have_two_chapter_owners():
    structure, canonical = base()
    canonical["entities"].append({
        "id": "CHAPTER:M:CH_02", "domain": "manual", "universe": "manuals",
        "type": "CHAPTER", "specs": {"PageRange": [21, 30]}
    })
    canonical["edges"].append({
        "from": "CHAPTER:M:CH_02", "to": "CLAUSE:M:PARA_1", "rel": "HAS_CLAUSE"
    })
    errors, _ = validate(structure, canonical)
    assert any("multiple chapter owners" in e for e in errors)


def test_source_provenance_is_required():
    structure, canonical = base()
    canonical["entities"][2].pop("source_page")
    errors, _ = validate(structure, canonical)
    assert any("missing source_page" in e for e in errors)
