#!/usr/bin/env python3
"""Build the offline search index (P5.1).

1. Cut every canonical clause (and table / drawing note) into passages of roughly 700 to 1,100
   characters at line boundaries -> data/search/passages.jsonl
2. Call scripts/build_search_index.js, which tokenises with lib/rdso_search.js and writes
   data/search/search_index.js (loaded by the browser and by the Node eval harness).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = ROOT / "data" / "search" / "passages.jsonl"
TARGET, HARD = 700, 1100


def chunks(text: str) -> list[str]:
    lines = [l for l in text.split("\n") if l.strip()]
    out, cur = [], ""
    for line in lines:
        if cur and (len(cur) >= TARGET or len(cur) + len(line) > HARD):
            out.append(cur)
            cur = ""
        cur = f"{cur}\n{line}" if cur else line
        while len(cur) > HARD * 2:  # a single enormous line (table row dump)
            out.append(cur[:HARD])
            cur = cur[HARD:]
    if cur:
        # avoid a tiny orphan tail: merge into the previous passage when short
        if out and len(cur) < 200:
            out[-1] = out[-1] + "\n" + cur
        else:
            out.append(cur)
    return out or [text]


def main() -> int:
    nodes = [json.loads(l) for l in (KG / "canonical" / "nodes.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by_id = {n["id"]: n for n in nodes}
    docs = {n["id"]: n for n in nodes if n["type"] == "DOCUMENT"}
    chapters = {n["id"]: n for n in nodes if n["type"] == "CHAPTER"}
    rows = []
    for n in nodes:
        if n["id"].startswith("CLAUSE:"):
            alias = n["id"].split(":")[1]
            ch = chapters.get("CHAPTER:" + ":".join(n["id"].split(":")[1:3]))
            chapter_title = ch["label"] if ch else ""
            doc = docs.get(n.get("document_id", ""), {})
            body = n["text"]
            title = f"{n['label']} {chapter_title}"
            for k, piece in enumerate(chunks(body)):
                rows.append({"id": f"{n['id']}#{k}", "clause": n["id"], "alias": alias, "doc": doc.get("label", alias),
                             "chapter": chapter_title, "para": str(n["specs"]["Paragraph"]), "title": title,
                             "page": n["page"], "type": "CLAUSE", "text": piece})
        elif n["type"] == "TABLE" and n.get("domain") == "manual":
            alias = n["id"].split(":")[1]
            text = n.get("source_text") or n.get("desc") or ""
            if len(text) > 40:
                for k, piece in enumerate(chunks(text)):
                    rows.append({"id": f"{n['id']}#{k}", "clause": n["id"], "alias": alias, "doc": alias, "chapter": "",
                                 "para": n["label"], "title": n["label"], "page": n.get("source_page") or 0,
                                 "type": "TABLE", "text": piece})
        elif n.get("domain") not in ("manual", "manuals") and n["type"] in {
                "NOTE", "COMPONENT", "SOP", "STANDARD", "FAILURE_MODE", "MATERIAL", "SPARE_PART", "REVISION", "DIMENSION",
                "HAZARD", "PROCEDURE", "BOM_ITEM", "ZONE", "SLEEPER", "FASTENER"}:
            text = (n.get("desc") or n.get("description") or "").strip()
            specs = n.get("specs") or {}
            spec_text = "; ".join(f"{k}: {v}" for k, v in specs.items() if isinstance(v, (str, int, float)))
            body = f"{text}\n{spec_text}".strip()
            if len(body) > 30:
                rows.append({"id": f"{n['id']}#0", "clause": n["id"], "alias": "DRAWINGS", "doc": "RDSO drawings",
                             "chapter": n["type"].title(), "para": n["id"], "title": n["label"], "page": 0,
                             "type": n["type"], "text": body})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} passages -> {OUT.relative_to(ROOT)}")
    r = subprocess.run(["node", str(ROOT / "scripts" / "build_search_index.js")], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode:
        return r.returncode
    # cross-references for the browser: outgoing per clause and incoming per target
    refs = [json.loads(l) for l in (KG / "canonical" / "crossrefs.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    out_refs: dict[str, list] = {}
    in_refs: dict[str, list] = {}
    for x in refs:
        out_refs.setdefault(x["source"], []).append([" ".join(x["raw"].split()), x["target_kind"], x["status"], x["targets"], x["scope_name"] or ""])
        for t in x["targets"]:
            if t != x["source"] and x["source"] not in in_refs.setdefault(t, []):
                in_refs[t].append(x["source"])
    js = "(typeof window!=='undefined'?window:globalThis).RDSO_CROSSREFS=" + json.dumps({"out": out_refs, "in": in_refs}, separators=(",", ":"), sort_keys=True) + ";\n"
    (ROOT / "data" / "search" / "crossrefs.js").write_text(js, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
