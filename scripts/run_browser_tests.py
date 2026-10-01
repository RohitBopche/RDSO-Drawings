#!/usr/bin/env python3
"""Run the headless-browser (CDP) suites against index.html, one after another.

    python scripts/run_browser_tests.py            # all suites
    python scripts/run_browser_tests.py manuals    # suites whose name contains 'manuals'

Uses tests/browser_env.js (CHROME_PATH, RDSO_ARTIFACT_DIR, RDSO_HEADLESS).
Screenshots go to a temp dir unless RDSO_ARTIFACT_DIR is set.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITES = [
    "verify_phase1_milestone1", "verify_phase2_revisions", "verify_phase3_graph",
    "verify_phase4_workflows", "verify_question_interface", "verify_learning_system",
    "verify_node_panel_upgrade", "verify_kg_interlinking", "verify_kg_app",
    "verify_kg_manuals", "verify_knowledge_universes", "test_inspect_alt11", "verify_retrieval_ui", "verify_review_packet", "verify_chat_ui", "verify_browse_ui", "verify_learn_ui", "verify_graph_ui",
]
# verify_semantic_intelligence.js needs a hand-started Chrome and a hard-coded path; not automated.


def main() -> int:
    flt = sys.argv[1:] 
    suites = [s for s in SUITES if not flt or any(f in s for f in flt)]
    if not (ROOT / "node_modules" / "ws").exists():
        print("node_modules/ws missing: run `npm ci` first")
        return 2
    results = []
    for s in suites:
        t = time.time()
        try:
            r = subprocess.run(["node", str(ROOT / "tests" / f"{s}.js")], cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=420, env=os.environ)
            ok, out = r.returncode == 0, r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            ok, out = False, "timeout"
        results.append((s, ok, time.time() - t))
        print(f"[{'PASS' if ok else 'FAIL'}] {s} ({results[-1][2]:.0f}s)")
        if not ok:
            print("\n".join(out.strip().splitlines()[-25:]))
    failed = [s for s, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} browser suites passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
