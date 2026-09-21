#!/usr/bin/env python3
"""Validate deterministic Manual source-heading hierarchy and ownership."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resolve_manual_hierarchy import resolve_heading_sequence


def main() -> int:
    path = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
    if not path.exists():
        print(f"FAIL: missing {path}")
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    checked = 0
    for manual in payload.get("manuals", []):
        for chapter in manual.get("chapters", []):
            checked += 1
            headings, heading_errors = resolve_heading_sequence(
                chapter.get("headings", []) or [], chapter.get("page_range", [])
            )
            errors.extend(f"{chapter.get('chapter_id')}: {e}" for e in heading_errors)
            refs = [h["reference"] for h in headings]
            if len(refs) != len(set(refs)):
                errors.append(f"{chapter.get('chapter_id')}: duplicate references remain after resolution")
            for heading in headings:
                if heading.get("heading_depth", heading.get("depth")) != heading.get("depth"):
                    errors.append(f"{chapter.get('chapter_id')}: inconsistent heading depth for {heading['reference']}")

    print(f"Checked {checked} manual chapters.")
    if errors:
        print(f"FAIL: {len(errors)} hierarchy issue(s)")
        for error in errors[:50]:
            print(f"  - {error}")
        return 1
    print("PASS: deterministic Manual source-heading hierarchy is structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
