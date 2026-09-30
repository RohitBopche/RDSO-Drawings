#!/usr/bin/env python3
"""Record human review decisions from review packets (P0-R.3, P7).

    python scripts/ingest_reviews.py decisions_Name_s1.json [more.json ...]
    python scripts/ingest_reviews.py --report          # only rebuild the accuracy report

Clause decisions go to canonical/reviews.jsonl (Gate M / provenance policy: one approval -> reviewed, two independent
approvals -> verified, any rejection -> disputed; the next rebuild applies it). Decisions on other kinds (cross-references,
measurements, tables, drawing links) go to canonical/extractor_reviews.jsonl: they do not change a node's status but measure
how often each extractor is right. "Unsure" is counted and not recorded as a decision.

Report: reports/review_accuracy.json  (per kind: reviewed, correct, wrong, unsure, error rate with 95% Wilson interval;
agreement between reviewers on items both saw).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAN = ROOT / "data" / "knowledge-graph" / "canonical"
REPORT = ROOT / "data" / "knowledge-graph" / "reports" / "review_accuracy.json"
PREFIX = {"clause": "CLAUSE:", "xref": "XREF:", "measurement": "MEAS:", "table": "TBL:", "drawing_link": "DLINK:"}
DECISIONS = {"approved", "rejected", "unsure"}


def read(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def known_ids() -> dict[str, set[str]]:
    kg = ROOT / "data" / "knowledge-graph"
    return {
        "clause": {n["id"] for n in read(CAN / "nodes.jsonl") if n["id"].startswith("CLAUSE:")},
        "xref": {r["ref_id"] for r in read(CAN / "crossrefs.jsonl")},
        "measurement": {m["measurement_id"] for m in read(CAN / "measurements.jsonl")},
        "table": {t["table_id"] for t in read(kg / "raw" / "tables.jsonl")},
        "drawing_link": {d["link_id"] for d in read(CAN / "drawing_links.jsonl")},
    }


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def process(files: list[dict], known: dict[str, set[str]], have: set[tuple[str, str]], now: str) -> tuple[list[dict], list[dict], list[str], int]:
    """-> (clause reviews, extractor reviews, errors, unsure count). `have` = (target, reviewer) already recorded."""
    clause_reviews, other, errors, unsure = [], [], [], 0
    seen = set(have)
    for f in files:
        who = (f.get("reviewer") or "").strip()
        if not who:
            errors.append(f"packet seed {f.get('packet_seed')}: no reviewer name")
            continue
        for d in f.get("decisions", []):
            kind, tid, dec = d.get("kind"), d.get("target_id"), d.get("decision")
            if kind not in PREFIX or dec not in DECISIONS or not str(tid).startswith(PREFIX[kind]) or tid not in known[kind]:
                errors.append(f"{who}: bad decision {kind!r} {tid!r} {dec!r}")
                continue
            if (tid, who) in seen:
                errors.append(f"{who}: {tid} already reviewed by this reviewer (skipped)")
                continue
            if dec == "unsure":
                unsure += 1
                continue
            seen.add((tid, who))
            rec = {"review_id": f"RV:{tid}:{who}", "target_ids": [tid], "decision": dec, "reviewer": who, "reviewed_at": now,
                   "note": d.get("note", ""), "kind": kind, "packet_seed": f.get("packet_seed")}
            (clause_reviews if kind == "clause" else other).append(rec)
    return clause_reviews, other, errors, unsure


def voided() -> dict[str, str]:
    """Decisions made on a packet item that did not show what it asked about (reviewer said so, or we found it later). They stay on
    record but do not count towards accuracy."""
    p = ROOT / "eval" / "reviews" / "voided.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def accuracy(all_reviews: list[dict], unsure: int = 0, void: dict[str, str] | None = None) -> dict:
    void = void or {}
    by_kind: dict[str, dict] = {}
    per_target: dict[str, dict[str, str]] = {}
    packets = void.get("_packets", {})

    def is_void(r: dict) -> bool:
        pk = packets.get(str(r.get("packet_seed")))
        return r["target_ids"][0] in void or bool(pk and r.get("kind") in pk["kinds"])

    n_void = sum(1 for r in all_reviews if is_void(r))
    all_reviews = [r for r in all_reviews if not is_void(r)]
    for r in all_reviews:
        k = by_kind.setdefault(r["kind"], {"reviewed": 0, "correct": 0, "wrong": 0})
        k["reviewed"] += 1
        k["correct" if r["decision"] == "approved" else "wrong"] += 1
        per_target.setdefault(r["target_ids"][0], {})[r["reviewer"]] = r["decision"]
    for k in by_kind.values():
        k["error_rate"] = round(k["wrong"] / k["reviewed"], 3)
        k["error_rate_95ci"] = wilson(k["wrong"], k["reviewed"])
    both = [v for v in per_target.values() if len(v) >= 2]
    agree = sum(len(set(v.values())) == 1 for v in both)
    return {"by_kind": dict(sorted(by_kind.items())), "unsure_not_recorded": unsure, "voided_decisions": n_void,
            "double_reviewed_items": len(both), "reviewer_agreement": round(agree / len(both), 3) if both else None,
            "note": "error rates are estimates for the sampled kind only when the packet items were drawn at random (the default); "
                    "small samples give wide intervals"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    rv_path, ex_path = CAN / "reviews.jsonl", CAN / "extractor_reviews.jsonl"
    reviews, extractor = read(rv_path), read(ex_path)
    unsure = 0
    if a.files:
        files = [json.loads(Path(f).read_text(encoding="utf-8")) for f in a.files]
        have = {(t, r["reviewer"]) for r in reviews + extractor for t in r["target_ids"]}
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        c, o, errors, unsure = process(files, known_ids(), have, now)
        for e in errors:
            print("[WARN]", e)
        reviews += c
        extractor += o
        rv_path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in reviews), encoding="utf-8")
        ex_path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in extractor), encoding="utf-8")
        print(f"recorded {len(c)} clause reviews and {len(o)} extractor reviews ({unsure} unsure not recorded)")
        if c:
            print("run scripts/rebuild_all.py so clause statuses follow the reviews")
    tagged = [dict(r, kind=r.get("kind", "clause")) for r in reviews if r["target_ids"][0].startswith("CLAUSE:")] + extractor
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(accuracy(tagged, unsure, voided()), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"report -> {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
