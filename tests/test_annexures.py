"""Annexure units: verbatim page text, valid page ranges, every manual covered; and the line-by-line coverage of the manuals stays high."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data/knowledge-graph"


def _units():
    return [json.loads(l) for l in (KG / "canonical/annexures.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def test_every_unit_line_is_verbatim_page_text_within_its_page_range():
    pages = {}
    for l in (KG / "raw/extracted_pages.jsonl").read_text(encoding="utf-8").splitlines():
        p = json.loads(l)
        pages[(p["document_id"].split(":")[1], p["page_number"])] = _norm(p.get("text_content") or "")
    for u in _units():
        assert 1 <= u["page"] <= u["page_end"], u["id"]
        blob = "".join(pages.get((u["manual"], n), "") for n in range(u["page"], u["page_end"] + 1))
        lines = [l for l in u["text"].split("\n") if l.strip()]
        assert lines, u["id"]
        missing = [l for l in lines if _norm(l) not in blob]
        assert not missing, (u["id"], missing[:2])


def test_all_six_manuals_have_annexure_units_and_ids_are_unique():
    units = _units()
    assert len({u["id"] for u in units}) == len(units)
    for alias, floor in {"IRPWM": 60, "TMM": 60, "STMM": 3, "USFD": 8, "AT_WELD": 8, "FBW": 12}.items():
        assert sum(1 for u in units if u["manual"] == alias and u.get("unit") is None) >= floor, alias


def test_line_by_line_coverage_of_every_manual_is_at_least_98_percent():
    out = subprocess.run([sys.executable, "scripts/coverage_audit.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    report = json.loads((KG / "reports/coverage_audit.json").read_text(encoding="utf-8"))
    for alias, r in report.items():
        assert r["uncovered_share"] <= 0.015, (alias, r["uncovered_share"], r["worst_pages"][:2])
