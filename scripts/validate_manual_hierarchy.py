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




def _coverage_audit(chapter: dict) -> tuple[list[str], list[str], dict]:
    """Return hard errors, warnings, and deterministic coverage metrics."""
    page_start, page_end = chapter.get("page_range", [None, None])
    pages = sorted(set(chapter.get("pages_seen", []) or []))
    headings = chapter.get("headings", []) or []
    refs = [h.get("reference") for h in headings if h.get("reference")]
    malformed = [r for r in refs if not re.fullmatch(r"\d+(?:\.\d+){0,2}", str(r)) and not re.match(r"^(ANNEXURE|APPENDIX|SCHEDULE|TABLE)", str(r), re.I)]
    errors = []
    warnings = []
    if page_start is not None and page_end is not None:
        out_of_range = [p for p in pages if not isinstance(p, int) or p < page_start or p > page_end]
        if out_of_range:
            errors.append(f"pages_seen outside declared range: {out_of_range[:10]}")
        expected = max(0, page_end - page_start + 1)
        missing = expected - len(pages)
        if missing > 0:
            warnings.append(f"{missing} declared page(s) not observed in extraction")
    if malformed:
        errors.append(f"malformed heading reference(s): {malformed[:10]}")
    if len(headings) == 0:
        warnings.append("zero source headings")
    elif len(headings) == 1:
        warnings.append("only one source heading")
    if refs and len(refs) != len(set(refs)):
        errors.append("duplicate source heading references")
    pages_with_headings = sorted({h.get("source_page") for h in headings if isinstance(h.get("source_page"), int)})
    metrics = {
        "pages_expected": max(0, page_end - page_start + 1) if page_start is not None and page_end is not None else None,
        "pages_seen": len(pages),
        "pages_with_headings": len(pages_with_headings),
        "headings": len(headings),
        "clauses": len(chapter.get("clauses", []) or []),
        "tables": len(chapter.get("tables", []) or []),
        "figures": len(chapter.get("figures", []) or []),
        "evidence": len(chapter.get("evidence", []) or []),
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
        for chapter in manual.get("chapters", []):
            manual_counts["chapters"] += 1
            headings, heading_errors = resolve_heading_sequence(chapter.get("headings", []) or [], chapter.get("page_range", []))
            chapter_errors = [f"{chapter.get('chapter_id')}: {e}" for e in heading_errors]
            cov_errors, cov_warnings, metrics = _coverage_audit(chapter)
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

        manual_rows.append({"manual_id": manual.get("document_id"), "alias": manual.get("alias"), **manual_counts})

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

