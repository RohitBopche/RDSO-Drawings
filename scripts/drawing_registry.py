#!/usr/bin/env python3
"""Drawing identity and revision evidence (P3.1, P3.2, P3.6).

For every PDF in drawings/ build a record that keeps what the *file name* says separate from what the *sheet* says:

  filename:  drawing numbers stated (single, list, or range endpoints) and the alteration marker (ALT_n / ALT_NIL)
  sheet:     drawing numbers and dates read by OCR from the sheet (raw/drawing_ocr.jsonl), each with its position
  checks:    identity_confirmed  every number stated in the file name is also read on the sheet
             alt_consistent      file name says ALT_NIL but the sheet shows several dated revision rows (or the reverse)

Nothing here is `verified`: file names are typed by people, OCR is a model. Output: canonical/drawings_registry.jsonl and
reports/drawing_registry_report.json (including the audit of the hand-made data/rdso_drawing_catalog.json).
Deterministic given the committed OCR file.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "canonical" / "drawings_registry.jsonl"
REPORT = KG / "reports" / "drawing_registry_report.json"

DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
ALT_RE = re.compile(r"[_\s-]ALT[_\s]*(NIL|\d+)$", re.I)
NUM_RE = re.compile(r"RDSO[_\s-]*T(?:[_\s-]*T)?[_\s-]*(\d{4})(?:_(\d+|[A-Z])(?![A-Za-z\d]))?", re.I)
SHEET_NUM = re.compile(r"R\.?\s*D\.?\s*S\.?\s*[O0]\.?\s*/?\s*T\s*[-–]?\s*(\d{4})(?:\s*[-/_]\s*(\d{1,3}|[A-Z]))?", re.I)
DATE_RE = re.compile(r"(?<!\d)(\d{2})[.\-/](\d{2})[.\-/](\d{4})(?!\d)")


def parse_filename(name: str) -> dict:
    stem = DATE_PREFIX.sub("", name[:-4] if name.lower().endswith(".pdf") else name)
    m = ALT_RE.search(stem)
    alt = None if not m else ("NIL" if m.group(1).upper() == "NIL" else int(m.group(1)))
    body = stem[:m.start()] if m else stem
    is_range = bool(re.search(r"\bto\b", body, re.I))
    nums = []
    for mm in NUM_RE.finditer(body):
        nums.append(f"T-{mm.group(1)}" + (f"/{mm.group(2).upper()}" if mm.group(2) else ""))
    kind = "range" if is_range and len(nums) >= 2 else ("list" if len(nums) >= 2 else "single")
    return {"numbers": nums, "kind": kind, "alteration": alt}


def sheet_numbers(lines: list[dict]) -> list[dict]:
    out = []
    for l in lines:
        for m in SHEET_NUM.finditer(l["text"]):
            out.append({"number": f"T-{m.group(1)}" + (f"/{m.group(2).upper()}" if m.group(2) else ""), "base": f"T-{m.group(1)}",
                        "raw": m.group(0), "box": l["box"], "confidence": l["confidence"]})
    return out


def sheet_dates(lines: list[dict]) -> list[dict]:
    out = []
    for l in lines:
        for m in DATE_RE.finditer(l["text"]):
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= d <= 31 and 1 <= mo <= 12 and 1950 <= y <= 2100:
                out.append({"date": f"{y:04d}-{mo:02d}-{d:02d}", "raw": m.group(0), "box": l["box"]})
    return out


def check(fn: dict, nums: list[dict], dates: list[dict]) -> dict:
    stated = {n.split("/")[0] for n in fn["numbers"]}
    seen = {n["base"] for n in nums}
    confirmed = bool(stated) and stated <= seen
    partial = bool(stated & seen) and not confirmed
    many_dates = len({d["date"] for d in dates}) >= 3
    # Only one direction is testable: OCR can miss small revision rows, but a sheet that shows several dated
    # revisions cannot be an "ALT_NIL" (never altered) sheet.
    alt_consistent = None if fn["alteration"] != "NIL" else not many_dates
    return {"identity_confirmed": confirmed, "identity_partial": partial, "alt_consistent": alt_consistent}


def build() -> tuple[list[dict], dict]:
    ocr = {}
    p = KG / "raw" / "drawing_ocr.jsonl"
    for l in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        ocr[(r["file"], r["page_number"])] = r
    recs = []
    for f in sorted((ROOT / "drawings").glob("*.pdf")):
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        o = ocr.get((f.name, 1))
        fn = parse_filename(f.name)
        nums = sheet_numbers(o["lines"]) if o and o["sha256"] == digest else []
        dates = sheet_dates(o["lines"]) if o and o["sha256"] == digest else []
        rec = {"drawing_id": "DRG:" + re.sub(r"[^A-Za-z0-9]+", "_", f.stem).strip("_").upper(), "file": f"drawings/{f.name}", "sha256": digest,
               "filename": fn, "sheet_numbers": nums, "sheet_dates": dates, "ocr_present": bool(o and o["sha256"] == digest),
               "checks": check(fn, nums, dates), "verification_status": "machine_extracted"}
        recs.append(rec)
    n = len(recs)
    conf = sum(r["checks"]["identity_confirmed"] for r in recs)
    part = sum(r["checks"]["identity_partial"] for r in recs)
    alt_bad = [r["file"] for r in recs if r["checks"]["alt_consistent"] is False]
    groups: dict[str, list[dict]] = {}
    for r in recs:
        if r["filename"]["numbers"]:
            groups.setdefault(r["filename"]["numbers"][0], []).append(r)
    lineage = {}
    for num, rs in sorted(groups.items()):
        if len(rs) < 2:
            continue
        num_alt = [(r["filename"]["alteration"], r) for r in rs if isinstance(r["filename"]["alteration"], int)]
        by_alt = max(num_alt, key=lambda x: x[0])[1]["file"] if num_alt else None
        dated = [(max((d["date"] for d in r["sheet_dates"]), default=""), r) for r in rs]
        by_date = max(dated, key=lambda x: x[0])[1]["file"] if any(d for d, _ in dated) else None
        lineage[num] = {"files": [{"file": r["file"], "alteration": r["filename"]["alteration"],
                                   "latest_sheet_date": max((d["date"] for d in r["sheet_dates"]), default=None)} for r in rs],
                        "latest_by_alteration": by_alt, "latest_by_sheet_date": by_date,
                        "agree": by_alt == by_date if by_alt and by_date else None}
    catalog = json.loads((ROOT / "data" / "rdso_drawing_catalog.json").read_text(encoding="utf-8"))
    by_file = {c["file"]: c for c in catalog}
    placeholder = sum(c["title"].startswith("RDSO Drawing Specification") for c in catalog)
    range_files = [r for r in recs if r["filename"]["kind"] != "single"]
    cat_single_for_multi = sum(1 for r in range_files if r["file"].split("/")[-1] in by_file)
    report = {"files": n, "identity_confirmed": conf, "identity_partial": part, "identity_unconfirmed": n - conf - part,
              "alt_inconsistent": alt_bad, "files_with_several_numbers": len(range_files), "lineage_groups": lineage,
              "catalog": {"entries": len(catalog), "placeholder_titles": placeholder,
                          "multi_drawing_files_described_by_one_number": cat_single_for_multi,
                          "note": "catalog titles that are just the file name carry no drawing information; key_highlights are unverified free text"}}
    return recs, report


def main() -> int:
    recs, report = build()
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in recs), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"drawings={report['files']} confirmed={report['identity_confirmed']} partial={report['identity_partial']} "
          f"unconfirmed={report['identity_unconfirmed']} alt_inconsistent={len(report['alt_inconsistent'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
