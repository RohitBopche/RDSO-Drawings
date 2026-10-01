"""P1-R.1: the browser reads the canonical store only; provision cards show canonical text."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_index_html_has_no_legacy_manuals_view():
    html = (ROOT / "expert.html").read_text(encoding="utf-8")
    assert "RDSO_MANUALS_KNOWLEDGE" not in html
    assert not (ROOT / "data" / "rdso_manuals_knowledge.json").exists()


def test_export_bundle_does_not_emit_legacy_view():
    assert "RDSO_MANUALS_KNOWLEDGE" not in (ROOT / "scripts" / "export_kg_bundle.py").read_text(encoding="utf-8")
    bundle = (ROOT / "data" / "rdso_kg_data.js").read_text(encoding="utf-8")
    assert "_root.RDSO_MANUALS_KNOWLEDGE" not in bundle


def test_clause_card_reads_canonical_text_field():
    html = (ROOT / "expert.html").read_text(encoding="utf-8")
    assert re.search(r"const verbatim = data\.text \|\|", html)
    assert "data.tolerance_texts" in html and "data.roles" in html
