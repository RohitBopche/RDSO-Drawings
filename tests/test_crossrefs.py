"""P2.1: cross-reference extraction and classification."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import crossrefs  # noqa: E402


def node(cid, text, para="1", page=1, typ="CLAUSE"):
    return {"id": cid, "type": typ, "label": "x", "text": text, "page": page, "specs": {"Paragraph": para}, "domain": "manual"}


def run(text, extra=None, deleted=None):
    nodes = [node("CLAUSE:IRPWM:CH_01:PARA_101", text, "101"),
             node("CLAUSE:IRPWM:CH_01:PARA_105", "target", "105"),
             node("CLAUSE:IRPWM:CH_06:PARA_619", "target", "619"),
             node("CLAUSE:IRPWM:CH_06:PARA_620", "target", "620"),
             {"id": "CHAPTER:IRPWM:CH_04", "type": "CHAPTER", "label": "c", "specs": {}}] + (extra or [])
    return crossrefs.extract(nodes, deleted or {"IRPWM": ["517"]})


def test_paragraph_lists_are_split_and_resolved():
    refs = [r for r in run("See Paras 619 and 620 for details.") if r["target_kind"] == "para"]
    assert [(r["number"], r["status"]) for r in refs] == [("619", "RESOLVED"), ("620", "RESOLVED")]
    assert refs[0]["targets"] == ["CLAUSE:IRPWM:CH_06:PARA_619"]


def test_back_reference_is_typed_and_subparagraph_kept():
    r = run("General - (Back to Para 105) and Para 619(3)(a) applies.")
    kinds = {x["number"]: (x["kind"], x["subref"]) for x in r if x["target_kind"] == "para"}
    assert kinds["105"][0] == "back_ref" and kinds["619"] == ("para", "(3)(a)")


def test_deleted_and_missing_paragraphs_are_distinguished():
    r = {x["number"]: x["status"] for x in run("Refer Para 517 and Para 999.") if x["target_kind"] == "para"}
    assert r == {"517": "DELETED", "999": "NOT_FOUND"}


def test_paragraph_of_another_document_is_external():
    r = [x for x in run("as per Para 1405 of Indian Railway Code for Engineering Department") if x["target_kind"] == "para"]
    assert r[0]["status"] == "EXTERNAL" and "Code" in r[0]["scope_name"]


def test_standards_are_external_and_the_verb_is_is_not_a_standard():
    r = run("conform to IS 456 and IRS T-19-2021, which is 720 mm wide")
    std = [x["raw"] for x in r if x["target_kind"] == "standard"]
    assert any("IS 456" in s for s in std) and any("IRS" in s for s in std) and not any(s.lower().startswith("is 720") for s in std)


def test_chapter_reference_resolves():
    r = [x for x in run("see Chapter 4 and Chapter 9") if x["target_kind"] == "chapter"]
    assert [(x["number"], x["status"]) for x in r] == [("4", "RESOLVED"), ("9", "NOT_FOUND")]


def test_annexure_number_does_not_swallow_following_words():
    extra = [{"id": "EVIDENCE:IRPWM:CH_08:P1:01", "type": "EVIDENCE", "label": "Annexure - 8/8", "source_page": 5, "domain": "manual"}]
    r = [x for x in run("bond in Annexure - 8/8 en route", extra) if x["target_kind"] == "annexure"]
    assert r[0]["number"] == "8/8" and r[0]["status"] == "RESOLVED"


def test_canonical_crossrefs_have_no_unclassified_records():
    refs = [json.loads(l) for l in (ROOT / "data/knowledge-graph/canonical/crossrefs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(refs) > 1000
    assert {r["status"] for r in refs} <= {"RESOLVED", "DELETED", "EXTERNAL", "AMBIGUOUS", "NOT_FOUND"}
