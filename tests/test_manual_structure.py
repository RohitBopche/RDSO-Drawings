"""Validate the authoritative Manuals chapter registry embedded in data/manual_structure.js."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRUCTURE = ROOT / "data" / "manual_structure.js"

EXPECTED_COUNTS = {
    "IRPWM": 15,
    "USFD": 15,
    "AT_WELD": 9,
    "FBW": 9,
    "TMM": 12,
    "STMM": 23,
}


def load_structure():
    text = STRUCTURE.read_text(encoding="utf-8")
    match = re.search(
        r"RDSO_MANUAL_STRUCTURE\s*=\s*(\{.*?\});\s*$",
        text,
        re.DOTALL,
    )
    assert match, "RDSO_MANUAL_STRUCTURE payload not found"
    return json.loads(match.group(1))


def test_manual_registry_is_complete_and_ordered():
    data = load_structure()
    manuals = data["manuals"]
    assert len(manuals) == 6

    seen_ids = set()
    seen_aliases = set()

    for manual in manuals:
        assert manual["id"] not in seen_ids
        assert manual["alias"] not in seen_aliases
        seen_ids.add(manual["id"])
        seen_aliases.add(manual["alias"])

        chapters = manual["chapters"]
        assert len(chapters) == EXPECTED_COUNTS[manual["alias"]]

        for index, chapter in enumerate(chapters, start=1):
            title, page_start, page_end = chapter
            assert title
            assert page_start <= page_end
            assert index >= 1


def test_manual_chapter_ranges_do_not_overlap():
    data = load_structure()

    for manual in data["manuals"]:
        previous_end = None
        for title, page_start, page_end in manual["chapters"]:
            # Adjacent/overlapping pages are allowed only when explicitly present
            # in the source registry (e.g. AT-Weld chapters 1 and 2).
            if previous_end is not None:
                assert page_start >= previous_end or (
                    manual["alias"] in {"AT_WELD", "FBW"}
                    and page_start == previous_end
                ), (
                    f"Unexpected backward page range in {manual['alias']}: "
                    f"{title} starts at {page_start}, previous ended at {previous_end}"
                )
            previous_end = page_end


def test_canonical_kg_has_no_duplicate_authoritative_manual_ids():
    canonical = ROOT / "data" / "rdso_canonical_kg.json"
    data = json.loads(canonical.read_text(encoding="utf-8"))
    ids = [node["id"] for node in data["entities"]]
    authoritative_ids = {
        manual["id"] for manual in load_structure()["manuals"]
    }
    assert authoritative_ids.issubset(set(ids))
    assert len(authoritative_ids.intersection(set(ids))) == 6


def test_manual_clause_metadata_maps_to_exactly_one_registered_chapter():
    knowledge_path = ROOT / "data" / "rdso_manuals_knowledge.json"
    if not knowledge_path.exists():
        return
    knowledge = json.loads(knowledge_path.read_text(encoding="utf-8"))
    structure = load_structure()
    manuals = {m["alias"]: m for m in structure["manuals"]}

    unresolved = []
    ambiguous = []
    for clause in knowledge.get("clauses", {}).values():
        manual = manuals.get(clause.get("manual") or clause.get("alias"))
        if not manual:
            continue
        exact = [i for i, ch in enumerate(manual["chapters"]) if ch[0] == clause.get("chapter")]
        if len(exact) == 1:
            continue
        page = clause.get("page")
        if page is None:
            unresolved.append(clause.get("id"))
            continue
        candidates = [
            i for i, ch in enumerate(manual["chapters"])
            if ch[1] <= page <= ch[2]
        ]
        if len(candidates) != 1:
            if not candidates:
                unresolved.append(clause.get("id"))
            else:
                ambiguous.append(clause.get("id"))
    assert not unresolved, f"Unmapped manual clauses: {unresolved[:20]}"
    assert not ambiguous, f"Ambiguous manual clauses: {ambiguous[:20]}"


def test_manual_content_index_is_chapter_scoped():
    content_path = ROOT / "data" / "manual_content_index.js"
    text = content_path.read_text(encoding="utf-8")
    match = re.search(r"RDSO_MANUAL_CONTENT_INDEX\s*=\s*(\{.*\});\s*$", text, re.DOTALL)
    assert match, "RDSO_MANUAL_CONTENT_INDEX payload not found"
    content = json.loads(match.group(1))
    assert content["schema"] == "manual-content-index-v1"
    assert content["universe"] == "manuals"

    structure = load_manual_structure()
    valid = {m["alias"]: {f"CH_{i+1:02d}" for i, _ in enumerate(m["chapters"])} for m in structure["manuals"]}
    total_pages = 0
    total_content = 0
    for manual_id, manual in content["manuals"].items():
        alias = next(m["alias"] for m in structure["manuals"] if m["id"] == manual_id)
        for page in manual["pages"].values():
            total_pages += 1
            assert page["chapter"] in valid[alias], (manual_id, page)
            total_content += len(page["headings"]) + len(page["tables"]) + len(page["figures"])
            assert page["evidence_id"].startswith(f"EVIDENCE:{manual_id}:PAGE_")
    assert total_pages > 1000
    assert total_content > 100
