import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ingest_all_manual_chapters import MANUAL_CHAPTER_REGISTRY
from validate_manual_chapter_content import validate_payload


def make_payload():
    manuals = []
    for doc_id, registry in MANUAL_CHAPTER_REGISTRY.items():
        chapters = []
        for spec in registry["chapters"]:
            chapters.append(
                {
                    "chapter_id": f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}",
                    "chapter_number": spec["num"],
                    "title": spec["title"],
                    "page_range": [spec["page_start"], spec["page_end"]],
                    "parent_manual_id": doc_id,
                    "universe": "manuals",
                    "order": spec["num"],
                    "structure_status": "STRUCTURE_VERIFIED",
                    "clauses": [],
                }
            )
        manuals.append(
            {
                "document_id": doc_id,
                "alias": registry["alias"],
                "title": registry["title"],
                "universe": "manuals",
                "total_chapters": len(chapters),
                "chapters": chapters,
            }
        )
    return {"manuals": manuals}


def test_authoritative_structure_passes_with_empty_content_warnings():
    errors, warnings = validate_payload(make_payload())
    assert errors == []
    assert warnings


def test_clause_must_stay_inside_owning_chapter_page_range():
    payload = make_payload()
    chapter = payload["manuals"][0]["chapters"][0]
    chapter["clauses"] = [
        {
            "clause_id": "CLAUSE:IRPWM:PARA_101",
            "page_number": chapter["page_range"][1] + 1,
            "verbatim_text": "bad ownership",
        }
    ]
    errors, _ = validate_payload(payload)
    assert any("falls outside owning chapter" in error for error in errors)


def test_duplicate_chapter_id_is_rejected():
    payload = make_payload()
    first = payload["manuals"][0]["chapters"][0]
    second = payload["manuals"][0]["chapters"][1]
    second["chapter_id"] = first["chapter_id"]
    errors, _ = validate_payload(payload)
    assert any("duplicate chapter ownership" in error for error in errors)


def test_wide_page_overlap_is_rejected():
    payload = make_payload()
    chapters = payload["manuals"][0]["chapters"]
    chapters[1]["page_range"] = [chapters[0]["page_range"][0], chapters[0]["page_range"][1]]
    errors, _ = validate_payload(payload)
    assert any("overlaps chapter" in error for error in errors)


def test_clause_cannot_belong_to_two_chapters():
    payload = make_payload()
    clause = {
        "clause_id": "CLAUSE:IRPWM:PARA_101",
        "page_number": 32,
        "verbatim_text": "same clause",
    }
    payload["manuals"][0]["chapters"][0]["clauses"] = [clause]
    payload["manuals"][0]["chapters"][1]["clauses"] = [dict(clause, page_number=62)]
    errors, _ = validate_payload(payload)
    assert any("assigned to multiple chapters" in error for error in errors)
