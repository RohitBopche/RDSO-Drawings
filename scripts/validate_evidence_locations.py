#!/usr/bin/env python3
"""Gate N: evidence is locatable and re-verifiable against the source PDFs.

- every edge cites evidence, or is listed in evidence_waivers.json (list may only shrink)
- evidence pages exist; PDF and page hashes match the registry, the files on disk and the raw layer
- regions lie inside the page; located quotes really occur on the cited page
- crop evidence files match their recorded hash
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
CANON = KG / "canonical"
MAX_WAIVERS = 12


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    errors: list[str] = []
    edges = read_jsonl(CANON / "edges.jsonl")
    evidence = read_jsonl(CANON / "evidence.jsonl")
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    ev = {e["evidence_id"]: e for e in evidence}
    waivers = json.loads((CANON / "evidence_waivers.json").read_text(encoding="utf-8"))["edges"]
    waived = {(w["from"], w["rel"], w["to"]) for w in waivers}
    if len(waivers) > MAX_WAIVERS:
        errors.append(f"waiver list grew: {len(waivers)} > {MAX_WAIVERS}")

    # 1. edges
    uncovered = set()
    for e in edges:
        ids = e.get("evidence_ids") or []
        if not ids:
            uncovered.add((e["from"], e["rel"], e["to"]))
        for i in ids:
            if i not in ev:
                errors.append(f"edge {e['from']}-{e['rel']}->{e['to']}: unknown evidence {i}")
    for k in sorted(uncovered - waived):
        errors.append(f"edge without evidence and not waived: {k}")
    for k in sorted(waived - uncovered):
        errors.append(f"stale waiver (edge now has evidence or is gone): {k}")

    # 2. registry / disk hashes
    disk: dict[str, str] = {}
    for did, r in registry.items():
        f = ROOT / r["file_path"]
        if f.exists() and r.get("sha256"):
            disk[did] = sha256_file(f)
            if disk[did] != r["sha256"]:
                errors.append(f"registry hash differs from file on disk: {did}")

    pages = {}
    for p in read_jsonl(KG / "raw" / "extracted_pages.jsonl"):
        pages[(p["document_id"], p["page_number"])] = p

    located = page_only = 0
    for e in evidence:
        if e.get("file_path"):
            f = ROOT / e["file_path"]
            if not f.exists():
                errors.append(f"{e['evidence_id']}: crop file missing")
            elif e.get("file_sha256") != sha256_file(f):
                errors.append(f"{e['evidence_id']}: crop hash mismatch")
            continue
        if "page_number" not in e:
            if e["evidence_id"].startswith(("ev:clause:", "ev:src:")):
                errors.append(f"{e['evidence_id']}: text evidence without page_number")
            continue
        did, pg = e["document_id"], e["page_number"]
        r = registry.get(did)
        if r is None:
            errors.append(f"{e['evidence_id']}: document {did} not in registry")
            continue
        if not 1 <= pg <= r["page_count"]:
            errors.append(f"{e['evidence_id']}: page {pg} outside 1..{r['page_count']}")
            continue
        if e.get("pdf_sha256") != r["sha256"]:
            errors.append(f"{e['evidence_id']}: pdf_sha256 differs from registry")
        raw = pages.get((did, pg))
        if raw is None:
            errors.append(f"{e['evidence_id']}: no raw page {did}#{pg}")
            continue
        if e.get("page_sha256") != hashlib.sha256(raw["text_content"].encode("utf-8")).hexdigest():
            errors.append(f"{e['evidence_id']}: page_sha256 differs from raw page text")
        region = e.get("region")
        if region:
            located += 1
            x0, y0, x1, y1 = region
            if not (0 <= x0 < x1 <= e["page_width"] + 1 and 0 <= y0 < y1 <= e["page_height"] + 1):
                errors.append(f"{e['evidence_id']}: region outside page")
            q = " ".join(e["quote"].split())[:50]
            if q not in " ".join(raw["text_content"].split()):
                errors.append(f"{e['evidence_id']}: quote not found on cited page")
        else:
            page_only += 1
            if not e["evidence_id"].startswith("ev:src:CHAPTER:"):
                errors.append(f"{e['evidence_id']}: only chapter evidence may be page-level")

    for m in errors[:40]:
        print(f"[ERROR] {m}")
    print(f"[SUMMARY] evidence locations: {'FAIL' if errors else 'PASS'}; evidence={len(evidence)} "
          f"located={located} page_only={page_only} edges={len(edges)} waived={len(waived)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
