"""Every learning card is a verbatim slice of a manual paragraph with one measured value hidden; no hand-written learning content remains."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_learning as L  # noqa: E402


def _nodes():
    out = {}
    for line in (ROOT / "data/knowledge-graph/canonical/nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if n["id"].startswith("CLAUSE:"):
            out[n["id"]] = n
    return out


def _flat(t):
    return " ".join(t.split())


def test_cards_are_committed_and_reproducible():
    cards = json.loads((ROOT / "data/learning/cards.json").read_text(encoding="utf-8"))
    assert cards == L.build() and len(cards) >= 100
    assert (ROOT / "data/learning/cards.js").read_text(encoding="utf-8").startswith("(typeof window")


def test_every_card_is_grounded_in_its_paragraph():
    nodes = _nodes()
    meas = {m["measurement_id"]: m for m in map(json.loads, (ROOT / "data/knowledge-graph/canonical/measurements.jsonl").read_text(encoding="utf-8").splitlines())}
    for c in json.loads((ROOT / "data/learning/cards.json").read_text(encoding="utf-8")):
        n = nodes[c["clause"]]
        assert c["sentence"] in _flat(n["text"]), c["id"]                      # verbatim slice of the paragraph
        assert c["front"].count("_____") == 1 and c["front"].replace("_____", c["answer"]) == c["sentence"], c["id"]
        assert c["answer"] in _flat(meas[c["measurement"]]["raw"]) and meas[c["measurement"]]["clause"] == c["clause"], c["id"]
        assert c["page"] == n["page"] and c["manual"] == c["clause"].split(":")[1], c["id"]
        assert len(c["options"]) == 4 and c["options"][c["correct"]] == c["answer"], c["id"]
        assert len({L.canonical(o) for o in c["options"]}) == 4, c["id"]        # no two options are the same value spelled differently


def test_no_hand_written_learning_content_in_the_expert_page():
    html = (ROOT / "expert.html").read_text(encoding="utf-8")
    assert "window.CANONICAL_FLASHCARDS = [];" in html and "window.CANONICAL_QUIZ_QUESTIONS = [];" in html
    assert "RDSO-ACS14-AUTH-99824" not in html and "CERTIFICATE OF ENGINEERING COMPETENCY" not in html
    assert "const CANONICAL_QUIZ_QUESTIONS = [\n" not in html and "CANONICAL_LEARNING_TRACKS = [\n" not in html
