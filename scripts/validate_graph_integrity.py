#!/usr/bin/env python3
"""Validate referential integrity of the canonical knowledge graph."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
CANONICAL = KG / "canonical"
VOCABULARY = KG / "schemas" / "vocabularies" / "relationship-types.json"

NODE_FILE = CANONICAL / "nodes.jsonl"
EDGE_FILE = CANONICAL / "edges.jsonl"
REQUIREMENT_FILE = CANONICAL / "requirements.jsonl"
DOCUMENT_FILE = CANONICAL / "documents.jsonl"
EVIDENCE_FILE = CANONICAL / "evidence.jsonl"
MAX_ERRORS = 25


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:{line_no}: invalid JSON: {exc.msg}")
    return records, errors


def add(errors: list[str], message: str) -> None:
    if len(errors) < MAX_ERRORS:
        errors.append(message)


def find_revision_cycles(edges: list[dict]) -> list[str]:
    graph: dict[str, list[str]] = {}
    for edge in edges:
        if edge.get("rel") == "SUPERSEDES":
            graph.setdefault(edge.get("from", ""), []).append(edge.get("to", ""))

    state: dict[str, int] = {}
    cycles: list[str] = []

    def visit(node: str, stack: list[str]) -> None:
        if state.get(node) == 1:
            start = stack.index(node) if node in stack else 0
            cycles.append(" -> ".join(stack[start:] + [node]))
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for target in graph.get(node, []):
            visit(target, stack + [node])
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            visit(node, [])
    return cycles


def main() -> int:
    errors: list[str] = []
    node_records, node_parse_errors = load_jsonl(NODE_FILE)
    edge_records, edge_parse_errors = load_jsonl(EDGE_FILE)
    requirement_records, requirement_parse_errors = load_jsonl(REQUIREMENT_FILE)
    document_records, document_parse_errors = load_jsonl(DOCUMENT_FILE)
    for error in node_parse_errors + edge_parse_errors + requirement_parse_errors + document_parse_errors:
        add(errors, error)

    node_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for record in node_records:
        node_id = record.get("id")
        if not isinstance(node_id, str) or not node_id:
            add(errors, "nodes: record has missing/invalid id")
            continue
        if node_id in node_ids:
            duplicate_ids.add(node_id)
        node_ids.add(node_id)
    for node_id in sorted(duplicate_ids):
        add(errors, f"nodes: duplicate id {node_id}")

    try:
        vocabulary_doc = json.loads(VOCABULARY.read_text(encoding="utf-8"))
        allowed_relationships = set(vocabulary_doc["items"]["enum"])
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        add(errors, f"vocabulary: unable to load relationship types: {exc}")
        allowed_relationships = set()

    edge_keys: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edge_records, 1):
        source = edge.get("from")
        target = edge.get("to")
        relation = edge.get("rel")
        if source not in node_ids:
            add(errors, f"edges:{index}: dangling from={source!r}")
        if target not in node_ids:
            add(errors, f"edges:{index}: dangling to={target!r}")
        if relation not in allowed_relationships:
            add(errors, f"edges:{index}: invalid relationship {relation!r}")
        key = (str(source), str(target), str(relation))
        if key in edge_keys:
            add(errors, f"edges:{index}: duplicate edge {key}")
        edge_keys.add(key)

        evidence_ids = edge.get("evidence_ids", [])
        if evidence_ids and not EVIDENCE_FILE.exists():
            add(errors, f"edges:{index}: evidence_ids present but {EVIDENCE_FILE.name} is missing")

    document_identity: dict[str, list[str]] = {}
    for record in document_records:
        if record.get("type") != "DOCUMENT":
            continue
        label = record.get("label") or record.get("name") or record.get("id")
        if isinstance(label, str):
            identity = " ".join(label.casefold().split())
            document_identity.setdefault(identity, []).append(str(record.get("id")))
    for identity, ids in document_identity.items():
        if len(ids) > 1:
            add(errors, f"documents: duplicate logical identity {identity!r}: {', '.join(ids)}")

    for index, requirement in enumerate(requirement_records, 1):
        for field in ("applies_to", "measurement_ids"):
            for reference in requirement.get(field, []) or []:
                if reference not in node_ids:
                    add(errors, f"requirements:{index}: {field} references missing entity {reference!r}")
        source_document = requirement.get("source_document_id")
        if source_document and source_document not in node_ids:
            add(errors, f"requirements:{index}: source_document_id references missing entity {source_document!r}")
        if requirement.get("evidence_ids") and not EVIDENCE_FILE.exists():
            add(errors, f"requirements:{index}: evidence_ids present but {EVIDENCE_FILE.name} is missing")

    for cycle in find_revision_cycles(edge_records):
        add(errors, f"revisions: SUPERSEDES cycle detected: {cycle}")

    if errors:
        print(f"FAIL graph integrity: {len(errors)} issue(s) reported")
        for error in errors:
            print(f"  {error}")
        return 1

    print(f"PASS graph integrity: {len(node_records)} nodes, {len(edge_records)} edges, {len(requirement_records)} requirements")
    print("PASS duplicate IDs, dangling references, relationship vocabulary, duplicate edges, document identities, requirement references, and revision cycles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
