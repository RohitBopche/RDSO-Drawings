"""P6.1 / P7.2: extractive answers are verifiable; feedback becomes review work, never silent truth."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_feedback as fbk  # noqa: E402


def node(js):
    r = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def answer(q):
    return node("require('./data/search/search_index.js');const S=require('./lib/rdso_search.js');"
                "const e=S.create(globalThis.RDSO_SEARCH_INDEX);const a=e.answer(" + json.dumps(q) + ");"
                "console.log(JSON.stringify({status:a.status,conf:a.confidence,cov:a.coverage,best:a.best&&a.best.clause,text:a.best&&a.best.text,"
                "sents:(a.sentences||[]).map(s=>[s.start,s.end,s.text])}))")


def test_answer_sentences_are_verbatim_slices_of_the_cited_passage():
    a = answer("What is the shortest rail piece allowed as a closure rail?")
    b = answer("Who has the authority to order a material train?")
    for r in (a, b):
        if r["status"] == "answer":
            assert r["sents"]
            for start, end, text in r["sents"]:
                assert r["text"][start:end] == text            # offsets reproduce the sentence exactly
    assert b["status"] == "answer" and b["best"] == "CLAUSE:IRPWM:CH_08:PARA_847"


def test_out_of_scope_gets_no_evidence_and_no_sentences():
    a = answer("What is the recipe for butter chicken?")
    assert a["status"] == "no_evidence" and a["sents"] == []


def test_paragraph_number_query_is_always_answered():
    a = answer("IRPWM 2024 225")
    assert a["status"] == "answer" and a["best"] == "CLAUSE:IRPWM:CH_02:PARA_225" and a["conf"] == "high"


def test_no_active_curated_answer_claims_verified():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    a = html.index("const CANONICAL_QA_DATABASE = [")
    b = html.index("function detectQuestionIntent")
    assert 'status: "VERIFIED"' not in html[a:b]
    assert html[a:b].count("retired: true") == 6                # manual-cited hand answers were retired


def test_feedback_ingest_builds_queue_gaps_and_candidates(tmp_path):
    (tmp_path / "data/knowledge-graph/intermediate").mkdir(parents=True)
    (tmp_path / "data/knowledge-graph/intermediate/review_queue.jsonl").write_text(
        json.dumps({"review_id": "OCR:x:1", "topic": "kept"}) + "\n", encoding="utf-8")
    (tmp_path / "eval").mkdir()
    log = tmp_path / "log.jsonl"
    log.write_text("\n".join(json.dumps(r) for r in [
        {"ts": "2026-10-01T10:00:00Z", "type": "query", "query": "coach cleaning procedure?", "status": "no_evidence", "coverage": 0.1},
        {"ts": "2026-10-01T10:01:00Z", "type": "query", "query": "Coach cleaning procedure", "status": "no_evidence", "coverage": 0.1},
        {"ts": "2026-10-01T10:02:00Z", "type": "feedback", "query": "monsoon patrol duties", "clause": "CLAUSE:IRPWM:CH_10:PARA_1003", "verdict": "up"},
        {"ts": "2026-10-01T10:03:00Z", "type": "feedback", "query": "gauge in points", "clause": "CLAUSE:IRPWM:CH_04:PARA_418", "verdict": "down"},
        {"ts": "2026-10-01T10:04:00Z", "type": "junk"},
    ]) + "\n", encoding="utf-8")
    first = fbk.ingest([log], root=tmp_path)
    assert first == {"events": 4, "review_items": 2, "gaps": 1, "candidates": 1}
    queue = [json.loads(l) for l in (tmp_path / "data/knowledge-graph/intermediate/review_queue.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(q["review_id"] == "OCR:x:1" for q in queue)                              # other queue items survive
    assert sum(q["review_id"].startswith("FB:gap") for q in queue) == 1                 # duplicate wording collapses
    assert any(q["review_id"].startswith("FB:down") and q["priority"] == "HIGH" for q in queue)
    gaps = json.loads((tmp_path / "data/knowledge-graph/reports/knowledge_gaps.json").read_text(encoding="utf-8"))
    assert gaps["refused_queries"] == [{"query": "coach cleaning procedure", "count": 2}]
    cand = [json.loads(l) for l in (tmp_path / "eval/candidates.jsonl").read_text(encoding="utf-8").splitlines()]
    assert cand[0]["label_status"] == "user_confirmed_unreviewed"
    assert fbk.ingest([log], root=tmp_path) == first                                    # idempotent
