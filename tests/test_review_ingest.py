"""Sprint N: review packets and ingestion."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_reviews as R  # noqa: E402
import provenance_policy as P  # noqa: E402

KNOWN = {"clause": {"CLAUSE:A:1"}, "xref": {"XREF:00001"}, "measurement": {"MEAS:000001"}, "table": set(), "drawing_link": set()}


def dec(kind, tid, d, note=""):
    return {"kind": kind, "target_id": tid, "decision": d, "note": note}


def test_process_routes_kinds_and_counts_unsure():
    f = {"reviewer": "Asha", "packet_seed": 1, "decisions": [dec("clause", "CLAUSE:A:1", "approved"), dec("xref", "XREF:00001", "rejected", "not a ref"),
                                                              dec("measurement", "MEAS:000001", "unsure")]}
    c, o, errors, unsure = R.process([f], KNOWN, set(), "t")
    assert [r["target_ids"] for r in c] == [["CLAUSE:A:1"]] and o[0]["decision"] == "rejected" and unsure == 1 and errors == []


def test_bad_input_rejected_and_duplicates_skipped():
    f = {"reviewer": "Asha", "decisions": [dec("clause", "CLAUSE:NOPE", "approved"), dec("xref", "CLAUSE:A:1", "approved"),
                                           dec("clause", "CLAUSE:A:1", "maybe"), dec("clause", "CLAUSE:A:1", "approved")]}
    c, o, errors, _ = R.process([f], KNOWN, set(), "t")
    assert len(c) == 1 and len(errors) == 3
    c2, _, e2, _ = R.process([f], KNOWN, {("CLAUSE:A:1", "Asha")}, "t")
    assert c2 == [] and any("already reviewed" in e for e in e2)
    _, _, e3, _ = R.process([{"reviewer": " ", "decisions": []}], KNOWN, set(), "t")
    assert e3


def test_two_approvals_verify_and_rejection_disputes():
    f1 = {"reviewer": "A", "decisions": [dec("clause", "CLAUSE:A:1", "approved")]}
    f2 = {"reviewer": "B", "decisions": [dec("clause", "CLAUSE:A:1", "approved")]}
    c, _, _, _ = R.process([f1, f2], KNOWN, set(), "t")
    assert P.review_status(c)["CLAUSE:A:1"] == "verified"
    f3 = {"reviewer": "C", "decisions": [dec("clause", "CLAUSE:A:1", "rejected")]}
    c3, _, _, _ = R.process([f1, f3], KNOWN, set(), "t")
    assert P.review_status(c3)["CLAUSE:A:1"] == "disputed"


def test_accuracy_report_and_agreement():
    recs = [{"kind": "xref", "target_ids": ["X1"], "decision": "approved", "reviewer": "A"},
            {"kind": "xref", "target_ids": ["X1"], "decision": "approved", "reviewer": "B"},
            {"kind": "xref", "target_ids": ["X2"], "decision": "rejected", "reviewer": "A"},
            {"kind": "xref", "target_ids": ["X2"], "decision": "approved", "reviewer": "B"}]
    a = R.accuracy(recs, 2)
    assert a["by_kind"]["xref"]["reviewed"] == 4 and a["by_kind"]["xref"]["wrong"] == 1
    assert a["double_reviewed_items"] == 2 and a["reviewer_agreement"] == 0.5 and a["unsure_not_recorded"] == 2
    lo, hi = R.wilson(1, 4)
    assert 0 < lo < 0.25 < hi < 1


def test_packet_is_reproducible_and_sampled():
    import make_review_packet as M
    a, _ = M.build(2, 3)
    b, _ = M.build(2, 3)
    assert [i["target_id"] for i in a] == [i["target_id"] for i in b]
    assert {i["kind"] for i in a} == set(M.KINDS) and len(a) == 10
    assert all(i["image"].startswith("data:image/png") for i in a if i["kind"] != "table")
