#!/usr/bin/env python3
"""Gate O: every image-only manual page has an OCR record tied to the current PDF hash."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def main() -> int:
    errors: list[str] = []
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    ocr = {(r["document_id"], r["page_number"]): r for r in read_jsonl(KG / "raw" / "ocr_pages.jsonl")}
    queue = {q.get("review_id") for q in read_jsonl(KG / "intermediate" / "review_queue.jsonl")}
    need = [(p["document_id"], p["page_number"]) for p in read_jsonl(KG / "raw" / "extracted_pages.jsonl")
            if p["document_id"] in registry and registry[p["document_id"]].get("category") == "MANUAL"
            and not p["is_extractable"]]
    for key in need:
        rec = ocr.get(key)
        if rec is None:
            errors.append(f"{key[0]} page {key[1]}: no OCR record")
            continue
        if rec["pdf_sha256"] != registry[key[0]]["sha256"]:
            errors.append(f"{key[0]} page {key[1]}: OCR record is for a different PDF version")
        weak = rec["line_count"] == 0 or rec["mean_confidence"] < 0.80
        if weak and f"OCR:{key[0]}:{key[1]}" not in queue:
            errors.append(f"{key[0]} page {key[1]}: weak OCR result not in the review queue")
    for key in set(ocr) - set(need):
        errors.append(f"{key[0]} page {key[1]}: OCR record for a page that has a text layer")
    for e in errors[:30]:
        print(f"[ERROR] {e}")
    weak = sum(1 for r in ocr.values() if r["line_count"] == 0 or r["mean_confidence"] < 0.80)
    print(f"[SUMMARY] OCR coverage: {'FAIL' if errors else 'PASS'}; image_only_pages={len(need)} ocr={len(ocr)} weak={weak} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
