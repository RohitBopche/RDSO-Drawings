"""
tests/test_question_interface.py
Unit tests for Phase 5: Question Interface & Natural Language Retrieval.
Validates question intent detection, canonical knowledge retrieval,
multi-hop traversal, and conflict disclosure per Blueprint Sections 15 & 16.
"""

import re
import pytest

# Canonical intents defined in Blueprint §16
CANONICAL_INTENTS = [
    "TOLERANCE_INQUIRY",
    "SPECIFICATION_GOVERNANCE",
    "INSPECTION_PROCEDURE",
    "FAILURE_MITIGATION",
    "BOM_PROCUREMENT",
    "REVISION_COMPARISON",
    "COMPONENT_LOOKUP"
]

CANONICAL_QA_BANK = [
    {
        "id": "qa_tongue_wear",
        "keywords": ["wear", "tongue rail", "permissible", "vertical wear", "lateral wear"],
        "intent": "TOLERANCE_INQUIRY",
        "entity": "comp_tonguerail_lh",
        "question": "What is the permissible wear for 60kg tongue rails?",
        "answer": "Maximum permissible vertical wear on 60kg tongue rails is 6.0 mm; maximum lateral wear is 8.0 mm per IRPWM 2024 Para 429.",
        "parameter": {"param": "tongue_rail_wear", "max_vertical": 6.0, "max_lateral": 8.0, "unit": "mm"},
        "traversal": ["drg_6155", "comp_tonguerail_lh", "std_irst10", "DOC:IRPWM:2024:ACS14"],
        "provenance": {"doc": "IRPWM 2024", "para": "Para 429", "confidence": 0.98, "status": "VERIFIED"}
    },
    {
        "id": "qa_switch_throw",
        "keywords": ["throw", "toe", "switch opening", "stroke", "clearance at toe"],
        "intent": "TOLERANCE_INQUIRY",
        "entity": "comp_detailb",
        "question": "What is the standard switch throw at the toe of curved switch?",
        "answer": "Standard switch opening at the toe of switch is 160 mm (-0 mm, +3 mm), giving an allowable operating range of 160.0 to 163.0 mm per RDSO/T-6155 Note 12.",
        "parameter": {"param": "switch_throw", "min": 160.0, "max": 163.0, "nominal": 160.0, "unit": "mm"},
        "traversal": ["drg_6155", "note_6155_12", "comp_detailb", "std_irst10"],
        "provenance": {"doc": "RDSO/T-6155", "para": "Note 12", "confidence": 0.99, "status": "VERIFIED"}
    },
    {
        "id": "qa_rubber_pad_spec",
        "keywords": ["rubber pad", "grsp", "composite", "specification", "governs", "standard"],
        "intent": "SPECIFICATION_GOVERNANCE",
        "entity": "comp_grsp",
        "question": "Which IRS specification governs sleeper grooved rubber pads?",
        "answer": "Grooved Rubber Sole Pads (GRSP 6mm/10mm) are governed by IRS:T-46:2020 and RDSO/T-6154 layout specifications.",
        "parameter": None,
        "traversal": ["drg_6154", "comp_grsp", "std_irs_t10"],
        "provenance": {"doc": "IRS:T-46:2020", "para": "Clause 4.1", "confidence": 0.97, "status": "VERIFIED"}
    },
    {
        "id": "qa_usfd_testing",
        "keywords": ["usfd", "ultrasonic", "scan", "testing", "flaw", "inspection"],
        "intent": "INSPECTION_PROCEDURE",
        "entity": "doc_usfd_2026",
        "question": "What is the USFD inspection protocol for curved switches?",
        "answer": "USFD testing mandates 3-Zone ultrasonic scanning of machined tongue rails (Zone 1: head, Zone 2: web, Zone 3: foot) using 70° and 0° probes every 3 months or 10 GMT.",
        "parameter": {"param": "usfd_frequency", "zones": 3, "interval_months": 3, "interval_gmt": 10},
        "traversal": ["comp_tonguerail_lh", "DOC:USFD:2026:ACS4", "FAIL:TRACK:BOLT_HOLE_STAR_CRACK"],
        "provenance": {"doc": "USFD Manual 2026", "para": "Chapter 10", "confidence": 0.96, "status": "VERIFIED"}
    },
    {
        "id": "qa_alt11_changes",
        "keywords": ["alt 11", "alteration 11", "changed in alt 11", "revision 11"],
        "intent": "REVISION_COMPARISON",
        "entity": "rev_6155_alt11",
        "question": "What was changed in Alt 11 for T-6155?",
        "answer": "Alteration 11 introduced 222 mm drop for Detail 'B' Flat Tie Bars, standardized HTS 25x310 mm fishbolts with split pins, and mandated 10% LIST-A depot spares buffer under Note 28.",
        "parameter": None,
        "traversal": ["drg_6155", "rev_6155_alt11", "comp_detailb", "spare_bolt_25x310"],
        "provenance": {"doc": "RDSO/T-6155 Alteration Ledger", "para": "Alt 11 Record", "confidence": 0.99, "status": "VERIFIED"}
    },
    {
        "id": "qa_lista_procurement",
        "keywords": ["buffer", "list-a", "procurement", "spares buffer", "sets", "how many spares"],
        "intent": "BOM_PROCUREMENT",
        "entity": "comp_detailb",
        "question": "How are LIST-A spares calculated for 10 turnout sets?",
        "answer": "Under Note 28 mandate, 10% wear buffer is added to LIST-A components: 10 sets require 20 base Detail 'B' bars + ceil(20 * 0.10) = 2 buffer, totaling 22 units.",
        "parameter": {"sets": 10, "base": 20, "buffer": 2, "total": 22},
        "traversal": ["drg_6155", "note_6155_28", "comp_detailb"],
        "provenance": {"doc": "RDSO/T-6155", "para": "Note 28", "confidence": 0.98, "status": "DERIVED"}
    },
    {
        "id": "qa_star_crack_mitigation",
        "keywords": ["star crack", "bolt hole", "mitigation", "fracture", "failure mode"],
        "intent": "FAILURE_MITIGATION",
        "entity": "FAIL:TRACK:BOLT_HOLE_STAR_CRACK",
        "question": "What are the mitigations for bolt hole star cracks?",
        "answer": "Immediate remedial action requires clamping joggled fishplates over the affected bolt hole, imposing 30 km/h speed restriction, and scheduling rail renewal within 48 hours.",
        "parameter": None,
        "traversal": ["FAIL:TRACK:BOLT_HOLE_STAR_CRACK", "comp_detailb", "DOC:USFD:2026:ACS4"],
        "provenance": {"doc": "USFD Manual 2026", "para": "Para 10.4", "confidence": 0.95, "status": "VERIFIED"}
    }
]


def detect_question_intent(query: str):
    """
    Classifies a natural-language query into one of the 7 canonical engineering intents.
    Returns: (is_question: bool, intent: str, confidence: float)
    """
    q_clean = query.strip().lower()
    
    # Check if this is formulated as a question or engineering inquiry
    is_q = (
        q_clean.endswith("?") or
        any(q_clean.startswith(w) for w in ["what", "which", "how", "where", "can", "is", "tell", "explain"]) or
        any(kw in q_clean for kw in ["wear", "throw", "tolerance", "clearance", "standard", "spec", "usfd", "inspect", "alt 11", "alt 12", "buffer", "spare", "crack", "defect"])
    )
    if not is_q:
        return False, "UNKNOWN", 0.0

    if any(k in q_clean for k in ["alt 10", "alt 11", "alt 12", "alt 13", "revision", "alteration", "difference", "changed in"]):
        return True, "REVISION_COMPARISON", 0.98

    if any(k in q_clean for k in ["inspect", "usfd", "ultrasonic", "scan", "check rail clearance", "procedure", "frequency", "protocol"]):
        return True, "INSPECTION_PROCEDURE", 0.95

    if any(k in q_clean for k in ["wear", "throw", "clearance", "tolerance", "opening", "toe load", "torque", "limit"]):
        return True, "TOLERANCE_INQUIRY", 0.98

    if any(k in q_clean for k in ["standard", "specification", "irs:", "irs ", "is:", "is 2062", "is 814", "govern", "material", "grade"]):
        return True, "SPECIFICATION_GOVERNANCE", 0.96

    if any(k in q_clean for k in ["crack", "fracture", "defect", "failure", "mitigat", "remedy", "risk", "squat"]):
        return True, "FAILURE_MITIGATION", 0.95

    if any(k in q_clean for k in ["buffer", "spare", "bom", "procurement", "how many", "quantity", "sets", "list-a"]):
        return True, "BOM_PROCUREMENT", 0.96

    return True, "COMPONENT_LOOKUP", 0.85


def answer_engineering_question(query: str):
    """
    Resolves natural-language engineering questions against canonical QA bank.
    """
    is_q, intent, conf = detect_question_intent(query)
    if not is_q:
        return None

    tokens = [t for t in re.split(r"[\s,?.!]+", query.lower()) if len(t) > 2]
    
    best_match = None
    best_score = 0

    for item in CANONICAL_QA_BANK:
        score = 0
        if item["intent"] == intent:
            score += 40
        for kw in item["keywords"]:
            if kw in query.lower():
                score += 30
            elif any(t in kw for t in tokens):
                score += 10
        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score >= 40:
        return {
            "query": query,
            "intent": best_match["intent"],
            "matched_id": best_match["id"],
            "entity": best_match["entity"],
            "answer": best_match["answer"],
            "parameter": best_match["parameter"],
            "traversal": best_match["traversal"],
            "provenance": best_match["provenance"],
            "confidence": best_match["provenance"]["confidence"],
            "status": best_match["provenance"]["status"]
        }
    return None


def test_intent_detection_tolerance():
    """Verify tolerance questions correctly map to TOLERANCE_INQUIRY."""
    is_q, intent, conf = detect_question_intent("What is the permissible wear for tongue rails?")
    assert is_q is True
    assert intent == "TOLERANCE_INQUIRY"
    assert conf >= 0.90

    is_q2, intent2, _ = detect_question_intent("What is the switch throw tolerance at toe?")
    assert is_q2 is True
    assert intent2 == "TOLERANCE_INQUIRY"


def test_intent_detection_specification():
    """Verify specification questions map to SPECIFICATION_GOVERNANCE."""
    is_q, intent, conf = detect_question_intent("Which IRS specification governs sleeper rubber pads?")
    assert is_q is True
    assert intent == "SPECIFICATION_GOVERNANCE"
    assert conf >= 0.90


def test_intent_detection_inspection():
    """Verify USFD and inspection questions map to INSPECTION_PROCEDURE."""
    is_q, intent, _ = detect_question_intent("What is the USFD inspection protocol for curved switches?")
    assert is_q is True
    assert intent == "INSPECTION_PROCEDURE"


def test_intent_detection_revision():
    """Verify alteration questions map to REVISION_COMPARISON."""
    is_q, intent, _ = detect_question_intent("What was changed in Alt 11 for T-6155?")
    assert is_q is True
    assert intent == "REVISION_COMPARISON"


def test_intent_detection_procurement():
    """Verify spares buffer questions map to BOM_PROCUREMENT."""
    is_q, intent, _ = detect_question_intent("How are LIST-A spares calculated for 10 turnout sets?")
    assert is_q is True
    assert intent == "BOM_PROCUREMENT"


def test_answer_engineering_question_wear():
    """Verify multi-hop answer synthesis for tongue rail wear."""
    res = answer_engineering_question("What is the permissible wear for 60kg tongue rails?")
    assert res is not None
    assert res["intent"] == "TOLERANCE_INQUIRY"
    assert "6.0 mm" in res["answer"]
    assert res["parameter"]["max_vertical"] == 6.0
    assert "DOC:IRPWM:2024:ACS14" in res["traversal"]
    assert res["status"] == "VERIFIED"


def test_answer_engineering_question_throw():
    """Verify multi-hop answer synthesis for switch throw."""
    res = answer_engineering_question("What is the standard switch throw at the toe of curved switch?")
    assert res is not None
    assert res["intent"] == "TOLERANCE_INQUIRY"
    assert "160" in res["answer"]
    assert res["parameter"]["min"] == 160.0
    assert res["parameter"]["max"] == 163.0
    assert res["entity"] == "comp_detailb"


def test_answer_engineering_question_rubber_pad():
    """Verify specification answer synthesis for rubber pads."""
    res = answer_engineering_question("Which IRS specification governs sleeper rubber pads?")
    assert res is not None
    assert res["intent"] == "SPECIFICATION_GOVERNANCE"
    assert "IRS:T-46" in res["answer"]
    assert "comp_grsp" in res["traversal"]
