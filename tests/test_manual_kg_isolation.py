import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manual_structure_has_explicit_chapters():
    path = ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json"
    assert path.exists(), f"missing {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    manuals = data["manuals"]
    assert len(manuals) == 6
    assert all(m["total_chapters"] == len(m["chapters"]) for m in manuals)
    for manual in manuals:
        orders = [c["chapter_number"] for c in manual["chapters"]]
        assert orders == list(range(1, len(orders) + 1))
        assert all(c["universe"] == "manuals" for c in manual["chapters"])


def test_canonical_manual_chapters_are_isolated():
    path = ROOT / "data" / "rdso_canonical_kg.json"
    assert path.exists(), f"missing {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in data["entities"]}

    for n in nodes.values():
        if n.get("domain") == "manual":
            assert n.get("universe", "manuals") == "manuals" or n["type"] in {"DOCUMENT", "CHAPTER", "CLAUSE", "TOLERANCE", "EQUIPMENT", "FAILURE_MODE"}

    structure = json.loads(
        (ROOT / "data" / "knowledge-graph" / "intermediate" / "all_chapters_extracted.json").read_text(encoding="utf-8")
    )
    authoritative_roots = {manual["document_id"] for manual in structure["manuals"]}
    assert authoritative_roots.issubset(nodes)

    for edge in data["edges"]:
        assert edge["from"] in nodes and edge["to"] in nodes, (
            f"dangling canonical edge: {edge['from']} -> {edge['to']}"
        )
        a = nodes[edge["from"]]
        b = nodes[edge["to"]]
        assert (a.get("domain") == "manual") == (b.get("domain") == "manual"), (
            f"cross-universe edge: {edge['from']} -> {edge['to']}"
        )
