"""Shared utilities for RDSO Knowledge Graph validation scripts."""

from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    """Load a JSONL file, returning (records, parse_errors)."""
    records: list[dict] = []
    errors: list[str] = []
    if not path.exists():
        return records, [f"Missing file: {path.name}"]
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:{line_no}: invalid JSON: {exc.msg}")
    return records, errors


def add_error(errors: list[str], message: str, max_errors: int = 25) -> None:
    """Append an error message, capped at max_errors."""
    if len(errors) < max_errors:
        errors.append(message)
