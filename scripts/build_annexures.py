#!/usr/bin/env python3
"""Annexures and appendices as searchable units (coverage layer).

The numbered paragraphs of a manual are only part of it: the annexures (forms, check-lists, tables, procedures, sketches with text) sit after
the paragraphs and are not part of any paragraph. This script cuts them out of the page text, one unit per annexure or appendix:

    start    a page whose first lines carry a heading "Annexure - 3/17 (Para 349)", "ANNEXURE-IV", "Appendix II" ...
    end      the page before the next annexure heading, or before a page that is body text again (mostly covered by paragraphs)
    text     the page text of those pages, without running headers and page numbers

Output: data/knowledge-graph/canonical/annexures.jsonl (one record per unit). The text is a verbatim copy of page text (checked by
tests/test_annexures.py) and every unit has its manual, chapter, page and page range. Indexed for search (kind "annexure") and shown in Browse.

    python scripts/build_annexures.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "canonical" / "annexures.jsonl"
ALIASES = ("IRPWM", "TMM", "STMM", "USFD", "AT_WELD", "FBW")
HEAD = re.compile(r"^\s*(annexures?|annex|appendix)\b[\s\-–—:.]*((?:[0-9]+(?:[./][0-9A-Za-z]+)*(?:\([A-Za-z0-9]\))?|[IVX]{1,5}(?:[-\s]?[A-Z])?(?:-?[‘'’“\"][A-Z][’'”\"])?)(?![0-9A-Za-z])\.?)\s*(.*)$", re.I)
SENTENCE_WORDS = re.compile(r"\b(is|are|gives?|shows?|shown|may|should|shall|has|have|will|of the|to be)\b", re.I)
TOP_LINES = 8


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def heading_of(text: str) -> tuple[str, str, str] | None:
    """(label, number, rest of the heading line) when one of the first lines of the page is an annexure heading."""
    for line in [l for l in text.split("\n") if l.strip()][:TOP_LINES]:
        m = HEAD.match(line)
        if not m:
            continue
        rest = m.group(3).strip()
        if len(line.strip()) > 110 or (rest and SENTENCE_WORDS.search(rest) and not rest.startswith("(")) or re.match(r"^[a-z]", rest):
            continue            # a sentence that mentions an annexure, not its heading
        kind = "Appendix" if m.group(1).lower() == "appendix" else "Annexure"
        number = re.sub(r"\s+", "", m.group(2)).rstrip(".")
        return f"{kind} {number}", number, rest
    return None


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
    nodes = read_jsonl(KG / "canonical" / "nodes.jsonl")
    chapters = [n for n in nodes if n["type"] == "CHAPTER" and n["id"].split(":")[1] in ALIASES]
    clause_blob = {a: norm(" ".join(n["text"] for n in nodes if n["id"].startswith(f"CLAUSE:{a}:"))) for a in ALIASES}
    records = []
    for alias in ALIASES:
        docp = sorted((p for p in pages if p["document_id"].split(":")[1] == alias), key=lambda p: p["page_number"])
        freq = Counter()
        for p in docp:
            for l in {norm(x) for x in (p.get("text_content") or "").split("\n") if x.strip()}:
                freq[l] += 1
        boiler = running_lines(docp)

        def clean(text: str) -> str:
            keep = [l for l in text.split("\n") if l.strip() and norm(l) not in boiler and not re.fullmatch(r"\s*(page\s*)?\d{1,3}\s*", l, re.I)]
            return "\n".join(keep)

        def covered(p: dict) -> float:
            lines = [norm(l) for l in (p.get("text_content") or "").split("\n") if len(l.strip()) >= 20]
            return sum(1 for l in lines if l in clause_blob[alias]) / len(lines) if lines else 0.0

        heads = {p["page_number"]: heading_of(p.get("text_content") or "") for p in docp}
        by_page = {p["page_number"]: p for p in docp}
        units: list[dict] = []
        cur = None
        for p in docp:
            pn, h = p["page_number"], heads[p["page_number"]]
            if h:
                if cur and cur["label"] == h[0] and pn == cur["pages"][-1] + 1:
                    cur["pages"].append(pn)         # same annexure continues on the next page
                    continue
                cur = {"label": h[0], "number": h[1], "rest": h[2], "pages": [pn]}
                units.append(cur)
            elif cur and pn == cur["pages"][-1] + 1 and covered(p) < 0.6:
                cur["pages"].append(pn)             # a continuation page that is not paragraph text again
            else:
                cur = None
        seen = Counter()
        for u in units:
            first = by_page[u["pages"][0]]
            text = "\n".join(clean(by_page[pn].get("text_content") or "") for pn in u["pages"]).strip()
            if len(text) < 60:
                continue
            title_lines = [l.strip() for l in (first.get("text_content") or "").split("\n") if l.strip()]
            at = next((i for i, l in enumerate(title_lines) if HEAD.match(l)), 0)
            def tidy(t: str) -> str:
                t = re.sub(r"^[\s–—:-]*(\(?\s*paras?\b[^)]*\)?)?[\s–—:-]*", "", t, flags=re.I).strip()      # "(Para 349)" is kept in refers_to_paras, not in the title
                return t
            parts = [tidy(u["rest"])] + [tidy(l) for l in title_lines[at + 1:at + 3]]
            title = parts[0] if len(parts[0]) >= 12 else " ".join(x for x in parts[:2] if x)
            title = title[:100]
            paras = re.findall(r"\bparas?\.?\s*([0-9][0-9A-Za-z.,()\s&]*)", u["rest"], re.I)
            ch = next((c for c in chapters if c["id"].split(":")[1] == alias and c["specs"].get("Page Range") and
                       c["specs"]["Page Range"][0] <= u["pages"][0] <= c["specs"]["Page Range"][1]), None)
            slug = re.sub(r"[^A-Za-z0-9]+", "_", u["number"]).strip("_")
            seen[slug] += 1
            aid = f"ANNEX:{alias}:{slug}" + (f"_{seen[slug]}" if seen[slug] > 1 else "")
            records.append({"id": aid, "manual": alias, "chapter": ch["id"] if ch else None, "label": u["label"], "number": u["number"],
                            "title": " ".join(title.split()), "refers_to_paras": [" ".join(x.split()).rstrip(",&) ") for x in paras],
                            "page": u["pages"][0], "page_end": u["pages"][-1], "text": text})
    # loose text: runs of lines that are in no paragraph and no annexure (a paragraph's tail on a continuation page, a worked example after a
    # table), kept so that the text is searchable and citable instead of being dropped
    loose = []
    for alias in ALIASES:
        docp = sorted((p for p in pages if p["document_id"].split(":")[1] == alias), key=lambda p: p["page_number"])
        mine = [r for r in records if r["manual"] == alias]
        blob = norm(" ".join([n["text"] for n in nodes if n["id"].startswith(f"CLAUSE:{alias}:")] + [r["text"] for r in mine]))
        first_clause_page = min((int(n["page"]) for n in nodes if n["id"].startswith(f"CLAUSE:{alias}:")), default=1)
        freq = Counter()
        for p in docp:
            for l in {norm(x) for x in (p.get("text_content") or "").split("\n") if x.strip()}:
                freq[l] += 1
        boiler = running_lines(docp)
        for p in docp:
            if p["page_number"] < first_clause_page:
                continue
            run, runs = [], []
            for line in (p.get("text_content") or "").split("\n"):
                st = line.strip()
                if not st:
                    continue
                unc = len(st) >= 20 and norm(st) not in blob and norm(st) not in boiler
                if unc or (run and len(st) < 20 and norm(st) not in boiler):
                    run.append((st, unc))
                elif run:
                    runs.append(run)
                    run = []
            if run:
                runs.append(run)
            k = 0
            for r in runs:
                while r and not r[-1][1]:
                    r = r[:-1]
                if sum(1 for _, u in r if u) < 3:
                    continue
                k += 1
                ch = next((c for c in chapters if c["id"].split(":")[1] == alias and c["specs"].get("Page Range") and c["specs"]["Page Range"][0] <= p["page_number"] <= c["specs"]["Page Range"][1]), None)
                loose.append({"id": f"ANNEX:{alias}:p{p['page_number']}" + (f"_{k}" if k > 1 else ""), "manual": alias, "chapter": ch["id"] if ch else None,
                              "label": f"Text on page {p['page_number']}", "number": f"p{p['page_number']}", "title": " ".join(r[0][0].split())[:100], "refers_to_paras": [],
                              "page": p["page_number"], "page_end": p["page_number"], "text": "\n".join(x for x, _ in r), "unit": "loose_text"})
    # front matter: everything before the first numbered paragraph (title page, contents, preface, correction-slip list, definitions)
    front = []
    for alias in ALIASES:
        docp = sorted((p for p in pages if p["document_id"].split(":")[1] == alias), key=lambda p: p["page_number"])
        first = min((int(n["page"]) for n in nodes if n["id"].startswith(f"CLAUSE:{alias}:")), default=1)
        part = [p for p in docp if p["page_number"] < first]
        freq = Counter()
        for p in docp:
            for l in {norm(x) for x in (p.get("text_content") or "").split("\n") if x.strip()}:
                freq[l] += 1
        text = "\n".join(l for p in part for l in (p.get("text_content") or "").split("\n") if l.strip() and freq[norm(l)] < 8)
        if len(text) > 200:
            front.append({"id": f"ANNEX:{alias}:front", "manual": alias, "chapter": None, "label": f"Front matter (pages 1 to {first - 1})", "number": "front", "title": "Title page, contents, preface, correction slips",
                          "refers_to_paras": [], "page": 1, "page_end": first - 1, "text": text, "unit": "front_matter"})
    records += loose + front
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    per = Counter(r["manual"] for r in records)
    print(f"{len(records)} units ({len(loose)} loose-text runs, {len(front)} front matter) {dict(per)} -> {OUT.relative_to(ROOT)}; {sum(len(r['text']) for r in records):,} characters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
