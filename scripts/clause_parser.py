"""Layout-aware clause parser (P0-R.6).

The earlier extractor matched numbering regexes page by page on flat text. That
truncated clauses at page ends and at 1,200 characters, accepted table numbers
and running headers as paragraphs, and could not tell a heading from a value.

This parser works on the whole document as a stream of layout rows
(page, position, font size, weight, text):

1. rows on the same baseline are merged (number and title split across cells);
2. running headers, footers and page numbers are removed; contents pages are skipped;
3. a *head* is a row that starts with the manual's paragraph numbering, is set in
   bold at the left margin (FBW: left margin only), and carries a title;
4. heads are filtered to the longest strictly increasing numbering chain, which
   rejects values, list items and cross-references that merely look like numbers;
5. the chapter comes from the numbering (101 -> chapter 1, 1001 -> chapter 10,
   8.2.4 -> chapter 8), not from hand-written page ranges;
6. a clause body is every remaining row up to the next head, across pages, stopped
   by CHAPTER / PART / SECTION / Annexure banners; a bare heading with no body is a
   section, not a clause.

Everything is deterministic for a given PDF and PyMuPDF version.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field

import pymupdf

# A banner is a short stand-alone heading row ("CHAPTER - 4", "PART - B", "Annexure - 2/1 (Para 204)"),
# not a sentence that merely starts with the word.
# Head titles that are really chapter/part banners ("145 CHAPTER - 4" = page number + banner)
BANNER_TITLE_RE = re.compile(r"^(CHAPTER|PART)\b|^SECTION\s*[-–:]\s*[IVX\d]", re.I)
BANNER_RE = re.compile(r"^((CHAPTER|PART|SECTION)\b.{0,50}|(ANNEXURE|APPENDIX)\b[^.,;]{0,45})$", re.I)
DELETED_RE = re.compile(r"^\(?\s*deleted\s*\)?\.?$", re.I)
PAGE_NO_RE = re.compile(r"^(\d{1,4}|[ivxlc]{1,6})$", re.I)

# Per-manual head profiles.
#   kind        hundreds: 101, 1001, 211A     decimal: 8.2.4
#   bold        heads must be set in bold
#   margin      max distance (pt) of the head from the page's left text margin
PROFILES = {
    "DOC:IRPWM:2024:ACS14": {"kind": "hundreds", "bold": True, "margin": 14, "min_size": 9},
    "DOC:TMM:2020:ACS10": {"kind": "hundreds", "bold": True, "margin": 14, "min_size": 9},
    "DOC:STMM:2024": {"kind": "hundreds", "bold": True, "margin": 14, "min_size": 9},
    "DOC:USFD:2026:ACS4": {"kind": "decimal", "bold": True, "margin": 60, "min_size": 9},
    "DOC:AT_WELD:2022": {"kind": "decimal", "bold": True, "margin": 60, "min_size": 9},
    "DOC:FBW:2022:CS5": {"kind": "decimal", "bold": False, "margin": 20, "min_size": 9},
}
HUNDREDS_RE = re.compile(r"^(\d{3,4}[A-Z]?)(?:\.?\s+|(?=[A-Z][a-z]))(\S.*)$")  # STMM sets "302Types of ..." without a space
DECIMAL_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,4})\.?\s+(\S.*)$")
NUMBER_ONLY_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,4})\.?$")


@dataclass
class Row:
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    size: float
    bold: bool
    text: str
    idx: int = 0


@dataclass
class Head:
    row: int
    number: str
    key: tuple
    title: str
    page: int
    chapter_hint: int | None = None


@dataclass
class Clause:
    number: str
    title: str
    page: int
    page_end: int
    text: str
    chapter_num: int | None = None
    deleted: bool = False
    row_span: tuple = (0, 0)


@dataclass
class ParseResult:
    clauses: list[Clause] = field(default_factory=list)
    heading_only: list[str] = field(default_factory=list)
    chapter_pages: dict = field(default_factory=dict)  # chapter number -> (first head page, last body page)
    stats: dict = field(default_factory=dict)


def _is_bold(span: dict) -> bool:
    return bool(span["flags"] & 16) or "bold" in span["font"].lower()


def load_rows(pdf_path: str) -> list[Row]:
    doc = pymupdf.open(pdf_path)
    pages: list[list[Row]] = []
    for pno, page in enumerate(doc, 1):
        raw: list[Row] = []
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in line["spans"]).strip()
                raw.append(Row(pno, line["bbox"][0], line["bbox"][1], line["bbox"][2], line["bbox"][3],
                               round(spans[0]["size"], 1), _is_bold(spans[0]), " ".join(text.split())))
        # merge rows sharing a baseline (table cells, number + title in separate spans)
        raw.sort(key=lambda r: (round(r.y0 / 3), r.x0))
        merged: list[Row] = []
        for r in raw:
            if merged and merged[-1].page == r.page and abs(merged[-1].y0 - r.y0) <= 3 and r.x0 >= merged[-1].x0:
                m = merged[-1]
                m.text = f"{m.text} {r.text}"
                m.x1 = max(m.x1, r.x1)
                m.y1 = max(m.y1, r.y1)
            else:
                merged.append(r)
        pages.append(merged)
    return _strip_running_rows(pages, [p.rect.height for p in doc])


def _norm(t: str) -> str:
    return re.sub(r"\d+", "#", t.lower())


def _strip_running_rows(pages: list[list[Row]], heights: list[float]) -> list[Row]:
    counts: dict[str, int] = {}
    for rows, h in zip(pages, heights):
        seen = {_norm(r.text) for r in rows if r.y0 < 0.07 * h or r.y1 > 0.92 * h}
        for k in seen:
            counts[k] = counts.get(k, 0) + 1
    threshold = max(3, int(0.15 * len(pages)))
    out: list[Row] = []
    for rows, h in zip(pages, heights):
        for r in rows:
            edge = r.y0 < 0.07 * h or r.y1 > 0.92 * h
            if edge and (PAGE_NO_RE.match(r.text) or counts.get(_norm(r.text), 0) >= threshold):
                continue
            out.append(r)
    for i, r in enumerate(out):
        r.idx = i
    return out


def _margins(rows: list[Row]) -> dict[int, float]:
    by_page: dict[int, list[float]] = {}
    for r in rows:
        if len(r.text) > 25:
            by_page.setdefault(r.page, []).append(r.x0)
    return {p: sorted(xs)[max(0, len(xs) // 10)] for p, xs in by_page.items()}


def _key(number: str, kind: str) -> tuple:
    if kind == "hundreds":
        m = re.match(r"(\d+)([A-Z]?)", number)
        return (int(m.group(1)), m.group(2))
    return tuple(int(x) for x in number.split("."))


def _lis(keys: list[tuple]) -> list[int]:
    """Indices of a longest strictly increasing subsequence (earliest on ties)."""
    tails: list[tuple] = []
    tail_idx: list[int] = []
    prev = [-1] * len(keys)
    for i, k in enumerate(keys):
        j = bisect.bisect_left(tails, k)
        if j == len(tails):
            tails.append(k)
            tail_idx.append(i)
        else:
            tails[j] = k
            tail_idx[j] = i
        prev[i] = tail_idx[j - 1] if j else -1
    out, i = [], tail_idx[-1] if tail_idx else -1
    while i != -1:
        out.append(i)
        i = prev[i]
    return out[::-1]


TOC_TAIL_RE = re.compile(r"(\.{3,}|\s)\d{1,3}\s*$")


def toc_pages(rows: list[Row], rx) -> set[int]:
    """Pages that list numbered entries with trailing page numbers (contents pages)."""
    hits: dict[int, int] = {}
    for r in rows:
        if rx.match(r.text) and TOC_TAIL_RE.search(r.text):
            hits[r.page] = hits.get(r.page, 0) + 1
    return {p for p, n in hits.items() if n >= 5}


def find_heads(rows: list[Row], profile: dict, pages: set[int] | None = None, chapter_nums: set[int] | None = None) -> tuple[list[Head], int]:
    """`pages`: restrict candidates to registered chapter pages (keeps TOC entries out of the chain)."""
    margins = _margins(rows)
    kind = profile["kind"]
    rx = HUNDREDS_RE if kind == "hundreds" else DECIMAL_RE
    toc = toc_pages(rows, rx)
    cands: list[Head] = []
    for r in rows:
        if r.page in toc or (pages is not None and r.page not in pages):
            continue
        if profile["bold"] and not r.bold:
            continue
        if r.size < profile["min_size"] or r.x0 > margins.get(r.page, 0) + profile["margin"]:
            continue
        m = rx.match(r.text)
        title = None
        if m:
            number, title = m.group(1), m.group(2)
            if not r.text[len(number):len(number) + 1].isspace() and not r.text[len(number):len(number) + 1] == ".":
                r.text = f"{number} {title}"  # "305Technical ..." -> "305 Technical ..."
        elif kind == "decimal":
            m = NUMBER_ONLY_RE.match(r.text)
            if m:
                number = m.group(1)
                nxt = rows[r.idx + 1] if r.idx + 1 < len(rows) else None
                title = nxt.text if nxt and nxt.page == r.page and not NUMBER_ONLY_RE.match(nxt.text) else ""
        if title is None:
            continue
        if chapter_nums is not None:
            lead = int(number.split(".")[0]) if kind == "decimal" else int(re.match(r"\d+", number).group()) // 100
            if lead not in chapter_nums:
                continue
        if kind == "decimal" and not (title == "" or title[0].isalpha() or title[0] in "(“\"'"):
            continue
        if kind == "hundreds" and not (title[0].isalpha() or title[0] in "(“\"'" or
                                       (title[0].isdigit() and sum(c.isalpha() for c in title) >= 3)):
            continue
        if BANNER_TITLE_RE.match(title):
            continue
        cands.append(Head(r.idx, number, _key(number, kind), title, r.page))
    keep = _lis([h.key for h in cands])
    return [cands[i] for i in keep], len(cands)


def _title(raw: str) -> str:
    t = re.split(r"\s[–-]\s|:-|:\s|\.\s", raw, maxsplit=1)[0].strip(" .:-–")
    return (t or raw)[:120]


def parse_manual(pdf_path: str, doc_id: str, chapters: list[dict]) -> ParseResult:
    """`chapters`: registry entries {num, page_start, page_end} for the manual."""
    profile = PROFILES[doc_id]
    rows = load_rows(pdf_path)
    registered = {p for ch in chapters for p in range(ch["page_start"], ch["page_end"] + 1)}
    chapter_nums = {ch["num"] for ch in chapters}
    heads, n_cands = find_heads(rows, profile, registered, chapter_nums)
    chapter_by_num = {ch["num"]: ch for ch in chapters}
    by_page_chapters: dict[int, list[dict]] = {}
    for ch in chapters:
        for p in range(ch["page_start"], ch["page_end"] + 1):
            by_page_chapters.setdefault(p, []).append(ch)

    res = ParseResult()
    assigned_chars = total_chars = 0
    for hi, h in enumerate(heads):
        lead = int(h.number.split(".")[0]) if profile["kind"] == "decimal" else int(re.match(r"\d+", h.number).group()) // 100
        chapter = chapter_by_num[lead]  # numbering owns the chapter; page range only bounds the search
        end_row = heads[hi + 1].row if hi + 1 < len(heads) else len(rows)
        body: list[Row] = []
        skipping_title = False
        for r in rows[h.row:end_row]:
            is_banner = r.idx != h.row and BANNER_RE.match(r.text) and (r.bold or r.text.isupper())
            if is_banner and len(body) <= 1:
                # A chapter banner printed between the paragraph number and its text (interleaved
                # layout): not part of the clause, and not its end either.
                skipping_title = True
                continue
            if is_banner:
                break
            if skipping_title and r.text.isupper() and len(body) <= 1:
                continue
            skipping_title = False
            body.append(r)
        text = "\n".join(r.text for r in body)
        after_head = "\n".join(r.text for r in body[1:]).strip()
        deleted = bool(DELETED_RE.match(after_head)) or bool(DELETED_RE.match(h.title))
        lo, hi = res.chapter_pages.get(chapter["num"], (h.page, h.page))
        res.chapter_pages[chapter["num"]] = (min(lo, h.page), max(hi, body[-1].page if body else h.page))
        if not after_head and not deleted and len(h.title) < 60:
            res.heading_only.append(h.number)
            continue  # a bare heading is a section, not a provision
        res.clauses.append(Clause(h.number, _title(h.title), h.page, body[-1].page if body else h.page, text,
                                  chapter["num"], deleted, (h.row, end_row)))
        assigned_chars += len(text)
    for r in rows:
        if any(ch["page_start"] <= r.page <= ch["page_end"] for ch in chapters):
            total_chars += len(r.text)
    res.stats = {
        "rows": len(rows), "head_candidates": n_cands, "heads_accepted": len(heads),
        "clauses": len(res.clauses), "heading_only": len(res.heading_only), "deleted": sum(c.deleted for c in res.clauses),
        "body_coverage": round(assigned_chars / total_chars, 3) if total_chars else 0.0,
    }
    return res
