#!/usr/bin/env python3
"""OCR the manual pages that have no extractable text layer (P0-R.7).

Writes `data/knowledge-graph/raw/ocr_pages.jsonl`, one record per image-only page:

    document_id, page_number, engine, engine_version, dpi, text, mean_confidence,
    lines [{text, confidence, box[x0,y0,x1,y1] in PDF points}], pdf_sha256

Engine: RapidOCR (PP-OCR models on onnxruntime, fully offline once installed).
OCR output depends on the model and runtime, so this step is *not* part of the
byte-identical rebuild; the committed file is validated (coverage, hashes) by Gate O and
regenerated only on purpose: `python scripts/ocr_pages.py`.
Pages already present with the same PDF hash are kept (incremental).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "raw" / "ocr_pages.jsonl"
DPI = 200
LOW_CONFIDENCE = 0.80


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def image_only_pages() -> dict[str, list[int]]:
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    out: dict[str, list[int]] = {}
    for p in read_jsonl(KG / "raw" / "extracted_pages.jsonl"):
        if p["document_id"] in registry and registry[p["document_id"]].get("category") == "MANUAL" and not p["is_extractable"]:
            out.setdefault(p["document_id"], []).append(p["page_number"])
    return {k: sorted(v) for k, v in sorted(out.items())}


def main() -> int:
    from importlib.metadata import version
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    engine_version = "rapidocr-onnxruntime " + version("rapidocr-onnxruntime")
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    existing = {(r["document_id"], r["page_number"]): r for r in read_jsonl(OUT)}
    scale = 72 / DPI
    records = []
    for doc_id, pages in image_only_pages().items():
        reg = registry[doc_id]
        pdf = pymupdf.open(ROOT / reg["file_path"])
        for pno in pages:
            prev = existing.get((doc_id, pno))
            if prev and prev["pdf_sha256"] == reg["sha256"] and prev["engine"] == engine_version:
                records.append(prev)
                continue
            pix = pdf[pno - 1].get_pixmap(dpi=DPI)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            result, _ = engine(img)
            lines = []
            for box, text, conf in (result or []):
                xs, ys = [pt[0] for pt in box], [pt[1] for pt in box]
                lines.append({"text": text, "confidence": round(float(conf), 3),
                              "box": [round(min(xs) * scale, 1), round(min(ys) * scale, 1),
                                      round(max(xs) * scale, 1), round(max(ys) * scale, 1)]})
            lines.sort(key=lambda l: (round(l["box"][1] / 4), l["box"][0]))
            mean = round(sum(l["confidence"] for l in lines) / len(lines), 3) if lines else 0.0
            records.append({"document_id": doc_id, "page_number": pno, "engine": engine_version, "dpi": DPI,
                            "text": "\n".join(l["text"] for l in lines), "mean_confidence": mean,
                            "line_count": len(lines), "lines": lines, "pdf_sha256": reg["sha256"]})
            print(f"{doc_id} p{pno}: {len(lines)} lines, mean conf {mean}")
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    low_pages = [r for r in records if r["mean_confidence"] < LOW_CONFIDENCE or r["line_count"] == 0]
    low = len(low_pages)
    queue_path = KG / "intermediate" / "review_queue.jsonl"
    queue = [r for r in read_jsonl(queue_path) if not str(r.get("review_id", "")).startswith("OCR:")]
    for r in low_pages:
        queue.append({"review_id": f"OCR:{r['document_id']}:{r['page_number']}", "entity_id": r["document_id"],
                      "topic": "Image-only page: OCR found no text or low confidence",
                      "question": "Is this page a figure/blank, or does it carry text or values that must be transcribed by hand?",
                      "source_doc": r["document_id"], "page": r["page_number"], "clause": "",
                      "priority": "LOW" if r["line_count"] == 0 else "MEDIUM"})
    queue_path.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in queue), encoding="utf-8")
    print(f"{len(records)} pages OCR'd, {low} low-confidence or empty -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
