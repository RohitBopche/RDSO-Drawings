#!/usr/bin/env python3
"""Build an offline human-review packet (P0-R.3, P7): a stratified random sample of extracted items shown next to their source page.

    python scripts/make_review_packet.py --per-kind 10 --seed 1     -> artifacts/review/packet_s1.html

One self-contained HTML file (images embedded, no server, no network). A reviewer enters their name, marks each item
Correct / Wrong / Unsure, and downloads `decisions_<name>.json`; `scripts/ingest_reviews.py` then records the decisions.
Sampling is random and reproducible from the seed, so error rates measured from the answers are unbiased estimates, and
the same seed given to two reviewers lets their agreement be measured.

Kinds: clause (boundary and text), xref (cross-reference), measurement, table, drawing_link.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import random
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = ROOT / "artifacts" / "review"
sys.path.insert(0, str(ROOT / "scripts"))
import render_evidence as RE  # noqa: E402

KINDS = ["clause", "xref", "measurement", "table", "drawing_link"]
QUESTION = {
    "clause": "Is this the complete paragraph, starting and ending where the highlighted region starts and ends, with the number and title right?",
    "xref": "Is the highlighted reference a real cross-reference, and is the classification (RESOLVED / DELETED / EXTERNAL ...) right?",
    "measurement": "Do the number, unit and comparator (at most / at least / range / tolerance / value) match what the text says?",
    "table": "Is this a real data table, with the right rows and columns and the header row(s) right?",
    "drawing_link": "Is the highlighted text really a drawing number, and is it the number shown?",
}


def read(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def png_b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def table_crop(t: dict, registry: dict, out_dir: Path) -> Path:
    reg = registry[t["document_id"]]
    page = pymupdf.open(ROOT / reg["file_path"])[t["page"] - 1]
    x0, y0, x1, y1 = t["bbox"]
    page.draw_rect(pymupdf.Rect(t["bbox"]), color=(0.85, 0.35, 0), width=1.2, overlay=True)
    clip = pymupdf.Rect(0, max(0, y0 - 20), page.rect.width, min(page.rect.height, y1 + 20))
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{RE.safe_name(t['table_id'])}.png"
    page.get_pixmap(dpi=90, clip=clip).save(p)
    return p


def build(per_kind: int, seed: int, only: list[str] | None = None) -> tuple[list[dict], dict]:
    rnd = random.Random(seed)
    nodes = {n["id"]: n for n in read(KG / "canonical" / "nodes.jsonl") if n["id"].startswith("CLAUSE:")}
    ev = {e["evidence_id"]: e for e in read(KG / "canonical" / "evidence.jsonl") if e["evidence_id"].startswith("ev:clause:")}
    registry = {r["id"]: r for r in read(KG / "raw" / "source_registry.jsonl")}
    pools = {
        "clause": sorted(nodes),
        "xref": [r["ref_id"] for r in read(KG / "canonical" / "crossrefs.jsonl")],
        "measurement": [m["measurement_id"] for m in read(KG / "canonical" / "measurements.jsonl") if m["source"] == "text"],
        "table": [t["table_id"] for t in read(KG / "raw" / "tables.jsonl")],
        "drawing_link": [d["link_id"] for d in read(KG / "canonical" / "drawing_links.jsonl")],
    }
    xrefs = {r["ref_id"]: r for r in read(KG / "canonical" / "crossrefs.jsonl")}
    meas = {m["measurement_id"]: m for m in read(KG / "canonical" / "measurements.jsonl")}
    tables = {t["table_id"]: t for t in read(KG / "raw" / "tables.jsonl")}
    dlinks = {d["link_id"]: d for d in read(KG / "canonical" / "drawing_links.jsonl")}
    items = []
    kind_of = {"CLAUSE:": "clause", "XREF:": "xref", "MEAS:": "measurement", "TBL:": "table", "DLINK:": "drawing_link"}
    for kind in KINDS:
        if only is not None:          # explicit targets (a re-review of given items) instead of a random sample
            chosen = [t for t in only if kind_of.get(next((p for p in kind_of if t.startswith(p)), "")) == kind and t in pools[kind]]
        else:
            chosen = rnd.sample(pools[kind], min(per_kind, len(pools[kind])))
        for tid in chosen:
            item = {"kind": kind, "target_id": tid}
            if kind == "clause":
                clause, span, shown = tid, None, tid
            elif kind == "xref":
                r = xrefs[tid]; clause, span = r["source"], (r["start"], r["end"])
                shown = f"{r['raw']}  ->  {r['kind']} {r['number']}, scope {r['scope']}, status {r['status']}"
            elif kind == "measurement":
                m = meas[tid]; clause, span = m["clause"], (m["start"], m["end"])
                lo, hi = m["lo"], m["hi"]
                shown = f"“{m['raw']}”  ->  {m['comparator']}, lo={lo}, hi={hi}, unit={m['unit']}, quantity={m['quantity']}"
            elif kind == "drawing_link":
                d = dlinks[tid]; clause, span = d["clause"], (d["start"], d["end"])
                shown = f"“{d['raw']}”  ->  drawing number {d['number']} ({d['status']})"
            else:
                t = tables[tid]; clause, span = t["clause"], None
                shown = f"{tid}: {t['n_rows']} rows x {t['n_cols']} columns, {t['header_rows']} header row(s), page {t['page']}"
            item.update({"clause": clause, "shown": shown, "question": QUESTION[kind]})
            text = nodes[clause]["text"] if clause in nodes else ""
            if span:
                a, b = span
                item["context"] = [text[max(0, a - 160):a], text[a:b], text[b:b + 160]]
            if kind == "table":
                p = table_crop(tables[tid], registry, ROOT / "artifacts" / "review" / "crops")
            else:
                e = ev.get(f"ev:{('clause:' + clause)}")
                p = RE.render(e, registry, 100, ROOT / "artifacts" / "review" / "crops") if e else None
            item["image"] = png_b64(p) if p else ""
            item["more_images"] = [png_b64(q) for q in RE.render_continuations(e, registry, 100, ROOT / "artifacts" / "review" / "crops")] \
                if kind != "table" and e else []
            items.append(item)
    rnd.shuffle(items)          # do not review one kind in a row
    meta = {"seed": seed, "per_kind": per_kind, "items": len(items)}
    return items, meta


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Review packet</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{font:15px/1.45 system-ui,sans-serif;margin:0 auto;max-width:980px;padding:16px;color:#1b1f24;background:#fff}
.card{border:1px solid #c9d1d9;border-radius:8px;padding:12px;margin:14px 0}.kind{font-size:12px;text-transform:uppercase;color:#57606a}
.shown{font-weight:600;margin:4px 0}.q{color:#57606a;margin:4px 0}.ctx{background:#f6f8fa;padding:8px;border-radius:6px;white-space:pre-wrap;font-size:13px}
mark{background:#ffd33d}img{max-width:100%;border:1px solid #d0d7de;margin-top:8px}.bar{position:sticky;top:0;background:#fff;padding:8px 0;border-bottom:1px solid #d0d7de;z-index:2}
label{margin-right:14px}input[type=text]{width:100%;margin-top:6px;padding:4px}
@media (prefers-color-scheme:dark){body{background:#0d1117;color:#e6edf3}.card{border-color:#30363d}.ctx{background:#161b22}.bar{background:#0d1117;border-color:#30363d}
.kind,.q{color:#8b949e}}</style></head><body>
<div class="bar"><b>Review packet</b> (seed __SEED__, __N__ items) &nbsp; Your name: <input id="who" type="text" style="width:220px;display:inline">
<button onclick="save()">Download decisions</button> <span id="count"></span></div>
<p>For each item, look at the highlighted region of the source page and answer the question. <b>Unsure</b> is a fine answer. Do not look at the
search engine or the extracted data elsewhere while deciding. Nothing leaves your computer.</p>
<div id="items"></div>
<script>
const ITEMS=__ITEMS__;
const root=document.getElementById('items');
ITEMS.forEach((it,i)=>{
  const c=document.createElement('div');c.className='card';
  const ctx=it.context?`<div class="ctx">${esc(it.context[0])}<mark>${esc(it.context[1])}</mark>${esc(it.context[2])}</div>`:'';
  c.innerHTML=`<div class="kind">${i+1}. ${it.kind} · ${esc(it.target_id)}</div><div class="shown">${esc(it.shown)}</div>
  <div class="q">${esc(it.question)}</div>${ctx}${it.image?`<img src="${it.image}" alt="source page crop">`:'<p>(no image for this item)</p>'}${(it.more_images||[]).map(m=>`<div class="kind">continues on the next page</div><img src="${m}" alt="continuation crop">`).join('')}
  <div><label><input type="radio" name="d${i}" value="approved"> Correct</label><label><input type="radio" name="d${i}" value="rejected"> Wrong</label>
  <label><input type="radio" name="d${i}" value="unsure"> Unsure</label><input type="text" name="n${i}" placeholder="note (what is wrong?)"></div>`;
  root.appendChild(c);
});
function esc(s){return String(s).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]))}
document.addEventListener('change',()=>{const n=ITEMS.filter((_,i)=>document.querySelector(`input[name=d${i}]:checked`)).length;document.getElementById('count').textContent=n+' / '+ITEMS.length+' answered'});
function collect(){
  const who=document.getElementById('who').value.trim();
  const decisions=[];ITEMS.forEach((it,i)=>{const r=document.querySelector(`input[name=d${i}]:checked`);
    if(r)decisions.push({target_id:it.target_id,kind:it.kind,decision:r.value,note:document.querySelector(`input[name=n${i}]`).value})});
  return {packet_seed:__SEED__,reviewer:who,decisions};
}
function save(){
  const out=collect();const who=out.reviewer;if(!who){alert('Enter your name first');return}
  const blob=new Blob([JSON.stringify(out,null,1)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='decisions_'+who.replace(/\\W+/g,'_')+'_s__SEED__.json';a.click();
}
</script></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-kind", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--targets", help="JSON file with a list of target ids to review again (not a random sample; error rates from such a packet are NOT unbiased)")
    ap.add_argument("--name", help="output name (default packet_s<seed>)")
    a = ap.parse_args()
    items, meta = build(a.per_kind, a.seed, json.loads(Path(a.targets).read_text(encoding="utf-8")) if a.targets else None)
    OUT.mkdir(parents=True, exist_ok=True)
    body = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    page = PAGE.replace("__ITEMS__", body).replace("__SEED__", str(a.seed)).replace("__N__", str(len(items)))
    p = OUT / f"{a.name or 'packet_s' + str(a.seed)}.html"
    p.write_text(page, encoding="utf-8")
    print(f"{len(items)} items -> {p.relative_to(ROOT)} ({p.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
