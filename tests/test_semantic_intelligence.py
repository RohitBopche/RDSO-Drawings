"""
tests/test_semantic_intelligence.py
Unit tests for Phase 7: Semantic Intelligence (§24, §36 of Blueprint).
Validates:
1. Semantic synonym expansion & taxonomy mapping.
2. Level 1-5 hybrid ranking scoring logic.
3. Concept similarity (cosine/Jaccard feature overlap) between entities.
4. Knowledge-gap detection & completeness auditing.
"""

import pytest


SEMANTIC_SYNONYM_REGISTRY = {
    "turnout": ["tongue rail", "curved switch", "t-6155", "t-6154", "thick-web", "1:12", "comp_tongue_rail"],
    "points": ["tongue rail", "curved switch", "t-6155", "switch assembly", "comp_tongue_rail"],
    "switch": ["tongue rail", "stock rail", "t-6155", "curved switch", "comp_tongue_rail"],
    "pad": ["grsp", "grooved rubber sole pad", "irs:t-46", "composite pad", "10mm", "comp_grsp"],
    "rubber": ["grsp", "irs:t-46", "elastomeric", "sole pad", "comp_grsp"],
    "clip": ["erc mk-v", "elastic rail clip", "irs:t-10", "toe load", "comp_erc"],
    "clamp": ["erc mk-v", "emergency clamp", "fishplate clamp", "comp_erc"],
    "crack": ["star crack", "bolt hole", "ultrasonic", "usfd", "imr", "obs", "fatigue", "man_usfd_ch10"],
    "defect": ["imr", "obs", "star crack", "usfd", "flaking", "man_usfd_ch10"],
    "flaw": ["ultrasonic", "usfd", "imr", "star crack", "echo", "man_usfd_ch10"],
    "tie bar": ["detail b", "flat tie bar", "222 mm drop", "alt 11", "tamping", "comp_detailb"],
    "tamping": ["222 mm drop", "detail b", "tamping tool tines", "mechanized maintenance", "comp_detailb", "man_tmm"],
    "wear": ["permissible wear", "tongue rail wear", "check rail clearance", "6.0 mm", "8.0 mm", "irpwm 2024 para 429", "man_irpwm_ch4"],
    "clearance": ["check rail clearance", "41-45 mm", "switch throw", "115 mm", "irpwm 2024 para 429"]
}


def expand_query_terms(query: str) -> list[str]:
    """Expands a search query with canonical railway engineering synonyms."""
    tokens = query.lower().strip().split()
    expanded = set(tokens)
    for t in tokens:
        if t in SEMANTIC_SYNONYM_REGISTRY:
            for syn in SEMANTIC_SYNONYM_REGISTRY[t]:
                expanded.add(syn.lower())
    return sorted(list(expanded))


def calculate_hybrid_score(node: dict, query: str, active_node_id: str | None = None) -> tuple[float, str]:
    """
    Computes Level 1-5 Hybrid Search Score per Blueprint §24:
    Score = S_lexical + S_metadata + S_semantic + S_graph
    Returns: (score, match_tier)
    """
    q = query.lower().strip()
    node_id = node.get("id", "").lower()
    label = node.get("label", "").lower()
    desc = node.get("desc", "").lower()
    node_type = node.get("type", "").upper()
    degree = node.get("degree", 1)

    s_lexical = 0.0
    s_metadata = 0.0
    s_semantic = 0.0
    s_graph = 0.0
    match_tier = "GENERAL"

    # 1. Lexical Scoring (Level 1)
    if q == node_id or q == label:
        s_lexical += 1000.0
        match_tier = "EXACT_ID"
    elif q in node_id or q in label:
        s_lexical += 400.0
        match_tier = "LEXICAL_MATCH"

    # 2. Metadata Scoring (Level 2)
    if node_type == "DRAWING" and any(k in q for k in ["6155", "6154", "drg", "drawing"]):
        s_metadata += 200.0
    elif node_type in q.upper():
        s_metadata += 100.0

    # 3. Semantic Expansion (Level 4)
    expanded = expand_query_terms(q)
    semantic_hits = 0
    for term in expanded:
        if term != q and (term in node_id or term in label or term in desc):
            semantic_hits += 1
            s_semantic += 150.0

    if semantic_hits > 0 and match_tier == "GENERAL":
        match_tier = "SEMANTIC_MATCH"

    # 4. Graph Centrality & Context (Level 3 & 5)
    s_graph += min(degree * 10.0, 100.0)
    if active_node_id and active_node_id in node.get("connections", []):
        s_graph += 150.0

    total_score = s_lexical + s_metadata + s_semantic + s_graph
    return total_score, match_tier


def compute_concept_similarity(node_a: dict, node_b: dict) -> float:
    """
    Calculates Jaccard / multi-attribute concept similarity between two entities.
    Returns float between 0.0 and 1.0 (0% to 100%).
    """
    if node_a.get("id") == node_b.get("id"):
        return 1.0

    features_a = set(node_a.get("tags", []) + [node_a.get("type", ""), node_a.get("domain", "")])
    features_b = set(node_b.get("tags", []) + [node_b.get("type", ""), node_b.get("domain", "")])

    intersection = len(features_a.intersection(features_b))
    union = len(features_a.union(features_b))
    jaccard = intersection / union if union > 0 else 0.0

    # Direct connection boost
    if node_b.get("id") in node_a.get("connections", []):
        jaccard = min(jaccard + 0.35, 1.0)

    return round(jaccard, 2)


def audit_knowledge_gaps(nodes: list[dict]) -> dict:
    """
    Scans graph entities for knowledge completeness:
    - Missing primary evidence references
    - Missing quantitative engineering tolerances
    - Untracked revision lineage
    """
    total = len(nodes)
    if total == 0:
        return {"completeness_pct": 100.0, "gaps": []}

    gaps = []
    complete_count = 0

    for n in nodes:
        node_gaps = []
        if not n.get("evidence_refs"):
            node_gaps.append("MISSING_EVIDENCE")
        if n.get("type") == "COMPONENT" and not n.get("tolerances"):
            node_gaps.append("MISSING_TOLERANCE")
        if n.get("type") == "DRAWING" and not n.get("revisions"):
            node_gaps.append("UNTRACKED_REVISIONS")

        if node_gaps:
            gaps.append({"id": n.get("id"), "label": n.get("label"), "gaps": node_gaps})
        else:
            complete_count += 1

    completeness_pct = round((complete_count / total) * 100, 1)
    return {
        "completeness_pct": completeness_pct,
        "total_nodes": total,
        "nodes_with_gaps": len(gaps),
        "gaps": gaps
    }


# =========================================================================
# TEST SUITE
# =========================================================================

def test_semantic_query_expansion():
    """Verify colloquial terms expand into statutory railway terminology."""
    exp_pad = expand_query_terms("pad")
    assert "grsp" in exp_pad
    assert "irs:t-46" in exp_pad
    assert "comp_grsp" in exp_pad

    exp_tamping = expand_query_terms("tamping")
    assert "222 mm drop" in exp_tamping
    assert "detail b" in exp_tamping
    assert "comp_detailb" in exp_tamping


def test_hybrid_ranking_exact_vs_semantic():
    """Verify exact ID ranks higher than semantic match, but semantic match boosts relevant entities."""
    node_detailb = {
        "id": "comp_detailb",
        "label": "Detail 'B' Flat Tie Bar",
        "desc": "Forged flat tie bar with 222 mm drop for tamping clearance",
        "type": "COMPONENT",
        "degree": 8,
        "connections": ["drg_6155"]
    }
    node_other = {
        "id": "comp_bolt",
        "label": "HTS Bolt",
        "desc": "25x310 mm bolt",
        "type": "COMPONENT",
        "degree": 2,
        "connections": []
    }

    # Query: exact id
    score_exact, tier_exact = calculate_hybrid_score(node_detailb, "comp_detailb")
    assert score_exact >= 1000.0
    assert tier_exact == "EXACT_ID"

    # Query: colloquial term "tamping"
    score_sem, tier_sem = calculate_hybrid_score(node_detailb, "tamping")
    score_other, _ = calculate_hybrid_score(node_other, "tamping")
    assert score_sem > score_other
    assert tier_sem == "SEMANTIC_MATCH"


def test_concept_similarity():
    """Verify concept similarity between connected turnout assets."""
    node_detailb = {
        "id": "comp_detailb",
        "type": "COMPONENT",
        "domain": "TURNOUT",
        "tags": ["switch", "tie_bar", "alt11", "forged"],
        "connections": ["drg_6155", "std_irs_t10"]
    }
    node_drg6155 = {
        "id": "drg_6155",
        "type": "DRAWING",
        "domain": "TURNOUT",
        "tags": ["switch", "curved_switch", "alt11", "1:12"],
        "connections": ["comp_detailb"]
    }
    node_unrelated = {
        "id": "man_welding",
        "type": "MANUAL",
        "domain": "WELDING",
        "tags": ["alumino_thermic", "crucible"],
        "connections": []
    }

    sim_related = compute_concept_similarity(node_detailb, node_drg6155)
    sim_unrelated = compute_concept_similarity(node_detailb, node_unrelated)

    assert sim_related > 0.4
    assert sim_unrelated == 0.0


def test_knowledge_gap_audit():
    """Verify knowledge gap detector flags missing evidence and calculates completeness."""
    sample_nodes = [
        {
            "id": "comp_detailb",
            "label": "Detail B",
            "type": "COMPONENT",
            "evidence_refs": ["EVID:T6155:ALT11:B"],
            "tolerances": {"drop": "222 mm"}
        },
        {
            "id": "comp_unknown",
            "label": "Unknown Bracket",
            "type": "COMPONENT",
            "evidence_refs": [],  # missing evidence
            "tolerances": {}  # missing tolerances
        }
    ]

    audit = audit_knowledge_gaps(sample_nodes)
    assert audit["total_nodes"] == 2
    assert audit["nodes_with_gaps"] == 1
    assert audit["completeness_pct"] == 50.0
    assert "MISSING_EVIDENCE" in audit["gaps"][0]["gaps"]
    assert "MISSING_TOLERANCE" in audit["gaps"][0]["gaps"]
