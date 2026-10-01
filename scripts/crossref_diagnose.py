#!/usr/bin/env python3
"""Why is a cross-reference not resolved? (Phase P2: broken and ambiguous reference report.)

For every NOT_FOUND or AMBIGUOUS reference this finds the reason and, where the source text shows it, the page the thing referred to is on:

    FIGURE_CAPTION_ON_PAGE   a line "Fig. 3.8 ..." exists in the manual's page text, but the figure is a picture, not a node
    FIGURE_NOT_IN_TEXT       no caption line anywhere in the manual (picture without extractable caption, or a misprint)
    ANNEXURE_HEADING_ON_PAGE an "Annexure ..." heading line exists in the page text, but no annexure node was made
    ANNEXURE_NOT_IN_TEXT     no such heading line in the manual
    TABLE_CAPTION_ON_PAGE / TABLE_NOT_IN_TEXT          same for tables
    PARA_NOT_IN_MANUAL       the paragraph number does not exist in the manual (outside its numbering, or a typo)
    SAME_LABEL_MANY_TARGETS  several tables or figures carry the same label ("Table II" in two chapters) and the source gives no way to choose

    python scripts/crossref_diagnose.py            # write data/knowledge-graph/reports/crossref_unresolved.json and print the summary
    python scripts/crossref_diagnose.py --check    # Gate: every unresolved reference has a reason and the committed report is current
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "reports" / "crossref_unresolved.json"
ALIASES = ("IRPWM", "TMM", "STMM", "USFD", "AT_WELD", "FBW")


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def base_number(raw_number: str) -> str:
    """'3.20.1(A)' -> '3.20.1'; 'II' stays; trailing sub-labels are not part of the caption number."""
    return re.sub(r"\s*\([A-Za-z0-9]+\)\s*$", "", raw_number).strip()


def caption_regex(kind: str, number: str) -> re.Pattern:
    n = r"\s*".join(re.escape(c) for c in number.replace(" ", ""))
    if kind == "figure":
        return re.compile(rf"(?im)^\s*(?:fig(?:ure)?s?\.?\s*(?:no\.?)?\s*){n}(?![\d.]*\d)")
    if kind == "annexure":
        return re.compile(rf"(?im)^\s*(?:annexure|annex)\s*[-–—:.]?\s*{n}\b")
    return re.compile(rf"(?im)^\s*(?:table)\s*[-–—:.]?\s*{n}\b")


def diagnose() -> list[dict]:
    refs = read_jsonl(KG / "canonical" / "crossrefs.jsonl")
    docs = {}
    for p in read_jsonl(KG / "raw" / "extracted_pages.jsonl"):
        docs.setdefault(p["document_id"], []).append((p["page_number"], p.get("text_content") or ""))
    registry_ids = {r["id"] for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    doc_of = {a: next((d for d in registry_ids if d.startswith(f"DOC:{a}:")), None) for a in ALIASES}
    cache: dict[tuple, list[int]] = {}
    out = []
    for r in refs:
        if r["status"] not in ("NOT_FOUND", "AMBIGUOUS"):
            continue
        alias = r["source"].split(":")[1]
        kind = r["target_kind"]
        num = base_number(re.sub(r"\s+", " ", str(r["number"])))
        rec = {"ref_id": r["ref_id"], "source": r["source"], "raw": " ".join(r["raw"].split()), "kind": kind, "status": r["status"], "pages": []}
        if r["status"] == "AMBIGUOUS":
            rec["reason"] = "SAME_LABEL_MANY_TARGETS"
            rec["candidates"] = r.get("candidates", [])
        elif kind == "para":
            rec["reason"] = "PARA_NOT_IN_MANUAL"
        elif kind in ("figure", "annexure", "table"):
            key = (alias, kind, num)
            if key not in cache:
                rx = caption_regex(kind, num)
                cache[key] = [pg for pg, txt in docs.get(doc_of[alias], []) if rx.search(txt)]
            rec["pages"] = cache[key]
            rec["reason"] = f"{kind.upper()}_{'CAPTION' if kind != 'annexure' else 'HEADING'}_ON_PAGE" if rec["pages"] else f"{kind.upper()}_NOT_IN_TEXT"
        else:
            rec["reason"] = "OTHER"
        out.append(rec)
    return out


def summarize(items: list[dict]) -> dict:
    by: dict[str, int] = {}
    for i in items:
        by[i["reason"]] = by.get(i["reason"], 0) + 1
    return {"total": len(items), "by_reason": dict(sorted(by.items()))}


def main() -> int:
    items = diagnose()
    report = {"summary": summarize(items), "items": items}
    text = json.dumps(report, indent=1, ensure_ascii=False) + "\n"
    print(json.dumps(report["summary"], indent=1))
    if "--check" not in sys.argv:
        OUT.write_text(text, encoding="utf-8")
    else:
        errors = []
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            errors.append("reports/crossref_unresolved.json is missing or stale; run scripts/crossref_diagnose.py --write")
        if any(i["reason"] == "OTHER" for i in items):
            errors.append("an unresolved reference has no reason")
        for e in errors:
            print(f"[ERROR] {e}")
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
