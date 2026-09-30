"""P0-R.3: reviewed/verified only through review records."""

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import provenance_policy as pp  # noqa: E402


def _rec(i):
    return {"id": i, "verification_status": "verified", "confidence": 1.0}


def test_gate_m_passes():
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_provenance_policy.py")],
                         capture_output=True, text=True, cwd=ROOT)
    assert res.returncode == 0, res.stdout + res.stderr


def test_review_status_levels():
    reviews = [
        {"target_ids": ["a", "b"], "decision": "approved", "reviewer": "r1"},
        {"target_ids": ["b"], "decision": "approved", "reviewer": "r2"},
        {"target_ids": ["b"], "decision": "approved", "reviewer": "r2"},
        {"target_ids": ["c"], "decision": "approved", "reviewer": "r1"},
        {"target_ids": ["c"], "decision": "disputed", "reviewer": "r2"},
    ]
    st = pp.review_status(reviews)
    assert st == {"a": "reviewed", "b": "verified", "c": "disputed"}


def test_apply_downgrades_unreviewed_and_relabels_text_facts():
    nodes = [{**_rec("n1"), "domain": "manual"}, {**_rec("n2"), "domain": "manual"}]
    evidence = [{"evidence_id": "e1", "verification_status": "verified", "confidence": 1.0}]
    facts = [{"id": "f1", "subject_id": "n1", "status": "VERIFIED", "confidence": 1.0,
              "extraction_method": pp.FALSE_TEXT_METHOD}]
    reviews = [{"target_ids": ["n2"], "decision": "approved", "reviewer": "r1"}]
    pp.apply(nodes, [], evidence, facts, reviews)
    assert nodes[0]["verification_status"] == "machine_extracted" and nodes[0]["confidence"] == 0.95
    assert nodes[1]["verification_status"] == "reviewed"
    assert evidence[0]["verification_status"] == "machine_extracted" and evidence[0]["confidence"] == 0.95
    assert facts[0]["status"] == "MACHINE_EXTRACTED"
    assert facts[0]["extraction_method"] == pp.TEXT_METHOD


def test_no_verified_without_review_in_canonical():
    canon = ROOT / "data/knowledge-graph/canonical"
    reviews = [json.loads(l) for l in (canon / "reviews.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    status = pp.review_status(reviews)
    for name, key in (("nodes.jsonl", "id"), ("requirements.jsonl", "id"), ("evidence.jsonl", "evidence_id")):
        for line in (canon / name).read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            assert rec["verification_status"] == status.get(rec[key], "machine_extracted"), rec[key]


def test_gate_m_detects_unreviewed_verified(tmp_path, monkeypatch):
    import validate_provenance_policy as g
    canon = tmp_path / "canonical"
    canon.mkdir()
    for name in ("nodes.jsonl", "requirements.jsonl", "evidence.jsonl", "reviews.jsonl"):
        (canon / name).write_text((ROOT / "data/knowledge-graph/canonical" / name).read_text(encoding="utf-8"), encoding="utf-8")
    lines = (canon / "nodes.jsonl").read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["verification_status"] = "verified"
    lines[0] = json.dumps(first)
    (canon / "nodes.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(g, "CANON", canon)
    assert g.main() == 1
