#!/usr/bin/env python3
"""Deterministic rebuild of every generated knowledge artifact from the source manuals.

    python scripts/rebuild_all.py

Order: chapter extraction -> compact canonical core -> unified canonical (+ metrics)
-> browser bundle. Running it twice, or on a clean checkout, must leave `git diff` empty;
CI enforces that.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "ingest_all_manual_chapters.py",
    "generate_canonical_kg.py",
    "unify_manual_canonical.py",
    "export_kg_bundle.py",
]


def main() -> int:
    for step in STEPS:
        print(f"[rebuild] {step}")
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / step)], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(r.stdout[-2000:] + r.stderr[-2000:])
            print(f"[rebuild] FAILED at {step}")
            return r.returncode
    print("[rebuild] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
