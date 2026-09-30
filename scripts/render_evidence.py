#!/usr/bin/env python3
"""Render source evidence as a highlighted page crop (P2.2). Offline, deterministic.

    python scripts/render_evidence.py CLAUSE:IRPWM:CH_04:PARA_429            # one clause
    python scripts/render_evidence.py --doc IRPWM --dpi 80                    # every clause of a manual
    python scripts/render_evidence.py --all                                   # everything (about 1,200 images)

Writes artifacts/evidence/<evidence id>.png (git-ignored cache). The browser viewer shows a crop from
that folder when it exists and otherwise falls back to the plain PDF page. The highlight rectangles are
the stored per-line regions of the evidence record, so what is drawn is exactly what Gate N verified.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = ROOT / "artifacts" / "evidence"
PAD = 36  # points of context above and below the highlighted text


def safe_name(evidence_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", evidence_id)


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def render(evidence: dict, registry: dict, dpi: int = 110, out_dir: Path = OUT) -> Path | None:
    """Return the written PNG path, or None when the evidence has no region to draw."""
    lines = evidence.get("line_regions") or ([evidence["region"]] if evidence.get("region") else [])
    if not lines:
        return None
    reg = registry[evidence["document_id"]]
    doc = pymupdf.open(ROOT / reg["file_path"])
    page = doc[evidence["page_number"] - 1]
    for box in lines:
        page.draw_rect(pymupdf.Rect(box), color=None, fill=(1, 0.85, 0), fill_opacity=0.35, overlay=True)
        page.draw_rect(pymupdf.Rect(box), color=(0.85, 0.35, 0), width=0.8, overlay=True)
    y0 = max(0, min(b[1] for b in lines) - PAD)
    y1 = min(page.rect.height, max(b[3] for b in lines) + PAD)
    clip = pymupdf.Rect(0, y0, page.rect.width, y1)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe_name(evidence['evidence_id'])}.png"
    page.get_pixmap(dpi=dpi, clip=clip).save(path)
    return path


def _norm(t: str) -> str:
    return re.sub(r"\s+", "", t).lower()


def _span_words(page, raw: str):
    """Word index ranges on `page` whose text, with spaces removed and case ignored, equals `raw` (tolerates "RDSO/T- 5855/1" versus
    the PDF's word split, and "60 Kg" versus "60Kg")."""
    import locate_evidence as L
    words = L.split_fused(page.get_text("words"))
    toks = [_norm(w[4]) for w in words]
    target = _norm(raw)
    hits = []
    if not target:
        return words, hits
    for i in range(len(toks)):
        if not toks[i] or not (target.startswith(toks[i]) or toks[i].startswith(target)):
            continue
        acc, j = "", i
        while j < len(toks) and len(acc) < len(target) and j - i < 12:
            acc += toks[j]
            j += 1
        # the span may end inside the last PDF word ("715" inside "715(1)", "Fig.12" inside "Fig.12(b)"): accept a trailing prefix
        if acc == target or (acc.startswith(target) and len(acc) - len(toks[j - 1]) < len(target)):
            hits.append(list(range(i, j)))
    return words, hits


def render_span(evidence: dict, registry: dict, clause_text: str, start: int, end: int, dpi: int = 110,
                out_dir: Path = OUT, name: str = "", page_end: int | None = None) -> Path | None:
    """Crop around ONE extracted span (a reference, value or drawing number): the clause lightly highlighted, the span boxed in red.
    The k-th occurrence of the span's words inside the clause region is used, where k = how many times the same words occur earlier in the clause."""
    raw = " ".join(clause_text[start:end].split())
    k = " ".join(clause_text[:start].split()).count(raw) if raw else 0
    segs = [(evidence["page_number"], evidence.get("line_regions") or [], evidence.get("region"))]
    segs += [(c["page_number"], c["line_regions"], c["region"]) for c in evidence.get("continuation") or []]
    partial = evidence.get("coverage") != "full_clause"     # clause region unknown beyond its opening: search its whole pages
    reg = registry[evidence["document_id"]]
    doc = pymupdf.open(ROOT / reg["file_path"])
    if partial and page_end and page_end > evidence["page_number"]:
        have = {p for p, _, _ in segs}
        segs += [(p, [], None) for p in range(evidence["page_number"] + 1, min(page_end, evidence["page_number"] + 6) + 1) if p not in have]
    found = []
    for pno, lines, region in segs:
        page = doc[pno - 1]
        words, hits = _span_words(page, raw)
        for h in hits:
            xs = [words[i] for i in h]
            y0, y1 = min(w[1] for w in xs), max(w[3] for w in xs)
            if (region and region[1] - 3 <= y0 and y1 <= region[3] + 3) or (partial and not lines) or (partial and pno == evidence["page_number"]):
                found.append((pno, lines, xs))
    if not found:
        return None
    pno, lines, xs = found[min(k, len(found) - 1)]
    page = doc[pno - 1]
    for box in lines:
        page.draw_rect(pymupdf.Rect(box), color=None, fill=(1, 0.9, 0.4), fill_opacity=0.25, overlay=True)
    by_line: dict[tuple, list] = {}
    for w in xs:
        by_line.setdefault((w[5], w[6]), []).append(w)
    y0 = y1 = None
    for ws in by_line.values():
        r = pymupdf.Rect(min(w[0] for w in ws) - 1.5, min(w[1] for w in ws) - 1.5, max(w[2] for w in ws) + 1.5, max(w[3] for w in ws) + 1.5)
        page.draw_rect(r, color=(0.9, 0.0, 0.0), width=1.6, overlay=True)
        y0, y1 = (r.y0, r.y1) if y0 is None else (min(y0, r.y0), max(y1, r.y1))
    clip = pymupdf.Rect(0, max(0, y0 - 70), page.rect.width, min(page.rect.height, y1 + 70))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe_name(name or evidence['evidence_id'] + f'@{start}')}.png"
    page.get_pixmap(dpi=dpi, clip=clip).save(path)
    return path


def render_continuations(evidence: dict, registry: dict, dpi: int = 110, out_dir: Path = OUT) -> list[Path]:
    """Crops of the pages a clause continues onto (evidence["continuation"]), highlighted the same way."""
    paths = []
    for seg in evidence.get("continuation") or []:
        sub = {"evidence_id": f"{evidence['evidence_id']}@p{seg['page_number']}", "document_id": evidence["document_id"],
               "page_number": seg["page_number"], "line_regions": seg["line_regions"], "region": seg["region"]}
        p = render(sub, registry, dpi, out_dir)
        if p:
            paths.append(p)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", help="clause id or evidence id")
    ap.add_argument("--doc", help="manual alias (IRPWM, TMM, ...)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args()
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    evidence = [e for e in read_jsonl(KG / "canonical" / "evidence.jsonl") if e["evidence_id"].startswith("ev:clause:")]
    if a.target:
        want = a.target if a.target.startswith("ev:") else f"ev:clause:{a.target}"
        evidence = [e for e in evidence if e["evidence_id"] == want]
    elif a.doc:
        evidence = [e for e in evidence if e["evidence_id"].split(":")[3] == a.doc]
    elif not a.all:
        ap.error("give a clause id, --doc or --all")
    done = 0
    for e in evidence:
        p = render(e, registry, a.dpi)
        render_continuations(e, registry, a.dpi)
        if p:
            done += 1
            if len(evidence) == 1:
                print(p.relative_to(ROOT))
    print(f"rendered {done}/{len(evidence)} evidence crops -> {OUT.relative_to(ROOT)}")
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
