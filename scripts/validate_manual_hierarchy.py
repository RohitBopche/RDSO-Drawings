#!/usr/bin/env python3
"""Validate deterministic Manual source-heading hierarchy and ownership."""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resolve_manual_hierarchy import resolve_heading_sequence, heading_kind




def _item_page(item: dict) -> int | None:
    """Return the persisted source page for an extracted item."""
    for key in ("source_page", "page_number", "page"):
        value = item.get(key)
        if isinstance(value, int):
            return value
    return None


def _coverage_audit(chapter: dict, unmapped_pages: list[int] | None = None) -> tuple[list[str], list[str], dict]:
    """Return hard errors, warnings, and deterministic page/content coverage metrics."""
    page_start, page_end = chapter.get("page_range", [None, None])
    pages = sorted({p for p in (chapter.get("pages_seen", []) or []) if isinstance(p, int)})
    headings = chapter.get("headings", []) or []
    clauses = chapter.get("clauses", []) or []
    tables = chapter.get("tables", []) or []
    figures = chapter.get("figures", []) or []
    evidence = chapter.get("evidence", []) or []
    refs = [h.get("reference") for h in headings if h.get("reference")]
    malformed = [r for r in refs if not re.fullmatch(r"\d+(?:\.\d+){0,2}", str(r)) and not re.match(r"^(ANNEXURE|APPENDIX|SCHEDULE|TABLE)", str(r), re.I)]
    errors = []
    warnings = []
    expected_pages = set(range(page_start, page_end + 1)) if page_start is not None and page_end is not None else set()
    seen_pages = set(pages)
    missing_pages = sorted(expected_pages - seen_pages)
    if page_start is not None and page_end is not None:
        out_of_range = [p for p in (chapter.get("pages_seen", []) or []) if not isinstance(p, int) or p < page_start or p > page_end]
        if out_of_range:
            errors.append(f"pages_seen outside declared range: {out_of_range[:10]}")
        if missing_pages:
            warnings.append(f"{len(missing_pages)} declared page(s) not observed in extraction")
    if malformed:
        errors.append(f"malformed heading reference(s): {malformed[:10]}")
    if len(headings) == 0:
        warnings.append("zero source headings")
    elif len(headings) == 1:
        warnings.append("only one source heading")
    if refs and len(refs) != len(set(refs)):
        errors.append("duplicate source heading references")

    def pages_for(items: list[dict]) -> set[int]:
        return {page for item in items if isinstance(item, dict) for page in [_item_page(item)] if page is not None}

    pages_with_headings = pages_for(headings)
    pages_with_clauses = pages_for(clauses)
    pages_with_tables = pages_for(tables)
    pages_with_figures = pages_for(figures)
    pages_with_evidence = pages_for(evidence)
    content_pages = pages_with_headings | pages_with_clauses | pages_with_tables | pages_with_figures | pages_with_evidence
    content_empty_pages = sorted(seen_pages - content_pages)
    unmapped = sorted({p for p in (unmapped_pages or []) if isinstance(p, int)})

    metrics = {
        "pages_expected": len(expected_pages) if expected_pages else None,
        "pages_seen": len(seen_pages),
        "missing_pages": missing_pages,
        "unmapped_pages": unmapped,
        "pages_with_headings": len(pages_with_headings),
        "pages_with_clauses": len(pages_with_clauses),
        "content_empty_pages": content_empty_pages,
        "coverage_ratio": (len(seen_pages & expected_pages) / len(expected_pages)) if expected_pages else None,
        "headings": len(headings),
        "clauses": len(clauses),
        "tables": len(tables),
        "figures": len(figures),
        "evidence": len(evidence),
        "first_heading": refs[0] if refs else None,
        "last_heading": refs[-1] if refs else None,
    }
    if len(headings) > 0 and metrics["pages_with_headings"] == 0:
        errors.append("headings have no valid source-page coverage")
    if errors:
        metrics["coverage_class"] = "MALFORMED"
    elif not headings:
        metrics["coverage_class"] = "NO_SOURCE_HEADINGS"
    elif len(headings) == 1 or len(warnings) > 0:
        metrics["coverage_class"] = "SPARSE"
    else:
        metrics["coverage_class"] = "HEALTHY"
    return errors, warnings, metrics

def audit_manual_corpus(payload: dict, canonical: dict | None = None) -> dict:
    """Return a machine-readable deterministic corpus audit report."""
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict] = []
    manual_rows: list[dict] = []
    class_counts = {"HEALTHY": 0, "SPARSE": 0, "NO_SOURCE_HEADINGS": 0, "MALFORMED": 0}
    canonical_entities = {e.get("id"): e for e in (canonical or {}).get("entities", []) if e.get("id")}
    canonical_edges = (canonical or {}).get("edges", [])

    for manual in payload.get("manuals", []):
        manual_counts = {"chapters": 0, "HEALTHY": 0, "SPARSE": 0, "NO_SOURCE_HEADINGS": 0, "MALFORMED": 0}
        manual_expected_pages: set[int] = set()
        manual_page_seen: set[int] = set()
        manual_missing_pages: set[int] = set()
        manual_page_owners: dict[int, list[str]] = {}
        manual_unmapped_pages = {p for p in (manual.get("unmapped_pages", []) or []) if isinstance(p, int)}
        manual_pages_with_headings: set[int] = set()
        manual_pages_with_clauses: set[int] = set()
        manual_content_empty_pages: set[int] = set()
        for chapter in manual.get("chapters", []):
            manual_counts["chapters"] += 1
            headings, heading_errors = resolve_heading_sequence(chapter.get("headings", []) or [], chapter.get("page_range", []))
            chapter_errors = [f"{chapter.get('chapter_id')}: {e}" for e in heading_errors]
            cov_errors, cov_warnings, metrics = _coverage_audit(chapter)
            page_start, page_end = chapter.get("page_range", [None, None])
            if isinstance(page_start, int) and isinstance(page_end, int) and page_end >= page_start:
                manual_expected_pages.update(range(page_start, page_end + 1))
            chapter_seen_pages = {p for p in (chapter.get("pages_seen", []) or []) if isinstance(p, int)}
            manual_page_seen.update(chapter_seen_pages)
            for page in chapter_seen_pages:
                manual_page_owners.setdefault(page, []).append(str(chapter.get("chapter_id")))
            manual_missing_pages.update(metrics["missing_pages"])
            manual_pages_with_headings.update(
                _item_page(h) for h in (chapter.get("headings", []) or []) if _item_page(h) is not None
            )
            manual_pages_with_clauses.update(
                _item_page(cl) for cl in (chapter.get("clauses", []) or []) if _item_page(cl) is not None
            )
            manual_content_empty_pages.update(metrics["content_empty_pages"])
            chapter_errors.extend(f"{chapter.get('chapter_id')}: {e}" for e in cov_errors)
            chapter_warnings = [f"{chapter.get('chapter_id')}: {w}" for w in cov_warnings]
            errors.extend(chapter_errors)
            warnings.extend(chapter_warnings)
            class_name = metrics["coverage_class"]
            class_counts[class_name] += 1
            manual_counts[class_name] += 1
            row = {"manual_id": manual.get("document_id"), "manual_alias": manual.get("alias"), "chapter_id": chapter.get("chapter_id"), **metrics, "errors": chapter_errors, "warnings": chapter_warnings}
            rows.append(row)

            refs = [h["reference"] for h in headings]
            if len(refs) != len(set(refs)):
                errors.append(f"{chapter.get('chapter_id')}: duplicate references remain after resolution")
            for heading in headings:
                if heading.get("heading_depth", heading.get("depth")) != heading.get("depth"):
                    errors.append(f"{chapter.get('chapter_id')}: inconsistent heading depth for {heading['reference']}")
            if canonical is not None and not heading_errors:
                alias = manual.get("alias", "")
                chapter_id = chapter.get("chapter_id")
                token = re.sub(r"[^A-Za-z0-9_]", "_", str(chapter_id))
                for heading in headings:
                    ref = heading["reference"]
                    kind = heading["heading_kind"]
                    prefix = "SECTION" if kind in {"SECTION", "ANNEXURE"} else "SUBSECTION"
                    hid = f"{prefix}:{alias}:{token}:SEC_{re.sub(r'[^A-Za-z0-9_]', '_', ref)}"
                    entity = canonical_entities.get(hid)
                    if not entity:
                        errors.append(f"{chapter_id}: missing canonical source-heading node {ref}")
                        continue
                    if entity.get("specs", {}).get("Structure Status") != "AUTHORITATIVE_SOURCE_HEADING":
                        errors.append(f"{chapter_id}: canonical heading {ref} is not authoritative")
                    parent = heading.get("parent_heading_ref")
                    owner = chapter_id
                    if parent:
                        pkind, _ = heading_kind(parent)
                        pprefix = "SECTION" if pkind in {"SECTION", "ANNEXURE"} else "SUBSECTION"
                        owner = f"{pprefix}:{alias}:{token}:SEC_{re.sub(r'[^A-Za-z0-9_]', '_', parent)}"
                    if not any(e.get("from") == owner and e.get("to") == hid and e.get("rel") == "HAS_SECTION" for e in canonical_edges):
                        errors.append(f"{chapter_id}: missing canonical HAS_SECTION for heading {ref}")

        manual_rows.append({
            "manual_id": manual.get("document_id"),
            "alias": manual.get("alias"),
            **manual_counts,
            "pages_expected": len(manual_expected_pages),
            "pages_seen": len(manual_page_seen),
            "missing_pages": sorted(manual_expected_pages - manual_page_seen),
            "observed_pages_with_multiple_chapters": sorted(
                page for page, owners in manual_page_owners.items() if len(owners) > 1
            ),
            "observed_page_owner_count": len(manual_page_owners),
            "unmapped_pages": sorted(manual_unmapped_pages),
            "pages_with_headings": len(manual_pages_with_headings),
            "pages_with_clauses": len(manual_pages_with_clauses),
            "content_empty_pages": sorted(manual_content_empty_pages),
            "coverage_ratio": (len(manual_page_seen & manual_expected_pages) / len(manual_expected_pages)) if manual_expected_pages else None,
        })

    return {"schema_version": "manual_hierarchy_audit_v1", "manuals": manual_rows, "chapters": rows, "class_counts": class_counts, "checked_chapters": len(rows), "error_count": len(errors), "warning_count": len(warnings), "errors": errors, "warnings": warnings, "status": "FAIL" if errors else "PASS"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate deterministic Manual source-heading hierarchy and coverage.")
    parser.add_argument("--json-out", type=Path, help="Write the machine-readable corpus audit report to this path.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    path = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
    if not path.exists():
        print(f"FAIL: missing {path}")
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical_path = ROOT / "data" / "rdso_canonical_kg.json"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8")) if canonical_path.exists() else None
    report = audit_manual_corpus(payload, canonical)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
        print(f"Wrote corpus audit report: {args.json_out}")

    print(f"Checked {report['checked_chapters']} manual chapters.")
    print("Coverage report:")
    for row in report["chapters"]:
        print(f"  {row['chapter_id']}: class={row['coverage_class']}, pages {row['pages_seen']}/{row['pages_expected']}, headings {row['headings']}, clauses {row['clauses']}, artifacts {row['tables']}/{row['figures']}/{row['evidence']}, first={row['first_heading']}, last={row['last_heading']}")
    print(f"Coverage classes: {report['class_counts']}")
    if report["warnings"]:
        print(f"WARN: {report['warning_count']} coverage warning(s)")
        for warning in report["warnings"][:50]:
            print(f"  - {warning}")
    if report["errors"]:
        print(f"FAIL: {report['error_count']} hierarchy issue(s)")
        for error in report["errors"][:50]:
            print(f"  - {error}")
        return 1
    print("PASS: deterministic Manual source-heading hierarchy is structurally valid.")
    return 0

