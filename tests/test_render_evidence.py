"""P2.2: highlighted evidence crops are rendered from the stored regions, offline."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_evidence as re_  # noqa: E402


def _ev(eid):
    for l in (ROOT / "data/knowledge-graph/canonical/evidence.jsonl").read_text(encoding="utf-8").splitlines():
        e = json.loads(l)
        if e["evidence_id"] == eid:
            return e


def test_crop_is_rendered_and_contains_highlight_colour(tmp_path):
    from PIL import Image
    reg = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data/knowledge-graph/raw/source_registry.jsonl").read_text(encoding="utf-8").splitlines()}
    e = _ev("ev:clause:CLAUSE:IRPWM:CH_04:PARA_429")
    path = re_.render(e, reg, dpi=60, out_dir=tmp_path)
    assert path and path.exists()
    img = Image.open(path).convert("RGB")
    assert img.width > 300 and 40 < img.height < 700          # a crop around the text, not the whole page
    yellow = sum(1 for px in img.getdata() if px[0] > 240 and px[1] > 200 and px[2] < 150)
    assert yellow > 500                                         # the cited lines are highlighted


def test_evidence_without_region_is_skipped(tmp_path):
    assert re_.render({"evidence_id": "ev:x", "document_id": "DOC:X"}, {}, out_dir=tmp_path) is None


def test_viewer_wires_the_crop_and_falls_back_to_the_pdf():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "manual-pdf-evidence-img" in html and "artifacts/evidence/" in html
    assert "cropImg.onerror" in html                            # no crop rendered -> plain PDF page as before
