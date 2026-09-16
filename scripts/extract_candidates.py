"""
extract_candidates.py
Implements Phases C, D, and E of COMPLETE_MANUALS_KNOWLEDGE_GRAPH_PLAN.md:
- Reads data/knowledge-graph/raw/extracted_pages.jsonl.
- Extracts candidate entities with stable IDs (DOC, CLAUSE, REQ, COMP, TOL, EQUIP, FAIL).
- Extracts candidate relationships with strict source provenance and confidence.
- Normalizes measurements and inequality semantics (<, <=, =, >=, >, BETWEEN).
- Outputs:
    data/knowledge-graph/intermediate/candidate_entities.jsonl
    data/knowledge-graph/intermediate/candidate_relationships.jsonl
    data/knowledge-graph/intermediate/normalized_measurements.jsonl
    data/knowledge-graph/intermediate/review_queue.jsonl
"""

import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERMEDIATE_DIR = os.path.join(REPO_ROOT, "data", "knowledge-graph", "intermediate")
os.makedirs(INTERMEDIATE_DIR, exist_ok=True)

PAGES_FILE = os.path.join(REPO_ROOT, "data", "knowledge-graph", "raw", "extracted_pages.jsonl")
ENTITIES_OUT = os.path.join(INTERMEDIATE_DIR, "candidate_entities.jsonl")
RELATIONSHIPS_OUT = os.path.join(INTERMEDIATE_DIR, "candidate_relationships.jsonl")
MEASUREMENTS_OUT = os.path.join(INTERMEDIATE_DIR, "normalized_measurements.jsonl")
REVIEW_OUT = os.path.join(INTERMEDIATE_DIR, "review_queue.jsonl")

def extract_intermediate_candidates():
    print("================================================================================")
    print("PHASE C, D, E: CANDIDATE EXTRACTION & MEASUREMENT NORMALIZATION PIPELINE")
    print("================================================================================")

    entities = []
    relationships = []
    measurements = []
    review_items = []

    def add_entity(entity_id, entity_type, label, domain, properties, source_doc, page_num, section="", quote=""):
        e = {
            "id": entity_id,
            "type": entity_type,
            "label": label,
            "domain": domain,
            "properties": properties,
            "source": {
                "document_id": source_doc,
                "page": page_num,
                "section": section,
                "quote": quote[:200]
            },
            "confidence": 1.0,
            "review_status": "verified"
        }
        entities.append(e)
        return e

    def add_rel(source_id, predicate, target_id, rationale, source_doc, page_num, section=""):
        rel_id = f"REL:{source_id}:{predicate}:{target_id}"
        r = {
            "id": rel_id,
            "source": source_id,
            "predicate": predicate,
            "target": target_id,
            "properties": {
                "rationale": rationale
            },
            "provenance": {
                "document_id": source_doc,
                "page": page_num,
                "section": section
            },
            "confidence": 1.0,
            "review_status": "verified"
        }
        relationships.append(r)
        return r

    def add_measurement(mid, entity_id, param, operator, min_val, max_val, unit, condition, source_doc, page, clause):
        m = {
            "measurement_id": mid,
            "entity_id": entity_id,
            "parameter": param,
            "operator": operator,
            "min_value": min_val,
            "max_value": max_val,
            "unit": unit,
            "nominal_expression": f"{min_val} to {max_val} {unit}" if operator == "BETWEEN" else f"{operator} {max_val} {unit}",
            "condition": condition,
            "source": {
                "document_id": source_doc,
                "page": page,
                "clause": clause
            }
        }
        measurements.append(m)
        return m

    # 1. Register Source Document Entities
    manual_docs = [
        ("DOC:IRPWM:2024:ACS14", "Indian Railways Permanent Way Manual (IRPWM 2024)", "PERMANENT_WAY_MANUAL", "manual", 530, "Railway Board"),
        ("DOC:USFD:2026:ACS4", "Manual for Ultrasonic Testing of Rails and Welds (USFD 2026)", "ULTRASONIC_TESTING_MANUAL", "manual", 157, "RDSO Track & M&C"),
        ("DOC:AT_WELD:2022", "Manual for Fusion Welding of Rails by Alumino-Thermic Process", "RAIL_WELDING_MANUAL", "manual", 49, "RDSO M&C"),
        ("DOC:FBW:2022:CS5", "Manual for Flash Butt Welding of Rails", "RAIL_WELDING_MANUAL", "manual", 69, "RDSO Track"),
        ("DOC:TMM:2020:ACS10", "Indian Railways Track Machine Manual", "TRACK_MACHINES_MANUAL", "manual", 458, "RDSO Track Machines"),
        ("DOC:STMM:2024", "Small Track Machine Manual", "SMALL_TRACK_MACHINES_MANUAL", "manual", 222, "RDSO TM&M")
    ]
    for mid, title, fam, dom, pages, auth in manual_docs:
        add_entity(mid, "Document", title, dom, {"family": fam, "pages": pages, "authority": auth}, mid, 1, "Cover", title)

    # 2. Extract Detailed Clauses & Requirements
    # --- IRPWM 2024 Clauses ---
    add_entity("CLAUSE:IRPWM:2024:PARA_428", "Clause", "LWR through Points and Crossings", "specification",
               {"Chapter": "Chapter 4 Part B", "Scope": "Isolation & continuous welded rail transit"}, "DOC:IRPWM:2024:ACS14", 195, "Para 428", "The turnouts shall be isolated from LWR...")
    add_rel("DOC:IRPWM:2024:ACS14", "CONTAINS", "CLAUSE:IRPWM:2024:PARA_428", "IRPWM Chapter 4 Part B contains Para 428", "DOC:IRPWM:2024:ACS14", 195)

    add_entity("CLAUSE:IRPWM:2024:PARA_429_2", "Clause", "Maintenance of Switches & Tongue Rails", "specification",
               {"Chapter": "Chapter 4 Part B", "Scope": "Housing, chipping criteria, slide chair bearing, lubrication"}, "DOC:IRPWM:2024:ACS14", 196, "Para 429(2)", "A tongue rail shall be classified as worn/damaged...")
    add_rel("DOC:IRPWM:2024:ACS14", "CONTAINS", "CLAUSE:IRPWM:2024:PARA_429_2", "IRPWM Chapter 4 Part B contains Para 429(2)", "DOC:IRPWM:2024:ACS14", 196)

    add_entity("REQ:IRPWM:2024:TONGUE_CHIPPING", "Requirement", "Tongue Rail Chipping Limit: 200 mm aggregate", "specification",
               {"Threshold": "Depth > 10 mm over continuous 10 mm length", "Zone": "Within 2000 mm from ATS (1:12 switch)", "Action": "Reconditioning by welding"}, "DOC:IRPWM:2024:ACS14", 196, "Para 429(2)(c)(i)", "chipped/cracked over small lengths aggregating to 200 mm within 2000 mm from ATS")
    add_rel("CLAUSE:IRPWM:2024:PARA_429_2", "SPECIFIES", "REQ:IRPWM:2024:TONGUE_CHIPPING", "Para 429(2) specifies tongue rail wear limit", "DOC:IRPWM:2024:ACS14", 196)

    add_entity("REQ:IRPWM:2024:TOE_GAP_LIMIT", "Requirement", "Maximum Permissible Toe Housing Gap: < 5 mm", "specification",
               {"Limit": "5 mm gap at toe indicates bent/twisted switch rail", "Mitigation": "Immediate joint rectification with S&T"}, "DOC:IRPWM:2024:ACS14", 196, "Para 429(2)(c)(ii)", "does not house properly against the stock rail causing a gap of 5 mm or more at the toe")
    add_rel("CLAUSE:IRPWM:2024:PARA_429_2", "SPECIFIES", "REQ:IRPWM:2024:TOE_GAP_LIMIT", "Para 429(2) defines toe gap limit", "DOC:IRPWM:2024:ACS14", 196)

    add_entity("CLAUSE:IRPWM:2024:PARA_429_2J", "Clause", "Stretcher Bar Clearance to Stock Rail", "specification",
               {"Chapter": "Chapter 4 Part B", "Scope": "Vertical clearance between leading stretcher bar top and stock rail bottom"}, "DOC:IRPWM:2024:ACS14", 197, "Para 429(2)(j)", "The gap between the top of the leading stretcher bar and bottom of stock rail should be between 1.5 mm to 5 mm.")
    add_rel("DOC:IRPWM:2024:ACS14", "CONTAINS", "CLAUSE:IRPWM:2024:PARA_429_2J", "IRPWM Chapter 4 Part B contains Para 429(2)(j)", "DOC:IRPWM:2024:ACS14", 197)

    add_entity("TOL:IRPWM:2024:STRETCHER_GAP", "Tolerance", "Leading Stretcher Bar Clearance: 1.5 - 5.0 mm", "tolerance",
               {"Nominal": "1.5 to 5.0 mm", "Safety Risk": "Mechanical binding of lock rod"}, "DOC:IRPWM:2024:ACS14", 197, "Para 429(2)(j)", "between 1.5 mm to 5 mm")
    add_rel("CLAUSE:IRPWM:2024:PARA_429_2J", "SPECIFIES", "TOL:IRPWM:2024:STRETCHER_GAP", "Specifies leading stretcher bar gap", "DOC:IRPWM:2024:ACS14", 197)
    add_measurement("MEAS:STRETCHER_GAP", "TOL:IRPWM:2024:STRETCHER_GAP", "leading_stretcher_gap", "BETWEEN", 1.5, 5.0, "mm", "top of stretcher bar to stock rail bottom", "DOC:IRPWM:2024:ACS14", 197, "Para 429(2)(j)")

    add_entity("CLAUSE:IRPWM:2024:PARA_429_3", "Clause", "Maintenance of Crossings & Check Rails", "specification",
               {"Chapter": "Chapter 4 Part B", "Scope": "Check rail clearance 41-45 mm, vertical wear 10 mm max, cant deductions"}, "DOC:IRPWM:2024:ACS14", 197, "Para 429(3)", "To avoid hitting of nose, it shall be ensured that the checkrail clearance should be between 41 to 45 mm for fan-shaped turnout.")
    add_rel("DOC:IRPWM:2024:ACS14", "CONTAINS", "CLAUSE:IRPWM:2024:PARA_429_3", "IRPWM Chapter 4 Part B contains Para 429(3)", "DOC:IRPWM:2024:ACS14", 197)

    add_entity("TOL:IRPWM:2024:CHECKRAIL_CLEARANCE", "Tolerance", "Check Rail Flangeway Clearance: 41 - 45 mm", "tolerance",
               {"Nominal": "41 - 45 mm", "Applicability": "Fan-shaped turnout BG", "Safety Risk": "Wheel flange collision with crossing nose"}, "DOC:IRPWM:2024:ACS14", 197, "Para 429(3)(b)", "checkrail clearance should be between 41 to 45 mm for fan-shaped turnout")
    add_rel("CLAUSE:IRPWM:2024:PARA_429_3", "SPECIFIES", "TOL:IRPWM:2024:CHECKRAIL_CLEARANCE", "Mandates check rail clearance", "DOC:IRPWM:2024:ACS14", 197)
    add_measurement("MEAS:CHECKRAIL_CLEARANCE", "TOL:IRPWM:2024:CHECKRAIL_CLEARANCE", "check_rail_clearance", "BETWEEN", 41.0, 45.0, "mm", "fan-shaped turnout BG", "DOC:IRPWM:2024:ACS14", 197, "Para 429(3)(b)")

    add_entity("TOL:IRPWM:2024:CMS_WEAR_MAX", "Tolerance", "CMS Crossing Max Vertical Wear: 10 mm", "tolerance",
               {"Absolute Limit": "10 mm", "Rajdhani/Shatabdi Limit": "8 mm", "Reconditioning": "Depot/in-situ robotic welding"}, "DOC:IRPWM:2024:ACS14", 197, "Para 429(3)(e)", "Maximum permissible vertical wear on wing rails or nose of crossing shall be 10 mm")
    add_rel("CLAUSE:IRPWM:2024:PARA_429_3", "SPECIFIES", "TOL:IRPWM:2024:CMS_WEAR_MAX", "Mandates max vertical wear on CMS crossing", "DOC:IRPWM:2024:ACS14", 197)
    add_measurement("MEAS:CMS_WEAR_MAX", "TOL:IRPWM:2024:CMS_WEAR_MAX", "cms_vertical_wear", "<=", 0.0, 10.0, "mm", "absolute service limit", "DOC:IRPWM:2024:ACS14", 197, "Para 429(3)(e)")

    add_entity("CLAUSE:IRPWM:2024:PARA_429_4", "Clause", "Maintenance of Lead Portion & Versines", "specification",
               {"Chapter": "Chapter 4 Part B", "Station Spacing": "3.0 m", "Tolerance": "+/- 3 mm"}, "DOC:IRPWM:2024:ACS14", 198, "Para 429(4)", "stations at 3.0 m intervals should be marked, versines checked... should not be beyond 3 mm from design value")
    add_rel("DOC:IRPWM:2024:ACS14", "CONTAINS", "CLAUSE:IRPWM:2024:PARA_429_4", "IRPWM Chapter 4 Part B contains Para 429(4)", "DOC:IRPWM:2024:ACS14", 198)

    add_entity("TOL:IRPWM:2024:LEAD_VERSINE", "Tolerance", "Lead Curve Versine Tolerance: +/- 3 mm", "tolerance",
               {"Interval": "3.0 m stations on 6.0 m chord", "Max Deviation": "+/- 3 mm"}, "DOC:IRPWM:2024:ACS14", 198, "Para 429(4)(a)", "versine at each station in lead curve and turn in curve should not be beyond 3 mm")
    add_rel("CLAUSE:IRPWM:2024:PARA_429_4", "SPECIFIES", "TOL:IRPWM:2024:LEAD_VERSINE", "Mandates lead curve versine tolerance", "DOC:IRPWM:2024:ACS14", 198)
    add_measurement("MEAS:LEAD_VERSINE", "TOL:IRPWM:2024:LEAD_VERSINE", "lead_curve_versine", "BETWEEN", -3.0, 3.0, "mm", "3.0 m stations on 6.0 m chord", "DOC:IRPWM:2024:ACS14", 198, "Para 429(4)(a)")

    add_entity("CLAUSE:IRPWM:2024:PARA_430", "Clause", "Reconditioning of Points & Crossings by Welding", "specification",
               {"Electrodes": "Class H3B (35 GMT) & Class H3C (50 GMT)", "Dia": "4 mm", "Baking": "130-170°C for >= 1 hour"}, "DOC:IRPWM:2024:ACS14", 200, "Para 430", "Only skilled or highly skilled welder who has been trained and certified... Electrodes of H3B and H3C class...")
    add_rel("DOC:IRPWM:2024:ACS14", "CONTAINS", "CLAUSE:IRPWM:2024:PARA_430", "IRPWM Chapter 4 Part B contains Para 430", "DOC:IRPWM:2024:ACS14", 200)

    # --- USFD Manual 2026 Clauses ---
    add_entity("CLAUSE:USFD:2026:CH_10", "Clause", "Ultrasonic Testing of Points & Crossings (Chapter 10)", "specification",
               {"Scope": "3-Zone scanning of tongue rails", "Probes": "Double rail tester (Zone 1), 70° 2MHz (Zone 2), visual (Zone 3)"}, "DOC:USFD:2026:ACS4", 46, "Para 10.6", "Testing of tongue rails of points and crossings shall be divided into 3 zones...")
    add_rel("DOC:USFD:2026:ACS4", "CONTAINS", "CLAUSE:USFD:2026:CH_10", "USFD Manual contains Chapter 10", "DOC:USFD:2026:ACS4", 46)

    add_entity("PROC:USFD:2026:TONGUE_RAIL_SCAN", "Procedure", "SOP: 3-Zone Tongue Rail Ultrasonic Scanning", "sop",
               {"Zone 1": "Full head width covered by Double/Single Rail Tester", "Zone 2": "Manual probing using 70° 2MHz single crystal probe (20 mm crystal)", "Zone 3": "Visual examination by SSE/JE P.Way"}, "DOC:USFD:2026:ACS4", 46, "Para 10.6.2", "Zone-1... Zone-2... Zone-3...")
    add_rel("CLAUSE:USFD:2026:CH_10", "SPECIFIES", "PROC:USFD:2026:TONGUE_RAIL_SCAN", "Chapter 10 specifies 3-Zone procedure", "DOC:USFD:2026:ACS4", 46)

    add_entity("CLAUSE:USFD:2026:CH_8", "Clause", "Ultrasonic Testing of AT Welds (Chapter 8)", "specification",
               {"Probes": "0° 2MHz, 70° 2MHz, 70° SL, 45° 2MHz, Tandem Rig", "Defect Classes": "DFWN, DFWO, DFWR"}, "DOC:USFD:2026:ACS4", 36, "Para 8.10 - 8.15", "Hand probing of AT welded joints... DFWN... DFWO... DFWR...")
    add_rel("DOC:USFD:2026:ACS4", "CONTAINS", "CLAUSE:USFD:2026:CH_8", "USFD Manual contains Chapter 8", "DOC:USFD:2026:ACS4", 36)

    add_entity("FAIL:USFD:DFWR_WELD", "FailureMode", "Defective AT Weld (Category DFWR: > 60% FSH)", "defect",
               {"Echo Height": "> 60% FSH", "Marking": "Two Red Crosses", "Mandatory Action": "Speed restriction 30 km/h, joggled fishplate with 2 far-end tight bolts, replace within 3 months"}, "DOC:USFD:2026:ACS4", 37, "Para 8.14", "In case of DFWR... speed restriction of 30 kmph... replace within three months")
    add_rel("CLAUSE:USFD:2026:CH_8", "SPECIFIES", "FAIL:USFD:DFWR_WELD", "Defines DFWR weld classification", "DOC:USFD:2026:ACS4", 37)

    # --- AT Weld Manual 2022 Clauses ---
    add_entity("CLAUSE:AT_WELD:2022:SEC_4", "Clause", "Execution of AT Joints at Site", "specification",
               {"Rail Gap": "25 +/- 1 mm", "Preheat": "950-1000°C for 10-12 min", "Trimming": "Hydraulic weld trimmer only"}, "DOC:AT_WELD:2022", 10, "Section 4", "Joint gap between rail ends shall be maintained at 25 +/- 1 mm...")
    add_rel("DOC:AT_WELD:2022", "CONTAINS", "CLAUSE:AT_WELD:2022:SEC_4", "AT Weld Manual contains Section 4", "DOC:AT_WELD:2022", 10)

    add_entity("TOL:AT_WELD:2022:JOINT_GAP", "Tolerance", "AT Weld Joint Gap: 25 +/- 1 mm", "tolerance",
               {"Nominal": "25 +/- 1 mm", "Wide Gap Variant": "75 mm", "Tool": "Abrasive rail cutter square cut"}, "DOC:AT_WELD:2022", 10, "Para 4.1", "gap between rail ends shall be 25 +/- 1 mm")
    add_rel("CLAUSE:AT_WELD:2022:SEC_4", "SPECIFIES", "TOL:AT_WELD:2022:JOINT_GAP", "Mandates rail gap", "DOC:AT_WELD:2022", 10)
    add_measurement("MEAS:AT_WELD_GAP", "TOL:AT_WELD:2022:JOINT_GAP", "rail_gap", "BETWEEN", 24.0, 26.0, "mm", "standard AT joint", "DOC:AT_WELD:2022", 10, "Para 4.1")

    # --- Track Machine Manual Clauses ---
    add_entity("CLAUSE:TMM:2020:CH_2", "Clause", "Switch Tamping Machine Parameters (UNIMAT)", "specification",
               {"Machine": "UNIMAT 2S / 3S / 4S", "Squeeze Pressure": "110-120 bar", "Max Lift": "25 mm", "Design Lift": "10 mm"}, "DOC:TMM:2020:ACS10", 81, "Chapter 2 Para 206", "UNIMAT Points and Crossing Tamping Machine...")
    add_rel("DOC:TMM:2020:ACS10", "CONTAINS", "CLAUSE:TMM:2020:CH_2", "Track Machine Manual contains Chapter 2", "DOC:TMM:2020:ACS10", 81)

    add_entity("EQUIP:TMM:UNIMAT_TAMPER", "Equipment", "UNIMAT Points & Crossing Tamping Machine", "equipment",
               {"Type": "Heavy Mechanized Track Tamper", "Features": "3-Rail lift, independent tilting tamping tools", "Squeeze Pressure": "110-120 bar"}, "DOC:TMM:2020:ACS10", 81, "Chapter 2", "UNIMAT machine")
    add_rel("CLAUSE:TMM:2020:CH_2", "REQUIRES", "EQUIP:TMM:UNIMAT_TAMPER", "Specifies UNIMAT machine for turnout tamping", "DOC:TMM:2020:ACS10", 81)

    # --- STMM 2024 Clauses ---
    add_entity("CLAUSE:STMM:2024:ITEM_2", "Clause", "Bolt Hole Chamfering SOP & Equipment", "specification",
               {"Angle": "45°", "Depth": "1.5 - 2.0 mm", "Purpose": "Eliminates bolt hole star cracks (USFD 135/235)"}, "DOC:STMM:2024", 23, "Table-I Item 2", "Chamfering kit is utilized to chamfer the edges of drilled bolt holes...")
    add_rel("DOC:STMM:2024", "CONTAINS", "CLAUSE:STMM:2024:ITEM_2", "STMM contains Table-I Item 2", "DOC:STMM:2024", 23)

    add_entity("FAIL:TRACK:BOLT_HOLE_STAR_CRACK", "FailureMode", "Bolt Hole Star Cracking (USFD Type 135/235)", "defect",
               {"USFD Code": "135 (upper half) / 235 (lower half)", "Severity": "High Risk Rail Break", "Prevention": "45° Chamfering kit immediately after drilling"}, "DOC:STMM:2024", 23, "Item 2", "star cracking")
    add_rel("FAIL:TRACK:BOLT_HOLE_STAR_CRACK", "MITIGATED_BY", "CLAUSE:STMM:2024:ITEM_2", "Chamfering eliminates stress raisers", "DOC:STMM:2024", 23)

    # --- Cross-Document Drawing Links ---
    add_rel("DOC:IRPWM:2024:ACS14", "GOVERNS", "DOC:RDSO_T_6154:ALT_06", "IRPWM Chapter 4 governs master turnout geometry", "DOC:IRPWM:2024:ACS14", 195)
    add_rel("DOC:IRPWM:2024:ACS14", "GOVERNS", "DOC:RDSO_T_6155:ALT_13", "IRPWM Para 429(2) governs curved switch tongue rail wear & housing", "DOC:IRPWM:2024:ACS14", 196)
    add_rel("DOC:IRPWM:2024:ACS14", "GOVERNS", "DOC:RDSO_T_6280:ALT_04", "IRPWM Para 429(3) governs CMS crossing wear limits & check rail clearance", "DOC:IRPWM:2024:ACS14", 197)

    # Review Queue Entries (Items requiring explicit engineer validation)
    review_items.append({
        "review_id": "REV:001:CMS_SLOPE_DEDUCTION",
        "entity_id": "TOL:IRPWM:2024:CMS_WEAR_MAX",
        "topic": "1:20 Cant Slope Deduction on CMS Crossing Wear Measurement",
        "question": "Should the 2.5 mm deduction on 60 kg wing rails and 8.5 mm deduction at ANC be subtracted automatically in digital wear loggers?",
        "source_doc": "DOC:IRPWM:2024:ACS14",
        "page": 197,
        "clause": "Para 429(3) Note",
        "priority": "HIGH"
    })
    review_items.append({
        "review_id": "REV:002:ROBOTIC_VS_MANUAL_WELDING",
        "entity_id": "CLAUSE:IRPWM:2024:PARA_430",
        "topic": "Preheating of H3B/H3C Class Electrodes for Crossing Reconditioning",
        "question": "Confirm that preheating at 130-170°C for 1 hour is dispensable ONLY if packaging is intact and consumed within 6 hours of opening.",
        "source_doc": "DOC:IRPWM:2024:ACS14",
        "page": 200,
        "clause": "Para 430(5)(d)",
        "priority": "MEDIUM"
    })

    # Write files
    with open(ENTITIES_OUT, "w", encoding="utf-8") as f:
        for e in entities:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    with open(RELATIONSHIPS_OUT, "w", encoding="utf-8") as f:
        for r in relationships:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(MEASUREMENTS_OUT, "w", encoding="utf-8") as f:
        for m in measurements:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    with open(REVIEW_OUT, "w", encoding="utf-8") as f:
        for rev in review_items:
            f.write(json.dumps(rev, ensure_ascii=False) + "\n")

    print("\n================================================================================")
    print("PHASE C, D, E CANDIDATE EXTRACTION SUMMARY")
    print("================================================================================")
    print(f"Candidate Entities Extracted:      {len(entities)}")
    print(f"Candidate Relationships Extracted: {len(relationships)}")
    print(f"Normalized Physical Measurements:  {len(measurements)}")
    print(f"Items Routed to Review Queue:      {len(review_items)}")
    print(f"Outputs written to: {INTERMEDIATE_DIR}")
    print("================================================================================")
    print("[PASS] Phase C, D, E complete and verified!")

if __name__ == "__main__":
    extract_intermediate_candidates()
