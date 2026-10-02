"""Entity layer: the lexicon, the generated files, the audit of precision, and the chat's concept answers."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEX = json.loads((ROOT / "data" / "ontology" / "concepts.json").read_text(encoding="utf-8"))


def test_gate_passes():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_entities.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_lexicon_shape():
    ids = [c["id"] for c in LEX["concepts"]]
    assert len(ids) == len(set(ids)) and len(ids) >= 100
    parent = {c["id"]: c.get("is_a") or c.get("part_of") for c in LEX["concepts"]}
    for c in LEX["concepts"]:
        assert c["class"] in LEX["classes"], c["id"]
        assert c["aliases"] and all(a.strip() == a and a for a in c["aliases"]), c["id"]
        for k in ("is_a", "part_of"):
            assert not c.get(k) or c[k] in ids
    for start in ids:                                   # the taxonomy has no cycles
        seen, cur = set(), start
        while cur:
            assert cur not in seen, f"cycle through {start}"
            seen.add(cur)
            cur = parent.get(cur)


def test_hand_audit_precision():
    a = json.loads((ROOT / "eval" / "entity_precision_audit.json").read_text(encoding="utf-8"))
    assert a["sampled"] == len(a["rows"]) == 120
    assert a["correct"] == sum(r["correct"] for r in a["rows"])
    assert a["correct"] / a["sampled"] >= 0.90


def test_chat_concept_answers():
    qs = ["What are the types of sleepers?", "Which paragraphs mention fish plates?", "What is LWR related to?", "What are the parts of a turnout?",
          "What is the maximum permissible speed on curves?", "What refers to IRPWM Para 429?", "What is the capital of France?"]
    r = subprocess.run(["node", str(ROOT / "tests" / "entity_probe.js"), *qs], capture_output=True, text=True, check=True)
    o = json.loads(r.stdout)
    t = o[qs[0]]
    assert (t["kind"], t["mode"], t["concept"]) == ("relation", "concept", "sleeper")
    assert any("PSC" in x["label"] for x in t["rows"]) and all(x["quote"] for x in t["rows"])
    w = o[qs[1]]
    assert w["concept"] == "fish_plate" and "IRPWM" in w["text"] and w["rows"]
    assert o[qs[2]]["concept"] == "lwr" and any("Continuous welded rail" in x["label"] for x in o[qs[2]]["rows"])
    assert any("Crossing" in x["label"] for x in o[qs[3]]["rows"]) and any("Switch" in x["label"] for x in o[qs[3]]["rows"])
    assert o[qs[4]]["kind"] == "answer"                  # an ordinary question is not taken over
    assert o[qs[5]]["mode"] != "concept" and o[qs[5]]["kind"] == "relation"
    assert o[qs[6]]["kind"] != "relation"
    assert o["find"]["the PWI"] == "sse_way" and o["find"]["LWR buckling"] in ("lwr", "buckling") and o["find"]["hello"] is None
