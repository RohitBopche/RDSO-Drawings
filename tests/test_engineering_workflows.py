"""
Automated unit tests for Phase 4: Engineering Workflows.
Tests Field Inspection tolerance evaluation and Note 28 10% LIST-A buffer calculation math
per Blueprint Sections 15, 16, 18, and 19.
"""

import math
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def evaluate_tolerance(parameter_name, measured_value):
    """
    Evaluates field measurements against canonical IRPWM tolerances.
    Returns: (is_pass: bool, status: str, message: str)
    """
    if parameter_name == "check_rail_clearance":
        # Statutory standard: 41 mm - 45 mm (IRPWM Para 429)
        if 41.0 <= measured_value <= 45.0:
            return True, "PASS", "Within statutory limit [41 - 45 mm]"
        elif measured_value < 41.0:
            return False, "DEFECT", "Clearance tight (<41 mm); high risk of wheel flange striking nose"
        else:
            return False, "DEFECT", "Clearance slack (>45 mm); wheel flange unguided at crossing"

    elif parameter_name == "switch_throw":
        # Statutory standard: 160 mm (-0, +3 mm) => 160 mm - 163 mm
        if 160.0 <= measured_value <= 163.0:
            return True, "PASS", "Nominal throw achieved [160 - 163 mm]"
        elif measured_value < 160.0:
            return False, "DEFECT", "Insufficient throw (<160 mm); tongue rail fails to open fully"
        else:
            return False, "DEFECT", "Excessive throw (>163 mm); risk of switch motor overload"

    elif parameter_name == "toe_load":
        # Statutory standard: min 1200 kg for ERC Mk-V (IRS:T-12:2009)
        if measured_value >= 1200.0:
            return True, "PASS", "Toe load satisfies high-speed requirement (>= 1200 kg)"
        else:
            return False, "DEFECT", "Sub-standard toe load (<1200 kg); risk of rail creep and turnover"

    elif parameter_name == "joh_opening":
        # Statutory standard: 60 mm (min 57 mm)
        if measured_value >= 57.0:
            return True, "PASS", "Adequate flange clearance (>= 57 mm)"
        else:
            return False, "DEFECT", "Flange clearance restricted (<57 mm)"

    return False, "UNKNOWN", f"Unknown parameter: {parameter_name}"


def calculate_turnout_procurement(order_sets, items):
    """
    Computes Bill of Materials and Note 28 10% depot wear spares buffer:
    total = base * order_sets + ceil(base * order_sets * 0.10) if list_a else base * order_sets
    """
    results = []
    for item in items:
        base_per_set = item["base_qty"]
        is_list_a = item.get("is_list_a", False)
        base_total = base_per_set * order_sets
        if is_list_a:
            buffer_qty = math.ceil(base_total * 0.10)
        else:
            buffer_qty = 0
        total_req = base_total + buffer_qty
        results.append({
            "code": item["code"],
            "name": item["name"],
            "is_list_a": is_list_a,
            "base_total": base_total,
            "buffer_qty": buffer_qty,
            "total_req": total_req
        })
    return results


def test_field_inspection_check_rail_tolerance():
    """Verify check rail clearance bounds checking."""
    # Nominal pass values
    assert evaluate_tolerance("check_rail_clearance", 41.0)[0] is True
    assert evaluate_tolerance("check_rail_clearance", 43.5)[0] is True
    assert evaluate_tolerance("check_rail_clearance", 45.0)[0] is True

    # Defect values
    pass_low, status_low, _ = evaluate_tolerance("check_rail_clearance", 39.5)
    assert pass_low is False
    assert status_low == "DEFECT"

    pass_high, status_high, _ = evaluate_tolerance("check_rail_clearance", 46.2)
    assert pass_high is False
    assert status_high == "DEFECT"


def test_field_inspection_switch_throw():
    """Verify switch throw tolerance (160 - 163 mm)."""
    assert evaluate_tolerance("switch_throw", 160.0)[0] is True
    assert evaluate_tolerance("switch_throw", 162.5)[0] is True

    assert evaluate_tolerance("switch_throw", 158.0)[0] is False
    assert evaluate_tolerance("switch_throw", 165.0)[0] is False


def test_field_inspection_toe_load():
    """Verify ERC Mk-V toe load minimum (1200 kg)."""
    assert evaluate_tolerance("toe_load", 1250.0)[0] is True
    assert evaluate_tolerance("toe_load", 1200.0)[0] is True
    assert evaluate_tolerance("toe_load", 1150.0)[0] is False


def test_note28_procurement_spares_buffer():
    """Verify Note 28 10% buffer calculation for single and bulk turnout orders."""
    sample_bom = [
        {"code": "comp_tongue_rail", "name": "Tongue Rail ZU-1-60 Set", "base_qty": 1, "is_list_a": True},
        {"code": "spare_bolt_25x310", "name": "HTS Fishbolts 25x310mm", "base_qty": 24, "is_list_a": True},
        {"code": "comp_tie_bar_b", "name": "Detail 'B' Flat Tie Bar", "base_qty": 2, "is_list_a": True},
        {"code": "turnout_layout_pscs", "name": "Special PSC Sleepers", "base_qty": 64, "is_list_a": False},
    ]

    # Case 1: Single turnout order (1 set)
    res_1 = calculate_turnout_procurement(1, sample_bom)
    # Tongue rail: 1 base + ceil(0.10) = 1 + 1 = 2
    tr_1 = next(r for r in res_1 if r["code"] == "comp_tongue_rail")
    assert tr_1["base_total"] == 1
    assert tr_1["buffer_qty"] == 1
    assert tr_1["total_req"] == 2

    # Bolts: 24 base + ceil(2.4) = 24 + 3 = 27
    bolt_1 = next(r for r in res_1 if r["code"] == "spare_bolt_25x310")
    assert bolt_1["base_total"] == 24
    assert bolt_1["buffer_qty"] == 3
    assert bolt_1["total_req"] == 27

    # Non LIST-A sleepers: 64 base + 0 buffer = 64
    sl_1 = next(r for r in res_1 if r["code"] == "turnout_layout_pscs")
    assert sl_1["buffer_qty"] == 0
    assert sl_1["total_req"] == 64

    # Case 2: Bulk order (10 sets)
    res_10 = calculate_turnout_procurement(10, sample_bom)
    bolt_10 = next(r for r in res_10 if r["code"] == "spare_bolt_25x310")
    # Bolts: 240 base + ceil(24.0) = 240 + 24 = 264
    assert bolt_10["base_total"] == 240
    assert bolt_10["buffer_qty"] == 24
    assert bolt_10["total_req"] == 264
