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
