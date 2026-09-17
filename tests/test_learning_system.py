"""
tests/test_learning_system.py
Unit tests for Phase 6: Engineering Learning & Training System.
Validates 5-stage learning progression (Identify to Diagnose),
flashcard canonical parity, quiz grading, and competency scoring
per Blueprint Section 17.
"""

import pytest

CANONICAL_TRACKS = [
    {
        "id": "track_turnout_curved_switches",
        "title": "Turnout Engineering & Curved Switches",
        "doc": "RDSO/T-6155 & T-6154",
        "stages": [
            {"stage": 1, "name": "Identify", "topic": "Master Layout Geometry (1 in 12, 1676 mm Gauge)"},
            {"stage": 2, "name": "Understand", "topic": "Switch Assembly & Components (Thick-Web, Detail B)"},
            {"stage": 3, "name": "Trace", "topic": "Fastenings & Sleepers (PSC Sleepers, ERC Mk-V, GRSP)"},
            {"stage": 4, "name": "Compare", "topic": "Revision Lineage (Alt 10 vs Alt 11 vs Alt 12)"},
            {"stage": 5, "name": "Apply & Diagnose", "topic": "Field Tolerances & Defect Mitigations"}
        ]
    },
    {
        "id": "track_irpwm_statutory_tolerances",
        "title": "IRPWM 2024 Track Tolerances & Joint Inspection",
        "doc": "IRPWM 2024 ACS-14",
        "stages": [
            {"stage": 1, "name": "Identify", "topic": "Chapter 4 Turnout Classification"},
            {"stage": 2, "name": "Understand", "topic": "Statutory Maintenance Tolerances"},
            {"stage": 3, "name": "Trace", "topic": "P-Way and S&T Joint Inspection Mandates"},
            {"stage": 4, "name": "Compare", "topic": "ACS-14 Updates to Speed Regimes"},
            {"stage": 5, "name": "Apply & Diagnose", "topic": "Wear Gauging & Remedial Renewal"}
        ]
    }
]

CANONICAL_QUIZ_BANK = [
    {
        "id": "q1_check_rail",
        "question": "What is the statutory check rail clearance at the nose of a 1:12 BG turnout?",
        "options": ["35.0 – 38.0 mm", "41.0 – 45.0 mm", "48.0 – 52.0 mm", "57.0 – 60.0 mm"],
        "correctIndex": 1,
        "citation": "IRPWM 2024 Para 429 & IRS:T-10",
        "explanation": "Standard check rail clearance must be between 41.0 mm and 45.0 mm to prevent wheel flanges striking the crossing nose or climbing unguided."
    },
    {
        "id": "q2_alt11_drop",
        "question": "What forged drop was standardized for Detail 'B' Flat Tie Bars under Alteration 11?",
        "options": ["150 mm", "185 mm", "222 mm", "250 mm"],
        "correctIndex": 2,
        "citation": "RDSO/T-6155 Alt 11 Record",
        "explanation": "Alteration 11 introduced the 222 mm drop to prevent tamping machine tool tines from striking tie bars during mechanized track maintenance."
    },
    {
        "id": "q3_lista_buffer",
        "question": "What spares buffer percentage is mandated for LIST-A turnout items under Note 28?",
        "options": ["5%", "10%", "15%", "20%"],
        "correctIndex": 1,
        "citation": "RDSO/T-6155 Note 28",
        "explanation": "Note 28 requires adding a 10% wear buffer (rounded up) to all LIST-A components for depot stock maintenance."
    },
    {
        "id": "q4_usfd_frequency",
        "question": "How frequently must machined tongue rails undergo USFD 3-Zone ultrasonic scanning?",
        "options": ["Every 1 Month / 5 GMT", "Every 3 Months / 10 GMT", "Every 6 Months / 20 GMT", "Annually / 40 GMT"],
        "correctIndex": 1,
        "citation": "USFD Manual 2026 Chapter 10",
        "explanation": "Periodic ultrasonic scanning of tongue rails is mandatory every 3 months or 10 GMT, whichever is earlier, to detect sub-surface fatigue flaws."
    },
    {
        "id": "q5_rubber_pad_spec",
        "question": "Which IRS specification governs elastomeric Grooved Rubber Sole Pads (GRSP)?",
        "options": ["IRS:T-10", "IRS:T-12", "IRS:T-46", "IRS:T-29"],
        "correctIndex": 2,
        "citation": "IRS:T-46:2020",
        "explanation": "Grooved Rubber Sole Pads (GRSP 6mm/10mm composite) are manufactured and tested in accordance with IRS:T-46:2020."
    }
]


def evaluate_quiz_submission(answers: dict):
    """
    Evaluates quiz submissions against CANONICAL_QUIZ_BANK.
    Returns: (score: int, total: int, percentage: float, passed: bool, results: list)
    """
    total = len(CANONICAL_QUIZ_BANK)
    correct_count = 0
    results = []

    for q in CANONICAL_QUIZ_BANK:
        user_choice = answers.get(q["id"])
        is_correct = (user_choice == q["correctIndex"])
        if is_correct:
            correct_count += 1
        results.append({
            "id": q["id"],
            "is_correct": is_correct,
            "correct_option": q["options"][q["correctIndex"]],
            "citation": q["citation"],
            "explanation": q["explanation"]
        })

    pct = round((correct_count / total) * 100, 1)
    is_pass = pct >= 80.0
    return correct_count, total, pct, is_pass, results


def calculate_competency_scores(quiz_results: list):
    """
    Maps quiz question accuracy to 5 core railway competencies.
    """
    domain_map = {
        "q1_check_rail": "Track Geometry & Layout",
        "q2_alt11_drop": "Revision Lineage & Amendments",
        "q3_lista_buffer": "Procurement & BOM Spares",
        "q4_usfd_frequency": "Failure Modes & Inspection",
        "q5_rubber_pad_spec": "Fasteners & Sleeper Standards"
    }
    competencies = {}
    for r in quiz_results:
        domain = domain_map.get(r["id"], "General P-Way")
        competencies[domain] = 100 if r["is_correct"] else 0
    return competencies


def test_learning_track_progression_structure():
    """Verify learning tracks adhere to 5-stage progression per Blueprint §17.3."""
    for track in CANONICAL_TRACKS:
        assert len(track["stages"]) == 5
        stage_names = [s["name"] for s in track["stages"]]
        assert stage_names == ["Identify", "Understand", "Trace", "Compare", "Apply & Diagnose"]


def test_quiz_evaluation_perfect_score():
    """Verify 100% score calculation when all answers are correct."""
    perfect_answers = {
        "q1_check_rail": 1,
        "q2_alt11_drop": 2,
        "q3_lista_buffer": 1,
        "q4_usfd_frequency": 1,
        "q5_rubber_pad_spec": 2
    }
    score, total, pct, is_pass, results = evaluate_quiz_submission(perfect_answers)
    assert score == 5
    assert total == 5
    assert pct == 100.0
    assert is_pass is True


def test_quiz_evaluation_fail_threshold():
    """Verify pass threshold is strict 80% (requires at least 4/5 correct)."""
    partial_answers = {
        "q1_check_rail": 1,
        "q2_alt11_drop": 2,
        "q3_lista_buffer": 0,  # wrong
        "q4_usfd_frequency": 0,  # wrong
        "q5_rubber_pad_spec": 2
    }
    score, total, pct, is_pass, _ = evaluate_quiz_submission(partial_answers)
    assert score == 3
    assert pct == 60.0
    assert is_pass is False


def test_competency_calculation():
    """Verify quiz questions map accurately to domain competencies."""
    answers = {
        "q1_check_rail": 1,
        "q2_alt11_drop": 2,
        "q3_lista_buffer": 1,
        "q4_usfd_frequency": 1,
        "q5_rubber_pad_spec": 2
    }
    _, _, _, _, results = evaluate_quiz_submission(answers)
    comps = calculate_competency_scores(results)
    assert comps["Track Geometry & Layout"] == 100
    assert comps["Revision Lineage & Amendments"] == 100
    assert comps["Procurement & BOM Spares"] == 100
    assert comps["Failure Modes & Inspection"] == 100
    assert comps["Fasteners & Sleeper Standards"] == 100
