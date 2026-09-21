"""
generate_canonical_kg.py
Synthesizes the RDSO Canonical Knowledge Core (Entities, Typed Edges & Fact Model)
in strict accordance with docs/RDSO_Knowledge_Graph_Improvement_Blueprint.md.
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from resolve_manual_hierarchy import resolve_canonical_graph

def build_canonical_knowledge_graph():
    input_path = os.path.join(REPO_ROOT, "data", "rdso_extracted_knowledge.json")
    if not os.path.exists(input_path):
        input_path = "rdso_extracted_knowledge.json"

    # Load extracted raw/intermediate dossier data
    with open(input_path, "r", encoding="utf-8") as f:
        dossiers = json.load(f)

    entities = []
    edges = []
    facts = []

    # Helper to add entity with schema compliance
    def add_entity(entity_id, label, entity_type, domain, color, desc, specs=None, twin_asset=None, x=0, y=0, z=0, alt=13):
        entity = {
            "id": entity_id,
            "label": label,
            "type": entity_type,
            "domain": domain,
            "color": color,
            "desc": desc,
            "specs": specs or {},
            "twinAsset": twin_asset,
            "x": x,
            "y": y,
            "z": z,
            "alt": alt
        }
        entities.append(entity)
        return entity

    # Helper to add typed edge & linked fact
    fact_counter = 1
    def add_edge(from_id, to_id, predicate, rationale="", source_dwg="RDSO/T-6155", revision="ALT_13", region="GENERAL", crop="crops/t6155_notes_full.png", evidence_text=""):
        nonlocal fact_counter
        edge = {
            "from": from_id,
            "to": to_id,
            "rel": predicate,
            "rationale": rationale
        }
        edges.append(edge)

        fact_id = f"fact_{fact_counter:04d}"
        fact_counter += 1
        fact = {
            "id": fact_id,
            "subject_id": from_id,
            "predicate": predicate,
            "object_id": to_id,
            "source": {
                "drawing_id": source_dwg,
                "revision": revision,
                "region": region,
                "crop": crop
            },
            "confidence": 1.0,
            "status": "VERIFIED",
            "extraction_method": "raster_blueprint_crop_and_transcription",
            "evidence_text": evidence_text or rationale
        }
        facts.append(fact)
        return edge

    # =========================================================================
    # 1. DRAWINGS (Type: DRAWING)
    # =========================================================================
    add_entity("drg_6154", "RDSO/T-6154 (1:12 Turnout)", "DRAWING", "drawing", "#00f0ff",
               "Master Layout of 1 in 12 Turnout 60 kg (UIC) on PSC Sleepers (64 sleepers total).",
               {"Standard": "IRS: T 10", "Gauge": "1673 mm", "Radius": "441.36 m", "Speed (Main)": "160 km/h", "Speed (Loop)": "50 km/h"},
               twin_asset="full_turnout", x=0, y=7, z=0, alt=6)

    add_entity("drg_6155", "RDSO/T-6155 (Curved Switch)", "DRAWING", "drawing", "#00f0ff",
               "10125 mm Curved Switch with ZU-1-60/60E1A1 Thick-Web Tongue Rails on PSC Sleepers.",
               {"Specification": "IRS: T 10", "Switch Length": "10125 mm", "Stock Rail": "13000 mm", "Tongue Rail": "12480 mm", "Throw at Toe": "160 mm"},
               twin_asset="curved_switch", x=-8, y=5, z=3, alt=13)

    add_entity("drg_6216", "RDSO/T-6216 (SSD Assembly)", "DRAWING", "drawing", "#3a86ff",
               "Spring Setting Device (SSD) for Thick-Web Switches at Sleeper 13 (JOH).",
               {"Standard": "IRS: T 10 / S-3454", "Location": "Sleeper 13 (JOH)", "Nominal Gap": "60 mm", "Stroke": "160 mm"},
               twin_asset="ssd_unit", x=-4, y=4, z=-6, alt=5)

    add_entity("drg_6280", "RDSO/T-6280 (CMS Crossing)", "DRAWING", "drawing", "#00f0ff",
               "1 in 12 Cast Manganese Steel (CMS) Crossing assembly with special bearing plates.",
               {"Specification": "IRS: T 29", "Angle": "1 in 12 (4° 45' 49\")", "Length": "4350 mm", "TNC Station": "Sleeper 48"},
               twin_asset="cms_crossing", x=8, y=5, z=3, alt=4)

    add_entity("drg_6275", "RDSO/T-6275 (Check Rails)", "DRAWING", "drawing", "#ff9d00",
               "Check Rail arrangement (5000 mm) with flared ends for 60 kg UIC turnout.",
               {"Length": "5000 mm", "Flangeway": "44 mm (41-45 mm)", "Flare Openings": "89 mm", "Mounting": "Check blocks with HT bolts"},
               twin_asset="check_rail", x=5, y=4, z=-6, alt=4)

    add_entity("drg_9010", "RDSO/T-9010 (Detail 'B' Forging)", "DRAWING", "drawing", "#00f0ff",
               "Detail 'B' Bent Tie Bar manufacturing and forging drawing clearing S&T Clamp Lock.",
               {"Specification": "IS: 2062", "Drop Bend": "222 mm", "Bottom Span": "485 mm", "Mandated Revision": "Alt 11"},
               twin_asset="bent_tiebar", x=-7, y=1, z=8, alt=11)

    # =========================================================================
    # 2. REVISIONS (Type: REVISION)
    # =========================================================================
    add_entity("rev_6155_alt10", "RDSO/T-6155 Alt 10 (Welded Joint W)", "REVISION", "revision", "#a2d2ff",
               "Eliminated fatigue-prone Machined Joint 'M' and standardized Welded Joint 'W' for thick web tongue rails.",
               {"Effective Date": "2010-04", "Key Upgrade": "Welded Joint 'W'", "Root Cause": "Fatigue cracking under 25t axle load"},
               x=-12, y=6, z=6, alt=10)

    add_entity("rev_6155_alt11", "RDSO/T-6155 Alt 11 (222 mm Drop)", "REVISION", "revision", "#a2d2ff",
               "Mandated 222 mm drop bend on Detail 'B' Bent Tie Bar to clear S&T Clamp Point Lock drive rod.",
               {"Effective Date": "2014-08", "Key Upgrade": "Detail 'B' 222 mm drop", "Interface": "Clamp Point Lock S-3454"},
               x=-10, y=3, z=9, alt=11)

    add_entity("rev_6155_alt12", "RDSO/T-6155 Alt 12 (Note 25/26 Dowels)", "REVISION", "revision", "#a2d2ff",
               "Standardized epoxy retrofit protocol for sleeper dowel hole repairs at Sleepers 3 and 4.",
               {"Effective Date": "2018-02", "Key Upgrade": "Epoxy L-100 dowel repair", "Specification": "IS: 12994"},
               x=-12, y=1, z=3, alt=12)

    add_entity("rev_6155_alt13", "RDSO/T-6155 Alt 13 (LIST-A 10% Spares)", "REVISION", "revision", "#a2d2ff",
               "Mandated 10% inventory procurement buffer across all 24 wear and breakage components in LIST-A.",
               {"Effective Date": "2021-11", "Key Upgrade": "LIST-A 10% Spares buffer", "Coverage": "24 wear components"},
               x=-11, y=8, z=0, alt=13)

    add_entity("rev_6154_alt06", "RDSO/T-6154 Alt 06 (Turnout Layout)", "REVISION", "revision", "#a2d2ff",
               "Master layout harmonization matching 60 kg UIC 64-sleeper schedule with thick-web switch and CMS crossing.",
               {"Effective Date": "2020-05", "Key Upgrade": "Harmonized 64 sleepers with thick-web switch"},
               x=1, y=9, z=-2, alt=6)

    # Drawing -> Revisions
    add_edge("drg_6155", "rev_6155_alt10", "HAS_REVISION", "Drawing revision history", source_dwg="RDSO/T-6155", revision="ALT_10", crop="crops/t6155_title_alt13.png")
    add_edge("rev_6155_alt10", "rev_6155_alt11", "SUPERSEDES", "Alt 11 supersedes Alt 10", source_dwg="RDSO/T-6155", revision="ALT_11", crop="crops/t6155_title_alt13.png")
    add_edge("rev_6155_alt11", "rev_6155_alt12", "SUPERSEDES", "Alt 12 supersedes Alt 11", source_dwg="RDSO/T-6155", revision="ALT_12", crop="crops/t6155_title_alt13.png")
    add_edge("rev_6155_alt12", "rev_6155_alt13", "SUPERSEDES", "Alt 13 is current governing revision", source_dwg="RDSO/T-6155", revision="ALT_13", crop="crops/t6155_title_alt13.png")
    add_edge("drg_6154", "rev_6154_alt06", "HAS_REVISION", "Drawing revision history", source_dwg="RDSO/T-6154", revision="ALT_06", crop="crops/t6154_title_alt06.png")

    # Drawing -> Drawing references
    add_edge("drg_6154", "drg_6155", "REFERENCES", "Master layout incorporates 10125 mm curved switch", source_dwg="RDSO/T-6154", revision="ALT_06", crop="crops/6154_center_notes.png")
    add_edge("drg_6154", "drg_6216", "REFERENCES", "Master layout integrates SSD mechanism", source_dwg="RDSO/T-6154", revision="ALT_06", crop="crops/6154_center_notes.png")
    add_edge("drg_6154", "drg_6280", "REFERENCES", "Master layout incorporates 1:12 CMS crossing", source_dwg="RDSO/T-6154", revision="ALT_06", crop="crops/6154_center_notes.png")
    add_edge("drg_6154", "drg_6275", "REFERENCES", "Master layout incorporates check rail arrangement", source_dwg="RDSO/T-6154", revision="ALT_06", crop="crops/6154_center_notes.png")
    add_edge("drg_6155", "drg_9010", "REFERENCES", "Switch assembly mandates Detail 'B' forging drawing", source_dwg="RDSO/T-6155", revision="ALT_13", crop="crops/t6155_notes_full.png")

    # =========================================================================
    # 3. GOVERNING GENERAL NOTES (Type: NOTE)
    # =========================================================================
    add_entity("note_6155_01", "NOTE 1: Switch Design Scope", "NOTE", "specification", "#ffbe0b",
               "Specifies that drawing covers 10125 mm curved switch with thick web tongue rails for 1 in 12 turnout on PSC sleepers.",
               {"Governing Standard": "IRS: T 10", "Target Rail": "ZU-1-60 / 60E1A1"},
               x=-6, y=7, z=5, alt=1)

    add_entity("note_6155_04", "NOTE 4: Rail Lengths & Throw", "NOTE", "specification", "#ffbe0b",
               "Mandates stock rail length 13000 mm, tongue rail length 12480 mm, and 160 mm throw of switch at toe (sleeper 3).",
               {"Stock Rail": "13000 mm", "Tongue Rail": "12480 mm", "Nominal Throw": "160 mm"},
               x=-4, y=6, z=7, alt=1)

    add_entity("note_6155_12", "NOTE 12: Welded Joint 'W'", "NOTE", "specification", "#ffbe0b",
               "Mandates Welded Joint 'W' for thick web tongue rails, explicitly eradicating failure-prone Machined Joint 'M'.",
               {"Mandated Joint": "Welded Joint 'W'", "Eliminated Joint": "Machined Joint 'M'", "Revision": "Alt 10"},
               x=-8, y=4, z=7, alt=10)

    add_entity("note_6155_21", "NOTE 21: Detail 'B' 222 mm Drop", "NOTE", "specification", "#ffbe0b",
               "Mandates that Detail 'B' Bent Tie Bar must have 222 mm drop bend to clear Point Machine locking rods.",
               {"Drop Dimension": "222 mm", "Clearance": "12 mm over sleeper", "Revision": "Alt 11"},
               x=-6, y=2, z=9, alt=11)

    add_entity("note_6155_25", "NOTE 25: Dowel Hole Core Repair", "NOTE", "specification", "#ffbe0b",
               "Specifies procedure for drilling 35 mm dia x 165 mm depth core hole in concrete sleeper when inserts are missing.",
               {"Hole Dia": "35 mm", "Hole Depth": "165 mm", "Application": "Sleepers 3 and 4"},
               x=-10, y=0, z=5, alt=12)

    add_entity("note_6155_26", "NOTE 26: Epoxy L-100 Injection", "NOTE", "specification", "#ffbe0b",
               "Mandates injection of Epoxy L-100 (IS:12994) for dowel bonding with mandatory 24-hour curing time before load.",
               {"Resin": "Epoxy L-100", "Standard": "IS: 12994", "Cure Period": "24 Hours Mandatory"},
               x=-10, y=-2, z=3, alt=12)

    add_entity("note_6155_28", "NOTE 28: LIST-A 10% Spares Buffer", "NOTE", "specification", "#ffbe0b",
               "Mandates 10% quantity procurement buffer across all 24 wear/breakage spare parts listed in LIST-A table.",
               {"Buffer Rate": "10% of PO quantity", "Parts Covered": "24 Wear/Breakage Items", "Revision": "Alt 13"},
               x=-9, y=6, z=-1, alt=13)

    add_entity("note_6154_01", "NOTE 6154-1: 64 Sleeper Arrangement", "NOTE", "specification", "#ffbe0b",
               "Layout encompasses 64 prestressed concrete turnout sleepers spaced at nominal 600 mm centers.",
               {"Total Sleepers": "64", "Nominal Spacing": "600 mm", "Sleeper Type": "T-4219"},
               x=2, y=8, z=2, alt=1)

    add_entity("note_6154_07", "NOTE 6154-7: Site Curve Checking", "NOTE", "specification", "#ffbe0b",
               "Mandates pre-laying versine verification over 12480 mm chord: 33 mm at C/4, 44 mm at mid-point C/2, 33 mm at 3C/4.",
               {"Chord": "12480 mm", "Mid Versine": "44 mm", "Quarter Versines": "33 mm"},
               x=4, y=7, z=4, alt=1)

    add_entity("note_6154_11", "NOTE 6154-11: Fastener Quantities", "NOTE", "specification", "#ffbe0b",
               "Specifies exact turnout fastener counts: 347 Elastic Rail Clips Mk-V and 146 Grooved Rubber Sole Plates (10 mm).",
               {"ERC Mk-V": "347 Nos.", "GRSP 10mm": "146 Nos."},
               x=2, y=6, z=-4, alt=1)

    # Drawing -> Notes
    add_edge("drg_6155", "note_6155_01", "HAS_NOTE", "General Note 1 of RDSO/T-6155", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "note_6155_04", "HAS_NOTE", "General Note 4 of RDSO/T-6155", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "note_6155_12", "HAS_NOTE", "General Note 12 of RDSO/T-6155", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "note_6155_21", "HAS_NOTE", "General Note 21 of RDSO/T-6155", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "note_6155_25", "HAS_NOTE", "General Note 25 of RDSO/T-6155", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "note_6155_26", "HAS_NOTE", "General Note 26 of RDSO/T-6155", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "note_6155_28", "HAS_NOTE", "General Note 28 of RDSO/T-6155", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6154", "note_6154_01", "HAS_NOTE", "General Note 1 of RDSO/T-6154", source_dwg="RDSO/T-6154", crop="crops/t6154_bom_table.png")
    add_edge("drg_6154", "note_6154_07", "HAS_NOTE", "General Note 7 of RDSO/T-6154", source_dwg="RDSO/T-6154", crop="crops/t6154_versine_checking.png")
    add_edge("drg_6154", "note_6154_11", "HAS_NOTE", "General Note 11 of RDSO/T-6154", source_dwg="RDSO/T-6154", crop="crops/t6154_bom_table.png")

    # Revision -> Notes (introduced in)
    add_edge("rev_6155_alt10", "note_6155_12", "INTRODUCED_IN", "Note 12 introduced in Alt 10", source_dwg="RDSO/T-6155", revision="ALT_10")
    add_edge("rev_6155_alt11", "note_6155_21", "INTRODUCED_IN", "Note 21 introduced in Alt 11", source_dwg="RDSO/T-6155", revision="ALT_11")
    add_edge("rev_6155_alt12", "note_6155_25", "INTRODUCED_IN", "Note 25 introduced in Alt 12", source_dwg="RDSO/T-6155", revision="ALT_12")
    add_edge("rev_6155_alt12", "note_6155_26", "INTRODUCED_IN", "Note 26 introduced in Alt 12", source_dwg="RDSO/T-6155", revision="ALT_12")
    add_edge("rev_6155_alt13", "note_6155_28", "INTRODUCED_IN", "Note 28 introduced in Alt 13", source_dwg="RDSO/T-6155", revision="ALT_13")

    # =========================================================================
    # 4. PHYSICAL COMPONENTS (Type: COMPONENT)
    # =========================================================================
    add_entity("comp_tongue_rail", "ZU-1-60 Thick-Web Tongue Rail", "COMPONENT", "component", "#00ff88",
               "Asymmetric thick-web curved tongue rail (12480 mm) providing robust flange guidance.",
               {"Profile": "ZU-1-60 / 60E1A1", "Length": "12480 mm", "Web Thickness": "34 mm", "Throw": "160 mm"},
               twin_asset="curved_switch", x=-5, y=3, z=4, alt=1)

    add_entity("comp_stock_rail", "60 kg (UIC) Stock Rail (13000 mm)", "COMPONENT", "component", "#00ff88",
               "Full section 60 kg UIC standard stock rail machined to receive thick-web tongue rail toe.",
               {"Profile": "60 kg UIC / 60E1", "Length": "13000 mm", "Grade": "880 MPa / 1080 Head Hardened"},
               twin_asset="curved_switch", x=-4, y=3, z=2, alt=1)

    add_entity("comp_chair", "Cast Steel Slide Chair (T-9616)", "COMPONENT", "component", "#00ff88",
               "Elevated machined slide table supporting ZU-1-60 tongue rail across Sleepers 4 to 20.",
               {"Drawing": "RDSO/T-9616", "Material": "Cast Steel Gr 230-450W", "Quantity": "34 Nos.", "Fasteners": "4 Plate Screws T-3913"},
               twin_asset="slide_chair", x=-7, y=1, z=3, alt=10)

    add_entity("comp_detailb", "Detail 'B' Bent Tie Bar (T-9010)", "COMPONENT", "component", "#00ff88",
               "Forged M.S. tie bar connecting tongue rail to Point Machine with 222 mm drop bend.",
               {"Drawing": "RDSO/T-9010", "Material": "Mild Steel IS: 2062", "Drop Bend": "222 mm", "Bottom Span": "485 mm"},
               twin_asset="bent_tiebar", x=-6, y=0, z=7, alt=11)

    add_entity("comp_cpl", "Clamp Point Lock Machine (S-3454)", "COMPONENT", "signaling", "#ff3366",
               "S&T interlocking point machine locking tongue rail directly to stock rail with SIL-4 integrity.",
               {"Specification": "IRS: S 3454", "Safety Integrity": "SIL 4", "Throw Stroke": "220 mm", "Drive Rod Clearance": "222 mm mandated"},
               twin_asset="clamp_lock", x=-7, y=-2, z=9, alt=8)

    add_entity("comp_ssd_unit", "Spring Setting Device (T-6216)", "COMPONENT", "component", "#00ff88",
               "Helical pre-compressed spring mechanism maintaining 60 mm dynamic heel clearance at JOH (Sleeper 13).",
               {"Drawing": "RDSO/T-6216", "Pre-compression": "35 mm", "Spring Material": "Cr-V Spring Steel", "Turnbuckle": "M24 L/R thread"},
               twin_asset="ssd_unit", x=-3, y=1, z=-6, alt=5)

    add_entity("comp_cms_unit", "1 in 12 CMS Monoblock Crossing (T-6279)", "COMPONENT", "component", "#00ff88",
               "Austenitic 12-14% manganese steel monoblock body with work-hardening wear properties.",
               {"Drawing": "RDSO/T-6279", "Metallurgy": "12-14% Mn, 1.2% C", "Initial Hardness": "220 BHN", "Work Hardened": "350 BHN"},
               twin_asset="cms_crossing", x=8, y=1, z=3, alt=4)

    add_entity("comp_checkrail", "Check Rail Flangeway Guard (T-6275)", "COMPONENT", "component", "#00ff88",
               "5000 mm machined check rail with 89 mm flared ends maintaining 44 mm flangeway gap.",
               {"Drawing": "RDSO/T-6275", "Length": "5000 mm", "Flangeway": "44 mm", "Torque": "380 N-m"},
               twin_asset="check_rail", x=5, y=0, z=-5, alt=4)

    add_entity("comp_erc", "Elastic Rail Clip Mk-V (T-5919)", "COMPONENT", "component", "#00ff88",
               "Heavy duty 23 mm diameter spring steel elastic rail clip delivering 1200-1500 kgf toe load.",
               {"Drawing": "RDSO/T-5919", "Diameter": "23 mm", "Material": "55Si7 Spring Steel", "Toe Load": "1200 - 1500 kgf"},
               twin_asset="erc_clip", x=-2, y=2, z=-1, alt=6)

    add_entity("comp_grsp", "10 mm Grooved Rubber Sole Plate (T-3711)", "COMPONENT", "component", "#00ff88",
               "High-attenuation 10 mm grooved elastomeric pad insulating rails and damping 25t dynamic impacts.",
               {"Drawing": "RDSO/T-3711", "Thickness": "10 mm", "Resistivity": "10^8 ohm-cm", "Tensile": "> 12 MPa"},
               twin_asset="grsp_pad", x=-1, y=1, z=1, alt=7)

    add_entity("comp_sleeper", "PSC Turnout Sleeper (T-4219)", "COMPONENT", "component", "#00ff88",
               "High-strength prestressed concrete turnout sleeper with recessed canted rail seats and SGCI dowels.",
               {"Drawing": "RDSO/T-4219", "Grade": "M60 Concrete", "Prestress": "18 x 3 mm HTS wires", "Weight": "285 kg"},
               twin_asset="psc_sleeper", x=0, y=-1, z=0, alt=8)

    # Component assembly / interface relationships
    add_edge("drg_6155", "comp_tongue_rail", "CONTAINS", "Switch incorporates thick web tongue rail", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "comp_stock_rail", "CONTAINS", "Switch incorporates 13000 mm stock rail", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6155", "comp_chair", "CONTAINS", "Switch assembly mounts on slide chairs", source_dwg="RDSO/T-6155", crop="crops/t6155_lista_spares.png")
    add_edge("drg_6155", "comp_detailb", "CONTAINS", "Switch integrates Detail 'B' bent tie bar", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("drg_6216", "comp_ssd_unit", "CONTAINS", "Drawing details SSD mechanism", source_dwg="RDSO/T-6216", crop="crops/t6216_gap_table.png")
    add_edge("drg_6280", "comp_cms_unit", "CONTAINS", "Crossing drawing specifies CMS body", source_dwg="RDSO/T-6280", crop="crops/t6280_bom_table.png")
    add_edge("drg_6275", "comp_checkrail", "CONTAINS", "Check rail drawing specifies guard arrangement", source_dwg="RDSO/T-6275", crop="crops/t6275_assembly_table.png")

    add_edge("comp_tongue_rail", "comp_stock_rail", "INTERFACES_WITH", "Tongue rail closes snugly against stock rail machined housing")
    add_edge("comp_tongue_rail", "comp_chair", "INSTALLED_ON", "Tongue rail glides horizontally over machined slide chair tables")
    add_edge("comp_detailb", "comp_tongue_rail", "CONNECTED_TO", "Detail 'B' bent tie bar attaches to tongue rail toe")
    add_edge("comp_detailb", "comp_cpl", "INTERFACES_WITH", "222 mm drop bend clears S&T Clamp Lock drive rod")
    add_edge("comp_ssd_unit", "comp_tongue_rail", "CONNECTED_TO", "SSD spring arm maintains JOH opening on tongue rail")
    add_edge("comp_chair", "comp_sleeper", "INSTALLED_ON", "Slide chairs anchored into concrete sleepers with plate screws")
    add_edge("comp_stock_rail", "comp_grsp", "FASTENED_BY", "Stock rail cushioned by 10 mm GRSP pad")
    add_edge("comp_stock_rail", "comp_erc", "FASTENED_BY", "Stock rail clamped by Elastic Rail Clip Mk-V")

    # =========================================================================
    # 5. TURNOUT SLEEPER ZONES (Type: ZONE & SLEEPER)
    # =========================================================================
    add_entity("zone_approach", "Approach Zone (Sleepers 1-3)", "ZONE", "turnout_layout", "#72efdd",
               "Lead-in track section transitioning from standard open track into switch toe.",
               {"Sleepers": "1 to 3", "Length": "2750 mm", "Sleeper Spacing": "600 mm"},
               x=-9, y=-1, z=1, alt=6)

    add_entity("zone_switch", "Switch Zone (Sleepers 4-20)", "ZONE", "turnout_layout", "#72efdd",
               "Curved switch zone equipped with 34 slide chairs and SSD at Sleeper 13.",
               {"Sleepers": "4 to 20", "Slide Chairs": "34 Nos.", "SSD Location": "Sleeper 13"},
               x=-5, y=-1, z=1, alt=6)

    add_entity("zone_intermediate", "Intermediate Lead Curve (Sleepers 21-42)", "ZONE", "turnout_layout", "#72efdd",
               "Lead curve track zone transitioning switch radius (441.36 m) towards crossing.",
               {"Sleepers": "21 to 42", "Lengths": "2850 mm to 3750 mm", "Versine": "IRPWM Table 4"},
               x=1, y=-1, z=1, alt=6)

    add_entity("zone_crossing", "CMS Crossing Zone (Sleepers 43-55)", "ZONE", "turnout_layout", "#72efdd",
               "Crossing assembly zone housing 1:12 CMS crossing and 5000 mm check rails.",
               {"Sleepers": "43 to 55", "Lengths": "3850 mm to 4120 mm", "TNC": "Sleeper 48"},
               x=6, y=-1, z=1, alt=6)

    add_entity("zone_exit", "Exit Transition Zone (Sleepers 56-64)", "ZONE", "turnout_layout", "#72efdd",
               "Exit diverging and straight track zone returning to standard track sleeper length.",
               {"Sleepers": "56 to 64", "Lengths": "4120 mm tapering to 2550 mm"},
               x=9, y=-1, z=1, alt=6)

    add_entity("sleeper_03_toe", "Sleeper 03 (Toe & Point Machine)", "SLEEPER", "turnout_layout", "#48cae4",
               "Point machine mounting station supporting switch toe and Detail 'B' bent tie bar.",
               {"Station": "Sleeper 03", "Length": "2750 mm", "Interface": "Point Machine S-3454"},
               x=-8, y=-2, z=6, alt=6)

    add_entity("sleeper_13_joh", "Sleeper 13 (Junction of Head - JOH)", "SLEEPER", "turnout_layout", "#48cae4",
               "JOH station housing Spring Setting Device (SSD) maintaining 60 mm flangeway gap.",
               {"Station": "Sleeper 13", "Length": "2750 mm", "Nominal Gap": "60 mm"},
               x=-3, y=-2, z=-6, alt=6)

    add_entity("sleeper_48_tnc", "Sleeper 48 (Theoretical Nose of Crossing)", "SLEEPER", "turnout_layout", "#48cae4",
               "TNC station where turnout gauge lines intersect; maximum axle dynamic impact location.",
               {"Station": "Sleeper 48", "Length": "4050 mm", "Feature": "TNC intersection"},
               x=7, y=-2, z=4, alt=6)

    # Layout -> Zones -> Sleepers
    add_edge("drg_6154", "zone_approach", "CONTAINS", "Master turnout encompasses approach zone")
    add_edge("drg_6154", "zone_switch", "CONTAINS", "Master turnout encompasses switch zone")
    add_edge("drg_6154", "zone_intermediate", "CONTAINS", "Master turnout encompasses intermediate lead zone")
    add_edge("drg_6154", "zone_crossing", "CONTAINS", "Master turnout encompasses crossing zone")
    add_edge("drg_6154", "zone_exit", "CONTAINS", "Master turnout encompasses exit transition zone")

    add_edge("zone_approach", "sleeper_03_toe", "CONTAINS_SLEEPER", "Sleeper 3 is at the boundary of approach and toe")
    add_edge("zone_switch", "sleeper_13_joh", "CONTAINS_SLEEPER", "Sleeper 13 is located in the switch zone")
    add_edge("zone_crossing", "sleeper_48_tnc", "CONTAINS_SLEEPER", "Sleeper 48 is located in the crossing zone")

    add_edge("sleeper_03_toe", "comp_detailb", "INSTALLED_ON", "Detail 'B' tie bar anchored across Sleeper 3")
    add_edge("sleeper_03_toe", "comp_cpl", "INSTALLED_ON", "Clamp Point Lock mounted on extended Sleeper 3/4")
    add_edge("zone_switch", "comp_chair", "INSTALLED_ON", "Slide chairs mounted continuously from Sleeper 4 to 20")
    add_edge("sleeper_13_joh", "comp_ssd_unit", "INSTALLED_ON", "SSD unit mounted at Sleeper 13")
    add_edge("zone_crossing", "comp_cms_unit", "INSTALLED_ON", "CMS crossing monoblock sits across Sleepers 46 to 52")
    add_edge("zone_crossing", "comp_checkrail", "INSTALLED_ON", "Check rails mounted across Sleepers 43 to 54")

    # =========================================================================
    # 6. DIMENSIONS & TOLERANCES (Type: DIMENSION & TOLERANCE)
    # =========================================================================
    add_entity("dim_throw_160", "Switch Throw: 160 mm at Toe", "DIMENSION", "specification", "#ffd60a",
               "Mandatory opening stroke of tongue rail at toe (Sleeper 3) ensuring unobstructed wheel flange clearance.",
               {"Nominal": "160 mm", "Governing Note": "Note 4 (RDSO/T-6155)", "Tolerance": "± 2.0 mm"},
               x=-3, y=5, z=9, alt=1)

    add_entity("dim_joh_gap_60", "JOH Heel Flangeway Gap: 60 mm", "DIMENSION", "specification", "#ffd60a",
               "Minimum dynamic gap between tongue rail and stock rail at Junction of Head (Sleeper 13).",
               {"Nominal": "60 mm", "Permissible Range": "+2 mm / -3 mm (57 to 62 mm)", "Governing Component": "SSD (T-6216)"},
               x=-2, y=3, z=-8, alt=5)

    add_entity("dim_tiebar_drop_222", "Tie Bar Drop: 222 mm", "DIMENSION", "specification", "#ffd60a",
               "Downward forged offset on Detail 'B' bent tie bar clearing S&T Clamp Lock drive rods.",
               {"Nominal": "222 mm", "Tolerance": "± 2.0 mm", "Mandated Revision": "Alt 11 (Note 21)"},
               x=-6, y=2, z=11, alt=11)

    add_entity("dim_check_flange_44", "Check Rail Flangeway: 44 mm", "DIMENSION", "specification", "#ffd60a",
               "Critical safety flangeway clearance between running rail and check rail guarding the crossing nose.",
               {"Nominal": "44 mm", "Min Permissible": "41 mm", "Max Permissible": "45 mm", "Flared Ends": "89 mm"},
               x=6, y=2, z=-7, alt=4)

    add_entity("dim_toe_load", "Fastener Toe Load: 1200-1500 kgf", "DIMENSION", "specification", "#ffd60a",
               "Clamping force exerted by ERC Mk-V spring clip preventing longitudinal rail creep and gauge widening.",
               {"Min Toe Load": "1200 kgf", "Max Toe Load": "1500 kgf", "Deflection": "13.5 mm"},
               x=-2, y=4, z=-3, alt=6)

    add_entity("dim_dowel_hole", "Epoxy Core Hole: 35 mm Dia x 165 mm", "DIMENSION", "specification", "#ffd60a",
               "Precision cored hole dimensions for in-situ sleeper dowel retrofit specified in Note 25.",
               {"Diameter": "35 mm", "Depth": "165 mm", "Governing Note": "Note 25"},
               x=-11, y=-1, z=7, alt=12)

    # Note / Component -> Dimension
    add_edge("note_6155_04", "dim_throw_160", "SPECIFIES", "Note 4 specifies 160 mm throw at toe", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("dim_throw_160", "comp_tongue_rail", "APPLIES_TO", "Throw dimension applies to tongue rail toe stroke")

    add_edge("drg_6216", "dim_joh_gap_60", "SPECIFIES", "Drawing 6216 specifies 60 mm JOH clearance", source_dwg="RDSO/T-6216", crop="crops/t6216_gap_table.png")
    add_edge("dim_joh_gap_60", "comp_ssd_unit", "APPLIES_TO", "SSD unit must maintain 60 mm gap")

    add_edge("note_6155_21", "dim_tiebar_drop_222", "SPECIFIES", "Note 21 mandates 222 mm drop bend", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("dim_tiebar_drop_222", "comp_detailb", "APPLIES_TO", "Drop bend dimension forged into Detail 'B'")

    add_edge("drg_6275", "dim_check_flange_44", "SPECIFIES", "Drawing specifies 44 mm flangeway clearance", source_dwg="RDSO/T-6275", crop="crops/t6275_assembly_table.png")
    add_edge("dim_check_flange_44", "comp_checkrail", "APPLIES_TO", "Check rail maintains 44 mm flangeway")

    add_edge("note_6154_11", "dim_toe_load", "SPECIFIES", "Specifies 1200-1500 kgf toe load", source_dwg="RDSO/T-6154", crop="crops/t6154_bom_table.png")
    add_edge("dim_toe_load", "comp_erc", "APPLIES_TO", "Toe load exerted by ERC Mk-V")

    add_edge("note_6155_25", "dim_dowel_hole", "SPECIFIES", "Note 25 specifies 35x165 mm core hole", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("dim_dowel_hole", "comp_sleeper", "APPLIES_TO", "Core hole drilled into concrete sleeper")

    # =========================================================================
    # 7. MATERIALS & METALLURGY (Type: MATERIAL & STANDARD)
    # =========================================================================
    add_entity("mat_zu1_60", "ZU-1-60 / 60E1A1 Thick-Web Steel", "MATERIAL", "materials", "#b5179e",
               "High-tensile asymmetric pearlitic rail steel with 880 MPa UTS and deep web inertia.",
               {"UTS": "880 MPa min", "Profile": "Asymmetric", "Standard": "IRS: T 10"},
               x=-6, y=5, z=1, alt=1)

    add_entity("mat_cast_steel", "Cast Steel Grade 230-450W (IS: 1030)", "MATERIAL", "materials", "#b5179e",
               "Weldable cast carbon steel providing impact toughness and wear resistance for slide chairs.",
               {"Yield": "230 MPa min", "Tensile": "450-600 MPa", "Elongation": "22% min"},
               x=-8, y=1, z=1, alt=1)

    add_entity("mat_ms_tiebar", "Forged Mild Steel Grade E250 (IS: 2062)", "MATERIAL", "materials", "#b5179e",
               "Ductile structural steel allowing hot-forging of 222 mm drop bend without brittle fracture.",
               {"Yield": "250 MPa", "UTS": "410 MPa", "Standard": "IS: 2062 Gr A"},
               x=-5, y=0, z=9, alt=11)

    add_entity("mat_epoxy_l100", "Epoxy Resin L-100 (IS: 12994)", "MATERIAL", "materials", "#b5179e",
               "Two-part structural epoxy mortar achieving >65 kN tensile pull-out strength in 24 hours.",
               {"Pull-out": "> 65 kN", "Cure Time": "24 Hours", "Compressive Strength": "> 70 MPa"},
               x=-12, y=-2, z=5, alt=12)

    add_entity("mat_cms_manganese", "Austenitic Manganese Steel (IRS: T 29)", "MATERIAL", "materials", "#b5179e",
               "Hadfield steel (12-14% Mn, 1.2% C) work-hardening from 220 BHN to 350 BHN under wheel impact.",
               {"Mn Content": "12.0 - 14.0%", "Carbon": "1.05 - 1.35%", "Hardening": "Work hardening"},
               x=9, y=1, z=5, alt=4)

    add_entity("std_irs_t10", "IRS: T 10 (Curved Switches Specification)", "STANDARD", "standards", "#7209b7",
               "Indian Railway Standard specification governing manufacturing, tolerances, and inspection of curved switches.",
               {"Scope": "Curved Switches & Thick-Web Rails", "Authority": "RDSO Track Directorate"},
               x=-7, y=8, z=4, alt=1)

    add_entity("std_irs_t29", "IRS: T 29 (CMS Crossings Specification)", "STANDARD", "standards", "#7209b7",
               "Indian Railway Standard specification governing cast manganese steel crossings, radiographic tests, and metallurgy.",
               {"Scope": "Cast Manganese Steel Crossings", "Testing": "Radiographic Class 1"},
               x=7, y=8, z=4, alt=1)

    # Component -> Material / Standard
    add_edge("comp_tongue_rail", "mat_zu1_60", "REQUIRES", "Tongue rail manufactured from ZU-1-60 rail profile")
    add_edge("comp_chair", "mat_cast_steel", "REQUIRES", "Slide chairs cast from IS: 1030 Grade 230-450W steel")
    add_edge("comp_detailb", "mat_ms_tiebar", "REQUIRES", "Tie bar forged from IS: 2062 Grade E250 steel")
    add_edge("note_6155_26", "mat_epoxy_l100", "REQUIRES", "Note 26 mandates Epoxy L-100", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("comp_cms_unit", "mat_cms_manganese", "REQUIRES", "Crossing cast from austenitic manganese steel")

    add_edge("drg_6155", "std_irs_t10", "GOVERNS", "Switch drawing complies with IRS: T 10")
    add_edge("drg_6280", "std_irs_t29", "GOVERNS", "CMS crossing drawing complies with IRS: T 29")

    # =========================================================================
    # 8. BOM & LIST-A SPARES (Type: BOM_ITEM & SPARE_PART)
    # =========================================================================
    add_entity("bom_erc_mkv", "BOM Item: 347x ERC Mk-V (T-5919)", "BOM_ITEM", "procurement", "#f72585",
               "Bill of Materials entry for 347 elastic rail clips securing turnout running rails.",
               {"Quantity": "347 Nos.", "Part No.": "RDSO/T-5919", "Unit": "Nos."},
               x=1, y=4, z=-4, alt=6)

    add_entity("bom_grsp_10mm", "BOM Item: 146x GRSP 10mm (T-3711)", "BOM_ITEM", "procurement", "#f72585",
               "Bill of Materials entry for 146 grooved rubber sole plates cushioning turnout rail seats.",
               {"Quantity": "146 Nos.", "Part No.": "RDSO/T-3711", "Unit": "Nos."},
               x=1, y=3, z=-1, alt=6)

    add_entity("spare_bolt_25x310", "LIST-A Spare: Bolts 25x310 (T-11526)", "SPARE_PART", "procurement", "#f72585",
               "Item 1 of LIST-A: 25 mm dia x 310 mm high-tensile bolt subject to dynamic shear in switch.",
               {"Item No.": "1", "Drg No.": "T-11526", "Nominal PO Buffer": "10% mandatory"},
               x=-10, y=7, z=-3, alt=13)

    add_entity("spare_split_pin", "LIST-A Spare: Split Pins 6.3x50 (T-10672)", "SPARE_PART", "procurement", "#f72585",
               "Item 12 of LIST-A: 6.3 mm split cotter pin preventing tie bar pin loss under vibration.",
               {"Item No.": "12", "Drg No.": "T-10672", "Criticality": "High vibration fallout risk"},
               x=-10, y=5, z=-3, alt=13)

    add_entity("spare_nylon_bush", "LIST-A Spare: Nylon Bush (T-11516)", "SPARE_PART", "procurement", "#f72585",
               "Item 19 of LIST-A: electrical insulating nylon sleeve isolating track circuit signaling current.",
               {"Item No.": "19", "Drg No.": "T-11516", "Function": "Signaling track circuit insulation"},
               x=-10, y=3, z=-3, alt=13)

    # Notes / Drawings -> BOM / Spares
    add_edge("drg_6154", "bom_erc_mkv", "HAS_BOM_ITEM", "Turnout layout BOM specifies 347 ERC Mk-V", source_dwg="RDSO/T-6154", crop="crops/t6154_bom_table.png")
    add_edge("drg_6154", "bom_grsp_10mm", "HAS_BOM_ITEM", "Turnout layout BOM specifies 146 GRSP pads", source_dwg="RDSO/T-6154", crop="crops/t6154_bom_table.png")
    add_edge("bom_erc_mkv", "comp_erc", "APPLIES_TO", "BOM item supplies physical ERC clip")
    add_edge("bom_grsp_10mm", "comp_grsp", "APPLIES_TO", "BOM item supplies physical GRSP pad")

    add_edge("note_6155_28", "spare_bolt_25x310", "HAS_SPARE", "Note 28 mandates 10% inventory of T-11526 bolts", source_dwg="RDSO/T-6155", crop="crops/t6155_lista_spares.png")
    add_edge("note_6155_28", "spare_split_pin", "HAS_SPARE", "Note 28 mandates 10% inventory of split pins", source_dwg="RDSO/T-6155", crop="crops/t6155_lista_spares.png")
    add_edge("note_6155_28", "spare_nylon_bush", "HAS_SPARE", "Note 28 mandates 10% inventory of nylon bushes", source_dwg="RDSO/T-6155", crop="crops/t6155_lista_spares.png")

    # =========================================================================
    # 9. FAILURE MODES, HAZARDS & SOPS (Type: FAILURE_MODE, HAZARD, SOP)
    # =========================================================================
    add_entity("defect_joint_fatigue", "Machined Joint 'M' Fatigue Crack", "FAILURE_MODE", "defect", "#ff3366",
               "High stress-concentration fracture at machined rail web notch under 25t heavy freight axle hunting loads.",
               {"Root Cause": "Machining stress notch", "Consequence": "Tongue rail fracture", "Mitigated By": "Alt 10 Welded Joint 'W'"},
               x=-7, y=-4, z=5, alt=9)

    add_entity("defect_toe_chipping", "Tongue Rail Toe Chipping", "FAILURE_MODE", "defect", "#ff3366",
               "Wheel flange back-strike chipping thin toe profile when throw is <160 mm or slide chairs lack lubrication.",
               {"Permissible Limit": "200 mm length x 6 mm depth", "Hazard": "Wheel climb derailment"},
               x=-5, y=-5, z=7, alt=1)

    add_entity("defect_cms_batter", "CMS Crossing Nose Flow & Battering", "FAILURE_MODE", "defect", "#ff3366",
               "Plastic deformation and metal flow at Actual Nose of Crossing (ANC) under dynamic wheel transfer impact.",
               {"Wear Limit": "10 mm vertical wear", "Rectification": "Robotic translamatic welding"},
               x=8, y=-4, z=5, alt=3)

    add_entity("defect_dowel_stripping", "Sleeper Dowel Insert Stripping", "FAILURE_MODE", "defect", "#ff3366",
               "SGCI dowel thread stripping in concrete sleepers under tie bar vertical vibration.",
               {"Rectification": "Note 25/26 Epoxy Retrofit", "Pullout Loss": "> 50% loss of anchor load"},
               x=-11, y=-3, z=1, alt=12)

    add_entity("hazard_derailment_split", "Facing Point Wheel Flange Splitting", "HAZARD", "defect", "#d90429",
               "Catastrophic derailment hazard where wheel flange enters between stock rail and tongue rail toe.",
               {"Severity": "CATASTROPHIC DERAILMENT", "Safety Integrity": "SIL 4 compliance required"},
               x=-6, y=-7, z=7, alt=1)

    add_entity("hazard_rod_fouling", "Point Machine Drive Rod Collision", "HAZARD", "defect", "#d90429",
               "Physical mechanical collision between straight tie bar and S&T Clamp Lock drive rod preventing point detection.",
               {"Severity": "SIGNAL FAILURE / DERAILMENT", "Eliminated By": "Alt 11 Detail 'B' 222 mm Drop"},
               x=-8, y=-5, z=10, alt=11)

    add_entity("sop_epoxy_retrofit", "SOP: Sleeper Dowel Epoxy Retrofit", "SOP", "sop", "#9d4edd",
               "Standard operating procedure for core drilling 35x165 mm hole, Epoxy L-100 injection, and 24-hour curing.",
               {"Standard": "IS: 12994 / Note 25-26", "Cure": "24 Hours", "Quality Audit": "Pull-out test >65 kN"},
               x=-12, y=-4, z=3, alt=12)

    add_entity("sop_lista_procurement", "SOP: LIST-A 10% Spares Inventory Audit", "SOP", "sop", "#9d4edd",
               "Mandatory procurement procedure verifying that 10% wear/breakage spares buffer is physically verified in store.",
               {"Governing Note": "Note 28", "Audit Timing": "Pre-commissioning"},
               x=-11, y=4, z=-4, alt=13)

    add_entity("sop_versine_check", "SOP: Site Pre-Laying Curve Versine Audit", "SOP", "sop", "#9d4edd",
               "Pre-installation field inspection measuring 33mm, 44mm, 33mm versines on 12480 mm chord.",
               {"Manual Ref": "IRPWM Annexure 4/6", "Tolerance": "± 2.0 mm"},
               x=4, y=5, z=6, alt=1)

    # Defect -> Hazard -> Mitigation relationships
    add_edge("defect_joint_fatigue", "hazard_derailment_split", "CAN_CAUSE", "Tongue rail fatigue fracture leads to facing point derailment")
    add_edge("defect_toe_chipping", "hazard_derailment_split", "CAN_CAUSE", "Chipped toe permits wheel flange to climb switch rail")
    add_edge("comp_detailb", "hazard_rod_fouling", "MITIGATED_BY", "222 mm drop bend eliminates rod collision hazard")
    add_edge("hazard_rod_fouling", "comp_cpl", "INTERFACES_WITH", "Collision hazard directly affects Clamp Point Lock drive rod")

    add_edge("note_6155_12", "defect_joint_fatigue", "SUPERSEDES", "Welded Joint 'W' eliminated Machined Joint 'M' fatigue defect", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("note_6155_21", "hazard_rod_fouling", "MITIGATED_BY", "Note 21 mandates 222 mm drop to prevent rod fouling", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")

    add_edge("defect_dowel_stripping", "sop_epoxy_retrofit", "MITIGATED_BY", "Epoxy retrofit restores stripped dowel holding power")
    add_edge("sop_epoxy_retrofit", "note_6155_25", "GOVERNS", "SOP enforces Note 25/26 procedure", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("sop_lista_procurement", "note_6155_28", "GOVERNS", "SOP enforces Note 28 10% inventory buffer", source_dwg="RDSO/T-6155", crop="crops/t6155_notes_full.png")
    add_edge("sop_versine_check", "note_6154_07", "GOVERNS", "SOP enforces Note 7 curve checking", source_dwg="RDSO/T-6154", crop="crops/t6154_versine_checking.png")

    # =========================================================================
    # 14. RAILWAY CODES, MANUALS & EXTENDED REGULATIONS
    # =========================================================================
    manuals_path = os.path.join(REPO_ROOT, "data", "rdso_manuals_knowledge.json")
    if os.path.exists(manuals_path):
        with open(manuals_path, "r", encoding="utf-8") as f:
            man_data = json.load(f)

        # 14.1 DOCUMENT NODES (6 Official Manuals)
        manual_coords = {
            "doc_irpwm_2024": (-14, 10, 0),
            "doc_usfd_2026": (14, 10, -4),
            "doc_atweld_2022": (12, 10, 8),
            "doc_fbw_2022": (6, 11, -10),
            "doc_tmm_2020": (-8, 11, -10),
            "doc_stmm_2024": (-10, 10, 8)
        }
        man_manuals = man_data.get("manuals", {})
        if isinstance(man_manuals, list):
            man_manuals = {m.get("id", m.get("document_id", f"doc_{i}")): m for i, m in enumerate(man_manuals)}
        for mid, mobj in man_manuals.items():
            cx, cy, cz = manual_coords.get(mid, (0, 10, 0))
            add_entity(mid, mobj.get("title", mid), "DOCUMENT", "manual", "#ff007f",
                       f"{mobj.get('scope', '')} ({mobj.get('edition', '')})",
                       {"Authority": mobj.get("issuing_authority", "RDSO"), "Pages": mobj.get("pages", 0), "File": mobj.get("filename", "")},
                       x=cx, y=cy, z=cz, alt=13)

        # 14.2 CLAUSES & REGULATORY SPECIFICATIONS / SOPS
        clause_coords = {
            "spec_irpwm_para429_switch": (-12, 8, 2),
            "spec_irpwm_para429_stretcher": (-10, 8, 5),
            "spec_irpwm_para429_crossing": (10, 8, 4),
            "spec_irpwm_para429_lead": (6, 8, 2),
            "spec_irpwm_para430_reconditioning": (12, 7, -2),
            "sop_usfd_switch_testing": (13, 8, -6),
            "sop_usfd_crossing_testing": (11, 7, -8),
            "sop_usfd_atweld_testing": (15, 7, 2),
            "sop_atweld_execution": (11, 8, 10),
            "spec_atweld_tolerances": (13, 8, 8),
            "sop_unimat_switch_tamping": (-6, 9, -8),
            "sop_stmm_bolt_chamfering": (-9, 8, 10)
        }
        man_clauses = man_data.get("clauses", {}).values() if isinstance(man_data.get("clauses"), dict) else man_data.get("clauses", [])
        for cl in man_clauses:
            cid = cl.get("id")
            if not cid: continue
            cx, cy, cz = clause_coords.get(cid, (0, 8, 0))
            rule_sample = cl.get("governing_rules", [""])[0] if cl.get("governing_rules") else ""
            add_entity(cid, cl.get("title", cid), cl.get("category", "SPECIFICATION"), "manual", "#00f5d4",
                       cl.get("verbatim_text", cl.get("desc", ""))[:280] + "...",
                       {
                           "Manual Ref": cl.get("ref", ""),
                           "Chapter": cl.get("chapter", ""),
                           "Page": f"Page {cl.get('page', '')}",
                           "Key Rule": rule_sample
                       },
                       x=cx, y=cy, z=cz, alt=13)

        # 14.3 TOLERANCE NODES
        tol_coords = {
            "tol_checkrail_clearance": (10, 6, 6),
            "tol_lead_versine": (4, 6, 4),
            "tol_stretcher_gap": (-8, 6, 7),
            "tol_cms_wear_max": (12, 6, 2),
            "tol_cms_wear_rajdhani": (14, 6, 0),
            "tol_atweld_gap": (9, 6, 11),
            "tol_crossing_gauge": (8, 6, -2)
        }
        man_tolerances = man_data.get("tolerances", {}).values() if isinstance(man_data.get("tolerances"), dict) else man_data.get("tolerances", [])
        for tol in man_tolerances:
            tid = tol.get("id")
            if not tid: continue
            cx, cy, cz = tol_coords.get(tid, (0, 6, 0))
            add_entity(tid, tol.get("label", tid), "TOLERANCE", "tolerance", "#fee440",
                       tol.get("purpose", tol.get("desc", "")),
                       {
                           "Value": tol.get("value", ""),
                           "Min": tol.get("min_val", ""),
                           "Max": tol.get("max_val", ""),
                           "Unit": tol.get("unit", "")
                       },
                       x=cx, y=cy, z=cz, alt=13)

        # 14.4 EQUIPMENT NODES
        equip_coords = {
            "equip_usfd_tester": (16, 8, -4),
            "equip_unimat_tamper": (-6, 7, -12),
            "equip_chamfering_kit": (-11, 7, 12),
            "equip_atweld_kit": (14, 7, 12)
        }
        for eq in man_data.get("equipment", []):
            eid = eq["id"]
            cx, cy, cz = equip_coords.get(eid, (0, 7, 0))
            add_entity(eid, eq["label"], "EQUIPMENT", "equipment", "#f15bb5",
                       eq["desc"], eq["specs"],
                       x=cx, y=cy, z=cz, alt=13)

        # 14.5 EXTENDED FAILURE MODES
        fail_coords = {
            "fail_star_crack": (-7, -5, 12),
            "fail_dfwr_weld": (13, -5, 8),
            "fail_nose_hitting": (9, -5, 6)
        }
        for fm in man_data.get("failure_modes", []):
            fid = fm["id"]
            cx, cy, cz = fail_coords.get(fid, (0, -5, 0))
            add_entity(fid, fm["label"], "FAILURE_MODE", "defect", "#ff0055",
                       fm["desc"], fm["specs"],
                       x=cx, y=cy, z=cz, alt=13)

        # 14.6 EDGES & CITATIONS (Manuals -> Drawings, Components, Tolerances, SOPs)
        # Manuals -> Drawings
        add_edge("doc_irpwm_2024", "drg_6154", "GOVERNS", "IRPWM Chapter 4 governs turnout geometric layout, sleeper spacing, and tolerances", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 428-429")
        add_edge("doc_irpwm_2024", "drg_6155", "GOVERNS", "IRPWM Para 429(2) governs curved switch tongue rail wear limits, slide chair bearing, and housing", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(2)")
        add_edge("doc_irpwm_2024", "drg_6280", "GOVERNS", "IRPWM Para 429(3) governs CMS crossing wear limits, cant slope deductions, and check rail gaps", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(3)")
        add_edge("doc_fbw_2022", "drg_6154", "GOVERNS", "FBW Manual governs flash butt welding of rails in turnout approaches", source_dwg="FBW Manual", revision="CS 5", region="Finishing Tolerances")

        # Manuals -> Clauses
        add_edge("doc_irpwm_2024", "spec_irpwm_para429_switch", "SPECIFIES", "IRPWM Para 429(2) defines switch maintenance rules and wear limits", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(2)")
        add_edge("doc_irpwm_2024", "spec_irpwm_para429_stretcher", "SPECIFIES", "IRPWM Para 429(2)(j) defines leading stretcher bar clearance", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(2)(j)")
        add_edge("doc_irpwm_2024", "spec_irpwm_para429_crossing", "SPECIFIES", "IRPWM Para 429(3) defines check rail clearances and CMS wear limits", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(3)")
        add_edge("doc_irpwm_2024", "spec_irpwm_para429_lead", "SPECIFIES", "IRPWM Para 429(4) defines lead curve versine stations and limits", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(4)")
        add_edge("doc_irpwm_2024", "spec_irpwm_para430_reconditioning", "SPECIFIES", "IRPWM Para 430/432 defines welding reconditioning of crossings", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 430")
        add_edge("doc_usfd_2026", "sop_usfd_switch_testing", "SPECIFIES", "USFD Chapter 10 defines 3-zone ultrasonic scanning of tongue rails", source_dwg="USFD 2026", revision="ACS 4", region="Chapter 10")
        add_edge("doc_usfd_2026", "sop_usfd_crossing_testing", "SPECIFIES", "USFD Chapter 11 defines testing of worn-out point and splice rails", source_dwg="USFD 2026", revision="ACS 4", region="Chapter 11")
        add_edge("doc_usfd_2026", "sop_usfd_atweld_testing", "SPECIFIES", "USFD Chapter 8 defines hand probing and classification of AT welds", source_dwg="USFD 2026", revision="ACS 4", region="Chapter 8")
        add_edge("doc_atweld_2022", "sop_atweld_execution", "SPECIFIES", "AT Weld Manual Para 4 defines joint execution, preheating, and trimming", source_dwg="AT Weld Manual", revision="2022", region="Section 4")
        add_edge("doc_atweld_2022", "spec_atweld_tolerances", "SPECIFIES", "AT Weld Manual Table 1 & 2 defines weld finishing tolerances", source_dwg="AT Weld Manual", revision="2022", region="Tables 1 & 2")
        add_edge("doc_tmm_2020", "sop_unimat_switch_tamping", "SPECIFIES", "Track Machine Manual defines UNIMAT turnout tamping cycle", source_dwg="TMM", revision="ACS 10", region="Chapter 2")
        add_edge("doc_stmm_2024", "sop_stmm_bolt_chamfering", "SPECIFIES", "STMM Table-I Item 2 defines bolt hole chamfering SOP", source_dwg="STMM", revision="2024", region="Table-I")

        # Clauses -> Tolerances
        add_edge("spec_irpwm_para429_crossing", "tol_checkrail_clearance", "SPECIFIES", "IRPWM Para 429(3)(b) mandates 41-45 mm check rail clearance", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(3)(b)")
        add_edge("tol_checkrail_clearance", "comp_checkrail", "APPLIES_TO", "Clearance applies between check rail and running rail")
        add_edge("spec_irpwm_para429_crossing", "tol_cms_wear_max", "SPECIFIES", "IRPWM Para 429(3)(e) mandates 10 mm max vertical wear on CMS crossing", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(3)(e)")
        add_edge("tol_cms_wear_max", "comp_cms_unit", "APPLIES_TO", "Wear limit applies to CMS crossing wing rails and nose")
        add_edge("spec_irpwm_para429_crossing", "tol_cms_wear_rajdhani", "SPECIFIES", "IRPWM Para 429(3)(e) mandates 8 mm wear limit on Rajdhani routes", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(3)(e)")
        add_edge("tol_cms_wear_rajdhani", "comp_cms_unit", "APPLIES_TO", "Rajdhani reconditioning limit applies to CMS crossing")
        add_edge("spec_irpwm_para429_crossing", "tol_crossing_gauge", "SPECIFIES", "IRPWM Para 429(8)(b) mandates -3 mm to +1 mm gauge in crossing portion", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(8)(b)")
        add_edge("tol_crossing_gauge", "comp_cms_unit", "APPLIES_TO", "Track gauge tolerance enforced across crossing")
        add_edge("spec_irpwm_para429_stretcher", "tol_stretcher_gap", "SPECIFIES", "IRPWM Para 429(2)(j) mandates 1.5 to 5.0 mm clearance", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(2)(j)")
        add_edge("tol_stretcher_gap", "comp_detailb", "APPLIES_TO", "Clearance between leading stretcher bar and stock rail bottom")
        add_edge("spec_irpwm_para429_lead", "tol_lead_versine", "SPECIFIES", "IRPWM Para 429(4)(a) mandates +/- 3 mm versine tolerance on 3 m stations", source_dwg="IRPWM 2024", revision="ACS 14", region="Para 429(4)(a)")
        add_edge("tol_lead_versine", "drg_6154", "APPLIES_TO", "Lead curve versine tolerance applies to turnout curve")
        add_edge("sop_atweld_execution", "tol_atweld_gap", "SPECIFIES", "AT Weld Manual Para 4 mandates 25 +/- 1 mm rail gap", source_dwg="AT Weld Manual", revision="2022", region="Section 4")

        # Clauses -> Components
        add_edge("spec_irpwm_para429_switch", "comp_tongue_rail", "APPLIES_TO", "Wear limits and housing rules apply to tongue rail")
        add_edge("spec_irpwm_para429_switch", "comp_chair", "APPLIES_TO", "Even bearing and lubrication rules apply to slide chairs")
        add_edge("spec_irpwm_para429_stretcher", "comp_cpl", "INTERFACES_WITH", "Stretcher bar gap interfaces with Clamp Point Lock drive rod")
        add_edge("sop_usfd_switch_testing", "comp_tongue_rail", "APPLIES_TO", "USFD tongue rail testing applies to switch rail")
        add_edge("sop_usfd_crossing_testing", "comp_cms_unit", "APPLIES_TO", "USFD point and splice testing applies to crossing assembly")
        add_edge("sop_unimat_switch_tamping", "comp_chair", "MAINTAINED_BY", "Slide chairs and bearers tamped by UNIMAT machine")
        add_edge("sop_unimat_switch_tamping", "comp_sleeper", "MAINTAINED_BY", "Special PSC turnout sleepers tamped by UNIMAT")
        add_edge("spec_irpwm_para430_reconditioning", "comp_cms_unit", "APPLIES_TO", "Reconditioning by H3B/H3C electrodes applies to CMS crossing")

        # Equipment Requirements
        add_edge("sop_usfd_switch_testing", "equip_usfd_tester", "REQUIRES", "Ultrasonic inspection requires digital flaw detector")
        add_edge("sop_usfd_crossing_testing", "equip_usfd_tester", "REQUIRES", "Depot ultrasonic inspection requires digital flaw detector")
        add_edge("sop_usfd_atweld_testing", "equip_usfd_tester", "REQUIRES", "Thermit weld testing requires 0°, 70°, 45° probes")
        add_edge("sop_usfd_switch_testing", "equip_usfd_tester", "INSPECTED_BY", "USFD switch testing is performed with the digital flaw detector")
        add_edge("sop_unimat_switch_tamping", "equip_unimat_tamper", "REQUIRES", "Mechanized tamping requires UNIMAT machine")
        add_edge("sop_atweld_execution", "equip_atweld_kit", "REQUIRES", "Joint preheating requires air-petrol burner kit")
        add_edge("sop_stmm_bolt_chamfering", "equip_chamfering_kit", "REQUIRES", "Hole chamfering requires 45° chamfering tool")

        # Failure Modes, Hazards & Mitigations
        add_edge("fail_star_crack", "hazard_derailment_split", "CAN_CAUSE", "Bolt hole star crack propagation causes rail break and derailment")
        add_edge("fail_star_crack", "sop_stmm_bolt_chamfering", "MITIGATED_BY", "45° chamfering relieves stress concentration and prevents star cracks")
        add_edge("fail_nose_hitting", "hazard_derailment_split", "CAN_CAUSE", "Flange striking nose can cause wheel climb and derailment")
        add_edge("fail_nose_hitting", "tol_checkrail_clearance", "MITIGATED_BY", "Maintaining check rail clearance 41-45 mm prevents nose collision")
        add_edge("fail_dfwr_weld", "hazard_derailment_split", "CAN_CAUSE", "Unattended DFWR weld fracture can cause sudden rail break under high axle loads")
        add_edge("fail_dfwr_weld", "sop_usfd_atweld_testing", "MITIGATED_BY", "USFD detection and immediate joggled fishplate protection mitigates failure")

        # Cross-Domain Links to Drawing Notes
        add_edge("note_6154_07", "spec_irpwm_para429_lead", "REFERENCES", "Note 7 versines directly align with IRPWM Para 429(4) versine rules", source_dwg="RDSO/T-6154", revision="ALT_06", region="Note 7")
        add_edge("note_6155_21", "spec_irpwm_para429_stretcher", "REFERENCES", "Note 21 tie bar drop directly corresponds to IRPWM Para 429(2)(j) stretcher bar clearance", source_dwg="RDSO/T-6155", revision="ALT_13", region="Note 21")



    # =========================================================================
    # 15. AUTHORITATIVE MANUAL STRUCTURE
    # =========================================================================
    # The Manuals universe is structurally independent from the Drawing universe.
    # Chapters come from the chapter-boundary registry/intermediate extraction,
    # not from semantic/entity extraction.
    chapter_path = os.path.join(REPO_ROOT, "data", "knowledge-graph", "intermediate", "all_chapters_extracted.json")
    if os.path.exists(chapter_path):
        with open(chapter_path, "r", encoding="utf-8") as f:
            chapter_data = json.load(f)

        chapter_coords = {}
        for manual_index, manual in enumerate(chapter_data.get("manuals", [])):
            manual_id = manual.get("document_id")
            if not manual_id:
                continue
            # Ensure the authoritative document exists in this canonical graph.
            if not any(e.get("id") == manual_id for e in entities):
                add_entity(
                    manual_id,
                    manual.get("title", manual_id),
                    "DOCUMENT",
                    "manual",
                    "#ff007f",
                    "Authoritative manual root. Structure is maintained independently from the Drawing KG.",
                    {"Universe": "manuals", "Total Chapters": manual.get("total_chapters", 0)},
                    x=-14 + (manual_index % 3) * 14,
                    y=10,
                    z=(manual_index // 3) * 8,
                    alt=13,
                )

            for ch in sorted(manual.get("chapters", []), key=lambda x: x.get("order", x.get("chapter_number", 0))):
                ch_id = ch.get("chapter_id")
                if not ch_id:
                    continue
                chapter_coords[ch_id] = True
                add_entity(
                    ch_id,
                    f"Chapter {ch.get('chapter_number')} — {ch.get('title', '')}",
                    "CHAPTER",
                    "manual",
                    "#00f5d4",
                    "Authoritative chapter node derived from the manual structure registry.",
                    {
                        "Chapter Number": ch.get("chapter_number"),
                        "Page Range": ch.get("page_range", []),
                        "Structure Status": ch.get("structure_status", "STRUCTURE_VERIFIED"),
                        "Topics": ch.get("topics", []),
                    },
                    x=0,
                    y=8,
                    z=0,
                    alt=13,
                )
                add_edge(
                    manual_id,
                    ch_id,
                    "CONTAINS_CHAPTER",
                    f"Authoritative chapter {ch.get('chapter_number')} in {manual.get('alias', manual_id)}",
                    source_dwg="MANUAL_STRUCTURE",
                    revision=manual.get("pipeline_version", "STRUCTURE"),
                    region=f"Chapter {ch.get('chapter_number')}",
                    crop="",
                    evidence_text=f"Registry chapter boundary: pages {ch.get('page_range', [])}",
                )

    # Authoritative chapter content: clauses extracted from the same chapter registry
    # are materialized as Manual-universe children with explicit provenance. Existing
    # legacy clause entities are enriched in place rather than duplicated.
    existing_entities = {e.get("id"): e for e in entities if e.get("id")}
    for manual in chapter_data.get("manuals", []) if os.path.exists(chapter_path) else []:
        manual_id = manual.get("document_id")
        alias = manual.get("alias", "")
        for ch in manual.get("chapters", []):
            chapter_id = ch.get("chapter_id")
            if not chapter_id:
                continue
            for clause in ch.get("clauses", []) or []:
                clause_id = clause.get("clause_id")
                if not clause_id:
                    continue
                page = clause.get("page_number")
                page_range = ch.get("page_range", [])
                provenance = {
                    "source_document": manual_id,
                    "source_page": page,
                    "source_section": clause.get("ref") or clause.get("title"),
                    "source_text": clause.get("verbatim_text", ""),
                    "confidence": clause.get("confidence"),
                    "extraction_method": clause.get("extraction_method", "deterministic_manual_clause_extraction"),
                    "chapter_id": chapter_id,
                    "chapter_page_range": page_range,
                }
                node = existing_entities.get(clause_id)
                if node is None:
                    node = add_entity(
                        clause_id,
                        clause.get("title", clause_id),
                        clause.get("category", "CLAUSE"),
                        "manual",
                        "#00f5d4",
                        clause.get("verbatim_text", clause.get("desc", ""))[:500],
                        {
                            "Manual Ref": clause.get("ref", ""),
                            "Chapter": ch.get("title", ""),
                            "Page": page,
                        },
                        x=0, y=6, z=0, alt=13,
                    )
                    existing_entities[clause_id] = node
                node["domain"] = "manual"
                node["universe"] = "manuals"
                node["provenance"] = provenance
                node["source_document"] = manual_id
                node["source_page"] = page
                node["source_section"] = clause.get("ref") or clause.get("title")
                node["source_text"] = clause.get("verbatim_text", "")
                node["confidence"] = clause.get("confidence")
                node["extraction_method"] = provenance["extraction_method"]
                node["parent_chapter_id"] = chapter_id
                node["specs"] = {**(node.get("specs") or {}), "Page": page, "Chapter": ch.get("title", ""), "Manual": manual_id}
                if not any(e.get("from") == chapter_id and e.get("to") == clause_id and e.get("rel") == "HAS_CLAUSE" for e in edges):
                    add_edge(
                        chapter_id,
                        clause_id,
                        "HAS_CLAUSE",
                        f"Authoritative extracted clause owned by chapter {ch.get('chapter_number')}",
                        source_dwg=manual_id,
                        revision=manual.get("pipeline_version", "STRUCTURE"),
                        region=clause.get("ref", f"Page {page}"),
                        crop="",
                        evidence_text=clause.get("verbatim_text", "")[:500],
                    )

    # Materialize deterministic section/subsection hierarchy from authoritative
    # clause references. These nodes are explicitly derived from numbering, not
    # claimed to be a source TOC until heading-level extraction is available.
    existing_entities = {e.get("id"): e for e in entities if e.get("id")}
    for manual in chapter_data.get("manuals", []) if os.path.exists(chapter_path) else []:
        manual_id = manual.get("document_id")
        alias = manual.get("alias", "")
        for ch in manual.get("chapters", []):
            chapter_id = ch.get("chapter_id")
            if not chapter_id:
                continue
            clauses = ch.get("clauses", []) or []
            section_nodes = {}
            subsection_nodes = {}
            for clause in clauses:
                clause_id = clause.get("clause_id")
                section_ref = clause.get("section_ref")
                subsection_ref = clause.get("subsection_ref")
                if not clause_id or not section_ref:
                    continue
                chapter_token = re.sub(r'[^A-Za-z0-9_]', '_', str(chapter_id))
                section_key = f"SECTION:{alias}:{chapter_token}:SEC_{re.sub(r'[^A-Za-z0-9_]', '_', str(section_ref))}"
                subsection_key = f"SUBSECTION:{alias}:{chapter_token}:SEC_{re.sub(r'[^A-Za-z0-9_]', '_', str(subsection_ref or section_ref))}"
                page = clause.get("page_number")
                source_section = clause.get("source_section") or clause.get("para_number")
                for node_id, node_type, ref, store in (
                    (section_key, "SECTION", section_ref, section_nodes),
                    (subsection_key, "SUBSECTION", subsection_ref or section_ref, subsection_nodes),
                ):
                    if node_id not in store:
                        node = existing_entities.get(node_id)
                        if node is None:
                            node = add_entity(
                                node_id,
                                f"{node_type.title()} {ref}",
                                node_type,
                                "manual",
                                "#00f5d4",
                                f"Manual content hierarchy node derived from clause numbering ({ref}).",
                                {
                                    "Reference": ref,
                                    "Chapter": ch.get("title", ""),
                                    "Page": page,
                                    "Structure Status": "DERIVED_FROM_CLAUSE_NUMBERING",
                                },
                                x=0, y=7 if node_type == "SECTION" else 6.5, z=0, alt=13,
                            )
                            existing_entities[node_id] = node
                        node.update({
                            "domain": "manual",
                            "universe": "manuals",
                            "source_document": clause.get("source_document") or manual_id,
                            "source_page": clause.get("source_page", page),
                            "source_section": source_section,
                            "source_text": clause.get("source_text", ""),
                            "confidence": clause.get("confidence", 0.95),
                            "extraction_method": clause.get("extraction_method", "deterministic_manual_clause_numbering"),
                            "parent_chapter_id": chapter_id,
                            "provenance": {
                                "source_document": clause.get("source_document") or manual_id,
                                "source_page": clause.get("source_page", page),
                                "source_section": source_section,
                                "source_text": clause.get("source_text", ""),
                                "confidence": clause.get("confidence", 0.95),
                                "extraction_method": clause.get("extraction_method", "deterministic_manual_clause_numbering"),
                                "chapter_id": chapter_id,
                                "chapter_page_range": ch.get("page_range", []),
                            },
                        })
                        store[node_id] = node
                if not any(e.get("from") == chapter_id and e.get("to") == section_key and e.get("rel") == "HAS_SECTION" for e in edges):
                    add_edge(chapter_id, section_key, "HAS_SECTION",
                             f"Derived section {section_ref} owned by chapter {ch.get('chapter_number')}",
                             source_dwg=manual_id, revision=manual.get("pipeline_version", "STRUCTURE"),
                             region=str(source_section), crop="", evidence_text=clause.get("source_text", "")[:500])
                if not any(e.get("from") == section_key and e.get("to") == subsection_key and e.get("rel") == "HAS_SECTION" for e in edges):
                    add_edge(section_key, subsection_key, "HAS_SECTION",
                             f"Derived subsection {subsection_ref or section_ref}",
                             source_dwg=manual_id, revision=manual.get("pipeline_version", "STRUCTURE"),
                             region=str(source_section), crop="", evidence_text=clause.get("source_text", "")[:500])
                if not any(e.get("from") == subsection_key and e.get("to") == clause_id and e.get("rel") == "HAS_CLAUSE" for e in edges):
                    add_edge(subsection_key, clause_id, "HAS_CLAUSE",
                             f"Clause {clause.get('para_number', '')} belongs to derived subsection {subsection_ref or section_ref}",
                             source_dwg=manual_id, revision=manual.get("pipeline_version", "STRUCTURE"),
                             region=str(source_section), crop="", evidence_text=clause.get("source_text", "")[:500])

    # Materialize authoritative source-derived Tables, Figures and Evidence.
    # These are direct Chapter children by default; no semantic parent inference is
    # performed here. Each node carries source-level provenance and a stable ID from
    # the deterministic extraction stage.
    existing_entities = {e.get("id"): e for e in entities if e.get("id")}
    for manual in chapter_data.get("manuals", []) if os.path.exists(chapter_path) else []:
        manual_id = manual.get("document_id")
        for ch in manual.get("chapters", []):
            chapter_id = ch.get("chapter_id")
            if not chapter_id:
                continue
            page_range = ch.get("page_range", [])
            for key, node_type, rel in (("tables", "TABLE", "HAS_TABLE"), ("figures", "FIGURE", "HAS_FIGURE"), ("evidence", "EVIDENCE", "HAS_EVIDENCE")):
                for artifact in ch.get(key, []) or []:
                    artifact_id = artifact.get("id")
                    if not artifact_id:
                        continue
                    page = artifact.get("source_page", artifact.get("page_number"))
                    node = existing_entities.get(artifact_id)
                    if node is None:
                        node = add_entity(
                            artifact_id,
                            artifact.get("title", artifact_id),
                            node_type,
                            "manual",
                            "#00f5d4",
                            artifact.get("source_text", "")[:500],
                            {
                                "Page": page,
                                "Chapter": ch.get("title", ""),
                                "Manual": manual_id,
                                "PageRange": page_range,
                            },
                            x=0, y=6, z=0, alt=13,
                        )
                        existing_entities[artifact_id] = node
                    source_section = artifact.get("source_section") or artifact.get("title")
                    source_text = artifact.get("source_text", "")
                    extraction_method = artifact.get("extraction_method", "deterministic_explicit_source_label")
                    confidence = artifact.get("confidence", 0.90)
                    provenance = {
                        "source_document": manual_id,
                        "source_page": page,
                        "source_section": source_section,
                        "source_text": source_text,
                        "confidence": confidence,
                        "extraction_method": extraction_method,
                        "chapter_id": chapter_id,
                        "chapter_page_range": page_range,
                    }
                    node.update({
                        "domain": "manual",
                        "universe": "manuals",
                        "source_document": manual_id,
                        "source_page": page,
                        "source_section": source_section,
                        "source_text": source_text,
                        "confidence": confidence,
                        "extraction_method": extraction_method,
                        "parent_chapter_id": chapter_id,
                        "provenance": provenance,
                    })
                    node["specs"] = {**(node.get("specs") or {}), "Page": page, "Chapter": ch.get("title", ""), "Manual": manual_id}
                    if not any(e.get("from") == chapter_id and e.get("to") == artifact_id and e.get("rel") == rel for e in edges):
                        add_edge(
                            chapter_id,
                            artifact_id,
                            rel,
                            f"Authoritative extracted {node_type.lower()} owned by chapter {ch.get('chapter_number')}",
                            source_dwg=manual_id,
                            revision=manual.get("pipeline_version", "STRUCTURE"),
                            region=str(source_section),
                            crop="",
                            evidence_text=source_text[:500],
                        )

    # Enrich Section/Subsection nodes with authoritative source headings when a\n    # conservative numbered heading was extracted. Numbering-derived structure remains\n    # the fallback; heading evidence never changes chapter ownership.\n    existing_entities = {e.get("id"): e for e in entities if e.get("id")}\n    for manual in chapter_data.get("manuals", []) if os.path.exists(chapter_path) else []:\n        manual_id = manual.get("document_id")\n        alias = manual.get("alias", "")\n        for ch in manual.get("chapters", []):\n            chapter_id = ch.get("chapter_id")\n            headings = ch.get("headings", []) or []\n            for heading in headings:\n                ref = heading.get("reference")\n                if not ref:\n                    continue\n                chapter_token = re.sub(r'[^A-Za-z0-9_]', '_', str(chapter_id))\n                parts = ref.split('.')\n                section_ref = parts[0]\n                subsection_ref = '.'.join(parts[:2]) if len(parts) >= 2 else section_ref\n                section_id = f"SECTION:{alias}:{chapter_token}:SEC_{re.sub(r'[^A-Za-z0-9_]', '_', section_ref)}"\n                subsection_id = f"SUBSECTION:{alias}:{chapter_token}:SEC_{re.sub(r'[^A-Za-z0-9_]', '_', subsection_ref)}"\n                for node_id, node_type, node_ref in ((section_id, "SECTION", section_ref), (subsection_id, "SUBSECTION", subsection_ref)):\n                    node = existing_entities.get(node_id)\n                    if not node:\n                        continue\n                    if node.get("extraction_method") == "deterministic_manual_clause_numbering" or not node.get("source_heading"):\n                        node["source_heading"] = heading.get("title", "")\n                        node["source_heading_reference"] = ref\n                        node["source_heading_page"] = heading.get("source_page")\n                        node["source_heading_text"] = heading.get("source_text", "")\n                        node["heading_confidence"] = heading.get("confidence", 0.92)\n                        node["heading_extraction_method"] = heading.get("extraction_method", "deterministic_numbered_source_heading")\n                        node["label"] = f"{node_type.title()} {node_ref} — {heading.get('title', '')}"\n                        node["provenance"] = {\n                            **(node.get("provenance") or {}),\n                            "source_heading": heading.get("title", ""),\n                            "source_heading_reference": ref,\n                            "source_heading_page": heading.get("source_page"),\n                            "source_heading_text": heading.get("source_text", ""),\n                            "heading_confidence": heading.get("confidence", 0.92),\n                            "heading_extraction_method": heading.get("extraction_method", "deterministic_numbered_source_heading"),\n                        }\n\n    # Resolve valid source-heading hierarchy as part of the normal publication
    # pipeline. Invalid chapters retain the deterministic clause-derived fallback;
    # the resolver never creates cross-universe relationships.
    if os.path.exists(chapter_path):
        canonical_preview = {"entities": entities, "edges": edges, "facts": facts, "metadata": {}}
        canonical_preview, hierarchy_errors = resolve_canonical_graph(
            chapter_data, canonical_preview
        )
        entities = canonical_preview["entities"]
        edges = canonical_preview["edges"]
        facts = canonical_preview["facts"]
        if hierarchy_errors:
            print(f"[WARN] Manual source-heading hierarchy issues: {len(hierarchy_errors)}")
            for error in hierarchy_errors[:20]:
                print(f"  - {error}")

    # Hard isolation gate: no canonical edge may cross between the Manuals and
    # Drawing universes. Future cross-domain relationships belong in a separate
    # relationship layer and must never be inferred here.
    entity_domains = {e["id"]: e.get("domain") for e in entities}
    allowed_manual_domains = {"manual"}
    blocked_cross_domain = []
    kept_edges = []
    kept_facts = []
    edge_to_fact = {}
    for idx, edge in enumerate(edges):
        from_domain = entity_domains.get(edge.get("from"))
        to_domain = entity_domains.get(edge.get("to"))
        if {from_domain, to_domain} == {"manual", "drawing"} or (
            from_domain in allowed_manual_domains and to_domain not in allowed_manual_domains
        ) or (
            to_domain in allowed_manual_domains and from_domain not in allowed_manual_domains
        ):
            blocked_cross_domain.append(edge)
            continue
        kept_edges.append(edge)
    allowed_edge_keys = {(e.get("from"), e.get("to"), e.get("rel"), e.get("rationale", "")) for e in kept_edges}
    for fact in facts:
        key = (
            fact.get("subject_id"),
            fact.get("object_id"),
            fact.get("predicate"),
            fact.get("evidence_text", ""),
        )
        # Facts are retained only when their endpoints remain in the isolated graph.
        if fact.get("subject_id") in entity_domains and fact.get("object_id") in entity_domains:
            sd = entity_domains.get(fact.get("subject_id"))
            od = entity_domains.get(fact.get("object_id"))
            if (sd == "manual") != (od == "manual") and ("manual" in {sd, od}):
                continue
            kept_facts.append(fact)
    edges = kept_edges
    facts = kept_facts

    if blocked_cross_domain:
        print(f"[INFO] Removed {len(blocked_cross_domain)} cross-universe manual/drawing edges from canonical KG.")


    # Final payload
    canonical_data = {
        "metadata": {
            "title": "RDSO Railway Track Canonical Knowledge Core",
            "version": "1.0.0",
            "standard_specification": "IRS: T 10 & IRS: T 29",
            "blueprint_reference": "docs/RDSO_Knowledge_Graph_Improvement_Blueprint.md",
            "total_entities": len(entities),
            "total_edges": len(edges),
            "total_facts": len(facts)
        },
        "entities": entities,
        "edges": edges,
        "facts": facts
    }

    output_path = os.path.join(REPO_ROOT, "data", "rdso_canonical_kg.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(canonical_data, f, indent=2)

    print(f"[+] Successfully generated Canonical Knowledge Core: {output_path}")
    print(f"    - Total Entities: {len(entities)}")
    print(f"    - Total Typed Edges: {len(edges)}")
    print(f"    - Total Source Facts: {len(facts)}")

if __name__ == "__main__":
    build_canonical_knowledge_graph()
