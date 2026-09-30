#!/usr/bin/env python3
"""Build eval/questions.jsonl, the retrieval / answer regression set (P7.1).

Sources, in order:
  handwritten   100 natural-language questions written from sampled clauses, gold = the clause
                that answers it (label_status author_drafted_unreviewed until a second person checks)
  ident         40 identifier queries built from clause numbers ("Para 429 IRPWM", "USFD 8.10")
  title_auto    120 queries that are a unique clause title (a lexical floor, not a quality claim)
  kw_auto       40 handwritten questions reduced to bare keywords
  oos           20 questions the manuals cannot answer; expected behaviour is to refuse
  blind         35 practitioner questions written before reading any clause (+12 railway-related
                questions the corpus cannot answer, category blind_oos)

Every item has a deterministic dev/test split (hash of the question); tune on dev, report test.
Deterministic: same inputs give the same file.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eval" / "questions.jsonl"
STOP = set("a an the of in on at for to is are was were be by with and or how what which who when where why does do can should shall must from that this it its as any all into between during after before".split())

OOS = [
    "What is the recipe for butter chicken?",
    "Who won the cricket world cup in 2011?",
    "How do I fix a memory leak in a Python program?",
    "What is the maintenance schedule of a Boeing 737 landing gear?",
    "How is income tax calculated for salaried employees?",
    "What is the tallest mountain in the world?",
    "How do I train a neural network for image classification?",
    "What is the fare for a metro ticket in Delhi?",
    "How to repair a smartphone screen?",
    "What is the speed limit for cars on national highways?",
    "How is a pacemaker implanted?",
    "Explain quantum entanglement.",
    "What are the symptoms of dengue fever?",
    "How do I bake a sourdough bread?",
    "Which movie won the best picture Oscar in 2020?",
    "How do you rewind the stator of a traction motor in a locomotive workshop?",
    "What is the ticket refund rule for cancelled passenger trains?",
    "What is the height of the Eiffel Tower?",
    "How does a wind turbine gearbox work?",
    "What is the exchange rate of the US dollar to the rupee?",
]


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def split_of(text: str) -> str:
    return "test" if int(hashlib.sha256(text.encode()).hexdigest(), 16) % 3 == 0 else "dev"


def keywords(q: str) -> str:
    toks = [t for t in re.findall(r"[A-Za-z0-9./:-]+", q) if t.lower() not in STOP]
    return " ".join(toks)


def main() -> int:
    rnd = random.Random(20260930)
    nodes = read_jsonl(ROOT / "data/knowledge-graph/canonical/nodes.jsonl")
    clauses = {n["id"]: n for n in nodes if n["id"].startswith("CLAUSE:")}
    items: list[dict] = []

    def add(question, gold, category, label_status, expect="answer"):
        items.append({"question": question, "gold": gold, "category": category, "expect": expect,
                      "label_status": label_status, "split": split_of(question)})

    hand = json.loads((ROOT / "eval" / "handwritten_questions.json").read_text(encoding="utf-8"))
    for h in hand:
        assert all(g in clauses for g in h["gold"]), h
        add(h["question"], h["gold"], "nl", "author_drafted_unreviewed")

    # identifier queries
    names = {"IRPWM": ["IRPWM", "IRPWM 2024", "permanent way manual"], "TMM": ["TMM", "track machine manual"],
             "STMM": ["STMM", "small track machines manual"], "USFD": ["USFD", "USFD manual"],
             "AT_WELD": ["AT welding manual", "thermit welding manual"], "FBW": ["FBW", "flash butt welding manual"]}
    pool = sorted(c for c in clauses)
    for cid in rnd.sample(pool, 40):
        alias = cid.split(":")[1]
        num = clauses[cid]["specs"]["Paragraph"]
        label = rnd.choice(names[alias])
        form = rnd.choice(["Para {n} {m}", "{m} {n}", "clause {n} of {m}", "{m} para {n}"])
        add(form.format(n=num, m=label), [cid], "ident", "auto")

    # unique clause titles
    from collections import Counter
    counts = Counter(c["label"].strip().lower() for c in clauses.values())
    cands = [c for c in clauses.values() if counts[c["label"].strip().lower()] == 1 and len(c["label"].split()) >= 3]
    for c in rnd.sample(sorted(cands, key=lambda x: x["id"]), 120):
        add(c["label"].strip(), [c["id"]], "title_auto", "auto")

    for h in rnd.sample(hand, 40):
        add(keywords(h["question"]), h["gold"], "kw_auto", "auto")

    for q in OOS:
        add(q, [], "oos", "author_drafted_unreviewed", expect="refuse")

    # Blind set: practitioner-style questions written BEFORE looking at any clause text, gold-labelled
    # afterwards by reading the candidates. Far less vocabulary leakage than `nl`.
    by_para = {(c["id"].split(":")[1], str(c["specs"]["Paragraph"])): c["id"] for c in clauses.values()}
    blind = json.loads((ROOT / "eval" / "blind_questions.json").read_text(encoding="utf-8"))
    for b in blind["answerable"]:
        gold = []
        for ref in b["gold"]:
            alias, para = ref.split(" ", 1)
            gold.append(by_para[(alias, para)])
        add(b["question"], gold, "blind", "author_blind_drafted")
    for q in blind["unanswerable"]:
        add(q, [], "blind_oos", "author_blind_drafted", expect="refuse")

    # reviewed user feedback (scripts/ingest_feedback.py -> a person accepts candidates into this file)
    rf = ROOT / "eval" / "reviewed_feedback.json"
    if rf.exists():
        for it in json.loads(rf.read_text(encoding="utf-8")):
            gold = [by_para[tuple(ref.split(" ", 1))] for ref in it["gold"]]
            add(it["question"], gold, "real", "user_confirmed_reviewed")

    seen = set()
    rows = []
    for it in items:
        if it["question"] in seen:
            continue
        seen.add(it["question"])
        it["id"] = f"Q{len(rows) + 1:04d}"
        rows.append(it)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    cats = Counter(r["category"] for r in rows)
    spl = Counter(r["split"] for r in rows)
    print(f"{len(rows)} questions {dict(cats)} split {dict(spl)} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
