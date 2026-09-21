"""Manual-universe query helpers.

Provides a deterministic, backend-ready query boundary for the Manuals KG.
The helpers intentionally load only authoritative manual structure and manual
domain nodes/edges. Drawing entities are never returned from these queries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STRUCTURE_PATH = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
CANONICAL_PATH = ROOT / "data" / "rdso_canonical_kg.json"


class ManualKG:
    """Read-only query boundary for the isolated Manuals universe."""

    def __init__(self, structure: dict[str, Any], canonical: dict[str, Any]):
        self.structure = structure
        self.entities = {
            e["id"]: e for e in canonical.get("entities", [])
            if e.get("domain") == "manual" or e.get("universe") == "manuals"
        }
        self.edges = [
            e for e in canonical.get("edges", [])
            if e.get("from") in self.entities and e.get("to") in self.entities
        ]
        self.manuals = {
            m["document_id"]: m for m in structure.get("manuals", [])
        }

    @classmethod
    def load(cls) -> "ManualKG":
        with STRUCTURE_PATH.open(encoding="utf-8") as f:
            structure = json.load(f)
        with CANONICAL_PATH.open(encoding="utf-8") as f:
            canonical = json.load(f)
        return cls(structure, canonical)

    def audit_summary(self) -> dict[str, Any]:
        """Return the latest deterministic Manual readiness summary when available."""
        report = self.structure.get("audit_summary")
        if isinstance(report, dict):
            return report
        return {
            "status": "UNAVAILABLE",
            "reason": "manual corpus audit summary is not embedded in the loaded structure",
        }

    def list_manuals(self) -> list[dict[str, Any]]:
        return [
            {
                "id": m["document_id"],
                "alias": m["alias"],
                "title": m["title"],
                "chapter_count": len(m.get("chapters", [])),
                "readiness": (m.get("audit", {}) or {}).get("status"),
                "coverage_ratio": (m.get("audit", {}) or {}).get("coverage_ratio"),
            }
            for m in self.structure.get("manuals", [])
        ]

    def get_manual(self, manual_id: str) -> dict[str, Any] | None:
        manual = self.manuals.get(manual_id)
        if not manual:
            return None
        return {
            "id": manual["document_id"],
            "alias": manual["alias"],
            "title": manual["title"],
            "readiness": (manual.get("audit", {}) or {}).get("status"),
            "coverage_ratio": (manual.get("audit", {}) or {}).get("coverage_ratio"),
            "chapters": [
                {
                    "id": c["chapter_id"],
                    "readiness": (c.get("audit", {}) or {}).get("status"),
                    "number": c.get("chapter_number", c.get("order")),
                    "title": c["title"],
                    "page_start": (
                        (c.get("page_range") or [None, None])[0]
                        if c.get("page_range") is not None
                        else c.get("page_start")
                    ),
                    "page_end": (
                        (c.get("page_range") or [None, None])[1]
                        if c.get("page_range") is not None
                        else c.get("page_end")
                    ),
                }
                for c in manual.get("chapters", [])
            ],
        }

    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
        node = self.entities.get(chapter_id)
        if not node or node.get("type") != "CHAPTER":
            return None
        children = []
        for edge in self.edges:
            if edge.get("from") != chapter_id:
                continue
            child = self.entities.get(edge.get("to"))
            if not child:
                continue
            if edge.get("rel") not in {
                "HAS_SECTION", "HAS_CLAUSE", "HAS_TABLE", "HAS_FIGURE", "HAS_EVIDENCE"
            }:
                continue
            children.append({
                "id": child["id"],
                "type": child.get("type"),
                "label": child.get("label"),
                "page": child.get("page", child.get("source_page")),
                "source_page": child.get("source_page", child.get("page")),
                "source_section": child.get("source_section"),
                "source_text": child.get("source_text"),
                "confidence": child.get("confidence"),
                "extraction_method": child.get("extraction_method"),
                "rel": edge.get("rel"),
            })
        children.sort(key=lambda x: (x["page"] if x["page"] is not None else 999999, x["id"]))
        return {
            "id": node["id"],
            "title": node.get("label"),
            "number": (node.get("specs") or {}).get("ChapterNumber"),
            "page_range": (node.get("specs") or {}).get("PageRange"),
            "children": children,
        }

    def chapter_children(self, chapter_id: str) -> list[dict[str, Any]]:
        chapter = self.get_chapter(chapter_id)
        return chapter["children"] if chapter else []

    def search(self, query: str, manual_id: str | None = None) -> list[dict[str, Any]]:
        terms = [t.lower() for t in query.split() if t.strip()]
        allowed_ids = None
        if manual_id:
            manual = self.manuals.get(manual_id)
            if not manual:
                return []
            allowed_ids = {c["chapter_id"] for c in manual.get("chapters", [])}
            allowed_ids.add(manual_id)
        results = []
        for node in self.entities.values():
            if allowed_ids is not None and node["id"] not in allowed_ids:
                continue
            haystack = " ".join([
                str(node.get("label", "")),
                str(node.get("desc", "")),
                json.dumps(node.get("specs", {}), ensure_ascii=False),
            ]).lower()
            if terms and all(term in haystack for term in terms):
                results.append({
                    "id": node["id"],
                    "type": node.get("type"),
                    "label": node.get("label"),
                    "universe": "manuals",
                })
        return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Query the isolated Manuals KG")
    parser.add_argument("command", choices=["manuals", "manual", "chapter", "search"])
    parser.add_argument("value", nargs="?")
    parser.add_argument("--manual", dest="manual_id")
    args = parser.parse_args()

    kg = ManualKG.load()
    if args.command == "manuals":
        result = kg.list_manuals()
    elif args.command == "audit":
        result = kg.audit_summary()
    elif args.command == "manual":
        result = kg.get_manual(args.value) if args.value else None
    elif args.command == "chapter":
        result = kg.get_chapter(args.value) if args.value else None
    else:
        result = kg.search(args.value or "", args.manual_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
