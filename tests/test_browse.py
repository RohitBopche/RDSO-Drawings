"""lib/rdso_browse.js rebuilds every clause of the six manuals, with text identical to the canonical graph."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_browse_model_reproduces_all_clauses():
    nodes = {}
    for line in (ROOT / "data/knowledge-graph/canonical/nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if n.get("type") == "CLAUSE" and n["id"].split(":")[1] in {"IRPWM", "TMM", "STMM", "USFD", "AT_WELD", "FBW"}:
            nodes[n["id"]] = n
    js = r"""
    const fs=require('fs');global.window=global;
    const src=fs.readFileSync('data/search/search_index.js','utf8');new Function('window','globalThis',src)(global,global);
    const B=require('./lib/rdso_browse.js');const m=B.build(global.RDSO_SEARCH_INDEX);
    const o={};Object.keys(m.byId).forEach(k=>o[k]=m.byId[k].text);
    console.log(JSON.stringify({texts:o,counts:m.manuals.map(x=>[x.alias,x.count]),par:[B.parentPara('FBW','13.1.1'),B.parentPara('IRPWM','616')]}));
    """
    out = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    got = json.loads(out)
    clause_ids = {i for i in got["texts"] if i.startswith("CLAUSE:")}
    assert clause_ids == set(nodes)                                    # every paragraph, no more
    annex = {i for i in got["texts"] if i.startswith("ANNEX:")}
    units = [json.loads(l) for l in (ROOT / "data/knowledge-graph/canonical/annexures.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert annex == {u["id"] for u in units}                           # every annexure, appendix, loose-text run and front matter unit
    assert all(" ".join(got["texts"][u["id"]].split()) == " ".join(u["text"].split()) for u in units)
    bad = [i for i in nodes if " ".join(got["texts"][i].split()) != " ".join((nodes[i].get("text") or "").split())]
    assert not bad, bad[:5]
    assert dict(got["counts"]) == {"IRPWM": 421, "TMM": 171, "STMM": 258, "USFD": 192, "AT_WELD": 73, "FBW": 57}
    assert got["par"] == ["13.1", None]
