"""Title-block and alteration-table extraction from drawing OCR lines (P3.3, P3.2).

Works on positioned OCR lines (box = [x0, y0, x1, y1] as fractions of the page), not on reading order. The sheet
layout is fixed: a bottom row SPECIFICATION | SCALE | ALT: | DESCRIPTION | DATE | drawing number, the alteration rows
stacked above it (number, description, date), and the drawing description in a block above the number.

Everything returned is `machine_extracted` with the boxes it came from; a field that cannot be located is None,
never guessed.
"""
from __future__ import annotations

import re

DATE_RE = re.compile(r"(?<!\d)(\d{2})[.\-/](\d{2})[.\-/](\d{4})(?!\d)")
NUM_ONLY = re.compile(r"^\s*(\d{1,2})\s*[.,]?\s*$")
SHEET_NUM = re.compile(r"R\.?\s*D\.?\s*S\.?\s*[O0]\.?\s*/?\s*T\s*[-–]?\s*(\d{4})(?:\s*[-/_]\s*(\d{1,3}|[A-Z]))?", re.I)
HEADERS = {"specification": r"SPECIFICATION", "scale": r"SCALE", "alt": r"ALT[:.]?", "description": r"DESCRIPTION", "date": r"DATE"}
LEGEND = re.compile(r"PROPERTY|RESEARCH\s*DESIGNS|MINISTRY|LUCKNOW|ANDSHALL|SHALL\s*NOT|REPRODUCED|PRIORCONSENT|PRIOR\s*CONSENT|WITHOUT", re.I)
REV_START = re.compile(r"^(REVISED|REDRAWN|NEW\b|ADDED|MODIFIED|DELETED|ALTERED|AMENDED|FIRST\s+ISSUE|ISSUED)", re.I)
NOISE = re.compile(r"^(R\.?\s*D\.?\s*S\.?\s*[O0]\.?|\(?T\)?|No\.?|OFF|PART|DESCRIPTION|STAMP.*|ADVANCE|J8EC)$", re.I)


def _cx(l):
    return (l["box"][0] + l["box"][2]) / 2


def _anchors(lines: list[dict]) -> dict:
    out = {}
    for key, pat in HEADERS.items():
        cands = [l for l in lines if re.fullmatch(pat, l["text"].strip(), re.I) and l["box"][1] > 0.85]
        if cands:
            out[key] = max(cands, key=lambda l: l["box"][1])   # lowest such line is the header row of the title block
    return out


def _drawing_number(lines: list[dict]):
    c = [l for l in lines if l["box"][1] > 0.85 and l["box"][0] > 0.55 and SHEET_NUM.search(l["text"])]
    return max(c, key=lambda l: l["box"][1]) if c else None


def extract(lines: list[dict]) -> dict:
    anchors = _anchors(lines)
    num = _drawing_number(lines)
    res = {"anchors_found": sorted(anchors), "drawing_number_line": None, "title": None, "title_lines": [],
           "specification": None, "scale": None, "alterations": []}
    if num:
        m = SHEET_NUM.search(num["text"])
        res["drawing_number_line"] = f"T-{m.group(1)}" + (f"/{m.group(2).upper()}" if m.group(2) else "")
        # description block: right-hand column above the drawing number
        x_lo = num["box"][0] - 0.07
        y_hi = num["box"][1]
        blk = [l for l in lines if l["box"][0] >= x_lo and y_hi - 0.22 <= l["box"][1] < y_hi - 0.004
               and not NOISE.match(l["text"].strip()) and len(l["text"].strip()) > 3]
        # the block is the run of lines below the "R. D. S. O." heading if it was read
        heading = [l for l in lines if l["box"][0] >= x_lo and l["box"][1] < y_hi and re.match(r"^R\.?$", l["text"].strip())]
        if heading:
            y0 = max(h["box"][1] for h in heading)
            blk = [l for l in blk if l["box"][1] > y0]
        legend = [l for l in blk if LEGEND.search(l["text"])]
        if legend:                                   # the description sits below the ownership legend
            y1 = max(l["box"][1] for l in legend)
            blk = [l for l in blk if l["box"][1] > y1]
        blk = [l for l in blk if not DATE_RE.search(l["text"])]
        blk.sort(key=lambda l: (l["box"][1], l["box"][0]))
        res["title_lines"] = [l["text"].strip() for l in blk]
        res["title"] = " ".join(res["title_lines"]) or None
    order = [k for k in ("specification", "scale", "alt", "description", "date") if k in anchors]

    def column(key):
        a = anchors.get(key)
        if not a:
            return None
        i = order.index(key)
        lo = (_cx(anchors[order[i - 1]]) + _cx(a)) / 2 if i else a["box"][0] - 0.05
        hi = (_cx(a) + _cx(anchors[order[i + 1]])) / 2 if i + 1 < len(order) else a["box"][2] + 0.05
        near = [l for l in lines if lo <= _cx(l) < hi and a["box"][1] - 0.035 < l["box"][1] < a["box"][1] - 0.004]
        return " ".join(l["text"].strip() for l in sorted(near, key=lambda l: (l["box"][1], l["box"][0]))) or None

    res["specification"] = column("specification")
    res["scale"] = column("scale")
    if "alt" in anchors and "description" in anchors:
        alt, desc = anchors["alt"], anchors["description"]
        num_lo, num_hi = alt["box"][0] - 0.02, alt["box"][2] + 0.002
        date_x = anchors["date"]["box"][0] - 0.03 if "date" in anchors else desc["box"][2]
        y_top, y_bot = alt["box"][1] - 0.2, alt["box"][1] - 0.004
        date_hi = num["box"][0] - 0.004 if num else 1.0
        nums = [l for l in lines if NUM_ONLY.match(l["text"]) and num_lo <= l["box"][0] <= num_hi and y_top < l["box"][1] < y_bot]
        d_lo = min(alt["box"][2] - 0.004, (max(l["box"][2] for l in nums) + 0.001) if nums else 9.0)
        starts = [l for l in lines if REV_START.match(l["text"].strip()) and d_lo <= l["box"][0] < date_x and y_top < l["box"][1] < y_bot]
        dts = [l for l in lines if DATE_RE.search(l["text"]) and date_x <= l["box"][0] < date_hi and y_top < l["box"][1] < y_bot]
        anchor_rows: list[dict] = []
        for kind, group in (("num", nums), ("start", starts), ("date", dts)):
            for l in group:
                for r in anchor_rows:
                    if abs(r["y"] - l["box"][1]) < 0.02:
                        r[kind] = l
                        break
                else:
                    anchor_rows.append({"y": l["box"][1], kind: l})
        anchor_rows.sort(key=lambda r: r["y"])
        for i, r in enumerate(anchor_rows):
            top = r["y"] - 0.014
            bottom = anchor_rows[i + 1]["y"] - 0.014 if i + 1 < len(anchor_rows) else y_bot
            band = [l for l in lines if top <= l["box"][1] < bottom]
            text = [l["text"].strip() for l in sorted(band, key=lambda l: (l["box"][1], l["box"][0]))
                    if d_lo <= l["box"][0] < date_x and not NUM_ONLY.match(l["text"])]
            dm = DATE_RE.search(r["date"]["text"]) if "date" in r else None
            res["alterations"].append({"number": int(NUM_ONLY.match(r["num"]["text"]).group(1)) if "num" in r else None,
                                       "date": f"{dm.group(3)}-{dm.group(2)}-{dm.group(1)}" if dm else None,
                                       "summary": text[0] if text else None, "details": text[1:], "y": round(r["y"], 4)})
    _infer_numbers(res["alterations"])
    return res


def _infer_numbers(rows: list[dict]) -> None:
    """A row whose number was not read, between two read numbers that leave exactly one value free, gets it (marked)."""
    for i, r in enumerate(rows):
        r["number_inferred"] = False
        if r["number"] is None and 0 < i < len(rows) - 1 and rows[i - 1]["number"] and rows[i + 1]["number"]:
            hi, lo = rows[i - 1]["number"], rows[i + 1]["number"]
            if hi - lo == 2:
                r["number"], r["number_inferred"] = lo + 1, True
