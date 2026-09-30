"""P0-R.7: every image-only manual page is OCR'd, and weak results are queued for review."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def test_gate_o_passes():
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_ocr_coverage.py")],
                         capture_output=True, text=True, cwd=ROOT)
    assert res.returncode == 0, res.stdout + res.stderr


def test_ocr_records_have_engine_and_hash():
    rows = [json.loads(l) for l in (ROOT / "data/knowledge-graph/raw/ocr_pages.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 64
    assert all(r["engine"].startswith("rapidocr") and len(r["pdf_sha256"]) == 64 for r in rows)


def test_gate_o_detects_missing_ocr_record(tmp_path, monkeypatch):
    import validate_ocr_coverage as g
    kg = tmp_path / "kg"
    shutil.copytree(ROOT / "data" / "knowledge-graph", kg, ignore=shutil.ignore_patterns("exports", "canonical"))
    ocr = kg / "raw" / "ocr_pages.jsonl"
    rows = ocr.read_text(encoding="utf-8").splitlines()
    ocr.write_text("\n".join(rows[1:]) + "\n", encoding="utf-8")
    monkeypatch.setattr(g, "KG", kg)
    assert g.main() == 1
