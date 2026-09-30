#!/usr/bin/env python3
"""Audit the hand-written answers in index.html (CANONICAL_QA_DATABASE) against the source text.

For each curated answer this checks every number written in its statement and parameter table against
the text of the manual clauses it cites (clause ids in `traversal`, `provenance.clause` and "Para N"
mentions). A number that does not occur in any cited clause is reported as unsupported. Answers about
drawings only (no manual citation) are reported as `uncited`: they cannot be checked against the manuals.

    python scripts/audit_curated_answers.py            # print the report
    python scripts/audit_curated_answers.py --write    # write data/knowledge-graph/reports/curated_answers_audit.json
    python scripts/audit_curated_answers.py --check    # Gate P: no active curated answer with numbers its cited clauses lack,
                                                       # and none may claim status VERIFIED
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "knowledge-graph" / "reports" / "curated_answers_audit.json"
NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?=\s*(?:mm|kg|km|kmph|m\b|%|deg|°|t\b|mpa|nos|sets|khz|mhz|days?|months?|years?))", re.I)


def load_answers() -> list[dict]:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    a = html.index("const CANONICAL_QA_DATABASE = [")
    b = html.index("];", a) + 2
    js = html[a:b].replace("const CANONICAL_QA_DATABASE =", "module.exports =")
    tmp = ROOT / "scratch_qa_extract.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        r = subprocess.run(["node", "-e", "console.log(JSON.stringify(require('./scratch_qa_extract.js')))"],
                           cwd=ROOT, capture_output=True, text=True)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return json.loads(r.stdout)


def main() -> int:
    nodes = {}
    for l in (ROOT / "data/knowledge-graph/canonical/nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(l)
        nodes[n["id"]] = n
    by_para = {(i.split(":")[1], str(n["specs"]["Paragraph"])): i for i, n in nodes.items() if i.startswith("CLAUSE:")}
    report = []
    answers = load_answers()
    for ans in answers:
        blob = json.dumps({"s": ans.get("statement", ""), "p": ans.get("params", [])})
        cited = {t["id"] for t in ans.get("traversal", []) if t["id"] in nodes and t["id"].startswith("CLAUSE:")}
        prov = ans.get("provenance", {})
        for m in re.finditer(r"\b(IRPWM|USFD|TMM|STMM|FBW|AT_WELD)?[^.;]{0,20}?Paras?\s*(\d+(?:\.\d+)*)", json.dumps(prov) + blob):
            alias = m.group(1) or "IRPWM"
            if (alias, m.group(2)) in by_para:
                cited.add(by_para[(alias, m.group(2))])
        text = " ".join(nodes[c]["text"] for c in cited)
        numbers = sorted({m.group(1) for m in NUM.finditer(blob)})
        unsupported = [n for n in numbers if not re.search(r"(?<![\d.])" + re.escape(n) + r"(?![\d])", text)]
        report.append({"id": ans["id"], "question": ans["question"], "cited_clauses": sorted(cited),
                       "numbers_checked": numbers, "unsupported_numbers": unsupported if cited else [],
                       "retired": bool(ans.get("retired")), "status": prov.get("status"),
                       "verdict": "uncited" if not cited else ("unsupported" if unsupported else "supported")})
    for r in report:
        print(f"{r['verdict']:<12} {r['id']:<34} cited={len(r['cited_clauses'])} unsupported={r['unsupported_numbers']}")
    if "--check" in sys.argv:
        bad = [r["id"] for r in report if not r["retired"] and r["verdict"] == "unsupported"]
        bad += [r["id"] + " (status VERIFIED)" for r in report if r["status"] == "VERIFIED"]
        for b in bad:
            print("[ERROR] curated answer not allowed:", b)
        return 1 if bad else 0
    if "--write" in sys.argv:
        OUT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
