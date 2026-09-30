#!/usr/bin/env python3
"""Gate T: drawing registry is complete, hash-bound and its identity checks hold (P3)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
MIN_CONFIRMED = 55


def main() -> int:
    errors = []
    recs = [json.loads(l) for l in (KG / "canonical" / "drawings_registry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    files = {f"drawings/{p.name}": p for p in (ROOT / "drawings").glob("*.pdf")}
    by_file = {r["file"]: r for r in recs}
    for f in sorted(set(files) - set(by_file)):
        errors.append(f"{f}: not in the drawing registry")
    for f in sorted(set(by_file) - set(files)):
        errors.append(f"{f}: registry entry has no PDF")
    ids = set()
    for f, r in by_file.items():
        if f not in files:
            continue
        if hashlib.sha256(files[f].read_bytes()).hexdigest() != r["sha256"]:
            errors.append(f"{f}: sha256 changed since the registry was built")
        if r["drawing_id"] in ids:
            errors.append(f"{f}: duplicate drawing_id {r['drawing_id']}")
        ids.add(r["drawing_id"])
        if not r["filename"]["numbers"]:
            errors.append(f"{f}: no drawing number in the file name")
        if not r["ocr_present"]:
            errors.append(f"{f}: no OCR record for this PDF hash (run scripts/ocr_drawings.py)")
        if r["verification_status"] != "machine_extracted":
            errors.append(f"{f}: unexpected verification status")
        if r["checks"]["alt_consistent"] is False:
            errors.append(f"{f}: file name says ALT_NIL but the sheet shows several dated revisions")
    confirmed = sum(r["checks"]["identity_confirmed"] for r in recs)
    if confirmed < MIN_CONFIRMED:
        errors.append(f"only {confirmed} drawings have their file-name number read on the sheet (< {MIN_CONFIRMED})")
    for e in errors[:30]:
        print("[ERROR]", e)
    print(f"[SUMMARY] drawings: {'FAIL' if errors else 'PASS'}; drawings={len(recs)} identity_confirmed={confirmed} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
