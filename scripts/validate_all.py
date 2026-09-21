#!/usr/bin/env python3
"""Unified Validation CLI for the RDSO Knowledge Graph publication gates."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

GATES = [
    ("Gate A: Structural Schema Validation", [sys.executable, str(ROOT / "scripts" / "validate_canonical_graph.py")]),
    ("Gate B: Identity Reference Audit", [sys.executable, str(ROOT / "scripts" / "audit_identity_references.py")]),
    ("Gate C: Graph Referential Integrity", [sys.executable, str(ROOT / "scripts" / "validate_graph_integrity.py")]),
    ("Gate D: Evidence Integrity", [sys.executable, str(ROOT / "scripts" / "validate_evidence_integrity.py")]),
    ("Gate E: Regression Test Suite", [sys.executable, "-m", "pytest", str(ROOT / "tests")]),
    ("Gate F: Manuals Structure & Universe Isolation", [sys.executable, str(ROOT / "scripts" / "validate_manual_knowledge_graph.py")]),
    ("Gate G: Manuals Frontend Hierarchy Contract", [sys.executable, "-m", "pytest", str(ROOT / "tests" / "test_manual_frontend_contract.py")]),
    ("Gate H: Manuals Query Boundary", [sys.executable, "-m", "pytest", str(ROOT / "tests" / "test_manual_kg_query.py")]),
    ("Gate I: Manuals Chapter & Content Ownership", [sys.executable, str(ROOT / "scripts" / "validate_manual_chapter_content.py")]),
    ("Gate J: Manuals Canonical Content Ownership", [sys.executable, str(ROOT / "scripts" / "validate_manual_canonical_content.py")]),
    ("Gate K: Manuals Source-Heading Hierarchy", [sys.executable, str(ROOT / "scripts" / "validate_manual_hierarchy.py")]),
]


def run_gate(name: str, cmd: list[str]) -> tuple[bool, str]:
    print(f"\n[RUNNING] {name}...")
    start = time.time()
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8")
    elapsed = time.time() - start
    output = res.stdout + res.stderr
    passed = res.returncode == 0
    status = f"PASS ({elapsed:.2f}s)" if passed else f"FAIL (exit {res.returncode})"
    print(f"[{status}] {name}")
    if not passed or "--verbose" in sys.argv or "-v" in sys.argv:
        print(output.strip())
    return passed, output


def main() -> int:
    print("=" * 80)
    print("RDSO KNOWLEDGE GRAPH — UNIFIED PUBLICATION VALIDATION PIPELINE")
    print("=" * 80)
    results = []
    for name, cmd in GATES:
        results.append((name, *run_gate(name, cmd)))

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    for name, passed, _ in results:
        print(f"  {'[PASS]' if passed else '[FAIL]':<8} {name}")
    print("=" * 80)
    return 0 if all(passed for _, passed, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
