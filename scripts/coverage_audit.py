#!/usr/bin/env python3
"""Is every aspect of each manual covered? A line-by-line audit of the page text against the knowledge base.

For every page of every manual, each text line of at least 20 characters is looked up in the paragraphs (clause texts) of that manual. A line
that is in no paragraph and no annexure unit (scripts/build_annexures.py) is classified:

    BOILERPLATE  repeated on many pages (running headers, footers, page marks)
    FRONT_MATTER before the first numbered paragraph (title page, contents, preface, correction slips)
    TABLE        on a page whose tables were extracted into the table store, or table-like (mostly numbers) lines
    ANNEXURE     on a page that is an annexure, appendix, figure or sketch page
    OCR          on a page recovered by OCR (lines not trusted for matching)
    UNCOVERED    none of the above: content that may be missing from the paragraphs

    python scripts/coverage_audit.py            # write data/knowledge-graph/reports/coverage_audit.json and print the summary
    python scripts/coverage_audit.py --check    # Gate Z: the report is current and UNCOVERED stays under the recorded ceilings
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "reports" / "coverage_audit.json"
MIN_LEN = 20
ALIASES = ("IRPWM", "TMM", "STMM", "USFD", "AT_WELD", "FBW")


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def running_lines(pages_of_doc: list[dict], min_pages: int = 8, edge: int = 3, share: float = 0.7) -> set[str]:
    """Normalised lines that are running headers or footers: on at least `min_pages` pages and, in at least `share` of those, among the first or
    last `edge` lines of the page. A line that merely repeats (a table label printed on many pages) is content, not boilerplate."""
    seen, at_edge = Counter(), Counter()
    for p in pages_of_doc:
        lines = [l for l in (p.get("text_content") or "").split("\n") if l.strip()]
        edges = {norm(l) for l in lines[:edge] + lines[-edge:]}
        for l in {norm(x) for x in lines}:
            seen[l] += 1
            if l in edges:
                at_edge[l] += 1
    return {l for l, c in seen.items() if c >= min_pages and at_edge[l] >= share * c}


def main() -> int:
    pages = read_jsonl(KG / "raw" / "extracted_pages.jsonl")
    nodes = [n for n in read_jsonl(KG / "canonical" / "nodes.jsonl") if n["id"].startswith("CLAUSE:")]
    ap = KG / "canonical" / "annexures.jsonl"
    annexes = read_jsonl(ap) if ap.exists() else []
    tables_js = (ROOT / "data" / "search" / "tables.js").read_text(encoding="utf-8")
    table_pages: dict[str, set[int]] = {}
    for m in re.finditer(r'"TBL:([A-Z_]+):P0*(\d+):', tables_js):
        table_pages.setdefault(m.group(1), set()).add(int(m.group(2)))
    ocr_pages = {(p["document_id"], p["page_number"]) for p in pages if p.get("extraction_method") == "ocr" or p.get("is_ocr")}
    report: dict[str, dict] = {}
    for alias in ALIASES:
        docp = sorted((p for p in pages if p["document_id"].split(":")[1] == alias), key=lambda p: p["page_number"])
        clause_blob = norm(" ".join([n["text"] for n in nodes if n["id"].split(":")[1] == alias] + [a["text"] for a in annexes if a["manual"] == alias]))
        first_clause_page = min((int(n["page"]) for n in nodes if n["id"].split(":")[1] == alias), default=1)
        freq = Counter()
        for p in docp:
            for line in {norm(l) for l in (p.get("text_content") or "").split("\n") if len(l.strip()) >= MIN_LEN}:
                freq[line] += 1
        boiler = running_lines(docp)
        stats = Counter()
        per_page = {}
        examples: dict[str, list] = {}
        for p in docp:
            pn = p["page_number"]
            text = p.get("text_content") or ""
            low = text.lower()
            annex_page = bool(re.search(r"^\s*(annexure|appendix)\b", text.strip(), re.I)) or len(re.findall(r"\bfig(?:ure)?\.?\s*\d", low)) >= 3 and len(text) < 1500
            page_unc = 0
            page_lines = 0
            for line in text.split("\n"):
                s = line.strip()
                if len(s) < MIN_LEN:
                    continue
                page_lines += 1
                n = norm(s)
                if n in clause_blob:
                    stats["COVERED"] += 1
                    continue
                digits = sum(c.isdigit() for c in s)
                if n in boiler:
                    kind = "BOILERPLATE"
                elif pn < first_clause_page:
                    kind = "FRONT_MATTER"
                elif (alias, pn) in {(a, q) for a in [alias] for q in table_pages.get(alias, set())} or digits > 0.35 * len(s):
                    kind = "TABLE"
                elif annex_page:
                    kind = "ANNEXURE"
                elif (p["document_id"], pn) in ocr_pages:
                    kind = "OCR"
                else:
                    kind = "UNCOVERED"
                stats[kind] += 1
                if kind == "UNCOVERED":
                    page_unc += 1
                    examples.setdefault(str(pn), []).append(s[:90])
            if page_lines:
                per_page[pn] = page_unc
        total = sum(stats.values())
        worst = sorted(per_page.items(), key=lambda kv: -kv[1])[:12]
        report[alias] = {"pages": len(docp), "lines_checked": total, "by_class": dict(sorted(stats.items())),
                         "uncovered_share": round(stats["UNCOVERED"] / total, 4) if total else 0,
                         "worst_pages": [{"page": pg, "uncovered_lines": n, "examples": examples.get(str(pg), [])[:3]} for pg, n in worst if n]}
    text = json.dumps(report, indent=1, ensure_ascii=False) + "\n"
    for a, r in report.items():
        print(f"{a:8} pages {r['pages']:4} lines {r['lines_checked']:6} {r['by_class']} uncovered {r['uncovered_share']*100:.1f}%")
    if "--check" not in sys.argv:
        OUT.write_text(text, encoding="utf-8")
        return 0
    errors = []
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
        errors.append("reports/coverage_audit.json is missing or stale; run scripts/coverage_audit.py")
    for e in errors:
        print(f"[ERROR] {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
