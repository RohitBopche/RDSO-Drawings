"""Relationship queries (Phase P4): an independent rebuild of the reference graph from crossrefs.jsonl must agree with the browser module on
who refers to whom, on shortest chains, and on drawing citations; every quoted sentence is a verbatim slice of the paragraph that prints
the reference and contains that reference."""
import json
import subprocess
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data/knowledge-graph/canonical"


def _flat(t):
    return " ".join(t.split())


def _load():
    texts = {}
    for l in (KG / "nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(l)
        if n["id"].startswith("CLAUSE:"):
            texts[n["id"]] = n["text"]
    fwd, back = {}, {}
    for l in (KG / "crossrefs.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        if r["status"] != "RESOLVED" or r["target_kind"] != "para":
            continue
        for t in r["targets"]:
            if not t.startswith("CLAUSE:") or t == r["source"]:
                continue
            a, b = (t, r["source"]) if r["kind"] == "back_ref" else (r["source"], t)       # "(Back to Para N)": N refers to this paragraph
            fwd.setdefault(a, set()).add(b)
            back.setdefault(b, set()).add(a)
    return texts, fwd, back


def _reach(g, start, depth):
    seen, frontier = {start}, [start]
    for _ in range(depth):
        frontier = [o for c in frontier for o in sorted(g.get(c, ())) if o not in seen and not seen.add(o)]
    return seen - {start}


def _bfs(fwd, back, a, b, limit=6):
    dist, q = {a: 0}, deque([a])
    while q:
        c = q.popleft()
        if dist[c] >= limit:
            continue
        for o in sorted(fwd.get(c, set()) | back.get(c, set())):
            if o not in dist:
                dist[o] = dist[c] + 1
                q.append(o)
    return dist.get(b)


def test_traces_paths_and_drawing_citations_match_an_independent_build():
    out = json.loads(subprocess.run(["node", "tests/graphq_probe.js"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    texts, fwd, back = _load()
    for key, t in out["traces"].items():
        cid, d = key.split("|")
        g = back if d == "in" else fwd
        assert t["total"] == len(_reach(g, cid, 2)), key                       # same set of paragraphs two steps out
    for p in out["paths"]:
        want = _bfs(fwd, back, p["a"], p["b"])
        assert p["length"] == want, p                                          # shortest chain has the same length
    links = [json.loads(l) for l in (KG / "drawing_links.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    for num, rows in out["drawings"].items():
        assert len(rows) == sum(1 for x in links if x["number"] == num), num


def test_every_quote_is_verbatim_and_contains_its_reference():
    out = json.loads(subprocess.run(["node", "tests/graphq_probe.js"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    texts, _, _ = _load()
    n = 0
    items = [x for t in out["traces"].values() for x in t["first"]] + [h for p in out["paths"] for h in (p["hops"] or [])] + \
            [{"at": r["clause"], "quote": r["quote"], "raw": r["raw"]} for rows in out["drawings"].values() for r in rows]
    for x in items:
        hay, q = _flat(texts[x["at"]]), x["quote"].replace("…", "").strip()
        assert q and q in hay, (x["at"], q[:80])
        assert _flat(x["raw"]).split()[0].rstrip(",;") in q or x["raw"] == "", (x["raw"], q[:80])
        n += 1
    assert n > 500
