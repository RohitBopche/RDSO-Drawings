#!/usr/bin/env python3
"""Gate V: the pilot acceptance checklist (Master section 28) for each of the six manuals, one reproducible check per line.

    python scripts/pilot_checklist.py            # print the table; exit 1 when any check FAILs
    python scripts/pilot_checklist.py --write    # also write data/knowledge-graph/reports/pilot_checklist.json
    python scripts/pilot_checklist.py --rebuild  # also run the full rebuild twice-over check (about 3 minutes)

SKIP means the check was not run here (only the determinism line, which CI runs). Thresholds are written below; the retrieval lines use
the author-drafted evaluation sets, so they show regressions, not independent accuracy.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "data" / "knowledge-graph"
OUT = KG / "reports" / "pilot_checklist.json"
MANUALS = {"IRPWM": "DOC:IRPWM:2024:ACS14", "TMM": None, "STMM": None, "USFD": None, "AT_WELD": None, "FBW": None}
SHORT_MAX = 0.10          # share of clauses that may be shorter than the short-clause limit
NL_RECALL_MIN = 0.85      # recall at 5 on the manual's own natural-language questions
NL_MIN_QUESTIONS = 10
REGION_MIN = 0.95         # share of the manual's evidence with a stored page region
XREF_STATUS = {"RESOLVED", "AMBIGUOUS", "EXTERNAL", "NOT_FOUND"}

CRITERIA = [
    ("pages", "All pages registered, PDF hash recorded"),
    ("hierarchy", "Hierarchy represented"),
    ("order", "Chapter order deterministic (contiguous numbering)"),
    ("provisions", "Provisions preserved (text present, few stubs)"),
    ("pages_resolve", "Source pages resolvable"),
    ("search", "Full-text search works (every paragraph found by its number)"),
    ("nl", "Natural-language queries retrieve evidence"),
    ("citations", "Citations resolve (evidence exists with page and region)"),
    ("opens", "Source page opens (PDF present, page in range)"),
    ("xrefs", "Cross-references resolve or are classified"),
    ("flagged", "Uncertain extraction flagged (status on every paragraph)"),
    ("no_answer", "No answer without evidence (off-topic questions refused)"),
    ("regression", "Regression tests exist"),
    ("determinism", "Re-running ingestion is deterministic"),
]


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def probe() -> dict:
    r = subprocess.run(["node", "tests/pilot_probe.js"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return json.loads(r.stdout)


def main() -> int:
    write, rebuild = "--write" in sys.argv, "--rebuild" in sys.argv
    registry = {r["id"]: r for r in read_jsonl(KG / "raw" / "source_registry.jsonl")}
    pages = {}
    for p in read_jsonl(KG / "raw" / "extracted_pages.jsonl"):
        pages.setdefault(p["document_id"], []).append(p)
    nodes = {}
    for n in read_jsonl(KG / "canonical" / "nodes.jsonl"):
        nodes[n["id"]] = n
    evidence = {e["evidence_id"]: e for e in read_jsonl(KG / "canonical" / "evidence.jsonl")}
    xrefs = read_jsonl(KG / "canonical" / "crossrefs.jsonl")
    reviews = set()
    rp = KG / "canonical" / "reviews.jsonl"
    if rp.exists():
        reviews = {t for r in read_jsonl(rp) for t in r.get("target_ids", [])}
    metrics = json.loads((KG / "reports" / "metrics.json").read_text(encoding="utf-8"))["manual_clauses"]
    probes = probe()
    questions = read_jsonl(ROOT / "eval" / "questions.jsonl")
    det = None
    if rebuild:
        subprocess.run([sys.executable, "scripts/rebuild_all.py"], cwd=ROOT, check=True, capture_output=True)
        det = subprocess.run(["git", "diff", "--quiet", "--", "data/"], cwd=ROOT).returncode == 0

    results = {}
    for alias in MANUALS:
        doc = next((d for d in registry if d.startswith(f"DOC:{alias}:")), None)
        reg = registry.get(doc, {})
        clauses = {i: n for i, n in nodes.items() if i.startswith(f"CLAUSE:{alias}:")}
        chapters = sorted(int(m.group(1)) for i in nodes if (m := re.fullmatch(rf"CHAPTER:{alias}:CH_(\d+)", i)))
        res: dict[str, tuple[str, str]] = {}

        def put(key: str, ok: bool, detail: str) -> None:
            res[key] = ("PASS" if ok else "FAIL", detail)

        pdf = ROOT / reg.get("file_path", "missing")
        sha_ok = pdf.exists() and hashlib.sha256(pdf.read_bytes()).hexdigest() == reg.get("sha256")
        n_pages = len(pages.get(doc, []))
        put("pages", bool(reg) and n_pages == reg.get("page_count") and sha_ok, f"{n_pages}/{reg.get('page_count')} pages, hash {'matches' if sha_ok else 'MISMATCH'}")
        orphan = [i for i, c in clauses.items() if c.get("parent_chapter_id") not in nodes]
        put("hierarchy", bool(chapters) and not orphan, f"{len(chapters)} chapters, {len(clauses)} paragraphs, {len(orphan)} without a chapter")
        put("order", chapters == list(range(1, len(chapters) + 1)), f"chapters {chapters[0] if chapters else '-'} to {chapters[-1] if chapters else '-'}")
        m = metrics.get(doc, {})
        with_text = sum(1 for c in clauses.values() if (c.get("text") or "").strip())
        short = m.get("short_clauses", 0)
        put("provisions", with_text == len(clauses) and len(clauses) > 0 and short <= SHORT_MAX * len(clauses), f"{with_text}/{len(clauses)} with text, {short} short")
        bad_page = [i for i, c in clauses.items() if not (1 <= int(c.get("page") or 0) <= (reg.get("page_count") or 0))]
        put("pages_resolve", not bad_page, f"{len(clauses) - len(bad_page)}/{len(clauses)} paragraphs have an existing page")
        pr = probes[alias]
        put("search", pr["ident_ok"] == pr["ident_n"], f"{pr['ident_ok']}/{pr['ident_n']} found first by number")
        recall = pr["nl_r5"] / pr["nl_n"] if pr["nl_n"] else 0
        put("nl", pr["nl_n"] >= NL_MIN_QUESTIONS and recall >= NL_RECALL_MIN, f"recall@5 {pr['nl_r5']}/{pr['nl_n']} = {recall:.2f} (author-drafted questions)")
        ev_ids = [e for c in clauses.values() for e in _ids(c)]
        missing = [e for e in ev_ids if e not in evidence]
        with_region = sum(1 for e in ev_ids if e in evidence and (evidence[e].get("line_regions") or evidence[e].get("region")))
        put("citations", bool(ev_ids) and not missing and with_region >= REGION_MIN * len(ev_ids), f"{len(ev_ids) - len(missing)}/{len(ev_ids)} resolve, {with_region} with a region")
        put("opens", pdf.exists() and not bad_page, f"{reg.get('file_path')} present, pages in range")
        mine = [x for x in xrefs if x["source"].startswith(f"CLAUSE:{alias}:")]
        unclassified = [x for x in mine if x["status"] not in XREF_STATUS]
        counts = {s: sum(1 for x in mine if x["status"] == s) for s in sorted(XREF_STATUS)}
        put("xrefs", bool(mine) and not unclassified, ", ".join(f"{v} {k.lower()}" for k, v in counts.items()))
        no_status = [i for i, c in clauses.items() if not c.get("verification_status")]
        fake = [i for i, c in clauses.items() if c.get("verification_status") in ("verified", "reviewed") and i not in reviews]
        put("flagged", not no_status and not fake, f"{len(clauses) - len(no_status)}/{len(clauses)} carry a status, {len(fake)} claim review without a record")
        put("no_answer", pr["oos_refused"] == pr["oos_n"], f"{pr['oos_refused']}/{pr['oos_n']} off-topic questions refused")
        mine_q = sum(1 for q in questions if any(g.startswith(f"CLAUSE:{alias}:") for g in q.get("gold", [])))
        put("regression", mine_q >= 2 * NL_MIN_QUESTIONS, f"{mine_q} evaluation questions with a gold paragraph in this manual")
        res["determinism"] = ("SKIP", "run with --rebuild, or see the CI rebuild step") if det is None else (("PASS" if det else "FAIL"), "rebuild_all leaves data/ unchanged" if det else "rebuild changed data/")
        results[alias] = res

    width = max(len(c[1]) for c in CRITERIA)
    fails = 0
    print(f"{'Criterion':<{width}}  " + "  ".join(f"{a:<7}" for a in MANUALS))
    for key, title in CRITERIA:
        cells = []
        for a in MANUALS:
            st = results[a][key][0]
            fails += st == "FAIL"
            cells.append(f"{st:<7}")
        print(f"{title:<{width}}  " + "  ".join(cells))
    print()
    for a in MANUALS:
        for key, title in CRITERIA:
            st, detail = results[a][key]
            if st == "FAIL":
                print(f"FAIL {a}: {title}: {detail}")
    print(f"\n{sum(1 for a in MANUALS for k, _ in CRITERIA if results[a][k][0] == 'PASS')} pass, {fails} fail, "
          f"{sum(1 for a in MANUALS for k, _ in CRITERIA if results[a][k][0] == 'SKIP')} skipped")
    if write:
        OUT.write_text(json.dumps({a: {k: {"status": v[0], "detail": v[1]} for k, v in r.items()} for a, r in results.items()}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 1 if fails else 0


def _ids(node: dict) -> list[str]:
    v = node.get("evidence_ids") or []
    if isinstance(v, str):
        try:
            v = json.loads(v.replace("'", '"'))
        except ValueError:
            v = re.findall(r"ev:[^'\",\]]+", v)
    return list(v)


if __name__ == "__main__":
    sys.exit(main())
