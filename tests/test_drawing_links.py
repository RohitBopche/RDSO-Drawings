"""Sprint K: clause-to-drawing citations and coverage."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import drawing_links as L  # noqa: E402


def nums(text):
    return [c["number"] for c in L.find_citations(text)]


def test_citation_forms():
    assert nums("as per drawing No. RDSO/T-6155 and RT-6154, RT- 4218") == ["6155", "6154", "4218"]
    assert nums("Drawing RDSO/T-1899.") == ["1899"]
    assert L.find_citations("RT-6155/1")[0]["sub"] == "1"


def test_not_drawings():
    assert nums("IS: 1367 and IRS T-10 and Para 4218 in the year 2019") == []
    assert nums("see Annexure T-2019 and page 3456") == []


def test_range_file_covers_middle_number():
    reg = [{"drawing_id": "DRG:A", "filename": {"numbers": ["T-6171", "T-6173"], "kind": "range"}},
           {"drawing_id": "DRG:B", "filename": {"numbers": ["T-6291", "T-6293"], "kind": "list"}}]
    cov = L.sheet_coverage(reg)
    assert cov["6172"] == ["DRG:A"] and "6292" not in cov and cov["6291"] == ["DRG:B"]


def test_gate_u_passes_and_detects_tampering():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/validate_drawing_links.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-400:]
    p = ROOT / "data/knowledge-graph/canonical/drawing_links.jsonl"
    orig = p.read_text(encoding="utf-8")
    try:
        lines = orig.splitlines()
        rec = json.loads(lines[0])
        rec["raw"] = "XX-0000"
        lines[0] = json.dumps(rec)
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts/validate_drawing_links.py")], capture_output=True, text=True)
        assert r.returncode == 1
    finally:
        p.write_text(orig, encoding="utf-8")


def test_known_held_sheets():
    rep = json.loads((ROOT / "data/knowledge-graph/reports/drawing_links_report.json").read_text(encoding="utf-8"))
    assert rep["distinct_numbers_with_sheet"] >= 4
    assert "CLAUSE:IRPWM:CH_02:PARA_229" in rep["clauses_citing_held_sheets"]


def test_clause_extras_match_canonical_records():
    import re
    raw = (ROOT / "data/search/clause_extras.js").read_text(encoding="utf-8")
    extras = json.loads(re.match(r"globalThis\.RDSO_CLAUSE_EXTRAS=(.*);\s*$", raw, re.S).group(1))
    meas = {}
    for l in (ROOT / "data/knowledge-graph/canonical/measurements.jsonl").read_text(encoding="utf-8").splitlines():
        m = json.loads(l)
        if m["source"] == "text":
            meas.setdefault(m["clause"], []).append(m)
    for clause, e in extras.items():
        for v in e.get("v", []):
            assert any(" ".join(m["raw"].split()) == v[5] and m["unit"] == v[3] for m in meas[clause])
        for _, f in e.get("d", []):
            assert (ROOT / f).exists()
    assert "CLAUSE:IRPWM:CH_02:PARA_229" in extras and extras["CLAUSE:IRPWM:CH_02:PARA_229"]["d"]
    assert len(raw) < 400_000
