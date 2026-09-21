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


def main() -> int:
    path = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
    if not path.exists():
        print(f"FAIL: missing {path}")
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical_path = ROOT / "data" / "rdso_canonical_kg.json"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8")) if canonical_path.exists() else None
    errors = []
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
    if errors:
        print(f"FAIL: {len(errors)} hierarchy issue(s)")
        for error in errors[:50]:
            print(f"  - {error}")
        return 1
    print("PASS: deterministic Manual source-heading hierarchy is structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
