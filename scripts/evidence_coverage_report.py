#!/usr/bin/env python3
"""Page crops for every paragraph (Phase P2): every paragraph has a stored page region and its crop renders; the paragraphs whose
highlight covers only the opening (coverage "prefix") are listed with the reason.

    python scripts/evidence_coverage_report.py            # write data/knowledge-graph/reports/evidence_coverage.json
    python scripts/evidence_coverage_report.py --check    # Gate W: every paragraph has a region, a deterministic sample renders, the report is current

Reasons for a prefix highlight: HAS_TABLE (the paragraph owns a table, whose cells come out of reading order), SPANS_PAGES (it continues
onto a page the locator could not match line by line), WAIVED (explained by hand in WAIVERS), OTHER (not allowed: fails the gate).
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "reports" / "evidence_coverage.json"
SAMPLE_EVERY = 30         # render every 30th paragraph in the check
# prefix-only paragraphs explained by hand after looking at the page crop
WAIVERS = {"CLAUSE:USFD:CH_05:PARA_5_1_3": "its sentence continues into a proforma format whose lines are not matched in reading order (crop checked 2026-10-01)"}


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def build() -> tuple[dict, list[dict], list[str]]:
    evidence = {e["evidence_id"]: e for e in read_jsonl(KG / "canonical" / "evidence.jsonl")}
    clauses = sorted((n for n in read_jsonl(KG / "canonical" / "nodes.jsonl") if n["id"].startswith("CLAUSE:")), key=lambda n: n["id"])
    tables_js = (ROOT / "data" / "search" / "tables.js").read_text(encoding="utf-8")
    owners = set(re.findall(r'"k":"(CLAUSE:[^"]+)"', tables_js))
    missing, prefix, per = [], [], {}
    for n in clauses:
        alias = n["id"].split(":")[1]
        e = evidence.get("ev:clause:" + n["id"])
        st = per.setdefault(alias, {"clauses": 0, "full_clause": 0, "prefix": 0})
        st["clauses"] += 1
        if not e or not (e.get("line_regions") or e.get("region")):
            missing.append(n["id"])
            continue
        if e.get("coverage") == "full_clause":
            st["full_clause"] += 1
        else:
            st["prefix"] += 1
            spans = int(n.get("page_end") or n["page"]) > int(n["page"])
            reason = "HAS_TABLE" if n["id"] in owners else ("SPANS_PAGES" if spans else ("WAIVED" if n["id"] in WAIVERS else "OTHER"))
            prefix.append({"clause": n["id"], "page": e["page_number"], "reason": reason, "also_spans_pages": spans, **({"note": WAIVERS[n["id"]]} if reason == "WAIVED" else {})})
    summary = {"clauses": len(clauses), "without_region": len(missing), "prefix_only": len(prefix), "per_manual": dict(sorted(per.items())),
               "prefix_by_reason": {r: sum(1 for p in prefix if p["reason"] == r) for r in sorted({p["reason"] for p in prefix})}}
    return {"summary": summary, "prefix_only": prefix, "without_region": missing}, clauses, missing


def main() -> int:
    report, clauses, missing = build()
    text = json.dumps(report, indent=1, ensure_ascii=False) + "\n"
    print(json.dumps(report["summary"], indent=1))
    if "--check" not in sys.argv:
        OUT.write_text(text, encoding="utf-8")
        return 0
    errors = []
    if missing:
        errors.append(f"{len(missing)} paragraphs have no stored page region, e.g. {missing[:3]}")
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
        errors.append("reports/evidence_coverage.json is missing or stale; run scripts/evidence_coverage_report.py")
    if any(p["reason"] == "OTHER" for p in report["prefix_only"]):
        errors.append("a prefix-only highlight has no explanation")
    sys.path.insert(0, str(ROOT / "scripts"))
    import render_evidence as R  # noqa: E402
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    evidence = {e["evidence_id"]: e for e in read_jsonl(KG / "canonical" / "evidence.jsonl")}
    with tempfile.TemporaryDirectory() as tmp:
        tried = 0
        for i, n in enumerate(clauses):
            if i % SAMPLE_EVERY:
                continue
            tried += 1
            if R.render(evidence["ev:clause:" + n["id"]], registry, 40, Path(tmp)) is None:
                errors.append(f"crop of {n['id']} did not render")
    for e in errors:
        print(f"[ERROR] {e}")
    print(f"[SUMMARY] evidence crops: {'FAIL' if errors else 'PASS'}; {tried} sampled crops rendered")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
