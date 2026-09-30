"""Cross-reference extraction and resolution (P2.1).

Finds references to paragraphs, annexures, tables, figures, chapters and external documents in
canonical clause text, and classifies each one:

    RESOLVED   a unique (or all-page) target exists in the canonical store
    DELETED    the paragraph exists only as a deletion tombstone (correction slip)
    EXTERNAL   the target is another document (IS / IRS / RDSO papers, Acts, Codes ...)
    AMBIGUOUS  more than one plausible target
    NOT_FOUND  an internal target that does not exist in the store

Every match is a record with the exact span in the source clause text, so it can be highlighted
and re-verified. "(Back to Para N)" editorial back-links are kept but typed `back_ref`.
Pure function of the node list plus the deleted-paragraph tombstones: deterministic.
"""

from __future__ import annotations

import re

ALIAS_BY_NAME = [
    ("IRPWM", re.compile(r"\bIRPWM\b|permanent\s+way\s+manual", re.I)),
    ("STMM", re.compile(r"\bSTMM\b|small\s+track\s+machines?\s+manual", re.I)),
    ("TMM", re.compile(r"\bTMM\b|track\s+machines?\s+manual", re.I)),
    ("USFD", re.compile(r"\bUSFD\s+manual|ultrasonic\s+testing\s+of\s+rails|manual\s+for\s+ultrasonic", re.I)),
    ("AT_WELD", re.compile(r"alumino[\s-]*thermic\s+welding\s+of\s+rails|fusion\s+welding\s+of\s+rails", re.I)),
    ("FBW", re.compile(r"flash\s+butt\s+welding\s+of\s+rails|manual\s+for\s+flash\s+butt", re.I)),
]
EXTERNAL_HINT = re.compile(r"\b(code|act|rules?|irs|is\s*:|is-|circular|board|letter|rdso|report|schedule|drawing|manual|"
                           r"specification|standard|instructions?|order|policy|gazette)\b", re.I)

ITEM = r"(\d+(?:\.\d+)*[A-Z]?)((?:\s?\([0-9A-Za-z]{1,4}\))*)"
PARA_TRIGGER = re.compile(r"\b(paras?|paragraphs?|clauses?|sub-?paras?)\b\.?\s*(?:no\.?s?)?\s*(?=\d)", re.I)
ITEM_RE = re.compile(ITEM)
LIST_SEP = re.compile(r"\s*(?:,|and|&|or|to)\s*", re.I)
ANNEXURE = re.compile(r"\b(annexures?|appendix)\b\s*[-–:.]?\s*(?:no\.?\s*)?([0-9]+(?:\s*/\s*[0-9]+[A-Za-z]?(?:\([A-Za-z0-9]\))?)?[A-Za-z]?\b|[IVX]{1,5}[A-Z]?\b)", re.I)
TABLE = re.compile(r"\btables?\b\s*[-–:.]?\s*(?:no\.?\s*)?([0-9]+(?:\.[0-9]+)?[A-Za-z]?(?:[-–][A-Za-z0-9]+)?|[IVX]{1,4}\b)", re.I)
FIGURE = re.compile(r"\b(?:fig(?:ure)?s?)\b\.?\s*(?:no\.?\s*)?([0-9]+(?:\.[0-9]+)*(?:\s?\([a-z]\))?)", re.I)
CHAPTER = re.compile(r"\bchapters?\b\s*[-–:.]?\s*(?:no\.?\s*)?(\d{1,2})\b", re.I)
STANDARD = re.compile(
    r"\b(IRS[\s:-]*[A-Z]{0,2}[\s:-]*\d+(?:[\s:-]+\d{2,4})*|(?-i:IS)[\s:-]+\d{2,5}(?:[\s:-]*\(?part\s*\d+\)?)?(?:[\s:-]+\d{4})?|"
    r"RT[-\s]?\d{4}|RDSO[/\s]+[A-Z]{1,3}[-/][A-Z0-9/.\-]{2,}|UIC[\s-]*\d{2,4}|EN[\s-]*\d{3,5})", re.I)
BACK_REF = re.compile(r"\(\s*back\s+to\s+[^)]*\)", re.I)


def norm_key(s: str) -> str:
    return re.sub(r"[\s\-–()]", "", s).upper()


def scope_after(text: str, end: int, own_alias: str) -> tuple[str, str | None]:
    """Where does the reference point? `of the Indian Railway Code`, `of IRPWM` ... -> (alias|EXTERNAL|own, name)."""
    tail = text[end:end + 90]
    m = re.match(r"\s*(?:\)|,)?\s*(?:of|in|under|as per)\s+(?:the\s+)?([^.;\n]{0,70})", tail, re.I)
    if not m:
        return own_alias, None
    phrase = m.group(1)
    for alias, rx in ALIAS_BY_NAME:
        if rx.search(phrase):
            return alias, phrase.strip()
    if re.match(r"(above|below|this|the\s+above|the\s+same|sub-?para|para)\b", phrase, re.I):
        return own_alias, None
    if EXTERNAL_HINT.search(phrase):
        return "EXTERNAL", phrase.strip()[:60]
    return own_alias, None


def build_targets(nodes: list[dict], deleted: dict[str, list[str]]):
    """Lookup tables for resolution."""
    clause_by = {}   # (alias, para) -> clause id
    section_by = {}  # (alias, reference) -> section node id (bare headings)
    annex_by: dict[tuple, list] = {}
    table_by: dict[tuple, list] = {}
    figure_by: dict[tuple, list] = {}
    chapters = set()
    for n in nodes:
        i = n["id"]
        if i.startswith("CLAUSE:"):
            clause_by[(i.split(":")[1], str(n["specs"]["Paragraph"]).upper())] = i
        elif n["type"] == "CHAPTER":
            chapters.add(i)
        elif n["type"] in ("SECTION", "SUBSECTION"):
            m = re.match(r"(?:SUB)?SECTION:([^:]+):[^:]+:SEC_(.+)$", i)
            if m:
                section_by.setdefault((m.group(1), m.group(2).replace("_", ".").upper()), i)
        if n.get("domain") == "manual" and n["type"] in ("TABLE", "FIGURE", "EVIDENCE"):
            alias = i.split(":")[1]
            label = n.get("label", "") + " " + n.get("source_section", "")
            for m in ANNEXURE.finditer(label):
                annex_by.setdefault((alias, norm_key(m.group(2))), []).append((n.get("source_page") or 0, i))
            for m in TABLE.finditer(label):
                table_by.setdefault((alias, norm_key(m.group(1))), []).append((n.get("source_page") or 0, i))
            for m in FIGURE.finditer(label):
                figure_by.setdefault((alias, norm_key(m.group(1))), []).append((n.get("source_page") or 0, i))
    return {"clause": clause_by, "section": section_by, "annex": annex_by, "table": table_by, "figure": figure_by,
            "chapters": chapters, "deleted": {a: {d.upper() for d in v} for a, v in deleted.items()}}


def extract(nodes: list[dict], deleted: dict[str, list[str]]) -> list[dict]:
    T = build_targets(nodes, deleted)
    out: list[dict] = []
    for n in nodes:
        if not n["id"].startswith("CLAUSE:"):
            continue
        cid, text = n["id"], n["text"]
        alias = cid.split(":")[1]
        kind_hundreds = alias in ("IRPWM", "TMM", "STMM")
        spans: list[tuple[int, int, str, dict]] = []
        back_spans = [(m.start(), m.end()) for m in BACK_REF.finditer(text)]

        def in_back(pos: int) -> bool:
            return any(a <= pos < b for a, b in back_spans)

        # paragraph references (with lists)
        for m in PARA_TRIGGER.finditer(text):
            pos = m.end()
            first = True
            while True:
                im = ITEM_RE.match(text, pos)
                if not im:
                    break
                num = im.group(1)
                plausible = (len(re.sub(r"\D", "", num.split(".")[0])) >= 3) if kind_hundreds else ("." in num or len(num) <= 2)
                if not plausible:
                    break
                spans.append((im.start(), im.end(), "para", {"number": num.upper(), "subref": im.group(2).replace(" ", ""),
                                                             "back": in_back(im.start())}))
                pos = im.end()
                sep = LIST_SEP.match(text, pos)
                if not sep:
                    break
                pos = sep.end()
                first = False
            _ = first
        for rx, kind, grp in ((ANNEXURE, "annexure", 2), (TABLE, "table", 1), (FIGURE, "figure", 1), (CHAPTER, "chapter", 1)):
            for m in rx.finditer(text):
                spans.append((m.start(), m.end(), kind, {"number": m.group(grp).strip(), "back": in_back(m.start())}))
        for m in STANDARD.finditer(text):
            spans.append((m.start(), m.end(), "standard", {"number": re.sub(r"\s+", " ", m.group(1)).strip().upper()}))

        # drop overlaps (earlier / longer wins)
        spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
        kept, last_end = [], -1
        for s in spans:
            if s[0] >= last_end:
                kept.append(s)
                last_end = s[1]

        for start, end, kind, info in kept:
            rec = {"source": cid, "source_page": n["page"], "start": start, "end": end, "raw": text[start:end],
                   "kind": "back_ref" if info.get("back") and kind == "para" else kind,
                   "target_kind": kind, "number": info["number"], "subref": info.get("subref", ""),
                   "scope": alias, "scope_name": None, "status": "NOT_FOUND", "targets": []}
            scope, name = scope_after(text, end, alias) if kind == "para" else (alias, None)
            rec["scope"], rec["scope_name"] = scope, name
            if kind == "standard" or scope == "EXTERNAL":
                rec["status"] = "EXTERNAL"
            elif kind == "para":
                key = (scope, info["number"])
                if key in T["clause"]:
                    rec["status"], rec["targets"] = "RESOLVED", [T["clause"][key]]
                elif info["number"] in T["deleted"].get(scope, set()):
                    rec["status"] = "DELETED"
                elif key in T["section"]:
                    rec["status"], rec["targets"] = "RESOLVED", [T["section"][key]]
            elif kind in ("annexure", "table", "figure"):
                hits = T[{"annexure": "annex", "table": "table", "figure": "figure"}[kind]].get((alias, norm_key(info["number"])), [])
                if hits:
                    rec["status"], rec["targets"] = "RESOLVED", [i for _, i in sorted(hits)]
            elif kind == "chapter":
                cid_ch = f"CHAPTER:{alias}:CH_{int(info['number']):02d}"
                if cid_ch in T["chapters"]:
                    rec["status"], rec["targets"] = "RESOLVED", [cid_ch]
            out.append(rec)
    for i, r in enumerate(out, 1):
        r["ref_id"] = f"XREF:{i:05d}"
    return out


def summarize(refs: list[dict]) -> dict:
    by_status: dict[str, int] = {}
    by_kind: dict[str, dict[str, int]] = {}
    for r in refs:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_kind.setdefault(r["target_kind"], {})
        by_kind[r["target_kind"]][r["status"]] = by_kind[r["target_kind"]].get(r["status"], 0) + 1
    return {"total": len(refs), "by_status": dict(sorted(by_status.items())),
            "by_kind": {k: dict(sorted(v.items())) for k, v in sorted(by_kind.items())}}
