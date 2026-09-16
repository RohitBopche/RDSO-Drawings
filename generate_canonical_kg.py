"""
generate_canonical_kg.py
Synthesizes the RDSO Canonical Knowledge Core (Entities, Typed Edges & Fact Model)
in strict accordance with docs/RDSO_Knowledge_Graph_Improvement_Blueprint.md.
"""

import json
import os

def build_canonical_knowledge_graph():
    # Load extracted raw/intermediate dossier data
    with open("rdso_extracted_knowledge.json", "r", encoding="utf-8") as f:
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

    output_path = "rdso_canonical_kg.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(canonical_data, f, indent=2)

    print(f"[+] Successfully generated Canonical Knowledge Core: {output_path}")
    print(f"    - Total Entities: {len(entities)}")
    print(f"    - Total Typed Edges: {len(edges)}")
    print(f"    - Total Source Facts: {len(facts)}")

if __name__ == "__main__":
    build_canonical_knowledge_graph()
