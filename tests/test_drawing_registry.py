"""Sprint I: drawing identity, revision lineage, Gate T."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import drawing_registry as D  # noqa: E402


def test_filename_forms():
    assert D.parse_filename("RDSO_T_6295_ALT_NIL.pdf") == {"numbers": ["T-6295"], "kind": "single", "alteration": "NIL"}
    assert D.parse_filename("2025-01-28-RDSO_T_6155_ALT_13.pdf")["alteration"] == 13
    r = D.parse_filename("RDSO_T_6275 TO RDSO_T_ 6275_4_ALT_4.pdf")
    assert r["numbers"] == ["T-6275", "T-6275/4"] and r["kind"] == "range"
    assert D.parse_filename("RDSO_T_7087 & RDSO_T_7088_ALT_1.pdf")["kind"] == "list"
    assert D.parse_filename("RDSO_T_3901 TO  RDSOT_T_3902_A_ALT_3.pdf")["numbers"] == ["T-3901", "T-3902/A"]
    assert D.parse_filename("RDSO_T_6280_Alt_2.pdf")["alteration"] == 2


def test_sheet_numbers_tolerate_ocr_zero_for_o():
    lines = [{"text": "RDS0/T-6295", "box": [0, 0, 1, 1], "confidence": 0.9}, {"text": "R.D.S.O./T-6155/1", "box": [0, 0, 1, 1], "confidence": 0.9}]
    got = [n["number"] for n in D.sheet_numbers(lines)]
    assert got == ["T-6295", "T-6155/1"]


def test_sheet_dates_reject_impossible():
    lines = [{"text": "27-01-2025 and 45-13-2025", "box": [0, 0, 1, 1]}]
    assert [d["date"] for d in D.sheet_dates(lines)] == ["2025-01-27"]


def test_identity_and_alt_checks():
    fn = {"numbers": ["T-6295"], "kind": "single", "alteration": "NIL"}
    nums = [{"base": "T-6295"}]
    dates = [{"date": f"2020-01-0{i}"} for i in (1, 2, 3)]
    c = D.check(fn, nums, dates)
    assert c["identity_confirmed"] and c["alt_consistent"] is False
    assert D.check(fn, [{"base": "T-1111"}], [])["identity_confirmed"] is False


def test_gate_t_passes_and_detects_missing_entry():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/validate_drawings.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-500:]
    p = ROOT / "data/knowledge-graph/canonical/drawings_registry.jsonl"
    orig = p.read_text(encoding="utf-8")
    try:
        p.write_text("\n".join(orig.splitlines()[1:]) + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts/validate_drawings.py")], capture_output=True, text=True)
        assert r.returncode == 1 and "not in the drawing registry" in r.stdout
    finally:
        p.write_text(orig, encoding="utf-8")


def test_lineage_latest_agrees_for_6155():
    rep = json.loads((ROOT / "data/knowledge-graph/reports/drawing_registry_report.json").read_text(encoding="utf-8"))
    g = rep["lineage_groups"]["T-6155"]
    assert g["latest_by_alteration"].endswith("ALT_13.pdf") and g["agree"] is True
