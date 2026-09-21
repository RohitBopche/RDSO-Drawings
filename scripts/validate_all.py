#!/usr/bin/env python3
"""Unified Validation CLI for RDSO Knowledge Graph (Task P0.2 / Gates A-E).

Executes all publication gates in strict accordance with the
RDSO Knowledge Graph Improvement Blueprint (Section 9 & Section 29):

1. Gate A — Structural Schema Validation (validate_canonical_graph.py)
2. Gate B — Identity Reference Audit (audit_identity_references.py)
3. Gate C — Graph Referential Integrity (validate_graph_integrity.py)
4. Gate D — Evidence Integrity (validate_evidence_integrity.py)
5. Gate E — Automated Regression Tests (pytest tests/)
6. Gate F — Manuals Structure & Universe Isolation (validate_manual_knowledge_graph.py)
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

GATES = [
    ("Gate A: Structural Schema Validation", [sys.executable, str(ROOT / "scripts" / "validate_canonical_graph.py")]),
    ("Gate B: Identity Reference Audit", [sys.executable, str(ROOT / "scripts" / "audit_identity_references.py")]),
    ("Gate C: Graph Referential Integrity", [sys.executable, str(ROOT / "scripts" / "validate_graph_integrity.py")]),
    ("Gate D: Evidence Integrity", [sys.executable, str(ROOT / "scripts" / "validate_evidence_integrity.py")]),
    ("Gate E: Regression Test Suite", [sys.executable, "-m", "pytest", str(ROOT / "tests")]),
    ("Gate F: Manuals Structure & Universe Isolation", [sys.executable, str(ROOT / "scripts" / "validate_manual_knowledge_graph.py")]),\n    ("Gate G: Manuals Frontend Hierarchy Contract", [sys.executable, "-m", "pytest", str(ROOT / "tests" / "test_manual_frontend_contract.py")]),\n    ("Gate H: Manuals Query Boundary", [sys.executable, "-m", "pytest", str(ROOT / "tests" / "test_manual_kg_query.py")]),
]


def run_gate(name: str, cmd: list[str]) -> tuple[bool, str]:
    print(f"\n[RUNNING] {name}...")
    start = time.time()
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8")
    elapsed = time.time() - start
    output = res.stdout + res.stderr
    passed = (res.returncode == 0)
    status_str = f"PASS ({elapsed:.2f}s)" if passed else f"FAIL (exit {res.returncode})"
    print(f"[{status_str}] {name}")
    if not passed or "--verbose" in sys.argv or "-v" in sys.argv:
        print(output.strip())
    return passed, output


def main() -> int:
    print("=" * 80)
    print("RDSO KNOWLEDGE GRAPH — UNIFIED PUBLICATION VALIDATION PIPELINE")
    print("=" * 80)

    all_passed = True
    results = []

    for name, cmd in GATES:
        passed, out = run_gate(name, cmd)
        results.append((name, passed))
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    for name, passed in results:
        mark = "[PASS]" if passed else "[FAIL]"
        print(f"  {mark:<8} {name}")
    print("=" * 80)

    if all_passed:
        print("[SUCCESS] All publication gates passed cleanly.")
        return 0
    else:
        print("[ERROR] One or more validation gates failed. Inspect logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
