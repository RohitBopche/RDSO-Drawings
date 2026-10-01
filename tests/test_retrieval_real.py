"""Retrieval on the 20 real questions: the expected paragraph is in the top five (recall at 5 of at least 0.90, the Phase P5 criterion) and
usually first. Also records the decision rule for a semantic (embedding) layer: it is built only if recall at 5 falls below these floors."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_real_question_recall():
    d = json.loads(subprocess.run(["node", "tests/real_recall.js"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    assert d["r5"] / d["n"] >= 0.90, d
    assert d["r1"] / d["n"] >= 0.85, d


def test_semantic_layer_not_justified_by_the_evaluation_sets():
    out = subprocess.run(["python", "scripts/eval_retrieval.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    rows = [l.split() for l in out.splitlines() if l.startswith("ALL")]
    assert len(rows) == 2 and all(float(r[4]) >= 0.95 for r in rows), out      # R@5 on development and test sets
