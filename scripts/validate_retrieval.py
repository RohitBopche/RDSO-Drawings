#!/usr/bin/env python3
"""Gate P: retrieval index freshness, eval-set integrity and no retrieval regression.

- the search index covers exactly the canonical clauses and their current text
- every eval question has valid gold clause ids (or is an out-of-scope refusal), a split, a category
- the dev/test split has both halves and no question appears twice
- test-split and dev-split Recall@5 / MRR have not dropped below eval/baseline.json (tolerance 0.01)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"


def main() -> int:
    errors: list[str] = []
    nodes = [json.loads(l) for l in (KG / "canonical" / "nodes.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    clauses = {n["id"]: n for n in nodes if n["id"].startswith("CLAUSE:")}

    # index freshness: node reads the index exactly as the browser does
    probe = ("require('./data/search/search_index.js');const i=globalThis.RDSO_SEARCH_INDEX;"
             "const by={};i.docs.forEach(d=>{if(d.type==='CLAUSE'&&!d.kind){by[d.clause]=(by[d.clause]||'')+' '+d.text;}});"
             "console.log(JSON.stringify({n:i.docs.length,by}))")
    r = subprocess.run(["node", "-e", probe], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        errors.append(f"cannot load data/search/search_index.js: {r.stderr[:200]}")
    else:
        idx = json.loads(r.stdout)["by"]
        if set(idx) != set(clauses):
            errors.append(f"search index clause set differs from canonical ({len(idx)} vs {len(clauses)}); run scripts/build_search_index.py")
        else:
            stale = [c for c, n in clauses.items() if " ".join(idx[c].split()) != " ".join(n["text"].split())]
            if stale:
                errors.append(f"search index text is stale for {len(stale)} clauses (e.g. {stale[0]})")

    # eval set integrity
    qpath = ROOT / "eval" / "questions.jsonl"
    qs = [json.loads(l) for l in qpath.read_text(encoding="utf-8").splitlines() if l.strip()]
    seen = set()
    for q in qs:
        if q["question"] in seen:
            errors.append(f"{q['id']}: duplicate question")
        seen.add(q["question"])
        if q["split"] not in ("dev", "test"):
            errors.append(f"{q['id']}: bad split")
        if q["expect"] == "answer":
            if not q["gold"] or any(g not in clauses for g in q["gold"]):
                errors.append(f"{q['id']}: gold clause missing from canonical: {q['gold']}")
        elif q["gold"]:
            errors.append(f"{q['id']}: refusal question must have no gold")
    cats = Counter((q["split"], q["category"]) for q in qs)
    for split in ("dev", "test"):
        if not any(k[0] == split and k[1] == "nl" for k in cats):
            errors.append(f"no natural-language questions in {split}")
    if len(qs) < 300:
        errors.append(f"eval set shrank to {len(qs)} questions")

    # regression against baseline
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "eval_retrieval.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        errors.append("retrieval regression vs eval/baseline.json:\n" + "\n".join(r.stdout.splitlines()[-8:]))

    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_curated_answers.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        errors.append("curated answers:\n" + "\n".join(l for l in r.stdout.splitlines() if l.startswith("[ERROR]")))

    # the engine's refusal threshold must equal the one chosen on dev (eval/baseline.json)
    base = json.loads((ROOT / "eval" / "baseline.json").read_text(encoding="utf-8"))
    m = re.search(r"opts\.refuseBelow == null \? ([0-9.]+)", (ROOT / "lib" / "rdso_search.js").read_text(encoding="utf-8"))
    if not m or abs(float(m.group(1)) - base["threshold"]) > 1e-9:
        errors.append(f"lib/rdso_search.js refuseBelow ({m.group(1) if m else '?'}) differs from eval/baseline.json threshold ({base['threshold']})")

    for e in errors[:20]:
        print(f"[ERROR] {e}")
    print(f"[SUMMARY] retrieval: {'FAIL' if errors else 'PASS'}; passages_index_ok={not errors} questions={len(qs)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
