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
SECTION_RE = re.compile(r"^SECTION:[^:]+:SEC_.+$")
SUBSECTION_RE = re.compile(r"^SUBSECTION:[^:]+:SEC_.+$")
ARTIFACT_RE = re.compile(r"^(TABLE|FIGURE|EVIDENCE):[^:]+:CH_\d{2}:P\d{4}:\d{2}_[0-9a-f]{8}$")


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
    seen_structural_ids: dict[str, str] = {}
    child_edges: dict[str, list[dict]] = {}
    relation_parent_types = {
        "HAS_SECTION": {"CHAPTER", "SECTION", "SUBSECTION"},
        "HAS_CLAUSE": {"CHAPTER", "SUBSECTION"},
        "HAS_TABLE": {"CHAPTER", "SECTION", "SUBSECTION"},
        "HAS_FIGURE": {"CHAPTER", "SECTION", "SUBSECTION"},
        "HAS_EVIDENCE": {"CHAPTER", "SECTION", "SUBSECTION"},
    }
    for edge in edges:
        rel = edge.get("rel")
        if rel not in ALLOWED:
            continue
        parent = edge.get("from")
        child = edge.get("to")
        if parent not in entities or child not in manual_ids:
            continue
        parent_node = entities[parent]
        child_node = entities[child]
        if child_node.get("type") in {"TABLE", "FIGURE", "EVIDENCE"}:
            if not ARTIFACT_RE.match(child):
                errors.append(f"{child}: invalid source artifact id")
            previous_type = seen_structural_ids.get(child)
            if previous_type and previous_type != child_node.get("type"):
                errors.append(f"{child}: structural artifact type collision")
            seen_structural_ids[child] = child_node.get("type")
        parent_chapter = (
            parent_node.get("parent_chapter_id")
            if parent_node.get("type") in {"SECTION", "SUBSECTION"}
            else (parent if parent in chapters else None)
        )
        if parent_chapter not in chapters:
            errors.append(f"{child}: structural parent {parent} is not owned by a canonical chapter")
            continue
        allowed_parents = relation_parent_types[rel]
        if parent_node.get("type") not in allowed_parents:
            errors.append(
                f"{parent} -> {child}: relation {rel} is invalid for parent type {parent_node.get('type')}"
            )
        child_edges.setdefault(child, []).append(edge)

        if parent in chapters:
            previous = ownership.get(child)
            if previous and previous != parent:
                errors.append(f"{child}: multiple chapter owners ({previous}, {parent})")
            ownership[child] = parent

        if child_node.get("domain") != "manual" or child_node.get("universe") != "manuals":
            errors.append(f"{child}: structural child is not isolated in manuals universe")
        for field in ("source_document", "source_text", "extraction_method"):
            if not child_node.get(field):
                errors.append(f"{child}: missing {field} provenance")
        if child_node.get("source_page") is None:
            errors.append(f"{child}: missing source_page provenance")
        if child_node.get("type") in {"TABLE", "FIGURE", "EVIDENCE"}:
            confidence = child_node.get("confidence")
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                errors.append(f"{child}: invalid confidence provenance")

        page_range = (chapters[parent_chapter].get("specs") or {}).get("PageRange")
        page = child_node.get("source_page")
        if isinstance(page_range, list) and len(page_range) == 2 and isinstance(page, int):
            if not page_range[0] <= page <= page_range[1]:
                errors.append(f"{child}: source_page {page} outside chapter {parent_chapter} range {page_range}")

        declared_parent = child_node.get("parent_chapter_id")
        if declared_parent and declared_parent != parent_chapter:
            errors.append(f"{child}: parent_chapter_id {declared_parent} disagrees with chapter owner {parent_chapter}")
        if child_node.get("type") in {"SECTION", "SUBSECTION"} and not declared_parent:
            errors.append(f"{child}: missing parent_chapter_id")
        if child_node.get("type") in {"SECTION", "SUBSECTION"} and child_node.get("source_heading"):
            if not child_node.get("source_heading_reference") or child_node.get("source_heading_page") is None:
                errors.append(f"{child}: incomplete source heading provenance")
            heading_confidence = child_node.get("heading_confidence")
            if not isinstance(heading_confidence, (int, float)) or not 0 <= heading_confidence <= 1:
                errors.append(f"{child}: invalid heading confidence provenance")

    # Every source-derived structural child must have exactly one direct chapter
    # owner, even when it is nested beneath Section/Subsection for UI traversal.
    for child, node in entities.items():
        if node.get("domain") != "manual" or node.get("universe") != "manuals":
            continue
        if node.get("type") not in {"SECTION", "SUBSECTION", "CLAUSE", "TABLE", "FIGURE", "EVIDENCE"}:
            continue

        # Sections/subsections form the navigable hierarchy and may be nested.
        # Their chapter ownership is carried by parent_chapter_id; only terminal
        # structural children require an explicit Chapter -> child ownership edge.
        if node.get("type") in {"SECTION", "SUBSECTION"}:
            declared_owner = node.get("parent_chapter_id")
            if declared_owner not in chapters:
                errors.append(f"{child}: expected exactly one chapter owner, found {declared_owner!r}")
            continue

        owners = []
        for edge in edges:
            if edge.get("rel") not in ALLOWED or edge.get("to") != child:
                continue
            parent = entities.get(edge.get("from"))
            if parent and parent.get("type") == "CHAPTER":
                owners.append(parent.get("id"))
        if len(set(owners)) != 1:
            errors.append(f"{child}: expected exactly one direct chapter owner, found {sorted(set(owners))}")


    for entity_id, node in entities.items():
        if node.get("type") == "SECTION" and not SECTION_RE.match(entity_id):
            errors.append(f"{entity_id}: invalid canonical section id")
        if node.get("type") == "SUBSECTION" and not SUBSECTION_RE.match(entity_id):
            errors.append(f"{entity_id}: invalid canonical subsection id")

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

    for manual in structure.get("manuals", []):
        for chapter in manual.get("chapters", []):
            for key, expected_type in (("tables", "TABLE"), ("figures", "FIGURE"), ("evidence", "EVIDENCE")):
                for artifact in chapter.get(key, []) or []:
                    aid = artifact.get("id")
                    if aid:
                        node = entities.get(aid)
                        if node is None:
                            errors.append(f"{aid}: authoritative {expected_type.lower()} missing from canonical KG")
                        elif node.get("type") != expected_type:
                            errors.append(f"{aid}: expected type {expected_type}, found {node.get('type')}")

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
