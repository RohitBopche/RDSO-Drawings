#!/usr/bin/env python3
"""Resolve deterministic Manual -> Section -> Subsection hierarchy.

This stage is deliberately non-LLM and source-order driven. It consumes the
authoritative manual chapter extraction and enriches the compact canonical KG.
Drawing entities/edges are left untouched and no cross-universe edges are created.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
CANONICAL = ROOT / "data" / "rdso_canonical_kg.json"

NUMERIC_REF = re.compile(r"^(\d+(?:\.\d+)*)$")
ANNEX_REF = re.compile(r"^(ANNEXURE|APPENDIX|SCHEDULE|TABLE)\s*[-:]?\s*([A-Z0-9IVX.-]+)$", re.I)


def heading_kind(reference: str) -> tuple[str, int]:
    ref = reference.strip()
    if NUMERIC_REF.fullmatch(ref):
        depth = ref.count(".") + 1
        return ("SECTION" if depth == 1 else "SUBSECTION", depth)
    if ANNEX_REF.fullmatch(ref):
        return ("ANNEXURE", 1)
    return ("SECTION", 1)


def numeric_parent(reference: str) -> str | None:
    if not NUMERIC_REF.fullmatch(reference):
        return None
    parts = reference.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else None


def heading_sort_key(reference: str):
    if NUMERIC_REF.fullmatch(reference):
        return (0, tuple(int(x) for x in reference.split(".")))
    return (1, reference.upper())


def resolve_heading_sequence(headings: list[dict], page_range: list[int]) -> tuple[list[dict], list[str]]:
    """Normalize, validate and annotate source headings in source order."""
    errors: list[str] = []
    normalized: list[dict] = []
    seen: set[str] = set()

    for order, raw in enumerate(headings, 1):
        ref = str(raw.get("reference", "")).strip()
        title = str(raw.get("title", "")).strip()
        page = raw.get("source_page", raw.get("page_number"))
        if not ref or not title:
            errors.append(f"heading {order}: reference/title missing")
            continue
        if ref in seen:
            errors.append(f"duplicate heading reference: {ref}")
            continue
        seen.add(ref)
        if not isinstance(page, int):
            errors.append(f"{ref}: source page is not an integer")
            continue
        if page_range and not (page_range[0] <= page <= page_range[1]):
            errors.append(f"{ref}: page {page} outside chapter range {page_range}")
        kind, depth = heading_kind(ref)
        parent = numeric_parent(ref)
        normalized.append({
            **raw,
            "reference": ref,
            "title": title,
            "heading_kind": kind,
            "depth": depth,
            "order": order,
            "parent_heading_ref": parent,
        })

    numeric = [h for h in normalized if NUMERIC_REF.fullmatch(h["reference"])]
    for current in numeric:
        parent = current["parent_heading_ref"]
        if parent:
            parent_index = next((i for i, h in enumerate(normalized) if h["reference"] == parent), -1)
            current_index = next((i for i, h in enumerate(normalized) if h["reference"] == current["reference"]), -1)
            if parent_index >= 0 and parent_index >= current_index:
                errors.append(f"{current['reference']}: parent {parent} appears after child")
            current["parent_resolution"] = "SOURCE_HEADING" if parent_index >= 0 else "CHAPTER_FALLBACK"
            current["parent_available_in_source"] = parent_index >= 0
            if parent_index < 0:
                current["parent_missing_reason"] = "source_parent_not_extracted"
        else:
            current["parent_resolution"] = "CHAPTER"
            current["parent_available_in_source"] = True
        previous = None
        for h in numeric:
            if h is current:
                break
            previous = h
        if previous and current["depth"] > previous["depth"] + 1:
            errors.append(f"{current['reference']}: hierarchy depth jumps from {previous['reference']}")

    # Source order is authoritative; reject backward numeric references within
    # the same heading family, but allow annexures/appendices after numbered content.
    last_numeric = None
    for h in normalized:
        if not NUMERIC_REF.fullmatch(h["reference"]):
            continue
        key = tuple(int(x) for x in h["reference"].split("."))
        if last_numeric is not None and key < last_numeric:
            errors.append(f"{h['reference']}: numeric heading order moves backward")
        last_numeric = key

    return normalized, errors


def node_id(prefix: str, alias: str, chapter_id: str, reference: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_]", "_", chapter_id)
    ref = re.sub(r"[^A-Za-z0-9_]", "_", reference)
    return f"{prefix}:{alias}:{token}:SEC_{ref}"


def resolve_canonical_graph(intermediate: dict, canonical: dict) -> tuple[dict, list[str]]:
    """Resolve valid authoritative source headings into an in-memory canonical KG."""
    entities = canonical.get("entities", [])
    edges = canonical.get("edges", [])
    facts = canonical.get("facts", [])
    by_id = {e.get("id"): e for e in entities if e.get("id")}

    def add_edge(frm, to, rel, evidence, manual_id, page, region):
        if any(e.get("from") == frm and e.get("to") == to and e.get("rel") == rel for e in edges):
            return
        edges.append({"from": frm, "to": to, "rel": rel, "rationale": evidence[:250]})
        facts.append({
            "id": f"fact_{len(facts) + 1:04d}", "subject_id": frm, "predicate": rel, "object_id": to,
            "source": {"drawing_id": manual_id, "revision": "MANUAL_STRUCTURE", "region": region, "crop": ""},
            "confidence": 1.0, "status": "VERIFIED",
            "extraction_method": "deterministic_manual_source_heading", "evidence_text": evidence[:500],
        })


    errors: list[str] = []
    resolved_count = 0

    for manual in intermediate.get("manuals", []):
        manual_id = manual.get("document_id")
        alias = manual.get("alias", "")
        for chapter in manual.get("chapters", []):
            chapter_id = chapter.get("chapter_id")
            page_range = chapter.get("page_range", [])
            headings, heading_errors = resolve_heading_sequence(chapter.get("headings", []) or [], page_range)
            errors.extend(f"{chapter_id}: {e}" for e in heading_errors)

            # Only structurally valid heading sequences are materialized. Existing
            # clause-derived nodes remain as fallback evidence, not as replacements.
            if heading_errors:
                continue

            previous_id = None
            for heading in headings:
                ref = heading["reference"]
                kind = heading["heading_kind"]
                prefix = "SECTION" if kind in {"SECTION", "ANNEXURE"} else "SUBSECTION"
                hid = node_id(prefix, alias, chapter_id, ref)
                parent_ref = heading.get("parent_heading_ref")
                parent_id = None
                if parent_ref:
                    parent_kind, _ = heading_kind(parent_ref)
                    parent_prefix = "SECTION" if parent_kind in {"SECTION", "ANNEXURE"} else "SUBSECTION"
                    parent_id = node_id(parent_prefix, alias, chapter_id, parent_ref)

                page = heading.get("source_page", heading.get("page_number"))
                provenance = {
                    "source_document": manual_id,
                    "source_page": page,
                    "source_section": ref,
                    "source_text": heading.get("source_text", ""),
                    "confidence": heading.get("confidence", 0.92),
                    "extraction_method": heading.get("extraction_method", "deterministic_numbered_source_heading"),
                    "chapter_id": chapter_id,
                    "chapter_page_range": page_range,
                    "heading_kind": kind,
                    "depth": heading["depth"],
                    "order": heading["order"],
                    "parent_heading_ref": parent_ref,
                    "parent_resolution": heading.get("parent_resolution", "CHAPTER"),
                    "parent_available_in_source": heading.get("parent_available_in_source", True),
                }
                entity = by_id.get(hid)
                if entity is None:
                    entity = {
                        "id": hid,
                        "label": f"{kind.title()} {ref} — {heading['title']}",
                        "type": prefix,
                        "domain": "manual",
                        "universe": "manuals",
                        "color": "#00f5d4",
                        "desc": heading["title"],
                        "specs": {},
                        "twinAsset": None,
                        "x": 0,
                        "y": 7 if prefix == "SECTION" else 6.5,
                        "z": 0,
                        "alt": 13,
                    }
                    entities.append(entity)
                    by_id[hid] = entity
                entity.update({
                    "label": f"{kind.title()} {ref} — {heading['title']}",
                    "source_document": manual_id,
                    "source_page": page,
                    "source_section": ref,
                    "source_text": heading.get("source_text", ""),
                    "confidence": heading.get("confidence", 0.92),
                    "extraction_method": heading.get("extraction_method", "deterministic_numbered_source_heading"),
                    "parent_chapter_id": chapter_id,
                    "heading_kind": kind,
                    "heading_depth": heading["depth"],
                    "heading_order": heading["order"],
                    "parent_heading_ref": parent_ref,
                    "parent_resolution": heading.get("parent_resolution", "CHAPTER"),
                    "parent_available_in_source": heading.get("parent_available_in_source", True),
                    "provenance": provenance,
                    "specs": {
                        **(entity.get("specs") or {}),
                        "Reference": ref,
                        "Page": page,
                        "Chapter": chapter.get("title", ""),
                        "Manual": manual_id,
                        "Structure Status": (
                            "AUTHORITATIVE_SOURCE_HEADING"
                            if heading.get("parent_resolution") != "CHAPTER_FALLBACK"
                            else "AUTHORITATIVE_SOURCE_HEADING_ORPHAN"
                        ),
                        "Parent Resolution": heading.get("parent_resolution", "CHAPTER"),
                        "Parent Available In Source": heading.get("parent_available_in_source", True),
                    },
                })

                owner = parent_id or chapter_id
                rel = "HAS_SECTION"
                add_edge(
                    owner,
                    hid,
                    rel,
                    (
                        f"Source heading {ref}: {heading['title']}"
                        if parent_id
                        else f"Source heading {ref}: {heading['title']} "
                             f"(parent {parent_ref or 'none'} unavailable; chapter fallback)"
                    ),
                    manual_id,
                    page,
                    ref,
                )
                previous_id = hid
                resolved_count += 1

            # Re-parent clauses to the deepest matching heading by reference.
            structural = [h for h in headings if NUMERIC_REF.fullmatch(h["reference"])]
            # Remove only clause-parent edges produced by the fallback numbering
            # hierarchy when an authoritative source heading can own that clause.
            matched_clause_ids = set()
            for clause in chapter.get("clauses", []) or []:
                pref = str(clause.get("para_number", ""))
                matches = [h for h in structural if pref == h["reference"] or pref.startswith(h["reference"] + ".")]
                if matches:
                    matched_clause_ids.add(clause.get("clause_id"))
            if matched_clause_ids:
                structural_ids = {e.get("id") for e in entities if e.get("type") in {"SECTION", "SUBSECTION"} and e.get("universe") == "manuals"}
                edges[:] = [e for e in edges if not (e.get("rel") == "HAS_CLAUSE" and e.get("to") in matched_clause_ids and e.get("from") in structural_ids)]
                facts[:] = [f for f in facts if not (f.get("predicate") == "HAS_CLAUSE" and f.get("object_id") in matched_clause_ids and f.get("subject_id") in structural_ids)]
            for clause in chapter.get("clauses", []) or []:
                cid = clause.get("clause_id")
                pref = str(clause.get("para_number", ""))
                # Preserve authoritative Chapter -> Clause ownership even when
                # the clause is additionally nested under a source heading.
                if cid and cid in by_id:
                    add_edge(
                        chapter_id,
                        cid,
                        "HAS_CLAUSE",
                        f"Clause {pref} belongs to chapter {chapter_id}",
                        manual_id,
                        clause.get("source_page"),
                        pref,
                    )
                matches = [h for h in structural if pref == h["reference"] or pref.startswith(h["reference"] + ".")]
                if not matches:
                    continue
                owner_h = max(matches, key=lambda h: (h["depth"], len(h["reference"])))
                prefix = "SECTION" if owner_h["heading_kind"] == "SECTION" else "SUBSECTION"
                hid = node_id(prefix, alias, chapter_id, owner_h["reference"])
                if hid in by_id:
                    add_edge(hid, cid, "HAS_CLAUSE", f"Clause {pref} belongs to source heading {owner_h['reference']}", manual_id, clause.get("source_page"), pref)

    canonical["entities"] = entities
    canonical["edges"] = edges
    canonical["facts"] = facts
    canonical.setdefault("metadata", {})["manual_hierarchy_resolver"] = "deterministic_source_heading_v1"
    canonical["metadata"]["manual_hierarchy_resolved_headings"] = resolved_count
    return canonical, errors


def main() -> int:
    if not INTERMEDIATE.exists() or not CANONICAL.exists():
        raise SystemExit("Missing manual intermediate or canonical KG")
    intermediate = json.loads(INTERMEDIATE.read_text(encoding="utf-8"))
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    canonical, errors = resolve_canonical_graph(intermediate, canonical)
    CANONICAL.write_text(json.dumps(canonical, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Resolved {canonical.get('metadata', {}).get('manual_hierarchy_resolved_headings', 0)} authoritative manual headings.")
    if errors:
        print(f"Hierarchy warnings/errors: {len(errors)}")
        for error in errors[:50]:
            print(f"  - {error}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
