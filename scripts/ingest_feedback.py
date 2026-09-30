#!/usr/bin/env python3
"""Turn exported browser feedback into review work and evaluation candidates (P7.2 / P7.3).

    python scripts/ingest_feedback.py path/to/rdso_feedback.jsonl [more.jsonl ...]

Effects (all deterministic and idempotent):
  data/feedback/feedback.jsonl        merged, de-duplicated log (local data, git-ignored)
  intermediate/review_queue.jsonl     one FB:* item per query that got no evidence, a thumbs-down, or a
                                      low-confidence answer; replaced on every run
  reports/knowledge_gaps.json         refused queries grouped by normalised text with counts
  eval/candidates.jsonl               thumbs-up queries with the confirmed clause: candidate evaluation
                                      questions. A reviewer copies accepted ones into
                                      eval/reviewed_feedback.json ({"question", "gold": ["IRPWM 429"]}) and
                                      build_eval_set.py adds them as category `real`.
Nothing is trusted automatically: candidates stay out of the evaluation set until a person accepts them.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FB = ROOT / "data" / "feedback" / "feedback.jsonl"
QUEUE = ROOT / "data" / "knowledge-graph" / "intermediate" / "review_queue.jsonl"
GAPS = ROOT / "data" / "knowledge-graph" / "reports" / "knowledge_gaps.json"
CANDIDATES = ROOT / "eval" / "candidates.jsonl"
LOW_COVERAGE = 0.75


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def norm(q: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", q.lower()))


def rid(prefix: str, text: str) -> str:
    return f"{prefix}:{hashlib.sha1(text.encode()).hexdigest()[:10]}"


def ingest(paths: list[Path], root: Path = ROOT) -> dict:
    fb, queue, gaps_p, cand_p = (root / "data/feedback/feedback.jsonl", root / "data/knowledge-graph/intermediate/review_queue.jsonl",
                                 root / "data/knowledge-graph/reports/knowledge_gaps.json", root / "eval/candidates.jsonl")
    rows = read_jsonl(fb)
    seen = {json.dumps(r, sort_keys=True) for r in rows}
    for p in paths:
        for r in read_jsonl(p):
            if r.get("type") not in ("query", "feedback") or not r.get("query"):
                continue
            key = json.dumps(r, sort_keys=True)
            if key not in seen:
                seen.add(key)
                rows.append(r)
    rows.sort(key=lambda r: (r.get("ts", ""), r["query"]))
    fb.parent.mkdir(parents=True, exist_ok=True)
    fb.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

    items, gaps, cands = [], Counter(), {}
    for r in rows:
        q = r["query"]
        if r["type"] == "query" and r.get("status") == "no_evidence":
            gaps[norm(q)] += 1
            items.append(("FB:gap", q, "No evidence found for this question. Is it outside the manuals, or is the wording/synonym missing?", "MEDIUM"))
        elif r["type"] == "query" and r.get("status") == "answer" and r.get("coverage", 1) < LOW_COVERAGE:
            items.append(("FB:low", q, "Answered with low evidence coverage. Is the top clause right?", "LOW"))
        elif r["type"] == "feedback" and r.get("verdict") == "down":
            items.append(("FB:down", q, f"A user marked {r.get('clause')} as the wrong provision. What is the right one?", "HIGH"))
        elif r["type"] == "feedback" and r.get("verdict") == "up" and r.get("clause"):
            cands[norm(q)] = {"question": q, "clause": r["clause"], "label_status": "user_confirmed_unreviewed"}
    keep = [x for x in read_jsonl(queue) if not str(x.get("review_id", "")).startswith("FB:")]
    seen_ids = set()
    for kind, q, question, prio in items:
        review_id = rid(kind, norm(q))
        if review_id in seen_ids:
            continue
        seen_ids.add(review_id)
        keep.append({"review_id": review_id, "entity_id": "", "topic": f"User question: {q}", "question": question,
                     "source_doc": "", "page": 0, "clause": "", "priority": prio})
    queue.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in keep), encoding="utf-8")
    gaps_p.parent.mkdir(parents=True, exist_ok=True)
    gaps_p.write_text(json.dumps({"refused_queries": [{"query": k, "count": v} for k, v in sorted(gaps.items(), key=lambda kv: (-kv[1], kv[0]))]},
                                 indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    cand_p.write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for _, v in sorted(cands.items())), encoding="utf-8")
    return {"events": len(rows), "review_items": len(seen_ids), "gaps": len(gaps), "candidates": len(cands)}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    print(json.dumps(ingest([Path(a) for a in sys.argv[1:]])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
