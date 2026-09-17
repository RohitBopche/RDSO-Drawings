#!/usr/bin/env python3
"""Inventory references to legacy canonical-identity aliases without modifying data."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "node_modules", "__pycache__"}
SKIP_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".woff", ".woff2"}
TEXT_SUFFIXES = {".json", ".jsonl", ".js", ".html", ".css", ".md", ".py", ".txt", ".yml", ".yaml", ".sh"}

@dataclass(frozen=True)
class Reference:
    path: str
    line: int
    alias: str
    context: str


def load_alias_map(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    aliases: dict[str, str] = {}
    canonical_ids: set[str] = set()
    for mapping in document.get("mappings", []):
        canonical = mapping.get("canonical_id")
        if not isinstance(canonical, str) or not canonical:
            raise ValueError("every mapping requires a non-empty canonical_id")
        if canonical in canonical_ids or canonical in aliases:
            raise ValueError(f"duplicate canonical identity: {canonical}")
        canonical_ids.add(canonical)
        for alias in mapping.get("aliases", []):
            if not isinstance(alias, str) or not alias:
                raise ValueError(f"invalid alias for {canonical}: {alias!r}")
            if alias == canonical:
                raise ValueError(f"alias equals canonical ID: {alias}")
            previous = aliases.get(alias)
            if previous and previous != canonical:
                raise ValueError(f"alias maps to multiple canonical IDs: {alias}")
            aliases[alias] = canonical
    return aliases


def should_scan(path: Path, excluded: set[Path]) -> bool:
    if path in excluded or any(part in SKIP_PARTS for part in path.parts):
        return False
    return path.suffix.lower() in TEXT_SUFFIXES and path.suffix.lower() not in SKIP_SUFFIXES


def scan(root: Path, aliases: dict[str, str], excluded: set[Path]) -> list[Reference]:
    patterns = [
        (alias, re.compile(r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])"))
        for alias in aliases
    ]
    findings: list[Reference] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not should_scan(path, excluded):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(lines, 1):
            for alias, pattern in patterns:
                if pattern.search(line):
                    findings.append(Reference(str(path.relative_to(root)), line_no, alias, line.strip()[:240]))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to scan")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    args = parser.parse_args()

    map_path = args.root / "data" / "knowledge-graph" / "canonical" / "identity_aliases.json"
    aliases = load_alias_map(map_path)
    findings = scan(args.root, aliases, {map_path.resolve()})

    if args.as_json:
        print(json.dumps([r.__dict__ for r in findings], indent=2))
        return 0

    print(f"PASS identity map: {len(aliases)} aliases validated")
    print(f"FOUND legacy references: {len(findings)}")
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.alias} | {finding.context}")
    print("PASS non-destructive audit: no files were modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
