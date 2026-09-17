#!/usr/bin/env python3
"""Validate evidence integrity and provenance references against Blueprint Gate D."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
CANONICAL = KG / "canonical"
SCHEMA_DIR = KG / "schemas"

EVIDENCE_FILE = CANONICAL / "evidence.jsonl"
EVIDENCE_SCHEMA_FILE = SCHEMA_DIR / "evidence.schema.json"
NODE_FILE = CANONICAL / "nodes.jsonl"
DOCUMENT_FILE = CANONICAL / "documents.jsonl"
EDGE_FILE = CANONICAL / "edges.jsonl"
REQUIREMENT_FILE = CANONICAL / "requirements.jsonl"
ALIAS_FILE = CANONICAL / "identity_aliases.json"

MAX_ERRORS = 25


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    if not path.exists():
        return records, [f"{path.name}: file does not exist"]
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:{line_no}: invalid JSON: {exc.msg}")
    return records, errors


def validate_record_schema(record: dict, schema: dict) -> list[str]:
    errors = []
    for required_prop in schema.get("required", []):
        if required_prop not in record:
            errors.append(f"missing required property {required_prop!r}")

    props = schema.get("properties", {})
    for key, value in record.items():
        prop_def = props.get(key)
        if not prop_def:
            continue
        expected_type = prop_def.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"{key}: expected string, got {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"{key}: expected number, got {type(value).__name__}")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"{key}: expected array, got {type(value).__name__}")

        if "enum" in prop_def and value not in prop_def["enum"]:
            errors.append(f"{key}: value {value!r} not in allowed enum {prop_def['enum']}")

        if "minimum" in prop_def and isinstance(value, (int, float)) and value < prop_def["minimum"]:
            errors.append(f"{key}: value {value} < minimum {prop_def['minimum']}")
        if "maximum" in prop_def and isinstance(value, (int, float)) and value > prop_def["maximum"]:
            errors.append(f"{key}: value {value} > maximum {prop_def['maximum']}")

    return errors


def main() -> int:
    errors: list[str] = []

    def add(msg: str):
        if len(errors) < MAX_ERRORS:
            errors.append(msg)

    if not EVIDENCE_FILE.exists():
        print(f"FAIL evidence integrity: {EVIDENCE_FILE.name} does not exist")
        return 1

    evidence_records, parse_errors = load_jsonl(EVIDENCE_FILE)
    for err in parse_errors:
        add(err)

    schema = {}
    if EVIDENCE_SCHEMA_FILE.exists():
        try:
            schema = json.loads(EVIDENCE_SCHEMA_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            add(f"evidence schema invalid: {exc}")

    # Load valid document and entity IDs
    valid_ids: set[str] = set()
    node_records, _ = load_jsonl(NODE_FILE)
    for r in node_records:
        if r.get("id"):
            valid_ids.add(r["id"])

    doc_records, _ = load_jsonl(DOCUMENT_FILE)
    for r in doc_records:
        if r.get("id"):
            valid_ids.add(r["id"])

    if ALIAS_FILE.exists():
        try:
            alias_doc = json.loads(ALIAS_FILE.read_text(encoding="utf-8"))
            for m in alias_doc.get("mappings", []):
                if m.get("canonical_id"):
                    valid_ids.add(m["canonical_id"])
                for a in m.get("aliases", []):
                    valid_ids.add(a)
        except Exception:
            pass

    evidence_ids: set[str] = set()
    for line_no, ev in enumerate(evidence_records, 1):
        eid = ev.get("evidence_id")
        if not eid:
            add(f"evidence:{line_no}: missing evidence_id")
            continue
        if eid in evidence_ids:
            add(f"evidence:{line_no}: duplicate evidence_id {eid!r}")
        evidence_ids.add(eid)

        # Schema constraints
        for s_err in validate_record_schema(ev, schema):
            add(f"evidence:{line_no}:{eid}: {s_err}")

        # Document reference
        doc_id = ev.get("document_id")
        if doc_id and doc_id not in valid_ids:
            add(f"evidence:{line_no}:{eid}: document_id {doc_id!r} not found in nodes or documents")

        # Source file existence check
        file_path_str = ev.get("file_path")
        if file_path_str:
            file_path = ROOT / file_path_str
            if not file_path.exists():
                add(f"evidence:{line_no}:{eid}: source file missing at {file_path_str}")

        # Crop image existence check
        crop_path_str = ev.get("crop_path")
        if crop_path_str:
            crop_path = ROOT / crop_path_str
            if not crop_path.exists():
                add(f"evidence:{line_no}:{eid}: crop image missing at {crop_path_str}")

    # Check incoming references from edges, requirements, nodes
    edge_records, _ = load_jsonl(EDGE_FILE)
    for index, edge in enumerate(edge_records, 1):
        for ref in edge.get("evidence_ids", []) or []:
            if ref not in evidence_ids:
                add(f"edges:{index}: dangling evidence reference {ref!r}")

    req_records, _ = load_jsonl(REQUIREMENT_FILE)
    for index, req in enumerate(req_records, 1):
        for ref in req.get("evidence_ids", []) or []:
            if ref not in evidence_ids:
                add(f"requirements:{index}: dangling evidence reference {ref!r}")

    if errors:
        print(f"FAIL evidence integrity: {len(errors)} issue(s) reported")
        for err in errors:
            print(f"  {err}")
        return 1

    print(f"PASS evidence integrity: {len(evidence_records)} evidence records verified")
    print("PASS document resolutions, physical source file paths, crop existence, and incoming evidence references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
