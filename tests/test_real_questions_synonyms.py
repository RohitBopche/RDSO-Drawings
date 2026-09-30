"""Sprint H: double-labelled real questions and reviewed synonyms."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import apply_reviewed_synonyms as S  # noqa: E402
import ingest_real_questions as R  # noqa: E402

REFS = {"IRPWM 506", "IRPWM 429", "USFD 8.10"}


def q(text, a, b):
    return {"question": text, "asked_by": "e", "labels": [dict(labeller="A", **a), dict(labeller="B", **b)]}


def test_agreeing_labels_are_accepted_and_disagreements_held_back():
    data = {"questions": [
        q("q1", {"gold": ["IRPWM 506"], "no_answer": False}, {"gold": ["IRPWM 506", "IRPWM 429"], "no_answer": False}),
        q("q2", {"gold": [], "no_answer": True}, {"gold": [], "no_answer": True}),
        q("q3", {"gold": ["IRPWM 506"], "no_answer": False}, {"gold": [], "no_answer": True}),
        q("q4", {"gold": ["IRPWM 506"], "no_answer": False}, {"gold": ["USFD 8.10"], "no_answer": False}),
    ]}
    acc, stats, errors = R.process(data, REFS)
    assert errors == []
    assert [a["question"] for a in acc] == ["q1", "q2"]
    assert acc[0]["gold"] == ["IRPWM 506"]
    assert stats["disagreements"] == 2 and stats["exact_set_agreement"] == 0.25


def test_single_labeller_unknown_ref_and_examples_rejected():
    data = {"questions": [
        {"question": "x", "labels": [{"labeller": "A", "gold": ["IRPWM 506"], "no_answer": False}]},
        {"question": "y", "labels": [{"labeller": "A", "gold": ["IRPWM 506"]}, {"labeller": "A", "gold": ["IRPWM 506"]}]},
        q("z", {"gold": ["IRPWM 9999"], "no_answer": False}, {"gold": ["IRPWM 9999"], "no_answer": False}),
        {"_example": True, "question": "ignored"},
    ]}
    acc, stats, errors = R.process(data, REFS)
    assert acc == [] and len(errors) == 3 and stats["questions"] == 3


def test_kappa():
    assert R.kappa([(True, True), (False, False), (True, True), (False, False)]) == 1.0
    assert R.kappa([(True, False), (False, True)]) == -1.0


CORPUS = "the switch expansion joint is fitted where a long welded rail ends"


def test_synonym_rules():
    syn = {"groups": [["lwr", "long welded rail"]]}
    good = {"group": ["SEJ", "switch expansion joint"], "reviewer": "r", "evidence": ["IRPWM 506"]}
    ok, err = S.validate([good], syn, CORPUS, REFS)
    assert len(ok) == 1 and not err
    bad = [
        {"group": ["only one"], "reviewer": "r", "evidence": ["IRPWM 506"]},
        {**good, "reviewer": " "},
        {**good, "evidence": ["IRPWM 1"]},
        {"group": ["zzz", "qqq"], "reviewer": "r", "evidence": ["IRPWM 506"]},
        {"group": ["LWR", "Long Welded Rail"], "reviewer": "r", "evidence": ["IRPWM 506"]},
    ]
    ok, err = S.validate(bad, syn, CORPUS, REFS)
    assert ok == [] and len(err) == 5
