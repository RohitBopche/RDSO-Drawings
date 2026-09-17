#!/usr/bin/env python3
"""Plan or apply exact legacy-to-canonical identity replacements.

The command is dry-run by default. Applying changes requires an explicit file
allow-list so a migration cannot accidentally rewrite unrelated application or
binary content.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAP_FILE = ROOT / "data" / "knowledge-graph" / "canonical" / "identity_aliases.json"
DEFAULT_FILES = (
    "data/knowledge-graph/canonical/nodes.jsonl",
    "data/knowledge-graph/canonical/edges.jsonl",
    "data/knowledge-graph/canonical/requirements.jsonl",
    "data/knowledge-graph/canonical/documents.jsonl",
)


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
            if alias == canonical or alias in canonical_ids:
                raise ValueError(f"alias collides with canonical identity: {alias}")
            previous = aliases.get(alias)
            if previous and previous != canonical:
                raise ValueError(f"alias maps to multiple canonical IDs: {alias}")
            aliases[alias] = canonical
    return aliases


def replace_exact(value: Any, aliases: dict[str, str]) -> tuple[Any, int]:
    if isinstance(value, str):
        replacement = aliases.get(value)
        return (replacement, 1) if replacement else (value, 0)
    if isinstance(value, list):
        result = []
        count = 0
        for item in value:
            updated, changed = replace_exact(item, aliases)
            result.append(updated)
            count += changed
        return result, count
    if isinstance(value, dict):
        result = {}
        count = 0
        for key, item in value.items():
            updated_key = aliases.get(key, key)
            updated, changed = replace_exact(item, aliases)
            result[updated_key] = updated
            count += changed + (updated_key != key)
        return result, count
    return value, 0


def migrate_jsonl(text: str, aliases: dict[str, str]) -> tuple[str, int]:
    output: list[str] = []
    changes = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            output.append(line)
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_no}: {exc.msg}") from exc
        updated, count = replace_exact(record, aliases)
        output.append(json.dumps(updated, ensure_ascii=False))
        changes += count
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, changes


def migrate_file(path: Path, aliases: dict[str, str], apply: bool) -> int:
    original = path.read_text(encoding="utf-8")
    updated, changes = migrate_jsonl(original, aliases)
    print(f"{path.relative_to(ROOT)}: {changes} exact identity replacements")
    if apply and changes:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(updated)
            temp_path = Path(handle.name)
        temp_path.replace(path)
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write replacements; default is dry-run")
    parser.add_argument("files", nargs="*", help="JSONL files relative to repository root")
    args = parser.parse_args()

    aliases = load_alias_map(MAP_FILE)
    paths = [ROOT / item for item in (args.files or DEFAULT_FILES)]
    invalid = [path for path in paths if not path.is_file() or path.suffix.lower() != ".jsonl"]
    if invalid:
        raise SystemExit("refusing non-existent or non-JSONL migration target: " + ", ".join(map(str, invalid)))

    total = sum(migrate_file(path, aliases, args.apply) for path in paths)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"{mode}: {total} exact identity replacements across {len(paths)} files")
    if not args.apply:
        print("No files were modified. Re-run with --apply only after reviewing the migration plan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
