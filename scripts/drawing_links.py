#!/usr/bin/env python3
"""Link manual clauses to the drawing sheets we hold (P3.6, P4).

Finds drawing numbers cited in clause text (RT-6154, RDSO/T-6155, T-1899 ...) and marks each citation as
SHEET_HELD (a sheet in drawings/ covers that number) or NO_SHEET. A sheet covers the numbers in its file name; a
"6171 To 6173" file also covers 6172 (range expansion). Matching is on the number only: the manuals write both `RT-` and `T-`
for the same RDSO track-drawing series, an assumption that is not verified against any RDSO index.

Output: canonical/drawing_links.jsonl (one record per citation, exact span) and reports/drawing_links_report.json.
Deterministic.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "canonical" / "drawing_links.jsonl"
REPORT = KG / "reports" / "drawing_links_report.json"

CITE = re.compile(r"(?<![A-Za-z0-9])(?:RDSO\s*/?\s*)?(?:RT|T)\s*[-–/:]?\s*(\d{4,5})(?:\s*[-/]\s*(\d{1,3}|[A-Z])(?![A-Za-z0-9]))?", re.I)
NOT_DRAWING_BEFORE = re.compile(r"(?:IS|IRS|IRSS?|IRPWM|STMM|TMM|ACS|SL|Sr|item|Para|Annexure|Fig|Table|Page|Pg|No)\W{0,3}$", re.I)


def sheet_coverage(registry: list[dict]) -> dict[str, list[str]]:
    cov: dict[str, list[str]] = {}
    for r in registry:
        fn = r["filename"]
        ns = [int(n.split("/")[0][2:]) for n in fn["numbers"]]
        span = set(ns)
        if fn["kind"] == "range" and len(ns) >= 2 and 0 < max(ns) - min(ns) <= 30:
            span |= set(range(min(ns), max(ns) + 1))
        for n in span:
            cov.setdefault(str(n), []).append(r["drawing_id"])
    return {k: sorted(set(v)) for k, v in cov.items()}


def find_citations(text: str) -> list[dict]:
    out = []
    for m in CITE.finditer(text):
        strong = bool(re.match(r"(?:RDSO|RT)", m.group(0), re.I))       # a bare "T-nnnn" needs more care than "RT-nnnn"
        if not strong and NOT_DRAWING_BEFORE.search(text[max(0, m.start() - 8):m.start()]):
            continue
        num = int(m.group(1))
        if not (1000 <= num <= 19999) or (1900 <= num <= 2100 and not strong):
            continue
        out.append({"start": m.start(), "end": m.end(), "raw": m.group(0), "number": str(num), "sub": (m.group(2) or "").upper()})
    return out


def build() -> tuple[list[dict], dict]:
    registry = [json.loads(l) for l in (KG / "canonical" / "drawings_registry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    cov = sheet_coverage(registry)
    recs = []
    for line in (KG / "canonical" / "nodes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(line)
        if not n["id"].startswith("CLAUSE:"):
            continue
        for c in find_citations(n.get("text", "")):
            sheets = cov.get(c["number"], [])
            recs.append({"clause": n["id"], **c, "status": "SHEET_HELD" if sheets else "NO_SHEET", "sheets": sheets,
                         "verification_status": "machine_extracted"})
    for i, r in enumerate(recs, 1):
        r["link_id"] = f"DLINK:{i:05d}"
    cited = {r["number"] for r in recs}
    held = {r["number"] for r in recs if r["status"] == "SHEET_HELD"}
    cited_sheets = {s for r in recs for s in r["sheets"]}
    report = {"citations": len(recs), "distinct_numbers_cited": len(cited), "distinct_numbers_with_sheet": len(held),
              "cited_numbers_without_sheet": sorted(cited - held), "sheets_held": len(registry),
              "sheets_cited_by_a_manual": len(cited_sheets),
              "sheets_never_cited": sorted(r["drawing_id"] for r in registry if r["drawing_id"] not in cited_sheets),
              "clauses_citing_held_sheets": sorted({r["clause"] for r in recs if r["status"] == "SHEET_HELD"}),
              "note": "number-only matching; RT- and T- prefixes treated as one series (unverified)"}
    return recs, report


def main() -> int:
    recs, report = build()
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in recs), encoding="utf-8")
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"citations={report['citations']} distinct={report['distinct_numbers_cited']} with_sheet={report['distinct_numbers_with_sheet']} "
          f"sheets_cited={report['sheets_cited_by_a_manual']}/{report['sheets_held']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
