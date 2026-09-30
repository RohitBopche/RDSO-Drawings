"""Structured measurements from clause text and tables (P2.3).

A bare "30 mm" is not a fact. A measurement keeps what it is a value *of*:

    quantity     wear, gap, clearance, speed, temperature, ...   (from a fixed keyword list, else None)
    subject      the words of the sentence (or the table row and column) the value belongs to
    comparator   max | min | range | tolerance | value
    lo, hi       numeric bounds in the stated unit
    unit         canonical unit (mm, cm, m, km, kmph, kg, kg/m, t, kn, mpa, %, degC, deg, mhz, hz, day, month, year,
                 hour, minute, second, gmt, litre)
    source       text (character span inside the clause text) or table (table id, row, column)

Deterministic and conservative: references such as "Para 429", "Annexure 4/2", "Fig 3.4", years, drawing and
standard numbers are not measurements. Everything is `machine_extracted`.
"""

from __future__ import annotations

import re

UNIT_MAP = {
    "mm": "mm", "cm": "cm", "km/h": "kmph", "kmph": "kmph", "kmh": "kmph", "km": "km", "m": "m", "metre": "m", "metres": "m",
    "meter": "m", "meters": "m", "kg/m": "kg/m", "kg": "kg", "kn": "kn", "mpa": "mpa", "t": "t", "tonne": "t", "tonnes": "t",
    "%": "%", "°c": "degC", "° c": "degC", "deg c": "degC", "degree": "deg", "degrees": "deg", "deg": "deg", "mhz": "mhz",
    "khz": "khz", "hz": "hz", "db": "db", "day": "day", "days": "day", "month": "month", "months": "month", "year": "year",
    "years": "year", "hour": "hour", "hours": "hour", "hr": "hour", "hrs": "hour", "minute": "minute", "minutes": "minute",
    "min": "minute", "mins": "minute", "second": "second", "seconds": "second", "sec": "second", "secs": "second",
    "gmt": "gmt", "litre": "litre", "litres": "litre", "liter": "litre", "liters": "litre",
}
UNIT_RE = (r"(km/h|kmph|kmh|kg/m|mm|cm|km|kn|mpa|khz|mhz|hz|db|kg|gmt|"
           r"metres?|meters?|tonnes?|litres?|liters?|degrees?|°\s?c|deg\s?c|days?|months?|years?|hours?|hrs?|"
           r"minutes?|mins?|seconds?|secs?|%|m|t)")
NUM = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
COMP_MAX = r"(?:not\s+(?:more|greater)\s+than|not\s+exceed(?:ing)?|maximum(?:\s+(?:of|is|shall\s+be))?|max\.?|up\s?to|upto|less\s+than|below|within|upper\s+limit)"
COMP_MIN = r"(?:not\s+less\s+than|at\s+least|minimum(?:\s+(?:of|is|shall\s+be))?|min\.?|more\s+than|greater\s+than|above|exceed(?:ing|s)?|lower\s+limit)"

RANGE = re.compile(rf"{NUM}\s*(?:to|and|-|–)\s*{NUM}\s*{UNIT_RE}(?![A-Za-z/²])", re.I)
PM = re.compile(rf"(?:±|\+/-|\+\s?-)\s*{NUM}\s*{UNIT_RE}(?![A-Za-z/²])", re.I)
PLUS_MINUS_PAIR = re.compile(rf"\+\s*{NUM}\s*{UNIT_RE}?\s*,?\s*[-−–]\s*{NUM}\s*{UNIT_RE}(?![A-Za-z/²])", re.I)
SINGLE = re.compile(rf"(?P<comp>{COMP_MAX}|{COMP_MIN})?\s*{NUM}\s*{UNIT_RE}(?![A-Za-z/²])", re.I)
SKIP_BEFORE = re.compile(r"(para(?:graph)?s?|annexure|appendix|fig(?:ure)?s?|table|clause|chapter|irs|(?-i:IS)|rt|no|sl|sr|item|drg|drawing|acs|"
                         r"note|section|rule)\W{0,4}$", re.I)
QUANTITIES = [
    ("wear", r"\bwear\b|\bworn\b"), ("gap", r"\bgap\b|\bopening\b"), ("clearance", r"clearance|flangeway"),
    ("speed", r"\bspeed\b|\bkmph\b|km/h"), ("temperature", r"temperature|\btd\b|\bt_d\b"),
    ("gauge", r"\bgauge\b"), ("cant", r"\bcant\b|super-?elevation"), ("height", r"\bheight\b|\bdepth\b|cushion"),
    ("width", r"\bwidth\b"), ("length", r"\blength\b"), ("distance", r"\bdistance\b|\bspacing\b|\bapart\b"),
    ("thickness", r"thickness"), ("diameter", r"diameter|\bdia\b"), ("radius", r"radius|\bcurve of\b"),
    ("load", r"\bload\b|\bforce\b|\bpressure\b|\bweight\b"), ("frequency", r"frequency|interval|periodicity|\bonce\b|\bevery\b|\bper\b"),
    ("time", r"\bduration\b|\btime\b|\bperiod\b|\bwithin\b"), ("gradient", r"gradient|slope"),
]
QUANTITY_RES = [(q, re.compile(p, re.I)) for q, p in QUANTITIES]
# a quantity only sticks if the unit can measure it; otherwise the nearest keyword was a coincidence
LENGTH = {"mm", "cm", "m", "km"}
COMPAT = {"wear": LENGTH, "gap": LENGTH, "clearance": LENGTH, "gauge": LENGTH, "cant": {"mm"}, "height": LENGTH, "width": LENGTH,
          "length": LENGTH, "distance": LENGTH, "thickness": LENGTH, "diameter": LENGTH, "radius": LENGTH, "speed": {"kmph"},
          "temperature": {"degC"}, "load": {"kg", "t", "kn", "mpa"}, "gradient": {"%", "deg"},
          "frequency": {"day", "month", "year", "hour", "minute", "second", "km", "m", "gmt"},
          "time": {"day", "month", "year", "hour", "minute", "second", "gmt"}}
# implausible for a railway value in this unit -> a code, model number or page furniture, not a measurement
UNIT_MAX = {"kmph": 400, "%": 100, "deg": 360, "degC": 100}
SIGNED_RANGE = re.compile(rf"([+\-−–]\s?\d+(?:\.\d+)?)\s*{UNIT_RE}?\s*to\s*([+\-−–]?\s?\d+(?:\.\d+)?)\s*{UNIT_RE}(?![A-Za-z/²])", re.I)
YEARISH = re.compile(r"^(19|20)\d\d$")


def to_num(s: str) -> float:
    return float(s.replace(",", ""))


def canon_unit(u: str) -> str | None:
    return UNIT_MAP.get(re.sub(r"\s+", " ", u.lower()).strip())


def quantity_of(window: str) -> str | None:
    best, pos = None, -1
    for q, rx in QUANTITY_RES:
        for m in rx.finditer(window):
            if m.start() >= pos:      # the keyword closest to the value wins
                best, pos = q, m.start()
    return best


def split_sentences(text: str) -> list[tuple[int, int]]:
    spans, last = [], 0
    for m in re.finditer(r"(?<=[.!?;])\s+(?=[A-Z(\d])|\n(?=\s*(?:\(\w{1,4}\)|\d+[.)]))", text):
        spans.append((last, m.start()))
        last = m.end()
    spans.append((last, len(text)))
    return [(a, b) for a, b in spans if b - a >= 10]


def _skip(text: str, start: int, raw_num: str) -> bool:
    if SKIP_BEFORE.search(text[max(0, start - 16):start]):
        return True
    if YEARISH.match(raw_num.split(".")[0]) and "." not in raw_num:
        return True
    return False


def _fix_quantity(q, unit, hi, lo):
    if q and unit not in COMPAT.get(q, {unit}):
        q = None
    return q


def _plausible(unit, lo, hi):
    lim = UNIT_MAX.get(unit)
    return lim is None or max(abs(x) for x in (lo, hi) if x is not None) <= lim


CONDITION_RES = [
    ("rail_section", re.compile(r"\b(?:52|60|90)\s?kg\b(?!\s*/\s*m)|\b60\s?E1\b|\bUIC\s?60\b|\b(?:90|110)\s?UTS\b", re.I)),
    ("sleeper", re.compile(r"\b(?:PSC|wooden|steel\s+trough|concrete|CST-?9|ST)\s+sleepers?\b", re.I)),
    ("geometry", re.compile(r"\b(?:straight\s+track|straight|curves?|curved|turnouts?|points\s+and\s+crossings?|crossings?|switch(?:es)?|SEJ|"
                            r"bridges?|tunnels?|level\s+crossings?|station\s+yards?|running\s+lines?|loop\s+lines?|main\s+lines?|"
                            r"transition|approach(?:es)?)\b", re.I)),
    ("gauge", re.compile(r"\b(?:BG|MG|NG|broad\s+gauge|metre\s+gauge|narrow\s+gauge)\b")),
    ("route_class", re.compile(r"\bGroup\s+[A-E]\b|\bZone[\s-]*(?:I{1,3}|IV|V)\b|\b[A-E]\s+class\s+routes?\b|\bQ\s+routes?\b|\brunning\s+track\b", re.I)),
    ("traffic", re.compile(r"\b(?:passenger|goods|freight|mixed)\s+(?:traffic|trains?|lines?)\b", re.I)),
]


def context_quality(window: str) -> str:
    """"prose" if the words around a value read as a sentence, "fragment" if they look like flattened table, figure or
    drawing labels (many one- or two-letter tokens, codes and numbers): such a value is often real text but its meaning is lost."""
    toks = window.split()
    if not toks:
        return "fragment"
    words = sum(1 for t in toks if re.fullmatch(r"[A-Za-z][a-z]{2,}[,.;:]?", t) or re.fullmatch(r"[A-Za-z]{3,}", t))
    return "prose" if words / len(toks) >= 0.5 else "fragment"


def conditions_in(sentence: str, own: tuple[int, int]) -> list[dict]:
    """What the sentence says the value applies to, excluding the value's own span (deterministic patterns, not understanding)."""
    out, seen = [], set()
    lo, hi = max(0, own[0] - 100), min(len(sentence), own[1] + 60)     # nearby words only: long flattened table text is noise
    for kind, rx in CONDITION_RES:
        for m in rx.finditer(sentence, lo, hi):
            if m.start() < own[1] and m.end() > own[0]:
                continue
            key = (kind, re.sub(r"s?\W*$", "", re.sub(r"\s+", "", m.group(0).lower())))
            if key not in seen:
                seen.add(key)
                out.append({"type": kind, "raw": " ".join(m.group(0).split())})
    return out


def extract_from_text(clause_id: str, text: str) -> list[dict]:
    out = []
    for s0, s1 in split_sentences(text):
        sent = text[s0:s1]
        used: list[tuple[int, int]] = []
        sent_records: list[tuple[int, int, int]] = []

        def free(a, b):
            return all(b <= x or a >= y for x, y in used)

        def emit(m, comparator, lo, hi, unit_raw, ext=0):
            unit = canon_unit(unit_raw)
            if not unit or not _plausible(unit, lo, hi):
                return
            a, b = m.start() - ext, m.end()
            used.append((a, b))
            window = sent[max(0, a - 110):a]
            q = _fix_quantity(quantity_of(window) or quantity_of(sent[:a]), unit, hi, lo)
            conds = conditions_in(sent, (a, b))
            cq = context_quality(sent[max(0, a - 100):b + 60])
            sent_records.append((len(out), a, b))
            out.append({"clause": clause_id, "source": "text", "conditions": conds, "context": cq, "start": s0 + a, "end": s0 + b, "raw": text[s0 + a:s0 + b].strip(),
                        "quantity": q, "comparator": comparator, "lo": lo, "hi": hi, "unit": unit,
                        "subject": " ".join(sent[max(0, a - 110):a].split())[-110:] or " ".join(sent.split())[:80]})

        for m in PLUS_MINUS_PAIR.finditer(sent):
            emit(m, "tolerance", -to_num(m.group(3)), to_num(m.group(1)), m.group(4))
        for m in SIGNED_RANGE.finditer(sent):
            if free(m.start(), m.end()):
                a = float(re.sub(r"[−–\s]", lambda x: "-" if x.group() != " " and x.group() in "−–" else "", m.group(1)).replace("--", "-"))
                b = float(re.sub(r"[−–\s]", lambda x: "-" if x.group() in "−–" else "", m.group(3)))
                if a < b:
                    emit(m, "range", a, b, m.group(4))
        for m in PM.finditer(sent):
            if free(m.start(), m.end()):
                emit(m, "tolerance", -to_num(m.group(1)), to_num(m.group(1)), m.group(2))
        for m in RANGE.finditer(sent):
            if free(m.start(), m.end()) and not _skip(sent, m.start(), m.group(1)):
                lo, hi = to_num(m.group(1)), to_num(m.group(2))
                if lo < hi:
                    emit(m, "range", lo, hi, m.group(3))
        for m in SINGLE.finditer(sent):
            if not free(m.start(), m.end()) or _skip(sent, m.start(), m.group(2)):
                continue
            if re.match(r"\s?[23\u00b2\u00b3]\b", sent[m.end():m.end() + 3]) and canon_unit(m.group(3)) in ("m", "cm", "mm", "km"):
                continue              # m2 / m3 / cm2: an area or volume, not a length
            comp = (m.group("comp") or "").lower()
            v = to_num(m.group(2))
            ns, ext = m.start(2), 0
            if not comp and ns >= 1 and sent[ns - 1] in "-\u2212\u2013" and (ns < 2 or not (sent[ns - 2].isalnum() or sent[ns - 2] in ")%")):
                v, ext = -v, 1        # an attached minus sign ("-10 mm"), not a dash between words or "tm - 12.5"; the span includes it
            tail = sent[m.end():m.end() + 16]
            if not comp and re.match(r"\s*(?:or|and)\s+(?:more|above|greater|higher|over)\b", tail, re.I):
                comp = "minimum"          # "440 m or more" is a lower bound
            elif not comp and re.match(r"\s*(?:or|and)\s+(?:less|below|lower|fewer|under)\b", tail, re.I):
                comp = "maximum"          # "100 mm or less" is an upper bound
            if re.match(COMP_MAX, comp, re.I):
                emit(m, "max", None, v, m.group(3), ext)
            elif re.match(COMP_MIN, comp, re.I):
                emit(m, "min", v, None, m.group(3), ext)
            else:
                emit(m, "value", v, v, m.group(3), ext)
        # a speed value in the same sentence is the speed band another value applies to
        for i, a, b in sent_records:
            r = out[i]
            if r["quantity"] == "speed":
                continue
            for j, a2, b2 in sent_records:
                o = out[j]
                if j != i and o["quantity"] == "speed" and o["unit"] == "kmph":
                    r["conditions"].append({"type": "speed_band", "raw": o["raw"]})
    out.sort(key=lambda r: r["start"])
    return out


def extract_from_table(t: dict) -> list[dict]:
    """Numeric cells that carry a unit (in the cell or in its column header)."""
    out = []
    heads = []
    for j in range(t["n_cols"]):
        parts = []
        for r in t["rows"][:t["header_rows"]]:
            if r[j].strip() and r[j].strip() not in parts:
                parts.append(r[j].strip())
        heads.append(" ".join(parts))
    for i, row in enumerate(t["rows"][t["header_rows"]:], t["header_rows"]):
        label = next((c for c in row if c.strip() and not re.fullmatch(r"[\d.()\s]+", c)), "")
        for j, cell in enumerate(row):
            c = cell.strip()
            if not c or not re.search(r"\d", c) or c == label or len(c) > 40:
                continue
            hu = re.search(rf"\(?\b{UNIT_RE}\b\)?", heads[j], re.I)
            um = re.search(rf"{NUM}\s*{UNIT_RE}(?![A-Za-z/²])", c, re.I)
            rm = re.fullmatch(rf"{NUM}(?:\s*(?:to|-|–)\s*{NUM})?", c)
            if um:
                unit_raw, lo_s = um.group(2), um.group(1)
                rng = RANGE.search(c)
                lo, hi, comp = (to_num(rng.group(1)), to_num(rng.group(2)), "range") if rng else (to_num(lo_s), to_num(lo_s), "value")
            elif rm and hu:
                unit_raw = hu.group(1)
                lo = to_num(rm.group(1))
                hi = to_num(rm.group(2)) if rm.group(2) else lo
                comp = "range" if rm.group(2) else "value"
            else:
                continue
            unit = canon_unit(unit_raw)
            if not unit or lo > hi or not _plausible(unit, lo, hi):
                continue
            q = _fix_quantity(quantity_of(f"{label} {heads[j]}"), unit, hi, lo)
            out.append({"clause": t["clause"], "source": "table", "table_id": t["table_id"], "row": i, "col": j, "raw": c,
                        "quantity": q, "comparator": comp, "lo": lo, "hi": hi, "unit": unit,
                        "subject": " | ".join(x for x in (label[:80], heads[j][:60]) if x)})
    return out
