"""Regression tests for P0-R.1/R.2: canonical is the single source of manual text."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "knowledge-graph" / "canonical"


def _jsonl(name):
    return [json.loads(l) for l in (CANON / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def test_gate_l_passes():
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_manual_text_integrity.py")],
                         capture_output=True, text=True, cwd=ROOT)
    assert res.returncode == 0, res.stdout + res.stderr


def test_every_clause_has_text_and_page():
    clauses = [n for n in _jsonl("nodes.jsonl") if n["id"].startswith("CLAUSE:") and n["type"] == "SPECIFICATION"]
    assert len(clauses) == 1838
    assert all(len(n["text"].strip()) >= 3 and n["page"] for n in clauses)


def test_no_dangling_or_empty_requirements():
    ids = {n["id"] for n in _jsonl("nodes.jsonl")}
    for r in _jsonl("requirements.jsonl"):
        assert r["id"] in ids
        assert r["statement"].strip() not in ("", "...")


def test_machine_extraction_is_not_labelled_verified():
    for n in _jsonl("nodes.jsonl"):
        if n["id"].startswith(("CLAUSE:", "TOL:")):
            assert n["verification_status"] == "machine_extracted", n["id"]


def test_gate_l_detects_empty_clause_text(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_manual_text_integrity as g

    nodes = _jsonl("nodes.jsonl")
    for n in nodes:
        if n["id"].startswith("CLAUSE:"):
            n["text"] = "..."
            break
    bad = tmp_path / "canonical"
    bad.mkdir()
    for name in ("edges.jsonl", "requirements.jsonl", "evidence.jsonl"):
        (bad / name).write_text((CANON / name).read_text(encoding="utf-8"), encoding="utf-8")
    (bad / "nodes.jsonl").write_text("".join(json.dumps(n) + "\n" for n in nodes), encoding="utf-8")
    monkeypatch.setattr(g, "CANON", bad)
    assert g.main() == 1
