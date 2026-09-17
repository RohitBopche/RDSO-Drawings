#!/usr/bin/env python3
"""Validate canonical knowledge-graph JSONL records against the schema contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "data" / "knowledge-graph" / "schemas"
CANONICAL_DIR = ROOT / "data" / "knowledge-graph" / "canonical"

FILES = {
    "nodes": (CANONICAL_DIR / "nodes.jsonl", SCHEMA_DIR / "entity.schema.json"),
    "edges": (CANONICAL_DIR / "edges.jsonl", SCHEMA_DIR / "edge.schema.json"),
    "requirements": (CANONICAL_DIR / "requirements.jsonl", SCHEMA_DIR / "requirement.schema.json"),
}


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fallback_validate(record: dict, schema: dict) -> list[str]:
    errors = []
    # Check top-level required
    for req in schema.get("required", []):
        if req not in record:
            errors.append(f"missing required property: {req}")
    # Check anyOf
    if "anyOf" in schema:
        matched = False
        for option in schema["anyOf"]:
            if all(r in record for r in option.get("required", [])):
                matched = True
                break
        if not matched:
            errors.append("did not match anyOf schema constraint")
    return errors


def validate_jsonl(label: str, path: Path, schema: dict) -> tuple[int, list[str]]:
    validator = Draft202012Validator(schema) if Draft202012Validator is not None else None
    count = 0
    errors: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"{label}:{line_no}: invalid JSON: {exc.msg}")
                continue
            count += 1
            if validator:
                for error in validator.iter_errors(record):
                    location = ".".join(str(p) for p in error.path) or "$"
                    errors.append(f"{label}:{line_no}:{location}: {error.message}")
                    if len(errors) >= 25:
                        return count, errors
            else:
                for err in _fallback_validate(record, schema):
                    errors.append(f"{label}:{line_no}:$: {err}")
                    if len(errors) >= 25:
                        return count, errors
    return count, errors


def main() -> int:
    total = 0
    failed = False
    for label, (data_path, schema_path) in FILES.items():
        if not data_path.exists() or not schema_path.exists():
            print(f"FAIL {label}: missing {data_path} or {schema_path}")
            failed = True
            continue
        count, errors = validate_jsonl(label, data_path, load_schema(schema_path))
        total += count
        if errors:
            failed = True
            print(f"FAIL {label}: {len(errors)} validation error(s), {count} records scanned")
            for error in errors[:25]:
                print(f"  {error}")
        else:
            print(f"PASS {label}: {count} records validated")

    print(f"Validated records: {total}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
