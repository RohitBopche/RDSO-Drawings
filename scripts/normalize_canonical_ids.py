#!/usr/bin/env python3
"""Validate and report the deterministic canonical-ID migration plan.

The first migration step is intentionally non-destructive: it proves that every
legacy alias has one canonical target and reports where aliases occur. Dataset
rewrites should be a separate, reviewed step after all consumers are migrated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
MAP_FILE = KG / "canonical" / "identity_aliases.json"
CANONICAL = KG / "canonical"
FILES_TO_SCAN = ("nodes.jsonl", "edges.jsonl", "requirements.jsonl", "documents.jsonl")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_alias_map(document: dict) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for mapping in document.get("mappings", []):
        canonical = mapping.get("canonical_id")
        if not isinstance(canonical, str) or not canonical:
            raise ValueError("every mapping requires a non-empty canonical_id")
        if canonical in aliases:
            raise ValueError(f"canonical ID is already used as an alias: {canonical}")
        for alias in mapping.get("aliases", []):
            if not isinstance(alias, str) or not alias:
                raise ValueError(f"invalid alias for {canonical}: {alias!r}")
            previous = aliases.get(alias)
            if previous and previous != canonical:
                raise ValueError(f"alias maps to multiple canonical IDs: {alias}")
            if alias == canonical:
                raise ValueError(f"alias equals canonical ID: {alias}")
            aliases[alias] = canonical
    return aliases


def scan_references(alias_map: dict[str, str]) -> dict[str, int]:
    counts = {alias: 0 for alias in alias_map}
    for filename in FILES_TO_SCAN:
        path = CANONICAL / filename
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            for alias in alias_map:
                if alias in raw:
                    counts[alias] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate mapping and report alias references")
    args = parser.parse_args()

    mapping = load_json(MAP_FILE)
    alias_map = build_alias_map(mapping)
    counts = scan_references(alias_map)

    print(f"PASS identity map: {len(alias_map)} aliases -> {len(mapping.get('mappings', []))} canonical IDs")
    for alias, canonical in sorted(alias_map.items()):
        print(f"  {alias} -> {canonical} ({counts[alias]} matching canonical-data lines)")

    if args.check:
        print("PASS non-destructive check: no canonical datasets were rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
