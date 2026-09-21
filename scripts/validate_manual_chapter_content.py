#!/usr/bin/env python3
"""Validate authoritative manual chapter boundaries and extracted content ownership."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"

sys.path.insert(0, str(ROOT / "scripts"))
from ingest_all_manual_chapters import MANUAL_CHAPTER_REGISTRY  # noqa: E402


def validate_payload(payload: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    manuals = payload.get("manuals")
    if not isinstance(manuals, list):
        return ["payload.manuals must be a list"], warnings

    expected_ids = set(MANUAL_CHAPTER_REGISTRY)
    actual_ids = {m.get("document_id") for m in manuals}
    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    if missing:
        errors.append(f"missing authoritative manuals: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected manuals in extracted payload: {', '.join(extra)}")

    seen_chapter_ids: set[str] = set()
    seen_clause_owners: dict[str, str] = {}
    for manual in manuals:
        doc_id = manual.get("document_id")
        registry = MANUAL_CHAPTER_REGISTRY.get(doc_id)
        if not registry:
            continue

        chapters = manual.get("chapters")
        if not isinstance(chapters, list):
            errors.append(f"{doc_id}: chapters must be a list")
            continue

        expected = registry["chapters"]
        if len(chapters) != len(expected):
            errors.append(
                f"{doc_id}: expected {len(expected)} chapters, found {len(chapters)}"
            )

        by_num = {c.get("chapter_number"): c for c in chapters}
        expected_nums = [c["num"] for c in expected]
        actual_nums = sorted(n for n in by_num if isinstance(n, int))
        if actual_nums != expected_nums:
            errors.append(
                f"{doc_id}: chapter numbering mismatch; expected {expected_nums}, found {actual_nums}"
            )

        ranges: list[tuple[int, int, int]] = []
        for spec in expected:
            num = spec["num"]
            ch = by_num.get(num)
            if not ch:
                errors.append(f"{doc_id}: missing chapter {num}")
                continue

            expected_id = f"CHAPTER:{registry['alias']}:CH_{num:02d}"
            chapter_id = ch.get("chapter_id")
            if chapter_id != expected_id:
                errors.append(
                    f"{doc_id}: chapter {num} has invalid chapter_id {chapter_id!r}; expected {expected_id!r}"
                )
            if chapter_id in seen_chapter_ids:
                errors.append(f"duplicate chapter ownership: {chapter_id}")
            seen_chapter_ids.add(chapter_id)

            if ch.get("parent_manual_id") != doc_id:
                errors.append(f"{chapter_id}: parent_manual_id does not match manual")
            if ch.get("universe") != "manuals":
                errors.append(f"{chapter_id}: universe must be 'manuals'")
            if ch.get("order") != num:
                errors.append(f"{chapter_id}: order must equal chapter number")
            if ch.get("structure_status") != "STRUCTURE_VERIFIED":
                errors.append(f"{chapter_id}: structure_status is not STRUCTURE_VERIFIED")

            page_range = ch.get("page_range")
            expected_range = [spec["page_start"], spec["page_end"]]
            if page_range != expected_range:
                errors.append(
                    f"{chapter_id}: page_range {page_range!r} != registry {expected_range!r}"
                )
            if (
                not isinstance(page_range, list)
                or len(page_range) != 2
                or not all(isinstance(x, int) for x in page_range)
                or page_range[0] > page_range[1]
            ):
                errors.append(f"{chapter_id}: invalid page_range {page_range!r}")
            else:
                ranges.append((num, page_range[0], page_range[1]))

            clauses = ch.get("clauses", [])
            if not isinstance(clauses, list):
                errors.append(f"{chapter_id}: clauses must be a list")
                continue

            seen_clause_ids: set[str] = set()
            for clause in clauses:
                cid = clause.get("clause_id")
                if not cid:
                    errors.append(f"{chapter_id}: clause without clause_id")
                    continue
                if cid in seen_clause_ids:
                    errors.append(f"{chapter_id}: duplicate clause_id {cid}")
                seen_clause_ids.add(cid)
                previous_owner = seen_clause_owners.get(cid)
                if previous_owner and previous_owner != chapter_id:
                    errors.append(f"{cid}: assigned to multiple chapters ({previous_owner}, {chapter_id})")
                seen_clause_owners[cid] = chapter_id

                page = clause.get("page_number")
                if not isinstance(page, int):
                    errors.append(f"{cid}: page_number must be an integer")
                    continue
                if page_range and not (page_range[0] <= page <= page_range[1]):
                    errors.append(
                        f"{cid}: page {page} falls outside owning chapter {chapter_id} range {page_range}"
                    )

                if not cid.startswith(f"CLAUSE:{registry['alias']}:"):
                    errors.append(
                        f"{cid}: clause id does not belong to manual alias {registry['alias']}"
                    )

        # Overlap audit: a one-page boundary overlap can be a deliberate TOC/page
        # convention (e.g. a chapter ending and the next chapter starting on the same page).
        # Wider overlap is treated as an error because it makes page-based ownership ambiguous.
        ranges.sort()
        for prev, cur in zip(ranges, ranges[1:]):
            if cur[1] <= prev[2]:
                overlap_start = cur[1]
                overlap_end = min(prev[2], cur[2])
                overlap_pages = overlap_end - overlap_start + 1
                if overlap_pages == 1 and prev[2] == cur[1]:
                    warnings.append(
                        f"{doc_id}: chapter {prev[0]} and {cur[0]} share boundary page {overlap_start}; "
                        "accepted as a one-page chapter-boundary overlap"
                    )
                else:
                    errors.append(
                        f"{doc_id}: chapter {prev[0]} range {prev[1:]} overlaps chapter {cur[0]} range {cur[1:]}"
                    )

        for spec in expected:
            ch = by_num.get(spec["num"])
            if ch is not None and not ch.get("clauses"):
                warnings.append(
                    f"{doc_id}: chapter {spec['num']} has zero extracted clauses; "
                    "verify source extraction coverage"
                )

    return errors, warnings


def main() -> int:
    if not INTERMEDIATE.exists():
        print(f"[ERROR] Missing authoritative extraction: {INTERMEDIATE}")
        return 1

    with INTERMEDIATE.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    errors, warnings = validate_payload(payload)
    for warning in warnings:
        print(f"[WARN] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")

    print(
        f"[SUMMARY] manual chapter/content validation: "
        f"{'PASS' if not errors else 'FAIL'}; errors={len(errors)} warnings={len(warnings)}"
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
