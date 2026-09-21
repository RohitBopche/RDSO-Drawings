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
