#!/usr/bin/env python3
"""Apply human-reviewed synonym groups to data/search/synonyms.json (P7.3).

Input:  eval/reviewed_synonyms.json  [{"group": ["phrase", ...], "reviewer": "name", "reason": "...", "evidence": ["IRPWM 429"]}]
Rules (a group that breaks one is rejected, nothing is applied):
  - at least two phrases, a named reviewer, and at least one evidence clause that exists;
  - at least one phrase of the group occurs verbatim in the manuals (synonyms come from the manuals' own usage);
  - the group is not already present.
Accepted groups are appended to `groups` and recorded in `reviewed` (who, why, evidence). Then rebuild the index and
run `python scripts/eval_retrieval.py --check` (Gate P does the same): a synonym that makes retrieval worse fails the gate.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "eval" / "reviewed_synonyms.json"
SYN = ROOT / "data" / "search" / "synonyms.json"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def load_corpus() -> tuple[str, set[str]]:
    texts, refs = [], set()
    for line in (ROOT / "data/knowledge-graph/canonical/nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if n["id"].startswith("CLAUSE:"):
            texts.append(norm(n.get("text", "")))
            refs.add(f"{n['id'].split(':')[1]} {n['specs']['Paragraph']}")
    return "\n".join(texts), refs


def validate(items: list[dict], syn: dict, corpus: str, refs: set[str]) -> tuple[list[dict], list[str]]:
    existing = [frozenset(norm(x) for x in g) for g in syn.get("groups", [])]
    ok, errors = [], []
    for it in items:
        g = [norm(x) for x in it.get("group", []) if x.strip()]
        tag = " / ".join(g)[:60]
        if len(set(g)) < 2:
            errors.append(f"needs at least two distinct phrases: {tag}")
        elif not it.get("reviewer", "").strip():
            errors.append(f"no reviewer named: {tag}")
        elif not any(r in refs for r in it.get("evidence", [])):
            errors.append(f"no existing evidence clause: {tag}")
        elif not any(p in corpus for p in g):
            errors.append(f"no phrase occurs in the manuals: {tag}")
        elif frozenset(g) in existing:
            errors.append(f"already present: {tag}")
        else:
            ok.append({"group": g, "reviewer": it["reviewer"].strip(), "reason": it.get("reason", ""), "evidence": it["evidence"]})
    return ok, errors


def main() -> int:
    if not SRC.exists():
        print("[INFO] eval/reviewed_synonyms.json not present; nothing to apply")
        return 0
    syn = json.loads(SYN.read_text(encoding="utf-8"))
    corpus, refs = load_corpus()
    ok, errors = validate(json.loads(SRC.read_text(encoding="utf-8")), syn, corpus, refs)
    for e in errors:
        print("[ERROR]", e)
    if errors:
        print(f"[SUMMARY] reviewed synonyms: FAIL; errors={len(errors)} (nothing applied)")
        return 1
    syn["groups"].extend(x["group"] for x in ok)
    syn.setdefault("reviewed", []).extend(ok)
    SYN.write_text(json.dumps(syn, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[SUMMARY] reviewed synonyms: PASS; applied={len(ok)}; now run build_search_index.py and eval_retrieval.py --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
