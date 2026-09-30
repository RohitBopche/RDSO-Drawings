"""Provenance policy (P0-R.3): the only way to `reviewed` / `verified` is a review record.

Everything produced by extraction pipelines is `machine_extracted`.
`canonical/reviews.jsonl` holds human decisions:

    {"review_id", "target_ids": [...], "decision": "approved|rejected|disputed",
     "reviewer", "reviewed_at", "note"}

Status derived per target id:
    any rejected/disputed -> disputed
    >= 2 distinct approving reviewers -> verified   (safety-relevant independence)
    1 approving reviewer -> reviewed
    otherwise -> machine_extracted
"""

from __future__ import annotations

MACHINE = "machine_extracted"
MAX_UNREVIEWED_CONFIDENCE = 0.95
FALSE_TEXT_METHOD = "raster_blueprint_crop_and_transcription"
TEXT_METHOD = "deterministic_text_extraction"
DECISIONS = {"approved", "rejected", "disputed"}


def review_status(reviews: list[dict]) -> dict[str, str]:
    approvals: dict[str, set[str]] = {}
    flagged: set[str] = set()
    for r in reviews:
        for tid in r.get("target_ids", []):
            if r["decision"] == "approved":
                approvals.setdefault(tid, set()).add(r["reviewer"])
            else:
                flagged.add(tid)
    out = {tid: ("reviewed" if len(who) == 1 else "verified") for tid, who in approvals.items()}
    out.update({tid: "disputed" for tid in flagged})
    return out


def apply(nodes: list[dict], reqs: list[dict], evidence: list[dict], facts: list[dict],
          reviews: list[dict]) -> None:
    """Mutate records in place so status/method/confidence never overstate provenance."""
    status = review_status(reviews)
    domain = {n["id"]: n.get("domain") for n in nodes}

    for rec, key in [(n, "id") for n in nodes] + [(r, "id") for r in reqs] + [(e, "evidence_id") for e in evidence]:
        rec["verification_status"] = status.get(rec[key], MACHINE)
        if rec["verification_status"] == MACHINE and isinstance(rec.get("confidence"), (int, float)):
            rec["confidence"] = min(rec["confidence"], MAX_UNREVIEWED_CONFIDENCE)
    for ev in evidence:
        if ev["verification_status"] == MACHINE:
            ev["confidence"] = min(ev.get("confidence", 0.0), MAX_UNREVIEWED_CONFIDENCE)
    for f in facts:
        f["status"] = status.get(f["id"], MACHINE).upper()
        if f["status"] == "MACHINE_EXTRACTED":
            f["confidence"] = min(f.get("confidence", 0.0), MAX_UNREVIEWED_CONFIDENCE)
        # Text-derived (manual) facts were mislabelled as raster/blueprint transcription.
        if f.get("extraction_method") == FALSE_TEXT_METHOD and domain.get(f["subject_id"]) == "manual":
            f["extraction_method"] = TEXT_METHOD
