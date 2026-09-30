"""P0-R.4: evidence carries page, region and hashes; every edge cites evidence."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "knowledge-graph" / "canonical"
sys.path.insert(0, str(ROOT / "scripts"))


def _jsonl(name):
    return [json.loads(l) for l in (CANON / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def test_gate_n_passes():
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_evidence_locations.py")],
                         capture_output=True, text=True, cwd=ROOT)
    assert res.returncode == 0, res.stdout + res.stderr


def test_every_clause_evidence_has_page_region_and_hashes():
    ev = {e["evidence_id"]: e for e in _jsonl("evidence.jsonl")}
    clauses = [n for n in _jsonl("nodes.jsonl") if n["id"].startswith("CLAUSE:")]
    assert clauses
    for n in clauses:
        e = ev[f"ev:clause:{n['id']}"]
        assert e["page_number"] == n["page"]
        assert len(e["region"]) == 4 and e["locator"] == "word_sequence"
        assert len(e["pdf_sha256"]) == 64 and len(e["page_sha256"]) == 64


def test_edges_cite_evidence_except_waived():
    waived = {(w["from"], w["rel"], w["to"]) for w in
              json.loads((CANON / "evidence_waivers.json").read_text(encoding="utf-8"))["edges"]}
    missing = {(e["from"], e["rel"], e["to"]) for e in _jsonl("edges.jsonl") if not e.get("evidence_ids")}
    assert missing == waived


def _run_gate_on(tmp_path, monkeypatch, mutate):
    import validate_evidence_locations as g
    kg = tmp_path / "kg"
    shutil.copytree(ROOT / "data" / "knowledge-graph", kg, ignore=shutil.ignore_patterns("exports", "intermediate"))
    mutate(kg / "canonical")
    monkeypatch.setattr(g, "KG", kg)
    monkeypatch.setattr(g, "CANON", kg / "canonical")
    return g.main()


def test_gate_n_detects_tampered_page_hash(tmp_path, monkeypatch):
    def mutate(canon):
        rows = [json.loads(l) for l in (canon / "evidence.jsonl").read_text(encoding="utf-8").splitlines()]
        for r in rows:
            if "page_sha256" in r:
                r["page_sha256"] = "0" * 64
                break
        (canon / "evidence.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    assert _run_gate_on(tmp_path, monkeypatch, mutate) == 1


def test_gate_n_detects_edge_without_evidence(tmp_path, monkeypatch):
    def mutate(canon):
        rows = [json.loads(l) for l in (canon / "edges.jsonl").read_text(encoding="utf-8").splitlines()]
        rows[0].pop("evidence_ids", None)
        (canon / "edges.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    assert _run_gate_on(tmp_path, monkeypatch, mutate) == 1
