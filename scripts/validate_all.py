#!/usr/bin/env python3
"""
validate_all.py
===============
Unified validation CLI executing the full verification suite defined in
docs/RDSO_Knowledge_Graph_Improvement_Blueprint.md Section 29 & 37:
1. Canonical Schema Validation (Gate A)
2. Graph Referential Integrity (Gate B & C)
3. Evidence & Provenance Integrity (Gate D)
4. Knowledge Core Vocabulary & Metrics (Gate E)
5. Identity Reference Audit
6. Automated Unit Tests (pytest)
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    {
        "name": "Canonical Schema Validation",
        "cmd": [sys.executable, str(ROOT / "scripts" / "validate_canonical_graph.py")],
        "desc": "Validates nodes, edges, and requirements against JSON schemas",
    },
    {
        "name": "Graph Referential Integrity",
        "cmd": [sys.executable, str(ROOT / "scripts" / "validate_graph_integrity.py")],
        "desc": "Ensures zero dangling edges, valid predicates, and no revision cycles",
    },
    {
        "name": "Evidence & Provenance Integrity",
        "cmd": [sys.executable, str(ROOT / "scripts" / "validate_evidence_integrity.py")],
        "desc": "Resolves document links, validates source files and blueprint crop existence",
    },
    {
        "name": "Canonical Knowledge Core Metrics",
        "cmd": [sys.executable, str(ROOT / "scripts" / "validate_canonical_kg.py")],
        "desc": "Audits domain distribution, predicates, and legacy compatibility core",
    },
    {
        "name": "Identity Reference Inventory",
        "cmd": [sys.executable, str(ROOT / "scripts" / "audit_identity_references.py")],
        "desc": "Audits non-destructive legacy identity references across repository",
    },
    {
        "name": "Pytest Unit Test Suite",
        "cmd": [sys.executable, "-m", "pytest", str(ROOT / "tests")],
        "desc": "Executes unit and contract tests for validators and identity audits",
    },
]


def run_step(step: dict) -> tuple[bool, float, str]:
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            step["cmd"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        duration = time.perf_counter() - start
        return (proc.returncode == 0), duration, proc.stdout.strip()
    except Exception as exc:
        duration = time.perf_counter() - start
        return False, duration, str(exc)


def main() -> int:
    print("=" * 80)
    print("RDSO TRACK KNOWLEDGE GRAPH — UNIFIED VALIDATION PIPELINE")
    print("Blueprint Quality Gates A through F Execution")
    print("=" * 80)

    results = []
    any_failed = False

    for step in STEPS:
        print(f"\n[RUNNING] {step['name']}...")
        success, duration, output = run_step(step)
        status_str = "PASS" if success else "FAIL"
        results.append((step["name"], status_str, duration))
        if not success:
            any_failed = True
            print(f"[{status_str}] {step['name']} failed in {duration:.2f}s:")
            print("-" * 60)
            print(output)
            print("-" * 60)
        else:
            print(f"[{status_str}] {step['name']} passed ({duration:.2f}s)")

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    for name, status_str, duration in results:
        indicator = "[OK] " if status_str == "PASS" else "[X]  "
        print(f"  {indicator} {name:<40} {status_str:<6} ({duration:.2f}s)")
    print("=" * 80)

    if any_failed:
        print("\nRESULT: FAILED — One or more validation checks failed. Address errors before publishing.")
        return 1

    print("\nRESULT: SUCCESS — 100% of Quality Gates passed! Knowledge Core is publish-ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
