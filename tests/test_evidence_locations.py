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
    exact = 0
    for n in clauses:
        e = ev[f"ev:clause:{n['id']}"]
        assert e["page_number"] == n["page"]
        assert len(e["pdf_sha256"]) == 64 and len(e["page_sha256"]) == 64
        assert e["locator"] in ("word_sequence", "anchor_only", "page_only")
        if e["locator"] != "page_only":
            assert len(e["region"]) == 4
        exact += e["locator"] == "word_sequence"
    assert exact / len(clauses) > 0.9


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


def test_clause_evidence_covers_the_whole_clause_not_its_first_300_characters():
    import json
    ev = {}
    for l in (ROOT / "data/knowledge-graph/canonical/evidence.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(l)
        ev[e["evidence_id"]] = e
    e = ev["ev:clause:CLAUSE:IRPWM:CH_04:PARA_410"]      # 469 characters; the old highlight stopped after about 300
    assert e["coverage"] == "full_clause" and len(e["line_regions"]) >= 6 and e["match_ratio"] >= 0.9


def test_locate_full_skips_page_furniture_and_follows_the_clause_onto_the_next_page():
    sys.path.insert(0, str(ROOT / "scripts"))
    import locate_evidence as L

    def w(t, y):
        return (0, y, 10, y + 5, t, 0, int(y), 0)
    p1 = [w(t, 10 + i) for i, t in enumerate("410 Title one two three four five six HEADER seven eight".split())]
    p2 = [w(t, 10 + i) for i, t in enumerate("nine ten FOOTER eleven twelve".split())]
    pages = {1: p1, 2: p2}
    q = "410 Title one two three four five six seven eight nine ten eleven twelve".split()
    segs, cov = L.locate_full(lambda n: pages.get(n), 1, 2, q)
    assert [s[0] for s in segs] == [1, 2] and cov >= 0.95
    assert all(p1[i][4] != "HEADER" for i in segs[0][1])
