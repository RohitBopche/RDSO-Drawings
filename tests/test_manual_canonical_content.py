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


def test_nested_section_subsection_ownership_and_page_bounds():
    structure = {
        "manuals": [{
            "document_id": "DOC:M:1",
            "chapters": [{
                "chapter_id": "CHAPTER:M:CH_01",
                "chapter_number": 1,
                "page_range": [10, 20],
                "clauses": [{
                    "clause_id": "CLAUSE:M:PARA_101",
                    "page_number": 12,
                }],
            }],
        }]
    }
    canonical = {
        "entities": [
            {"id": "CHAPTER:M:CH_01", "type": "CHAPTER", "domain": "manual",
             "universe": "manuals", "specs": {"PageRange": [10, 20]}},
            {"id": "SECTION:M:SEC_101", "type": "SECTION", "domain": "manual",
             "universe": "manuals", "parent_chapter_id": "CHAPTER:M:CH_01",
             "source_document": "DOC:M:1", "source_page": 12,
             "extraction_method": "deterministic_manual_clause_numbering"},
            {"id": "SUBSECTION:M:SEC_101", "type": "SUBSECTION", "domain": "manual",
             "universe": "manuals", "parent_chapter_id": "CHAPTER:M:CH_01",
             "source_document": "DOC:M:1", "source_page": 12,
             "extraction_method": "deterministic_manual_clause_numbering"},
            {"id": "CLAUSE:M:PARA_101", "type": "CLAUSE", "domain": "manual",
             "universe": "manuals", "parent_chapter_id": "CHAPTER:M:CH_01",
             "source_document": "DOC:M:1", "source_page": 12,
             "extraction_method": "deterministic_manual_clause_numbering"},
        ],
        "edges": [
            {"from": "CHAPTER:M:CH_01", "to": "SECTION:M:SEC_101", "rel": "HAS_SECTION"},
            {"from": "SECTION:M:SEC_101", "to": "SUBSECTION:M:SEC_101", "rel": "HAS_SECTION"},
            {"from": "SUBSECTION:M:SEC_101", "to": "CLAUSE:M:PARA_101", "rel": "HAS_CLAUSE"},
            {"from": "CHAPTER:M:CH_01", "to": "CLAUSE:M:PARA_101", "rel": "HAS_CLAUSE"},
        ],
    }
    errors, warnings = validate(structure, canonical)
    assert errors == []
    assert warnings == []


def test_structural_child_requires_exactly_one_direct_chapter_owner():
    structure = {"manuals": []}
    canonical = {
        "entities": [
            {"id": "CHAPTER:M:CH_01", "type": "CHAPTER", "domain": "manual", "universe": "manuals",
             "specs": {"PageRange": [1, 10]}},
            {"id": "CHAPTER:M:CH_02", "type": "CHAPTER", "domain": "manual", "universe": "manuals",
             "specs": {"PageRange": [11, 20]}},
            {"id": "CLAUSE:M:PARA_1", "type": "CLAUSE", "domain": "manual", "universe": "manuals",
             "parent_chapter_id": "CHAPTER:M:CH_01", "source_document": "DOC:M:1",
             "source_page": 5, "extraction_method": "test"},
        ],
        "edges": [
            {"from": "CHAPTER:M:CH_01", "to": "CLAUSE:M:PARA_1", "rel": "HAS_CLAUSE"},
            {"from": "CHAPTER:M:CH_02", "to": "CLAUSE:M:PARA_1", "rel": "HAS_CLAUSE"},
        ],
    }
    errors, _ = validate(structure, canonical)
    assert any("exactly one direct chapter owner" in e for e in errors)


def test_invalid_structural_parent_relation_is_rejected():
    structure = {"manuals": []}
    canonical = {
        "entities": [
            {"id": "CHAPTER:M:CH_01", "type": "CHAPTER", "domain": "manual", "universe": "manuals",
             "specs": {"PageRange": [1, 10]}},
            {"id": "CLAUSE:M:PARA_1", "type": "CLAUSE", "domain": "manual", "universe": "manuals",
             "parent_chapter_id": "CHAPTER:M:CH_01", "source_document": "DOC:M:1",
             "source_page": 5, "extraction_method": "test"},
        ],
        "edges": [
            {"from": "CLAUSE:M:PARA_1", "to": "CHAPTER:M:CH_01", "rel": "HAS_CLAUSE"},
        ],
    }
    errors, _ = validate(structure, canonical)
    assert any("is not owned by a canonical chapter" in e for e in errors)


def test_source_artifact_provenance_and_id_passes():
    structure = {"manuals": [{"document_id": "DOC:M:1", "chapters": [{"chapter_id": "CHAPTER:M:CH_01", "page_range": [10, 20], "clauses": [], "tables": [{"id": "TABLE:M:CH_01:P0012:01_abcdef12"}]}]}]}
    canonical = {"entities": [
        {"id": "CHAPTER:M:CH_01", "type": "CHAPTER", "domain": "manual", "universe": "manuals", "specs": {"PageRange": [10, 20]}},
        {"id": "TABLE:M:CH_01:P0012:01_abcdef12", "type": "TABLE", "domain": "manual", "universe": "manuals", "parent_chapter_id": "CHAPTER:M:CH_01", "source_document": "DOC:M:1", "source_page": 12, "source_text": "Table 1 — limits", "extraction_method": "deterministic_explicit_source_label", "confidence": 0.9}
    ], "edges": [{"from": "CHAPTER:M:CH_01", "to": "TABLE:M:CH_01:P0012:01_abcdef12", "rel": "HAS_TABLE"}]}
    errors, _ = validate(structure, canonical)
    assert errors == []


def test_source_artifact_id_and_confidence_are_validated():
    structure = {"manuals": [{"document_id": "DOC:M:1", "chapters": [{"chapter_id": "CHAPTER:M:CH_01", "page_range": [10, 20], "clauses": [], "figures": [{"id": "FIGURE:M:BAD"}]}]}]}
    canonical = {"entities": [
        {"id": "CHAPTER:M:CH_01", "type": "CHAPTER", "domain": "manual", "universe": "manuals", "specs": {"PageRange": [10, 20]}},
        {"id": "FIGURE:M:BAD", "type": "FIGURE", "domain": "manual", "universe": "manuals", "parent_chapter_id": "CHAPTER:M:CH_01", "source_document": "DOC:M:1", "source_page": 12, "source_text": "Figure 1", "extraction_method": "test", "confidence": 1.5}
    ], "edges": [{"from": "CHAPTER:M:CH_01", "to": "FIGURE:M:BAD", "rel": "HAS_FIGURE"}]}
    errors, _ = validate(structure, canonical)
    assert any("invalid source artifact id" in e for e in errors)
    assert any("invalid confidence provenance" in e for e in errors)
