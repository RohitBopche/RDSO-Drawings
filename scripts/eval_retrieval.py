#!/usr/bin/env python3
"""Evaluate retrieval against eval/questions.jsonl (P7.1).

    python scripts/eval_retrieval.py            # print dev + test report
    python scripts/eval_retrieval.py --write    # also write eval/baseline.json (deliberate act)
    python scripts/eval_retrieval.py --check    # fail if test-split metrics regress vs baseline

Metrics per category and split: Recall@1/3/5/10, MRR. For out-of-scope questions the report gives
the refusal rate at the coverage threshold; for answerable ones the false-refusal rate.
The refusal threshold is chosen on the dev split only (maximise balanced accuracy) and then
applied unchanged to the test split.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "eval" / "questions.jsonl"
BASELINE = ROOT / "eval" / "baseline.json"
TOLERANCE = 0.01


def load_questions() -> list[dict]:
    return [json.loads(l) for l in QUESTIONS.read_text(encoding="utf-8").splitlines() if l.strip()]


def run_engine(questions: list[dict]) -> dict[str, dict]:
    r = subprocess.run(["node", str(ROOT / "scripts" / "search_cli.js"), "--batch", str(QUESTIONS)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return {x["id"]: x for x in json.loads(r.stdout)}


def rank_of(gold: list[str], results: list[dict]) -> int | None:
    for i, res in enumerate(results, 1):
        if res["clause"] in gold:
            return i
    return None


def refused(o: dict, threshold: float) -> bool:
    """Search-level refusal: too little of the question is covered by the best passage and no
    paragraph number in the question resolved to a clause."""
    return o["coverage"] < threshold and not o.get("identifierHit")


def choose_threshold(questions, out) -> float:
    dev = [q for q in questions if q["split"] == "dev"]
    best, best_t = -1.0, 0.0
    for t in [x / 100 for x in range(0, 101, 2)]:
        ans = [q for q in dev if q["expect"] == "answer"]
        ref = [q for q in dev if q["expect"] == "refuse"]
        if not ans or not ref:
            continue
        tpr = sum(refused(out[q["id"]], t) for q in ref) / len(ref)            # refused correctly
        tnr = sum(not refused(out[q["id"]], t) for q in ans) / len(ans)        # answered correctly
        bal = (tpr + tnr) / 2
        if bal > best + 1e-9:
            best, best_t = bal, t
    return best_t


def evaluate(questions, out, threshold) -> dict:
    report: dict = {"threshold": threshold, "splits": {}}
    for split in ("dev", "test"):
        cats: dict[str, dict] = defaultdict(lambda: {"n": 0, "r1": 0, "r3": 0, "r5": 0, "r10": 0, "mrr": 0.0, "ranks": []})
        refuse = {"n": 0, "refused": 0}
        answerable = {"n": 0, "refused": 0}
        for q in (q for q in questions if q["split"] == split):
            o = out[q["id"]]
            if q["expect"] == "refuse":
                refuse["n"] += 1
                refuse["refused"] += refused(o, threshold)
                continue
            rk = rank_of(q["gold"], o["results"])
            answerable["n"] += 1
            answerable["refused"] += refused(o, threshold)
            for key in (q["category"], "ALL"):
                c = cats[key]
                c["n"] += 1
                if rk:
                    c["r1"] += rk <= 1
                    c["r3"] += rk <= 3
                    c["r5"] += rk <= 5
                    c["r10"] += rk <= 10
                    c["mrr"] += 1 / rk
        report["splits"][split] = {
            "categories": {k: {"n": v["n"], "recall@1": round(v["r1"] / v["n"], 3), "recall@3": round(v["r3"] / v["n"], 3),
                               "recall@5": round(v["r5"] / v["n"], 3), "recall@10": round(v["r10"] / v["n"], 3),
                               "mrr": round(v["mrr"] / v["n"], 3)} for k, v in sorted(cats.items())},
            "refusal": {"out_of_scope": refuse["n"], "correctly_refused": refuse["refused"],
                        "answerable": answerable["n"], "wrongly_refused": answerable["refused"]},
        }
    return report


def print_report(report):
    print(f"refusal threshold (chosen on dev): coverage < {report['threshold']}")
    for split, data in report["splits"].items():
        print(f"\n== {split} ==")
        print(f"{'category':<12}{'n':>5}{'R@1':>8}{'R@3':>8}{'R@5':>8}{'R@10':>8}{'MRR':>8}")
        for k, v in data["categories"].items():
            print(f"{k:<12}{v['n']:>5}{v['recall@1']:>8}{v['recall@3']:>8}{v['recall@5']:>8}{v['recall@10']:>8}{v['mrr']:>8}")
        r = data["refusal"]
        print(f"refusal: {r['correctly_refused']}/{r['out_of_scope']} out-of-scope refused; "
              f"{r['wrongly_refused']}/{r['answerable']} answerable wrongly refused")


def main() -> int:
    questions = load_questions()
    out = run_engine(questions)
    report = evaluate(questions, out, choose_threshold(questions, out))
    print_report(report)
    if "--write" in sys.argv:
        BASELINE.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {BASELINE.relative_to(ROOT)}")
    if "--check" in sys.argv:
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        bad = []
        for split in ("dev", "test"):
            for cat, v in base["splits"][split]["categories"].items():
                cur = report["splits"][split]["categories"].get(cat, {})
                for metric in ("recall@5", "mrr"):
                    if cur.get(metric, 0) < v[metric] - TOLERANCE:
                        bad.append(f"{split}/{cat} {metric}: {cur.get(metric)} < baseline {v[metric]}")
            for key in ("correctly_refused",):
                if report["splits"][split]["refusal"][key] < base["splits"][split]["refusal"][key] - 1:
                    bad.append(f"{split} refusal regressed")
        for b in bad:
            print("[REGRESSION]", b)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
