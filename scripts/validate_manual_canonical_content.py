#!/usr/bin/env python3
"""Validate authoritative Manual chapter content ownership in the canonical KG."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRUCTURE = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
CANONICAL = ROOT / "data" / "rdso_canonical_kg.json"

ALLOWED = {"HAS_SECTION", "HAS_CLAUSE", "HAS_TABLE", "HAS_FIGURE", "HAS_EVIDENCE"}
CHAPTER_RE = re.compile(r"^CHAPTER:[^:]+:CH_\d{2}$")


def validate(structure: dict, canonical: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    entities = {e.get("id"): e for e in canonical.get("entities", []) if e.get("id")}
    edges = canonical.get("edges", [])
    manual_ids = {
        e["id"] for e in entities.values()
        if e.get("domain") == "manual" or e.get("universe") == "manuals"
    }
    chapters = {
        e["id"]: e for e in entities.values()
        if e.get("type") == "CHAPTER" and e.get("domain") == "manual"
    }

    ownership: dict[str, str] = {}
    for edge in edges:
        if edge.get("rel") not in ALLOWED:
            continue
        parent = edge.get("from")
        child = edge.get("to")
        if parent not in chapters or child not in manual_ids:
            continue
        previous = ownership.get(child)
        if previous and previous != parent:
            errors.append(f"{child}: multiple chapter owners ({previous}, {parent})")
        ownership[child] = parent

        node = entities[child]
        if node.get("domain") != "manual" or node.get("universe") != "manuals":
            errors.append(f"{child}: structural child is not isolated in manuals universe")
        if not node.get("source_document"):
            errors.append(f"{child}: missing source_document provenance")
        if node.get("source_page") is None:
            errors.append(f"{child}: missing source_page provenance")
        if not node.get("extraction_method"):
            errors.append(f"{child}: missing extraction_method provenance")

        parent_node = chapters[parent]
        page_range = (parent_node.get("specs") or {}).get("PageRange")
        page = node.get("source_page")
        if isinstance(page_range, list) and len(page_range) == 2 and isinstance(page, int):
            if not page_range[0] <= page <= page_range[1]:
                errors.append(f"{child}: source_page {page} outside chapter {parent} range {page_range}")

        declared_parent = node.get("parent_chapter_id")
        if declared_parent and declared_parent != parent:
            errors.append(f"{child}: parent_chapter_id {declared_parent} disagrees with edge owner {parent}")

    for chapter_id in chapters:
        if not CHAPTER_RE.match(chapter_id):
            errors.append(f"{chapter_id}: invalid canonical chapter id")
    if not chapters:
        errors.append("no manual chapter nodes found")

    authoritative_ids = set()
    for manual in structure.get("manuals", []):
        for chapter in manual.get("chapters", []):
            cid = chapter.get("chapter_id")
            for clause in chapter.get("clauses", []) or []:
                clause_id = clause.get("clause_id")
                if clause_id:
                    authoritative_ids.add((cid, clause_id))
                    if clause_id not in entities:
                        errors.append(f"{clause_id}: authoritative clause missing from canonical KG")
                    elif (cid, clause_id) not in {(owner, child) for child, owner in ownership.items()}:
                        errors.append(f"{clause_id}: authoritative chapter ownership edge missing for {cid}")

    for child, owner in ownership.items():
        if child.startswith("CLAUSE:") and (owner, child) not in authoritative_ids:
            warnings.append(f"{child}: canonical clause child is not present in current authoritative extraction")

    return errors, warnings


def main() -> int:
    if not STRUCTURE.exists() or not CANONICAL.exists():
        print("[ERROR] Missing authoritative structure or canonical KG")
        return 1
    with STRUCTURE.open(encoding="utf-8") as f:
        structure = json.load(f)
    with CANONICAL.open(encoding="utf-8") as f:
        canonical = json.load(f)
    errors, warnings = validate(structure, canonical)
    for w in warnings:
        print(f"[WARN] {w}")
    for e in errors:
        print(f"[ERROR] {e}")
    print(f"[SUMMARY] manual canonical content ownership: {'PASS' if not errors else 'FAIL'}; errors={len(errors)} warnings={len(warnings)}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
