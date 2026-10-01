#!/usr/bin/env python3
"""Gate Y: citation verifier. Every sentence, table cell and line the chat shows, for every evaluation question, real question and probe
question, must be a verbatim part of the paragraph (or stored table) it cites; every answer carries a manual, paragraph and page. A self-test
seeds a fabricated sentence and requires the verifier to catch exactly that one.

    python scripts/verify_answers.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_ANSWERS = 300


def run(env_extra: dict | None = None) -> dict:
    env = dict(os.environ, **(env_extra or {}))
    r = subprocess.run(["node", "tests/answer_verifier.js"], cwd=ROOT, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return json.loads(r.stdout)


def main() -> int:
    real = run()
    errors = [f"{v['what']}: {v.get('text', '')!r} ({v['why']}) for question {v['q']!r}" for v in real["violations"][:20]]
    if real["answers"] < MIN_ANSWERS:
        errors.append(f"only {real['answers']} answered questions were verified (< {MIN_ANSWERS})")
    seeded = run({"RDSO_SEED_BAD": "1"})
    caught = [v for v in seeded["violations"] if v["q"] == "seeded"]
    if len(caught) != 1 or "999 Kmph" not in caught[0]["text"]:
        errors.append(f"the verifier self-test did not catch exactly the fabricated sentence: {caught}")
    for e in errors:
        print(f"[ERROR] {e}")
    print(f"[SUMMARY] citation verifier: {'FAIL' if errors else 'PASS'}; {real['answers']} answers ({real['refused']} refused), "
          f"{real['fragments']} fragments, {len(real['violations'])} violations, self-test caught the seeded fabrication")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
