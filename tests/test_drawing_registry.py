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


import title_block as TB  # noqa: E402


def L(text, x0, y0, x1=None, y1=None):
    return {"text": text, "box": [x0, y0, x1 or x0 + 0.03, y1 or y0 + 0.01], "confidence": 0.9}


def synthetic_sheet():
    return [
        L("SPECIFICATION", 0.70, 0.975), L("SCALE", 0.74, 0.975), L("ALT:", 0.765, 0.975, 0.78), L("DESCRIPTION", 0.82, 0.975),
        L("DATE", 0.90, 0.975), L("RDSO/T-6155", 0.93, 0.973, 0.98),
        L("IRS: T 10.", 0.71, 0.955), L("NOT TO SCALE", 0.735, 0.955, 0.77),
        L("13.", 0.767, 0.90, 0.775), L("REVISED & REDRAWN", 0.79, 0.90), L("27-01-2025", 0.90, 0.90),
        L("12.", 0.767, 0.93, 0.775), L("REVISED & REDRAWN", 0.79, 0.93), L("01-10-2024", 0.90, 0.93),
        L("R.", 0.93, 0.87), L("10125 mm CURVED SWITCH", 0.93, 0.90), L("FOR 1 IN 12 TURNOUT", 0.93, 0.92),
    ]


def test_title_block_fields_and_alteration_rows():
    x = TB.extract(synthetic_sheet())
    assert x["drawing_number_line"] == "T-6155"
    assert x["specification"] == "IRS: T 10." and x["scale"] == "NOT TO SCALE"
    assert x["title"] == "10125 mm CURVED SWITCH FOR 1 IN 12 TURNOUT"
    assert [(a["number"], a["date"]) for a in x["alterations"]] == [(13, "2025-01-27"), (12, "2024-10-01")]
    assert x["alterations"][0]["summary"] == "REVISED & REDRAWN"


def test_missing_anchors_give_none_not_guesses():
    x = TB.extract([L("some drawing text", 0.3, 0.3)])
    assert x["title"] is None and x["alterations"] == [] and x["specification"] is None


def test_alt_table_check():
    fn = {"alteration": 13}
    assert D.alt_table_check(fn, {"alterations": [{"number": 13}, {"number": 12}]})["alt_matches_table"] is True
    assert D.alt_table_check(fn, {"alterations": [{"number": 80}]})["alt_matches_table"] is False
    assert D.alt_table_check(fn, {"alterations": [{"number": None}]})["alt_matches_table"] is None
    assert D.alt_table_check({"alteration": "NIL"}, {"alterations": [{"number": 1}]})["alt_matches_table"] is None
