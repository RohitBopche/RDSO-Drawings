"""
ingest_all_manual_chapters.py
==============================
Deep Chapter-by-Chapter Manuals Knowledge Extraction Pipeline.
Extracts every chapter across all 6 official Indian Railways manuals:
- IRPWM 2024 (ACS 1-14) (15 Chapters)
- USFD Manual 2026 (14 Chapters + Annexures)
- AT Weld Manual 2022 (8 Sections + Annexures)
- FBW Manual 2022 (8 Sections + Annexures)
- Track Machine Manual 2020 (12 Chapters)
- STMM 2024 (23 Chapters + Table-I)

Outputs: data/knowledge-graph/intermediate/all_chapters_extracted.json
"""

import json
import os
import re
import sys
import hashlib
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

EXTRACTED_PAGES_PATH = 'data/knowledge-graph/raw/extracted_pages.jsonl'
OUTPUT_DIR = 'data/knowledge-graph/intermediate'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'all_chapters_extracted.json')

# Authoritative Chapter Boundary Registry
MANUAL_CHAPTER_REGISTRY = {
    'DOC:IRPWM:2024:ACS14': {
        'alias': 'IRPWM',
        'title': 'Indian Railways Permanent Way Manual 2024 (ACS 1-14)',
        'chapters': [
            {'num': 1, 'title': 'Duties of Permanent Way Officials', 'page_start': 31, 'page_end': 60,
             'topics': ['ADEN', 'SSE/P.Way (In-charge)', 'JE/SSE (Sectional)', 'Gangmate', 'Keyman', 'Patrolman', 'Inspection Schedules']},
            {'num': 2, 'title': 'Track Structure and Components', 'page_start': 61, 'page_end': 86,
             'topics': ['Rails 60kg/52kg', 'PSC Sleepers', 'Fastenings ERC', 'Ballast Cushion 250-350mm', 'Formation', 'Glued Joints', 'SEJs', 'Bridges']},
            {'num': 3, 'title': 'Installation and Maintenance of Welded Rails', 'page_start': 87, 'page_end': 174,
             'topics': ['SWR', 'LWR/CWR', 'Destressing', 'Temperature Zones I-IV', 'Rail Tensors', 'Hot/Cold Weather Patrolling', 'Buckling Safety']},
            {'num': 4, 'title': 'Curves & Turnouts (Part A: Curves, Part B: Points & Crossings)', 'page_start': 175, 'page_end': 292,
             'topics': ['Curves Cant & Versines', 'Turnouts 1:8.5 & 1:12', 'Curved Switches', 'CMS Crossings', 'Check Rail Clearance 41-45mm', 'Throw 115±3mm', 'Paras 428-435']},
            {'num': 5, 'title': 'Track Monitoring & Tolerances', 'page_start': 293, 'page_end': 306,
             'topics': ['OMS-2000', 'TRC Recording', 'TQI Quality Index', 'Track Geometry Limits', 'Urgent Maintenance & Service Tolerances']},
            {'num': 6, 'title': 'Maintenance of Permanent Way', 'page_start': 307, 'page_end': 370,
             'topics': ['Systematic Overhauling', 'Deep Screening', 'Mechanized Tamping', 'Ballast Regulating', 'Rail Lubrication', 'Track Drainage']},
            {'num': 7, 'title': 'Permanent Way Renewals', 'page_start': 371, 'page_end': 390,
             'topics': ['Through Rail Renewal (TRR)', 'Through Sleeper Renewal (TSR)', 'Turnout Renewal (TTR)', 'Casual Renewals', 'Scrap Disposal']},
            {'num': 8, 'title': 'Engineering Restrictions, Indicators & Working of Trolleys', 'page_start': 391, 'page_end': 426,
             'topics': ['Caution Orders', 'Speed Indicators', 'Detonators', 'Emergency Protection', 'Motor Trolleys & Lorries']},
            {'num': 9, 'title': 'Level Crossings and Gateman', 'page_start': 427, 'page_end': 456,
             'topics': ['Special/A/B/C Classification', 'Manning & Equipment', 'Check Rail Clearance 51-57mm', 'Interlocking', 'Census']},
            {'num': 10, 'title': 'Patrolling of the Railway Line', 'page_start': 457, 'page_end': 468,
             'topics': ['Keyman Patrol', 'Monsoon Patrolling', 'Hot Weather Patrolling', 'Cold Weather Patrolling', 'Security Patrolling']},
            {'num': 11, 'title': 'Action During Accidents, Breaches & Pre-Monsoon Precautionary Measures', 'page_start': 469, 'page_end': 504,
             'topics': ['Derailment Investigation', 'Track Parameter Proforma A-H', 'Clue Preservation', 'Breach Restoration']},
            {'num': 12, 'title': 'CRS Sanction for Works Affecting Passenger Running Lines', 'page_start': 505, 'page_end': 514,
             'topics': ['Commissioner of Railway Safety Sanction', 'Opening New Lines', 'New Rolling Stock', 'Yard Remodelling']},
            {'num': 13, 'title': 'Track Management System (TMS)', 'page_start': 515, 'page_end': 518,
             'topics': ['WebTMS Digital Protocols', 'Inspection Entry', 'Defect Tracking', 'Gang Diary']},
            {'num': 14, 'title': 'Training, Competency & References', 'page_start': 519, 'page_end': 526,
             'topics': ['Induction Training', 'Refresher Courses', 'Competency Certificates']},
            {'num': 15, 'title': 'Emerging Track Technology Items', 'page_start': 527, 'page_end': 530,
             'topics': ['Rail Grinding (RGM/SRGM)', 'High-Speed Recording', 'Mobile Flash Butt Welding', 'Digital Asset Twins']}
        ]
    },
    'DOC:USFD:2026:ACS4': {
        'alias': 'USFD',
        'title': 'Manual for Ultrasonic Testing of Rails and Welds 2026 (ACS 1-4)',
        'chapters': [
            {'num': 1, 'title': 'Rail Defects and Their Codification', 'page_start': 13, 'page_end': 19,
             'topics': ['Defect Codification 100/200/300/400', 'Transverse Fissures 111/211', 'Horizontal Splits', 'Bolt Hole Cracks']},
            {'num': 2, 'title': 'Yardsticks for USFD Testing', 'page_start': 20, 'page_end': 20,
             'topics': ['GMT Testing Intervals', '8 GMT / 10 GMT / 12 GMT Periodicities']},
            {'num': 3, 'title': 'Ultrasonic Rail Testing Equipment and Accessories', 'page_start': 21, 'page_end': 23,
             'topics': ['Single Rail Tester (SRT)', 'Double Rail Tester (DRT)', 'SPURT Car', 'Probe Array']},
            {'num': 4, 'title': 'Calibration, Sensitivity Setting & Functions of Probes', 'page_start': 24, 'page_end': 31,
             'topics': ['0° Normal Probe', '70° Flaw Detector Probes', '37° Probes', 'Standard Calibration Piece', 'Gain Setting']},
            {'num': 5, 'title': 'Procedure to be Followed by USFD Operators for Undertaking Testing', 'page_start': 32, 'page_end': 33,
             'topics': ['Field Scanning Discipline', 'Walking Speed ≤ 2-3 km/h', 'Daily Calibration']},
            {'num': 6, 'title': 'Flaw Classification & Need Based Periodic Testing', 'page_start': 34, 'page_end': 37,
             'topics': ['IMR/IMRW Urgent Actions', 'OBS/OBSW Observation', 'Emergency Joggled Clamping', 'Speed Restrictions']},
            {'num': 7, 'title': 'Limitations of Ultrasonic Flaw Detection & Personnel Responsibilities', 'page_start': 38, 'page_end': 40,
             'topics': ['Blind Zones', 'Operator Responsibilities', 'JE/SSE USFD Supervision', 'ADEN Test Checks']},
            {'num': 8, 'title': 'Procedure for Ultrasonic Testing of Alumino-Thermic (AT) Welds', 'page_start': 41, 'page_end': 53,
             'topics': ['0° 2MHz Head & Web', '70° 2MHz Fusion Zone', '45° Tandem Web & Foot', 'DFWN/DFWO/DFWR Classifications']},
            {'num': 9, 'title': 'Ultrasonic Testing of Flash Butt and Gas Pressure Welds', 'page_start': 54, 'page_end': 56,
             'topics': ['FBW Testing Technique', 'Acceptance Standards', 'Flaw Assessment']},
            {'num': 10, 'title': 'Ultrasonic Testing of Rails Required for Fabrication of Points & Crossings', 'page_start': 57, 'page_end': 59,
             'topics': ['Fabrication Testing Criteria', 'Flaw-free Certification for Switches & CMS']},
            {'num': 11, 'title': 'Ultrasonic Testing Technique of Worn Out Point and Splice Rails Before Reconditioning', 'page_start': 60, 'page_end': 66,
             'topics': ['3-Zone Scanning (Zone 1 Tongue, Zone 2 Lead, Zone 3 Crossing)', 'Resurfacing Salvage Limits']},
            {'num': 12, 'title': 'Ultrasonic Testing of Rails by SPURT Car', 'page_start': 67, 'page_end': 67,
             'topics': ['High-Speed Ultrasonic Vehicle', 'Real-time B-Scan Recording']},
            {'num': 13, 'title': 'Reporting and Analysis of Rail/Weld Failures', 'page_start': 68, 'page_end': 69,
             'topics': ['Failure Proformas Annexure III/IV', 'Sample Preservation 150mm', 'RDSO M&C Directorate Analysis']},
            {'num': 14, 'title': 'Phased Array Ultrasonic Testing (PAUT) of Rails and Welds', 'page_start': 70, 'page_end': 70,
             'topics': ['Multi-element PAUT', 'Sectorial S-Scan', 'High-Resolution Volumetric Imaging']},
            {'num': 15, 'title': 'Annexures & Flaw Classification Tables (Annexure I to VIII)', 'page_start': 71, 'page_end': 157,
             'topics': ['Annexure II-A Rail Flaws', 'Annexure II-B Weld Flaws', 'Calibration Test Pieces', 'Inspection Registers']}
        ]
    },
    'DOC:AT_WELD:2022': {
        'alias': 'AT_WELD',
        'title': 'Manual for Fusion Welding of Rails by Alumino-Thermic Process 2022',
        'chapters': [
            {'num': 1, 'title': 'Scope & General Requirements', 'page_start': 7, 'page_end': 7,
             'topics': ['Applicability 52kg/60kg', '90 UTS/110 UTS/Cr-Mo Metallurgy']},
            {'num': 2, 'title': 'Selection and Suitability of Rails for Welding', 'page_start': 7, 'page_end': 7,
             'topics': ['End Straightness', 'Removal of Bolt Holes', 'Fishplate Wear Limits']},
            {'num': 3, 'title': 'Welding Technique, Consumables & Equipment', 'page_start': 8, 'page_end': 9,
             'topics': ['Portion Storage (Dry/Moisture-proof)', 'Crucible Magnesite Lining', 'Thimble', 'Ignition Match']},
            {'num': 4, 'title': 'Execution of Joints at Site', 'page_start': 10, 'page_end': 14,
             'topics': ['Rail Gap 25±1mm', 'Preheating to 1000±20°C', 'CAP / Compressed Air-LPG', 'Pouring & Solidification 4-6 min']},
            {'num': 5, 'title': 'Operations Subsequent to Welding (Demoulding & Trimming)', 'page_start': 15, 'page_end': 16,
             'topics': ['Hydraulic Weld Trimmer', 'No Hammering', 'Wedge Clearance', 'Initial Chipping']},
            {'num': 6, 'title': 'Final Operations, Repacking & Traffic Passage', 'page_start': 17, 'page_end': 20,
             'topics': ['Cooling Time 30 min before Traffic', '5-Sleeper Immediate Repacking', 'Rough Grinding']},
            {'num': 7, 'title': 'Finishing Tolerances (Tables 1 & 2)', 'page_start': 21, 'page_end': 22,
             'topics': ['1m Straight Edge Vertical +0.5/-0mm', '1m Straight Edge Lateral ±0.5mm', '10cm Straight Edge Tolerances']},
            {'num': 8, 'title': 'Testing, Acceptance, Warranty & Defect Marking', 'page_start': 23, 'page_end': 25,
             'topics': ['USFD Acceptance Testing within 48h', 'Hardness Traverse HAZ', 'Warranty Replacement']},
            {'num': 9, 'title': 'Annexures & Inspection Proformas (Annexure 1 to 10)', 'page_start': 26, 'page_end': 49,
             'topics': ['Welder Competency Certification', 'Weld Register Proforma', 'Check List for AT Welds']}
        ]
    },
    'DOC:FBW:2022:CS5': {
        'alias': 'FBW',
        'title': 'Flash Butt Welding Manual 2022 (with Correction Slips 1-5)',
        'chapters': [
            {'num': 1, 'title': 'Scope & General Principles', 'page_start': 4, 'page_end': 4,
             'topics': ['Stationary Flash Butt Plants', 'Mobile Flash Butt Welders (MFBW)']},
            {'num': 2, 'title': 'Selection & Suitability of Rails', 'page_start': 4, 'page_end': 4,
             'topics': ['End Squareness', 'End Crop 150mm', 'Ultrasonic Clearance']},
            {'num': 3, 'title': 'Preparation of Rails to be Welded', 'page_start': 5, 'page_end': 6,
             'topics': ['Electrode Contact Area Cleaning', 'Rust & Scale Removal']},
            {'num': 4, 'title': 'Welding Procedure & Parameters', 'page_start': 7, 'page_end': 8,
             'topics': ['Preheating Impulses', 'Flashing Speed', 'Upset Force 35-50t', 'Clamping Force 100-120t', 'Automatic Stripping']},
            {'num': 5, 'title': 'Post-Weld Heat Treatment (PWHT)', 'page_start': 9, 'page_end': 13,
             'topics': ['Controlled Cooling', 'PWHT for 110 UTS and Head Hardened (HH) Rails']},
            {'num': 6, 'title': 'Finishing Tolerances', 'page_start': 14, 'page_end': 15,
             'topics': ['1m Straight Edge Vertical +0.3/-0mm', '1m Straight Edge Lateral ±0.3mm']},
            {'num': 7, 'title': 'Quality Control, Testing & Acceptance (Bend Test)', 'page_start': 16, 'page_end': 19,
             'topics': ['Transverse Deflection Bend Test min 25-35mm', 'Macro/Micro Metallurgical Examination', 'Hardness Profile']},
            {'num': 8, 'title': 'Marking, Records & Quality Assurance', 'page_start': 20, 'page_end': 24,
             'topics': ['Joint Numbering Code', 'Flash Butt Register', 'Welding Team Specs']},
            {'num': 9, 'title': 'Annexures & Specifications (Annexure 1 to 12)', 'page_start': 25, 'page_end': 69,
             'topics': ['QAP Guidelines', 'Plant Commissioning Standards', 'Deflection Test Machine Specs']}
        ]
    },
    'DOC:TMM:2020:ACS10': {
        'alias': 'TMM',
        'title': 'Indian Railways Track Machine Manual 2020 (ACS 1-10)',
        'chapters': [
            {'num': 1, 'title': 'Organisational Structure, Duties and Inspections', 'page_start': 24, 'page_end': 41,
             'topics': ['Role of TMO', 'Zonal HQ Organisation', 'Field Organisation', 'CPOH Workshops', 'Duties of XEN/AXEN/SSE/JE TM']},
            {'num': 2, 'title': 'Tamping Machines & Dynamic Track Stabilizer (DTS)', 'page_start': 42, 'page_end': 120,
             'topics': ['Plain Track Tampers (CSM 08-32, 3X)', 'Points & Crossings Tampers (UNIMAT 08-475, 4S)', 'Squeezing Pressure 110-120 bar', 'DTS Stabilization Modes']},
            {'num': 3, 'title': 'Ballast Cleaning and Handling Machines', 'page_start': 121, 'page_end': 155,
             'topics': ['Ballast Cleaning Machine (BCM)', 'Shoulder BCM (SBCM)', 'Turnout BCM (TBC)', 'Cutter Bar Depth', 'Screening Mesh']},
            {'num': 4, 'title': 'Track Relaying Machines', 'page_start': 156, 'page_end': 181,
             'topics': ['Plasser Quick Relaying System (PQRS)', 'Track Relaying Train (TRT)', 'AMECA T-28 Turnout Relayer', 'Portal Cranes']},
            {'num': 5, 'title': 'Special Purpose Track Machines', 'page_start': 182, 'page_end': 259,
             'topics': ['Rail Grinding Machines (RGM 72/96-Stone)', 'Switch Rail Grinding Machine (SRGM)', 'Ballast Regulating Machine (BRM)', 'Mobile Flash Butt Welder']},
            {'num': 6, 'title': 'Planning and Deployment of Track Machines', 'page_start': 260, 'page_end': 266,
             'topics': ['Annual Machine Planning', 'Traffic Block Protocols', 'Integrated Corridor Blocks']},
            {'num': 7, 'title': 'Rules for Movement and Block Working', 'page_start': 267, 'page_end': 318,
             'topics': ['Block Protection', 'Track Infringement Precautions', 'Operating Speeds', 'Red Hand Signal Lamps', 'Stabling Rules']},
            {'num': 8, 'title': 'Periodical Maintenance and Associated Infrastructural Facilities', 'page_start': 319, 'page_end': 363,
             'topics': ['Maintenance Schedules (Daily, 50h, 100h, 250h, 500h, 1000h)', 'Intermediate Overhaul (IOH)', 'Periodical Overhaul (POH) at CPOH']},
            {'num': 9, 'title': 'Manpower and Training', 'page_start': 364, 'page_end': 374,
             'topics': ['Staffing Yardsticks', 'IRICEN/IRITM Training', 'Machine Operator Certification']},
            {'num': 10, 'title': 'Stores and Contracts', 'page_start': 375, 'page_end': 383,
             'topics': ['Spares Provisioning', 'Annual Maintenance Contracts (AMC)', 'OEM Spares Procurement']},
            {'num': 11, 'title': 'Monitoring of Track Machines', 'page_start': 384, 'page_end': 399,
             'topics': ['TMS Machine Module', 'Performance Evaluation', 'Machine Availability & Utilization Metrics']},
            {'num': 12, 'title': 'Track Machine Engines', 'page_start': 400, 'page_end': 458,
             'topics': ['Diesel Engine Operation', 'Hydraulic Transmission', 'Pneumatic Systems', 'Electrical Circuit Diagnostics']}
        ]
    },
    'DOC:STMM:2024': {
        'alias': 'STMM',
        'title': 'Small Track Machines Manual 2024',
        'chapters': [
            {'num': 1, 'title': 'Organizational Structure, Duties and Inspections & Yardsticks (Table-I)', 'page_start': 1, 'page_end': 29,
             'topics': ['Table-I Yardsticks of Small Track Machines', 'Duties of ADEN, SSE/P.Way In-Charge', 'Depot Organisation']},
            {'num': 2, 'title': 'Abrasive Rail Cutter (ARC) & Rail Cutting Wheels', 'page_start': 30, 'page_end': 41,
             'topics': ['Power Disc Cutter', 'Cutting Time < 3 min', 'Squareness Tolerance ±0.5mm', 'Abrasive Disc Safety']},
            {'num': 3, 'title': 'Rail Drilling Machine (RDM - Engine & Battery Operated)', 'page_start': 42, 'page_end': 56,
             'topics': ['Engine & Battery Drills', 'Drilling Time < 3-4 min', 'Hole Tolerance ±0.5mm']},
            {'num': 4, 'title': 'Compressed Air Petrol Preheating Machine (CAP)', 'page_start': 57, 'page_end': 65,
             'topics': ['Preheating for AT Welds', 'Burner Nozzle Alignment', 'Pressure 0.2-0.3 kg/cm²']},
            {'num': 5, 'title': 'Weld Trimmer (Power Pack Version) for AT Welding', 'page_start': 66, 'page_end': 76,
             'topics': ['Hydraulic Power Pack Trimmer', 'Trimming Shear Blades', 'Clearance 0.5-1.5mm']},
            {'num': 6, 'title': 'Rail Profile Weld Grinder (RPWG)', 'page_start': 77, 'page_end': 82,
             'topics': ['Weld Head Grinding', 'CMS Crossing Flange Grinding', 'Profile Matching Template']},
            {'num': 7, 'title': 'Generators (Portable AC & DC Welding Generator)', 'page_start': 83, 'page_end': 98,
             'topics': ['Site Lighting Generator', 'DC Welding for Rail Joint & Crossing Resurfacing']},
            {'num': 8, 'title': 'Hydraulic Track Jack (Non-Infringing Type)', 'page_start': 99, 'page_end': 105,
             'topics': ['10t / 15t Non-infringing Track Jack', 'Lifting Capacity', 'Tripod Mechanism']},
            {'num': 9, 'title': 'Hydraulic Rail Tensor (Non-Infringing Type 70t)', 'page_start': 106, 'page_end': 111,
             'topics': ['70 Tonne Rail Tensor', 'Stroke 300mm', 'Destressing Operations', 'Clamping Wedge Safety']},
            {'num': 10, 'title': 'Toe Load Measuring Devices (Mechanical MTLMD & Electronic ETLMD)', 'page_start': 112, 'page_end': 119,
             'topics': ['ERC Toe Load Testing (850-1040 kg)', 'Measurement Accuracy ±1%', 'Sampling Yardsticks']},
            {'num': 11, 'title': 'Light Weight Rail (Mono) cum Road Trolley', 'page_start': 120, 'page_end': 123,
             'topics': ['Material Transportation', 'Non-infringing Quick Detachment']},
            {'num': 12, 'title': 'Self-Propelled Light Weight Trolley', 'page_start': 124, 'page_end': 129,
             'topics': ['Inspection Trolley', 'Speed Limit 15 km/h', 'Deadman Handle']},
            {'num': 13, 'title': 'Powered Material Trolley', 'page_start': 130, 'page_end': 135,
             'topics': ['Heavy Tool Hauling', 'Payload Capacity 1-2 Tonnes']},
            {'num': 14, 'title': 'Box Type Gauge cum Level (BG) with Spirit Level', 'page_start': 136, 'page_end': 139,
             'topics': ['BG Gauge 1676mm', 'Cant Sensitivity 1mm', 'Calibration on Test Bench']},
            {'num': 15, 'title': 'Bolt Hole Chamfering Kit', 'page_start': 140, 'page_end': 146,
             'topics': ['Hydraulic/Mechanical Chamfering', 'Torque Wrench 500 N-m', 'Work Hardening of Hole Rim']},
            {'num': 16, 'title': 'Electronic Rail Thermometer & Temperature Loggers', 'page_start': 147, 'page_end': 153,
             'topics': ['Magnetic Surface Probe', 'Accuracy ±1°C', 'Continuous Ambient & Rail Temp Logging']},
            {'num': 17, 'title': 'Gang / Worksite Remote Control Hooter', 'page_start': 154, 'page_end': 158,
             'topics': ['Look-out Warning', 'Audible Range 1000m', 'Worker Safety on Approaching Trains']},
            {'num': 18, 'title': 'Hydraulic Track Lifting cum Slewing Device (TRALIS)', 'page_start': 159, 'page_end': 163,
             'topics': ['Track Alignment & Slew', 'Lifting Stroke 100mm', 'Slewing Stroke 150mm']},
            {'num': 19, 'title': 'Track Based Lubricators (Electronic & Hydraulic Types)', 'page_start': 164, 'page_end': 175,
             'topics': ['Gauge Face Lubrication', 'Curve Rail Wear Reduction', 'Sensor Triggering']},
            {'num': 20, 'title': 'Off-Track Portable Tampers', 'page_start': 176, 'page_end': 178,
             'topics': ['Hand-held Tampers for Turnouts & P&C', '4-Tool Power Unit']},
            {'num': 21, 'title': 'Manpower and Training for Small Track Machines', 'page_start': 179, 'page_end': 185,
             'topics': ['Divisional STM Maintenance Staff', 'Technician Certification']},
            {'num': 22, 'title': 'Maintenance Infrastructure & Depots', 'page_start': 186, 'page_end': 192,
             'topics': ['Central STM Depots', 'Zonal Workshop Facilities', 'Testing Test Benches']},
            {'num': 23, 'title': 'Stores and Contracts for STM', 'page_start': 193, 'page_end': 222,
             'topics': ['Spare Parts Inventory', 'Annual Maintenance Contracts (AMC)', 'Procurement Specifications']}
        ]
    }
}

# Regex Matchers for Entities and Facts
TOL_RANGE_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:to|-|±)\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|km/h|°C|bar|tonnes|kg|kN)', re.IGNORECASE)
TOL_SINGLE_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(mm|km/h|°C|bar|tonnes|kg)\s*(?:max|min|nominal|clearance|tolerance)?', re.IGNORECASE)
REQUIREMENT_RE = re.compile(r'([^.?!;\n]*\b(?:shall|must|mandatory|strictly prohibited|prior approval|personal inspection)\b[^.?!;\n]*)', re.IGNORECASE)
ROLE_RE = re.compile(r'\b(ADEN|Sr\.?\s*DEN|DEN|CTE|SSE/?P\.?Way|JE/?P\.?Way|Gangmate|Mate|Keyman|Patrolman|Gateman|USFD Operator|CRS|Signal Staff)\b', re.IGNORECASE)
EQUIP_RE = re.compile(r'\b(UNIMAT|CSM|Duomatic|3X|DTS|BCM|RGM|SRGM|T-28|Abrasive Cutter|Rail Drilling Machine|Chamfering Kit|Rail Tensor|Toe Load Measuring Device|ETLMD|MTLMD|0° Probe|70° Probe|37° Probe|45° Tandem|Straight Edge|Feeler Gauge|Weld Trimmer|Profile Grinder)\b', re.IGNORECASE)
FAIL_RE = re.compile(r'\b(IMR|IMRW|OBS|OBSW|DFWN|DFWO|DFWR|Transverse Fissure|Horizontal Split|Bolt Hole Crack|Squat|Wheel Burn|CMS Wear|Tongue Rail Chipping|Gauge Face Wear)\b', re.IGNORECASE)
COMP_RE = re.compile(r'\b(RDSO/T-6154|RDSO/T-6155|T-6154|T-6155|T-4018|T-4218|T-2496|T-8746|Tongue Rail|Stock Rail|Slide Chair|Check Rail|CMS Crossing|Switch Assembly|Stretcher Bar|Lead Curve|Turnout 1:12|Turnout 1:8\.5)\b', re.IGNORECASE)


def get_chapter_for_page(doc_id, page_num):
    reg = MANUAL_CHAPTER_REGISTRY.get(doc_id)
    if not reg:
        return None
    for ch in reg['chapters']:
        if ch['page_start'] <= page_num <= ch['page_end']:
            return ch
    # Never silently assign out-of-range pages to the first/last chapter.
    # Unmapped pages are handled explicitly by the caller for review.
    return None


def _stable_artifact_id(alias, kind, chapter_num, page_num, ordinal, text):
    digest = hashlib.sha1((text or '').encode('utf-8')).hexdigest()[:8]
    return f"{kind}:{alias}:CH_{chapter_num:02d}:P{page_num:04d}:{ordinal:02d}_{digest}"


def _extract_labeled_blocks(text, patterns):
    """Deterministically extract explicitly labeled source blocks."""
    matches = []
    combined = re.compile("|".join(f"(?:{re.sub(r'\\(\\?m\\)', '', p)})" for p in patterns), re.IGNORECASE | re.MULTILINE)
    found = list(combined.finditer(text or ""))
    for i, match in enumerate(found):
        start = match.start()
        end = found[i + 1].start() if i + 1 < len(found) else len(text or "")
        block = (text or "")[start:end].strip()
        if len(block) < 8:
            continue
        label = match.group(0).strip()
        matches.append((label, block[:2500]))
    return matches


def extract_structural_content(doc_id, chapter_num, page_num, text):
    """Extract only explicitly labeled source artifacts; never infer arbitrary semantic nodes."""
    reg = MANUAL_CHAPTER_REGISTRY.get(doc_id)
    alias = reg['alias'] if reg else 'DOC'
    tables, figures, evidence = [], [], []

    table_patterns = [
        r'^\s*(?:TABLE|Table)\s*(?:[-.:]?\s*)?(?:[A-Z0-9IVX]+(?:[-.][A-Z0-9IVX]+)*)?[^\n]{0,120}$',
        r'^\s*Table[- ]?\d+(?:\s*[-.:\s]\s*[^\n]{0,100})?$',
    ]
    figure_patterns = [
        r'^\s*(?:FIGURE|Figure|Fig\.)\s*(?:[-.:]?\s*)?(?:[A-Z0-9IVX]+(?:[-.][A-Z0-9IVX]+)*)?[^\n]{0,120}$',
    ]
    evidence_patterns = [
        r'^\s*(?:Evidence|EVIDENCE)\s*[:.-]?[^\n]{0,120}$',
        r'^\s*(?:Annexure|ANNEXURE|Appendix|APPENDIX)\s*[A-Z0-9IVX-]*[^\n]{0,120}$',
        r'^\s*(?:Proforma|PROFORMA|Checklist|CHECKLIST|Register|REGISTER)\s*(?:[:.-]?\s*)[^\n]{0,120}$',
    ]

    for kind, patterns, target in (("TABLE", table_patterns, tables), ("FIGURE", figure_patterns, figures), ("EVIDENCE", evidence_patterns, evidence)):
        seen = set()
        for label, block in _extract_labeled_blocks(text, patterns):
            key = (label.lower(), block[:600])
            if key in seen:
                continue
            seen.add(key)
            ordinal = len(target) + 1
            target.append({
                'id': _stable_artifact_id(alias, kind, chapter_num, page_num, ordinal, block),
                'title': label,
                'page_number': page_num,
                'source_document': doc_id,
                'source_page': page_num,
                'source_section': label,
                'source_text': block,
                'confidence': 0.90,
                'extraction_method': 'deterministic_explicit_source_label',
            })
    return {'tables': tables, 'figures': figures, 'evidence': evidence}


def extract_source_headings(doc_id, page_num, text):
    """Extract conservative numbered source headings from page text.

    Only standalone numbered lines are candidates. Requirement-like prose,
    long sentence fragments, and obvious table/figure/page labels are rejected.
    The output is evidence about source structure, not inferred semantic structure.
    """
    headings = []
    pattern = re.compile(
        r"(?m)^\s*(\d+(?:\.\d+){0,2})\.?\s+([A-Z][^\n]{2,140})\s*$"
    )
    reject_terms = {
        "shall", "should", "must", "will", " is ", " are ", " were ",
        " may ", " can ", " required ", " ensure ", " provided ",
    }
    for match in pattern.finditer(text or ""):
        reference = match.group(1).strip()
        title = re.sub(r"\s+", " ", match.group(2).strip()).strip(" .:-")
        if not title:
            continue
        if len(title.split()) > 20:
            continue
        lowered = f" {title.lower()} "
        if any(term in lowered for term in reject_terms):
            continue
        if re.search(r"\b(?:figure|fig\.?|table|page|sketch)\s*[-.:]?\s*\d", lowered):
            continue
        headings.append({
            "reference": reference,
            "title": title,
            "page_number": page_num,
            "source_document": doc_id,
            "source_page": page_num,
            "source_section": reference,
            "source_text": match.group(0).strip(),
            "confidence": 0.92,
            "extraction_method": "deterministic_numbered_source_heading",
        })
    return headings


def normalize_source_heading_candidates(headings):
    """Reduce repeated/paragraph-like numbered candidates to a conservative sequence.

    This is deterministic source-structure filtering. Repeated references are
    suppressed, large plain-integer references are treated as likely page/
    clause-number noise, and backward numeric movement is excluded.
    """
    ordered = []
    seen_refs = set()
    previous = None
    for item in sorted(headings, key=lambda h: (int(h.get("source_page", 0)), h.get("source_text", ""))):
        ref = str(item.get("reference", "")).strip()
        if not ref or ref in seen_refs:
            continue
        parts = ref.split(".")
        if not all(part.isdigit() for part in parts):
            continue
        if len(parts) == 1 and ref.isdigit() and len(ref) >= 3:
            continue
        title = str(item.get("title", "")).strip()
        words = re.findall(r"[A-Za-z]+", title)
        if not words:
            continue
        numeric_ref = tuple(int(part) for part in parts)
        if previous is not None and numeric_ref < previous:
            continue
        seen_refs.add(ref)
        previous = numeric_ref
        ordered.append(item)
    return ordered


def extract_clauses_from_text(doc_id, page_num, text):
    """
    Extracts individual statutory clauses from page text based on numbering schemes.
    """
    clauses = []
    reg = MANUAL_CHAPTER_REGISTRY.get(doc_id)
    alias = reg['alias'] if reg else 'DOC'
    
    # Custom regex patterns per manual
    if doc_id == 'DOC:IRPWM:2024:ACS14':
        pattern = re.compile(r'(?:^|\n)\s*(\d{3,4})\.?\s+([A-Z][^\n\.\(]{3,80})', re.MULTILINE)
    elif doc_id == 'DOC:USFD:2026:ACS4':
        pattern = re.compile(r'(?:^|\n)\s*(\d+\.\d+(?:\.\d+)?)\.?\s+([A-Z][^\n\.\(]{3,80})', re.MULTILINE)
    elif doc_id in ('DOC:AT_WELD:2022', 'DOC:FBW:2022:CS5'):
        pattern = re.compile(r'(?:^|\n)\s*(\d+(?:\.\d+)?)\.?\s+([A-Z][^\n\.\(]{3,80})', re.MULTILINE)
    else: # TMM and STMM
        pattern = re.compile(r'(?:^|\n)\s*(\d{3,4})\.?\s+([A-Z][^\n\.\(]{3,80})', re.MULTILINE)
        
    matches = list(pattern.finditer(text))
    
    for i, m in enumerate(matches):
        para_num = m.group(1).strip()
        # Filter out false positives (e.g. Figure numbers or page numbers)
        if any(bad in m.group(2).upper() for bad in ['FIGURE', 'TABLE', 'PAGE', 'ACS -', 'SKETCH']):
            continue
            
        title = m.group(2).strip()
        start_pos = m.start()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
        clause_body = text[start_pos:end_pos].strip()
        
        # Extract tolerances
        tolerances = []
        for tr in TOL_RANGE_RE.finditer(clause_body):
            tolerances.append({
                'text': tr.group(0),
                'min': float(tr.group(1)),
                'max': float(tr.group(2)),
                'unit': tr.group(3)
            })
        for ts in TOL_SINGLE_RE.finditer(clause_body):
            tolerances.append({
                'text': ts.group(0),
                'value': float(ts.group(1)),
                'unit': ts.group(2)
            })
            
        # Extract requirements
        reqs = [r.strip() for r in REQUIREMENT_RE.findall(clause_body) if len(r.strip()) > 10][:3]
        
        # Roles, Equipment, Failure Modes, Components
        roles = sorted(list(set(ROLE_RE.findall(clause_body))))
        equips = sorted(list(set(EQUIP_RE.findall(clause_body))))
        fails = sorted(list(set(FAIL_RE.findall(clause_body))))
        comps = sorted(list(set(COMP_RE.findall(clause_body))))
        
        # Deterministic Stable ID
        clean_para = re.sub(r'[^A-Za-z0-9_]', '_', para_num)
        clause_id = f"CLAUSE:{alias}:PARA_{clean_para}"
        
        # Summary (first 2 clean sentences)
        sentences = [s.strip() for s in re.split(r'\. |\n', clause_body) if len(s.strip()) > 15]
        summary = ". ".join(sentences[:2]) + ("." if sentences else "")
        if len(summary) > 250:
            summary = summary[:247] + "..."
            
        # Deterministic content hierarchy derived from the clause reference.
        # This is explicitly marked as derived, not treated as an authoritative
        # TOC/heading hierarchy until source headings are ingested.
        section_ref = para_num.split('.')[0].split('(')[0]
        subsection_match = re.match(r'^([^.(]+(?:\\.[^.(]+)?(?:\\([^)]*\\))?)', para_num)
        subsection_ref = subsection_match.group(1) if subsection_match else section_ref

        clauses.append({
            'clause_id': clause_id,
            'para_number': para_num,
            'section_ref': section_ref,
            'subsection_ref': subsection_ref,
            'title': title,
            'page_number': page_num,
            'source_document': doc_id,
            'source_page': page_num,
            'source_section': para_num,
            'source_text': clause_body[:1200],
            'confidence': 0.95,
            'extraction_method': 'deterministic_manual_clause_numbering',
            'summary': summary if summary else title,
            'verbatim_text': clause_body[:1200], # Keep high-fidelity block
            'tolerances': tolerances[:5],
            'requirements': reqs,
            'roles': roles,
            'equipment': equips,
            'failure_modes': fails,
            'related_components': comps
        })
        
    return clauses


def main():
    print("================================================================================")
    print("           DEEP CHAPTER-BY-CHAPTER MANUALS KNOWLEDGE EXTRACTION")
    print("================================================================================")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    manual_data = {doc_id: {
        'document_id': doc_id,
        'alias': meta['alias'],
        'title': meta['title'],
        'chapters': {ch['num']: {
            'chapter_id': f"CHAPTER:{meta['alias']}:CH_{ch['num']:02d}",
            'chapter_number': ch['num'],
            'title': ch['title'],
            'page_range': [ch['page_start'], ch['page_end']],
            'parent_manual_id': doc_id,
            'universe': 'manuals',
            'order': ch['num'],
            'structure_status': 'STRUCTURE_VERIFIED',
            'topics': ch['topics'],
            'headings': [],
            'pages_seen': [],
            'clauses': [],
            'tables': [],
            'figures': [],
            'evidence': [],
            'unmapped_pages': []
        } for ch in meta['chapters']}
    } for doc_id, meta in MANUAL_CHAPTER_REGISTRY.items()}
    
    total_pages_read = 0
    total_clauses_extracted = 0
    pages_by_doc = {}
    unmapped_pages_by_doc = {}
    
    print(f"Reading raw pages from: {EXTRACTED_PAGES_PATH} ...")
    with open(EXTRACTED_PAGES_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            doc_id = data.get('document_id')
            if doc_id not in MANUAL_CHAPTER_REGISTRY:
                continue
                
            total_pages_read += 1
            pages_by_doc[doc_id] = pages_by_doc.get(doc_id, 0) + 1
            pnum = data.get('page_number', 0)
            txt = data.get('text_content', '')
            
            # Identify chapter
            target_ch = get_chapter_for_page(doc_id, pnum)
            if not target_ch:
                # Preserve extraction gaps explicitly; never contaminate a neighboring chapter.
                manual_data[doc_id].setdefault('unmapped_pages', []).append(pnum)
                unmapped_pages_by_doc.setdefault(doc_id, []).append(pnum)
                continue
                
            ch_num = target_ch['num']
            if pnum not in manual_data[doc_id]['chapters'][ch_num]['pages_seen']:
                manual_data[doc_id]['chapters'][ch_num]['pages_seen'].append(pnum)
            
            # Extract source headings, clauses and explicitly labeled source artifacts.
            headings = extract_source_headings(doc_id, pnum, txt)
            manual_data[doc_id]['chapters'][ch_num]['headings'].extend(headings)
            extracted = extract_clauses_from_text(doc_id, pnum, txt)
            if extracted:
                manual_data[doc_id]['chapters'][ch_num]['clauses'].extend(extracted)
                total_clauses_extracted += len(extracted)
            structural = extract_structural_content(doc_id, ch_num, pnum, txt)
            for key in ('tables', 'figures', 'evidence'):
                manual_data[doc_id]['chapters'][ch_num][key].extend(structural[key])

    # Deduplicate source headings and structural artifacts while preserving source order.
    for doc_id, manual in manual_data.items():
        for chapter in manual['chapters'].values():
            seen_headings = set()
            unique_headings = []
            for heading in chapter.get('headings', []):
                key = (heading.get('reference'), heading.get('source_page'), heading.get('title'))
                if key in seen_headings:
                    continue
                seen_headings.add(key)
                unique_headings.append(heading)
            chapter['headings'] = normalize_source_heading_candidates(unique_headings)
            chapter['pages_seen'] = sorted(set(chapter.get('pages_seen', [])))
            chapter['unmapped_pages'] = []
            for key in ('tables', 'figures', 'evidence'):
                seen = set()
                unique = []
                for item in chapter.get(key, []):
                    item_key = item.get('id')
                    if item_key in seen:
                        continue
                    seen.add(item_key)
                    unique.append(item)
                chapter[key] = unique

    # Format structured output
    structured_manuals = []
    total_chapters_count = 0
    
    for doc_id, mdata in manual_data.items():
        ch_list = []
        for ch_num, cinfo in sorted(mdata['chapters'].items()):
            # Deduplicate clauses by clause_id, preserving richest
            seen_clauses = {}
            for cl in cinfo['clauses']:
                cid = cl['clause_id']
                if cid not in seen_clauses or len(cl['verbatim_text']) > len(seen_clauses[cid]['verbatim_text']):
                    seen_clauses[cid] = cl
            cinfo['clauses'] = list(seen_clauses.values())
            for key in ('tables', 'figures', 'evidence'):
                seen_artifacts = {}
                for artifact in cinfo[key]:
                    aid = artifact.get('id')
                    if aid and (aid not in seen_artifacts or len(artifact.get('source_text', '')) > len(seen_artifacts[aid].get('source_text', ''))):
                        seen_artifacts[aid] = artifact
                cinfo[key] = list(seen_artifacts.values())
            ch_list.append(cinfo)
            total_chapters_count += 1
            
        structured_manuals.append({
            'document_id': doc_id,
            'alias': mdata['alias'],
            'title': mdata['title'],
            'universe': 'manuals',
            'total_chapters': len(ch_list),
            'total_clauses': sum(len(c['clauses']) for c in ch_list),
            'total_tables': sum(len(c['tables']) for c in ch_list),
            'total_figures': sum(len(c['figures']) for c in ch_list),
            'total_evidence': sum(len(c['evidence']) for c in ch_list),
            'unmapped_pages': sorted(set(mdata.get('unmapped_pages', []))),
            'chapters': ch_list
        })

    final_payload = {
        'extracted_at': datetime.now().isoformat(),
        'pipeline_version': '4.1.0-deterministic-structural-artifacts',
        'total_manuals': len(structured_manuals),
        'total_chapters': total_chapters_count,
        'total_pages_processed': total_pages_read,
        'total_clauses_extracted': total_clauses_extracted,
        'total_unmapped_pages': sum(len(set(v)) for v in unmapped_pages_by_doc.values()),
        'manuals': structured_manuals
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_payload, f, indent=2, ensure_ascii=False)
        
    print(f"\n[SUCCESS] Extraction Complete!")
    print(f"  Processed Manuals: {len(structured_manuals)}")
    print(f"  Processed Pages:   {total_pages_read}")
    print(f"  Cataloged Chapters: {total_chapters_count}")
    print(f"  Extracted Clauses: {total_clauses_extracted}")
    print(f"  Extracted Tables:   {sum(m['total_tables'] for m in structured_manuals)}")
    print(f"  Extracted Figures:  {sum(m['total_figures'] for m in structured_manuals)}")
    print(f"  Extracted Evidence: {sum(m['total_evidence'] for m in structured_manuals)}")
    print(f"  Saved Payload to:  {OUTPUT_FILE}")
    print("\nBreakdown by Manual:")
    for m in structured_manuals:
        print(f"  - {m['alias']}: {m['total_chapters']} Chapters, {m['total_clauses']} Unique Clauses ({pages_by_doc.get(m['document_id'], 0)} pages), unmapped={len(m.get('unmapped_pages', []))}")
    print("================================================================================")

if __name__ == '__main__':
    main()
