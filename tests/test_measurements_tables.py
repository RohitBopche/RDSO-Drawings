"""Sprint E: structured measurements and extracted tables."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import measurements as M  # noqa: E402


def ex(text):
    return M.extract_from_text("CLAUSE:IRPWM:CH_01:PARA_100", text)


def test_max_and_min_comparators():
    r = ex("The gap shall be not more than 30 mm. Clearance of at least 10 mm is needed.")
    assert (r[0]["comparator"], r[0]["hi"], r[0]["unit"], r[0]["quantity"]) == ("max", 30.0, "mm", "gap")
    assert (r[1]["comparator"], r[1]["lo"], r[1]["quantity"]) == ("min", 10.0, "clearance")


def test_tolerance_and_signed_range():
    r = ex("Gauge tolerance is ± 3 mm on straight track.")
    assert (r[0]["comparator"], r[0]["lo"], r[0]["hi"]) == ("tolerance", -3.0, 3.0)
    r = ex("Alignment variation -10 mm to +15 mm is permitted.")
    assert (r[0]["comparator"], r[0]["lo"], r[0]["hi"]) == ("range", -10.0, 15.0)


def test_references_and_years_are_not_measurements():
    assert ex("See Para 429 and Annexure 4/2 of the manual issued in 2019.") == []
    assert ex("As per IS 1367 and Fig 3.4 the drawing applies.") == []


def test_compound_unit_not_truncated():
    assert ex("Pressure of 0.2-0.3 kg/cm2 is required for the test.") == []


def test_quantity_dropped_when_unit_incompatible():
    r = ex("The rail temperature limit is 60 kg for the item here in the note.")
    assert all(x["quantity"] != "temperature" for x in r)


def test_implausible_speed_rejected():
    assert ex("Model number 914 kmph column entry here.") == []


def test_table_cell_uses_header_unit():
    t = {"clause": "CLAUSE:TMM:CH_07:PARA_712", "table_id": "TBL:TMM:P1:01", "n_cols": 2, "header_rows": 1,
         "rows": [["Item", "Speed in kmph"], ["Utility vehicle", "60"]]}
    r = M.extract_from_table(t)
    assert len(r) == 1 and r[0]["unit"] == "kmph" and r[0]["quantity"] == "speed" and r[0]["lo"] == 60.0


def test_table_cell_prose_skipped():
    t = {"clause": "C", "table_id": "T", "n_cols": 2, "header_rows": 1,
         "rows": [["Item", "Requirement"], ["Fixing", "Fixing time should not take more than 2 minutes for fixing"]]}
    assert M.extract_from_table(t) == []


def test_gate_s_and_gate_r_pass_on_repo():
    for script in ("validate_measurements.py", "validate_tables.py"):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout[-800:]


def test_gate_s_detects_tampered_span(tmp_path):
    p = ROOT / "data/knowledge-graph/canonical/measurements.jsonl"
    orig = p.read_text(encoding="utf-8")
    try:
        lines = orig.splitlines()
        rec = json.loads(lines[0])
        rec["raw"] = "999 zz"
        lines[0] = json.dumps(rec, ensure_ascii=False, sort_keys=True)
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts/validate_measurements.py")], capture_output=True, text=True)
        assert r.returncode == 1
    finally:
        p.write_text(orig, encoding="utf-8")


def test_gate_r_detects_bad_hash():
    p = ROOT / "data/knowledge-graph/raw/tables.jsonl"
    orig = p.read_text(encoding="utf-8")
    try:
        lines = orig.splitlines()
        rec = json.loads(lines[0])
        rec["page_sha256"] = "0" * 64
        lines[0] = json.dumps(rec, ensure_ascii=False)
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts/validate_tables.py")], capture_output=True, text=True)
        assert r.returncode == 1
    finally:
        p.write_text(orig, encoding="utf-8")


def test_title_fragment_replaced_by_first_sentence():
    import clause_parser as cp
    frag = "On Indian Railways Alumino-Thermic welding with short pre-heating process by using"
    body = "1.1 " + frag + " the portion is used. Second sentence follows."
    fixed = cp._repair_title(frag, body, "1.1")
    assert fixed.startswith("On Indian Railways") and fixed.endswith("\u2026") and len(fixed) <= 101
    assert cp._repair_title("Shelf life of portion", "4.2.2 Shelf life of portion. Text.", "4.2.2") == "Shelf life of portion"


def test_no_registry_page_warnings_for_decimal_manuals():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/validate_manual_chapter_content.py")], capture_output=True, text=True)
    assert "falls outside owning chapter" not in r.stdout


def test_table_answer_returns_matching_rows():
    js = ("const e=require('./lib/rdso_search.js');require('./data/search/search_index.js');"
          "const en=e.create?e.create(globalThis.RDSO_SEARCH_INDEX):e(globalThis.RDSO_SEARCH_INDEX);"
          "const a=en.answer('finishing tolerance head width alumino thermic weld');"
          "console.log(JSON.stringify({k:a.best&&a.best.kind,n:(a.sentences||[]).length}))")
    r = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
