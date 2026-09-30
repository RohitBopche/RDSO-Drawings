#!/usr/bin/env python3
"""OCR the drawing sheets (P3): raster PDFs with no text layer.

Writes `data/knowledge-graph/raw/drawing_ocr.jsonl`, one record per drawing PDF page:
    file, page_number, sha256, engine, scale, width_px, height_px, lines [{text, confidence, box [x0,y0,x1,y1] in 0..1 of the page}]
Like the manual OCR this is a committed artifact (model-dependent, not part of the byte-identical rebuild); the
registry step checks it against the PDF hash. Incremental: unchanged files (same hash and engine) are kept.
"""
from __future__ import annotations

import hashlib
import json
import sys
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "knowledge-graph" / "raw" / "drawing_ocr.jsonl"
MAX_SIDE = 3000


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    ev = "rapidocr-onnxruntime " + version("rapidocr-onnxruntime")
    existing = {}
    if OUT.exists():
        for l in OUT.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            existing[(r["file"], r["page_number"])] = r
    records = []
    for f in sorted((ROOT / "drawings").glob("*.pdf")):
        digest = sha256(f)
        doc = pymupdf.open(f)
        for pno in range(1, len(doc) + 1):
            prev = existing.get((f.name, pno))
            if prev and prev["sha256"] == digest and prev["engine"] == ev:
                records.append(prev)
                continue
            page = doc[pno - 1]
            z = min(MAX_SIDE / max(page.rect.width, page.rect.height), 1.0)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z))
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            result, _ = engine(img)
            lines = []
            for box, text, conf in (result or []):
                xs, ys = [pt[0] for pt in box], [pt[1] for pt in box]
                lines.append({"text": text, "confidence": round(float(conf), 3),
                              "box": [round(min(xs) / pix.w, 4), round(min(ys) / pix.h, 4), round(max(xs) / pix.w, 4), round(max(ys) / pix.h, 4)]})
            lines.sort(key=lambda l: (round(l["box"][1] * 200), l["box"][0]))
            records.append({"file": f.name, "page_number": pno, "sha256": digest, "engine": ev, "scale": round(z, 4),
                            "width_px": pix.w, "height_px": pix.h, "lines": lines})
            print(f"{f.name}: {len(lines)} lines", flush=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    print(f"{len(records)} drawing pages -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
