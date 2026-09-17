#!/usr/bin/env python3
"""Build a deterministic, non-destructive inventory of legacy identity references."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "node_modules", "__pycache__"}
SKIP_SUFFIXES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".gz", ".tar",
    ".woff", ".woff2", ".ttf", ".otf", ".ico", ".mp3", ".mp4", ".mov", ".avi",
    ".xlsx", ".xls", ".pptx", ".docx", ".ods", ".bin", ".exe", ".dll",
}

@dataclass(frozen=True)
class Reference:
    path: str
    line: int
    alias: str
    canonical_id: str
    reference_kind: str
    context: str


def load_alias_map(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    aliases: dict[str, str] = {}
    canonical_ids: set[str] = set()
    mappings = document.get("mappings", [])
    if not isinstance(mappings, list):
        raise ValueError("identity map 'mappings' must be a list")
    for mapping in mappings:
        canonical = mapping.get("canonical_id")
        if not isinstance(canonical, str) or not canonical:
            raise ValueError("every mapping requires a non-empty canonical_id")
        if canonical in canonical_ids or canonical in aliases:
            raise ValueError(f"duplicate canonical identity: {canonical}")
        canonical_ids.add(canonical)
        raw_aliases = mapping.get("aliases", [])
        if not isinstance(raw_aliases, list):
            raise ValueError(f"aliases must be a list for {canonical}")
        for alias in raw_aliases:
            if not isinstance(alias, str) or not alias:
                raise ValueError(f"invalid alias for {canonical}: {alias!r}")
            if alias == canonical:
                raise ValueError(f"alias equals canonical ID: {alias}")
            previous = aliases.get(alias)
            if previous and previous != canonical:
                raise ValueError(f"alias maps to multiple canonical IDs: {alias}")
            aliases[alias] = canonical
    return aliases


def is_binary(path: Path) -> bool:
    try:
        sample = path.open("rb").read(8192)
    except OSError:
        return True
    return b"\x00" in sample


def should_scan(path: Path, excluded: set[Path]) -> bool:
    if path in excluded or any(part in SKIP_PARTS for part in path.parts):
        return False
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    return path.is_file()


def classify_reference(path: Path, line: str) -> str:
    lowered = line.lower()
    if path.suffix.lower() in {".json", ".jsonl"}:
        if '"id"' in lowered or '"document_id"' in lowered:
            return "canonical_data_identity"
        if '"from"' in lowered or '"to"' in lowered:
            return "canonical_graph_reference"
        if '"source_document_id"' in lowered or '"applies_to"' in lowered:
            return "canonical_requirement_reference"
        return "structured_data_reference"
    if path.parts and path.parts[0] == "scripts":
        return "tooling_reference"
    if path.suffix.lower() in {".js", ".html", ".css"}:
        return "application_reference"
    return "documentation_or_text_reference"


def scan(root: Path, aliases: dict[str, str], excluded: set[Path]) -> list[Reference]:
    patterns = [
        (alias, re.compile(r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])"))
        for alias in aliases
    ]
    findings: list[Reference] = []
    for path in sorted(root.rglob("*")):
        if not should_scan(path, excluded) or is_binary(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        relative = str(path.relative_to(root))
        for line_no, line in enumerate(lines, 1):
            for alias, pattern in patterns:
                if pattern.search(line):
                    findings.append(Reference(
                        path=relative,
                        line=line_no,
                        alias=alias,
                        canonical_id=aliases[alias],
                        reference_kind=classify_reference(path, line),
                        context=line.strip()[:240],
                    ))
    return findings


def build_report(root: Path, aliases: dict[str, str], findings: list[Reference]) -> dict:
    by_alias = {alias: 0 for alias in aliases}
    by_kind: dict[str, int] = {}
    by_file: dict[str, int] = {}
    for finding in findings:
        by_alias[finding.alias] += 1
        by_kind[finding.reference_kind] = by_kind.get(finding.reference_kind, 0) + 1
        by_file[finding.path] = by_file.get(finding.path, 0) + 1
    return {
        "schema_version": 1,
        "audit": "legacy_identity_reference_inventory",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "non_destructive": True,
        "alias_count": len(aliases),
        "reference_count": len(findings),
        "summary": {
            "references_by_alias": dict(sorted(by_alias.items())),
            "references_by_kind": dict(sorted(by_kind.items())),
            "files_with_references": len(by_file),
        },
        "aliases": [
            {"alias": alias, "canonical_id": aliases[alias], "reference_count": by_alias[alias]}
            for alias in sorted(aliases)
        ],
        "references": [asdict(finding) for finding in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to scan")
    parser.add_argument("--output", type=Path, help="write the machine-readable JSON report to this path")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON to stdout")
    args = parser.parse_args()

    root = args.root.resolve()
    map_path = root / "data" / "knowledge-graph" / "canonical" / "identity_aliases.json"
    aliases = load_alias_map(map_path)
    findings = scan(root, aliases, {map_path.resolve()})
    report = build_report(root, aliases, findings)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"PASS identity map: {len(aliases)} aliases validated")
        print(f"FOUND legacy references: {len(findings)}")
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.alias} -> {finding.canonical_id} [{finding.reference_kind}] | {finding.context}")
        if args.output:
            print(f"WROTE inventory: {args.output}")
        print("PASS non-destructive audit: no repository files were modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
