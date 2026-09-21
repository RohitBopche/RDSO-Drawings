#!/usr/bin/env python3
"""Validate deterministic Manual source-heading hierarchy and ownership."""

from __future__ import annotations

import json
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resolve_manual_hierarchy import resolve_heading_sequence




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
    return errors, warnings, metrics

def main() -> int:
    path = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
    if not path.exists():
        print(f"FAIL: missing {path}")
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical_path = ROOT / "data" / "rdso_canonical_kg.json"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8")) if canonical_path.exists() else None
    errors = []
    warnings = []
    coverage_rows = []
    checked = 0
    canonical_entities = {e.get("id"): e for e in (canonical or {}).get("entities", []) if e.get("id")}
    canonical_edges = (canonical or {}).get("edges", [])
    for manual in payload.get("manuals", []):
        for chapter in manual.get("chapters", []):
            checked += 1
            headings, heading_errors = resolve_heading_sequence(
                chapter.get("headings", []) or [], chapter.get("page_range", [])
            )
            errors.extend(f"{chapter.get('chapter_id')}: {e}" for e in heading_errors)
            cov_errors, cov_warnings, metrics = _coverage_audit(chapter)
            errors.extend(f"{chapter.get('chapter_id')}: {e}" for e in cov_errors)
            warnings.extend(f"{chapter.get('chapter_id')}: {w}" for w in cov_warnings)
            coverage_rows.append((chapter.get('chapter_id'), metrics))
            refs = [h["reference"] for h in headings]
            if len(refs) != len(set(refs)):
                errors.append(f"{chapter.get('chapter_id')}: duplicate references remain after resolution")
            for heading in headings:
                if heading.get("heading_depth", heading.get("depth")) != heading.get("depth"):
                    errors.append(f"{chapter.get('chapter_id')}: inconsistent heading depth for {heading['reference']}")
            if canonical is not None and not heading_errors:
                manual = next((m for m in payload.get("manuals", []) if chapter in m.get("chapters", [])), None)
                alias = (manual or {}).get("alias", "")
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

    print(f"Checked {checked} manual chapters.")
    print("Coverage report:")
    for chapter_id, metrics in coverage_rows:
        print(f"  {chapter_id}: pages {metrics['pages_seen']}/{metrics['pages_expected']}, headings {metrics['headings']}, clauses {metrics['clauses']}, artifacts {metrics['tables']}/{metrics['figures']}/{metrics['evidence']}, first={metrics['first_heading']}, last={metrics['last_heading']}")
    if warnings:
        print(f"WARN: {len(warnings)} coverage warning(s)")
        for warning in warnings[:50]:
            print(f"  - {warning}")
    if errors:
        print(f"FAIL: {len(errors)} hierarchy issue(s)")
        for error in errors[:50]:
            print(f"  - {error}")
        return 1
    print("PASS: deterministic Manual source-heading hierarchy is structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
