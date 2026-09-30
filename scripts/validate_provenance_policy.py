#!/usr/bin/env python3
"""Gate M: provenance policy. Nothing is reviewed/verified without a review record.

Checks nodes, requirements, evidence and facts against `canonical/reviews.jsonl`,
forbids unreviewed confidence of 1.0 and text-derived facts labelled as raster
transcription, and validates review records themselves.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import provenance_policy as pp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "knowledge-graph" / "canonical"
CORE = ROOT / "data" / "rdso_canonical_kg.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    errors: list[str] = []
    nodes = read_jsonl(CANON / "nodes.jsonl")
    reqs = read_jsonl(CANON / "requirements.jsonl")
    evidence = read_jsonl(CANON / "evidence.jsonl")
    reviews = read_jsonl(CANON / "reviews.jsonl")
    facts = json.loads(CORE.read_text(encoding="utf-8")).get("facts", [])
    ids = {n["id"] for n in nodes} | {r["id"] for r in reqs} | {e["evidence_id"] for e in evidence} | {f["id"] for f in facts}

    seen = set()
    for r in reviews:
        for k in ("review_id", "target_ids", "decision", "reviewer", "reviewed_at"):
            if not r.get(k):
                errors.append(f"review {r.get('review_id')}: missing {k}")
        if r.get("decision") not in pp.DECISIONS:
            errors.append(f"review {r.get('review_id')}: bad decision {r.get('decision')!r}")
        if r.get("review_id") in seen:
            errors.append(f"review {r.get('review_id')}: duplicate")
        seen.add(r.get("review_id"))
        for t in r.get("target_ids", []):
            if t not in ids:
                errors.append(f"review {r.get('review_id')}: unknown target {t}")

    expected = pp.review_status(reviews)
    checks = [("node", n["id"], n.get("verification_status"), n.get("confidence")) for n in nodes]
    checks += [("requirement", r["id"], r.get("verification_status"), r.get("confidence")) for r in reqs]
    checks += [("evidence", e["evidence_id"], e.get("verification_status"), e.get("confidence")) for e in evidence]
    checks += [("fact", f["id"], f.get("status", "").lower(), f.get("confidence")) for f in facts]
    for kind, rid, status, conf in checks:
        want = expected.get(rid, pp.MACHINE)
        if status != want:
            errors.append(f"{kind} {rid}: status {status!r} but review records imply {want!r}")
        if want == pp.MACHINE and isinstance(conf, (int, float)) and conf > pp.MAX_UNREVIEWED_CONFIDENCE:
            errors.append(f"{kind} {rid}: unreviewed confidence {conf} > {pp.MAX_UNREVIEWED_CONFIDENCE}")

    domain = {n["id"]: n.get("domain") for n in nodes}
    for f in facts:
        if f.get("extraction_method") == pp.FALSE_TEXT_METHOD and domain.get(f["subject_id"]) == "manual":
            errors.append(f"fact {f['id']}: manual (text) fact labelled as raster transcription")

    for e in errors[:40]:
        print(f"[ERROR] {e}")
    counts: dict[str, int] = {}
    for _, _, s, _ in checks:
        counts[s] = counts.get(s, 0) + 1
    print(f"[SUMMARY] provenance policy: {'FAIL' if errors else 'PASS'}; reviews={len(reviews)} "
          f"statuses={dict(sorted(counts.items()))} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
