#!/usr/bin/env python3
"""Entity layer: concepts found in the manual text, with typed links.

Reads  data/ontology/concepts.json (curated concept lexicon) and the canonical paragraph and annexure text.
Writes data/knowledge-graph/canonical/
  entities.jsonl           one row per concept: label, class, aliases, curated is_a / part_of, counts per manual
  entity_mentions.jsonl    every place a concept is named: source id, character span (checked against the text)
  entity_relations.jsonl   IS_A / PART_OF (curated) and DISCUSSED_WITH (two concepts in one sentence, in >= MIN_SUPPORT paragraphs, with example sentences)
  entity_limits.jsonl      HAS_LIMIT: a measured value that sits in the same sentence as a concept
The taxonomy is curated; mentions, co-occurrence and limits are computed from the text and carry spans, so each can be shown as a quotation.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "knowledge-graph" / "canonical"
LEXICON = ROOT / "data" / "ontology" / "concepts.json"
MIN_SUPPORT = 3          # paragraphs in which two concepts must share a sentence
SENT_END = re.compile(r"[.;:?!]\s+(?=[A-Z(\d])")


def load(path):
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def case_sensitive(alias: str) -> bool:
    return bool(re.search(r"[A-Z]{2}", alias)) or alias in ("P.Way", "P-Way", "P&C")


def compile_lexicon(concepts):
    errors, owner = [], {}
    ids = {c["id"] for c in concepts}
    for c in concepts:
        for k in ("is_a", "part_of"):
            if c.get(k) and c[k] not in ids:
                errors.append(f"{c['id']}: {k} {c[k]} is not a concept")
        for a in c["aliases"]:
            key = a if case_sensitive(a) else a.lower()
            if key in owner and owner[key] != c["id"]:
                errors.append(f"alias {a!r} belongs to both {owner[key]} and {c['id']}")
            owner[key] = c["id"]
    if errors:
        sys.exit("concepts.json invalid:\n  " + "\n  ".join(errors))
    pats = {}
    for cs in (True, False):
        als = sorted((a for a in owner if (case_sensitive(a) if cs else not case_sensitive(a))), key=lambda a: (-len(a), a))
        if not als:
            continue
        body = "|".join(re.escape(a).replace(r"\ ", r"\s+") for a in als)
        pats[cs] = re.compile(r"(?<![A-Za-z0-9])(" + body + r")(?:s|es)?(?![A-Za-z0-9])", 0 if cs else re.I)
    return pats, owner


def mentions_in(text, pats, owner):
    flat = re.sub(r"\s", " ", text)
    found = []
    for cs, pat in pats.items():
        for m in pat.finditer(flat):
            key = m.group(1) if cs else re.sub(r"\s+", " ", m.group(1)).lower()
            key = re.sub(r"\s+", " ", key)
            cid = owner.get(key)
            if cid is None:                        # alias written with several spaces: owner keys hold single spaces
                continue
            found.append((m.start(), m.end(), cid))
    found.sort()
    out, last = [], -1                              # drop a span inside an earlier, longer one
    for s, e, cid in found:
        if s < last:
            continue
        out.append((s, e, cid)); last = e
    return out


def sentence_bounds(text):
    cuts = [0] + [m.end() for m in SENT_END.finditer(text)] + [len(text)]
    return list(zip(cuts[:-1], cuts[1:]))


def main():
    lex = json.loads(LEXICON.read_text(encoding="utf-8"))
    concepts = lex["concepts"]
    pats, owner = compile_lexicon(concepts)
    by_id = {c["id"]: c for c in concepts}

    sources = []                                    # (id, manual, kind, text)
    for n in load(CANON / "nodes.jsonl"):
        if n["type"] == "CLAUSE" and n.get("text"):
            sources.append((n["id"], n["id"].split(":")[1], "paragraph", n["text"]))
    for a in load(CANON / "annexures.jsonl"):
        sources.append((a["id"], a["manual"], "annexure", a["text"]))
    sources.sort()

    mention_rows, paras_of = [], defaultdict(set)
    pair_sents = defaultdict(lambda: defaultdict(list))   # (a,b) -> source -> [(s,e)]
    limit_rows = []
    meas_by_src = defaultdict(list)
    for m in load(CANON / "measurements.jsonl"):
        if m.get("source") == "text" and m.get("clause"):
            meas_by_src[m["clause"]].append(m)

    for sid, manual, kind, text in sources:
        found = mentions_in(text, pats, owner)
        for s, e, cid in found:
            mention_rows.append({"entity": f"ENT:{cid}", "source": sid, "manual": manual, "kind": kind, "start": s, "end": e})
            paras_of[cid].add(sid)
        if not found or sid.endswith(":front"):    # contents pages list names, they do not discuss them
            continue
        for (a, b) in sentence_bounds(text):
            inside = [f for f in found if a <= f[0] < b]
            ids = sorted({f[2] for f in inside})
            for x, y in combinations(ids, 2):
                pair_sents[(x, y)][sid].append((a, b))
        for ms in meas_by_src.get(sid, []):
            at = text.find(ms["raw"], max(0, ms["start"] - 60))
            if at < 0 or text[at:at + len(ms["raw"])] != ms["raw"]:
                continue
            for (a, b) in sentence_bounds(text):
                if a <= at < b:
                    for cid in sorted({f[2] for f in found if a <= f[0] < b}):
                        limit_rows.append({"entity": f"ENT:{cid}", "measurement": ms["measurement_id"], "source": sid, "manual": manual,
                                           "raw": ms["raw"], "quantity": ms.get("quantity"), "lo": ms.get("lo"), "hi": ms.get("hi"), "unit": ms.get("unit"),
                                           "at": [at, at + len(ms["raw"])], "sentence": [a, b], "basis": "same sentence"})
                    break

    # entities
    per_manual = defaultdict(Counter)
    for r in mention_rows:
        per_manual[r["entity"]][r["manual"]] += 1
    ents = []
    for c in concepts:
        eid = f"ENT:{c['id']}"
        ents.append({"id": eid, "label": c["label"], "class": c["class"], "aliases": c["aliases"], "is_a": f"ENT:{c['is_a']}" if c.get("is_a") else None,
                     "part_of": f"ENT:{c['part_of']}" if c.get("part_of") else None, "basis": "curated lexicon, mentions from text",
                     "mentions": sum(per_manual[eid].values()), "paragraphs": len(paras_of[c["id"]]),
                     "by_manual": dict(sorted(per_manual[eid].items()))})
    ents.sort(key=lambda r: r["id"])

    # relations
    rels = []
    for c in concepts:
        for k, t in (("is_a", "IS_A"), ("part_of", "PART_OF")):
            if c.get(k):
                rels.append({"type": t, "from": f"ENT:{c['id']}", "to": f"ENT:{c[k]}", "basis": "curated"})
    for (x, y), srcs in pair_sents.items():
        if len(srcs) < MIN_SUPPORT:
            continue
        ex = []
        for sid in sorted(srcs, key=lambda i: (not i.startswith("CLAUSE:"), i))[:3]:      # paragraphs before annexures
            ex.append({"source": sid, "sentence": list(srcs[sid][0])})
        n_x, n_y = len(paras_of[x]), len(paras_of[y])
        rels.append({"type": "DISCUSSED_WITH", "from": f"ENT:{x}", "to": f"ENT:{y}", "basis": "same sentence",
                     "support": len(srcs), "from_paragraphs": n_x, "to_paragraphs": n_y,
                     "manuals": sorted({s.split(":")[1] if s.startswith("CLAUSE") else s.split(":")[1] for s in srcs}), "examples": ex})
    rels.sort(key=lambda r: (r["type"], r["from"], r["to"]))

    mention_rows.sort(key=lambda r: (r["source"], r["start"], r["entity"]))
    limit_rows.sort(key=lambda r: (r["entity"], r["source"], r["measurement"]))
    for name, rows in (("entities", ents), ("entity_mentions", mention_rows), ("entity_relations", rels), ("entity_limits", limit_rows)):
        with (CANON / f"{name}.jsonl").open("w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    used = sum(1 for e in ents if e["mentions"])
    print(f"entities {len(ents)} ({used} found in text), mentions {len(mention_rows)}, relations {len(rels)} "
          f"(curated {sum(1 for r in rels if r['basis']=='curated')}, co-mention {sum(1 for r in rels if r['type']=='DISCUSSED_WITH')}), limits {len(limit_rows)}")


if __name__ == "__main__":
    main()
