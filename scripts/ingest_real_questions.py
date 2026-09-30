#!/usr/bin/env python3
"""Validate double-labelled real engineer questions and write eval/reviewed_real.json (P7.1).

Input:  eval/real_questions.json   (see eval/real_questions_template.json)
Output: eval/reviewed_real.json            questions both labellers agree on (any shared gold clause, or both no_answer)
        data/knowledge-graph/reports/real_question_agreement.json   agreement statistics and disagreements

A question enters the evaluation set only when it has labels from two different people. Where they disagree
the question is reported for adjudication and is NOT used. Agreement is reported as exact-set agreement and as
Cohen's kappa on the answerable / no-answer decision. Nothing is written if the input file is absent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "eval" / "real_questions.json"
OUT = ROOT / "eval" / "reviewed_real.json"
REPORT = ROOT / "data" / "knowledge-graph" / "reports" / "real_question_agreement.json"


def known_refs() -> set[str]:
    refs = set()
    for line in (ROOT / "data/knowledge-graph/canonical/nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if n["id"].startswith("CLAUSE:"):
            refs.add(f"{n['id'].split(':')[1]} {n['specs']['Paragraph']}")
    return refs


def kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def process(data: dict, refs: set[str]) -> tuple[list[dict], dict, list[str]]:
    errors, accepted, disagreements, decisions = [], [], [], []
    exact = 0
    seen = set()
    items = [q for q in data.get("questions", []) if not q.get("_example")]
    for q in items:
        text = (q.get("question") or "").strip()
        if not text:
            errors.append("empty question")
            continue
        if text in seen:
            errors.append(f"duplicate question: {text[:60]}")
            continue
        seen.add(text)
        labels = q.get("labels", [])
        names = {l.get("labeller") for l in labels}
        if len(labels) < 2 or len(names) < 2 or None in names:
            errors.append(f"needs labels from two different people: {text[:60]}")
            continue
        bad = [r for l in labels for r in l.get("gold", []) if r not in refs]
        if bad:
            errors.append(f"unknown clause reference {bad[0]!r} in: {text[:60]}")
            continue
        if any(l.get("no_answer") and l.get("gold") for l in labels):
            errors.append(f"label has both no_answer and gold: {text[:60]}")
            continue
        a, b = labels[0], labels[1]
        decisions.append((not a.get("no_answer"), not b.get("no_answer")))
        ga, gb = set(a.get("gold", [])), set(b.get("gold", []))
        if a.get("no_answer") and b.get("no_answer"):
            accepted.append({"question": text, "gold": [], "no_answer": True, "asked_by": q.get("asked_by", "")})
            exact += 1
        elif not a.get("no_answer") and not b.get("no_answer") and ga & gb:
            accepted.append({"question": text, "gold": sorted(ga & gb), "no_answer": False, "asked_by": q.get("asked_by", "")})
            exact += ga == gb
        else:
            disagreements.append({"question": text, "labels": labels})
    n = len(decisions)
    stats = {"questions": len(items), "accepted": len(accepted), "disagreements": len(disagreements), "errors": len(errors),
             "exact_set_agreement": round(exact / n, 3) if n else None, "kappa_answerable": kappa(decisions),
             "note": "kappa is on the answerable / no-answer decision; disagreements need adjudication and are not used",
             "disagreement_items": disagreements}
    return accepted, stats, errors


def main() -> int:
    if not SRC.exists():
        print("[INFO] eval/real_questions.json not present; nothing to ingest (see eval/real_questions_template.json)")
        return 0
    accepted, stats, errors = process(json.loads(SRC.read_text(encoding="utf-8")), known_refs())
    for e in errors:
        print("[ERROR]", e)
    if errors:
        print(f"[SUMMARY] real questions: FAIL; errors={len(errors)}")
        return 1
    OUT.write_text(json.dumps(accepted, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(stats, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[SUMMARY] real questions: PASS; accepted={stats['accepted']}/{stats['questions']} kappa={stats['kappa_answerable']} exact={stats['exact_set_agreement']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
