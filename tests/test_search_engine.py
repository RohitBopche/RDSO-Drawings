"""P5.1: the offline search engine (lib/rdso_search.js) and the retrieval eval set."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def node(js: str):
    r = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def search(query, **opts):
    js = ("require('./data/search/search_index.js');const S=require('./lib/rdso_search.js');"
          "const e=S.create(globalThis.RDSO_SEARCH_INDEX);"
          f"const r=e.search({json.dumps(query)},{json.dumps(opts)});"
          "console.log(JSON.stringify({top:r.results.map(x=>x.clause),cov:r.coverage,hit:r.identifierHit,manuals:r.manuals,paras:r.paras,terms:r.terms}))")
    return node(js)


def test_stemmer_and_normalisation():
    out = node("const S=require('./lib/rdso_search.js');console.log(JSON.stringify([S.analyze('1 in 12 turnout, 1:12 and 60 kg rails'),"
               "S.analyze('fractured rails renewals'),S.analyze('Para 8.2.4 of SSE/P.Way')]))")
    assert "1in12" in out[0] and out[0].count("1in12") == 2 and "60kg" in out[0]
    assert out[1] == ["fractur", "rail", "renew"]
    assert "8.2.4" in out[2]


def test_paragraph_number_query_finds_the_paragraph():
    r = search("Para 429 IRPWM")
    assert r["top"][0] == "CLAUSE:IRPWM:CH_04:PARA_429" and r["hit"]


def test_manual_name_scopes_and_year_is_not_a_paragraph():
    r = search("IRPWM 2024 225")
    assert r["paras"] == ["225"] and r["top"][0] == "CLAUSE:IRPWM:CH_02:PARA_225"
    r = search("clause 710 of small track machines manual")
    assert r["manuals"] == ["STMM"] and r["top"][0] == "CLAUSE:STMM:CH_07:PARA_710"


def test_natural_language_question_retrieves_the_clause():
    r = search("How is casual renewal of a defective or fractured rail carried out?")
    assert r["top"][0] == "CLAUSE:IRPWM:CH_06:PARA_616" and r["cov"] > 0.7


def test_abbreviation_expands_to_the_spelled_out_form():
    assert "flaw" in " ".join(node("require('./data/search/search_index.js');const S=require('./lib/rdso_search.js');"
                                   "const e=S.create(globalThis.RDSO_SEARCH_INDEX);"
                                   "console.log(JSON.stringify(e.search('USFD testing').expanded))"))


def test_out_of_scope_question_has_low_evidence_coverage():
    assert search("Who won the cricket world cup in 2011?")["cov"] < 0.3


def test_eval_set_composition():
    qs = [json.loads(l) for l in (ROOT / "eval/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    cats = {q["category"] for q in qs}
    assert {"nl", "ident", "title_auto", "kw_auto", "oos"} <= cats
    assert sum(q["category"] == "nl" for q in qs) >= 100 and sum(q["expect"] == "refuse" for q in qs) >= 20
    assert all(q["split"] in ("dev", "test") for q in qs)
