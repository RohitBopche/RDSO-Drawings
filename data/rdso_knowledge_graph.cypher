// ==============================================================================
// RDSO Track Infrastructure Knowledge Graph - Full Turnout & Switch Ecosystem
// Indian Railways Standard Drawings DDL & Semantic Graph Schema
// Focus: RDSO/T-6154, T-6155 (Alt 10-13), T-6216/6217, T-6275, T-6279/6280, T-7075/7076
// ==============================================================================

// 1. Constraints & Indexes
CREATE CONSTRAINT unique_drawing_number IF NOT EXISTS
FOR (d:StandardDrawing) REQUIRE d.drawingNumber IS UNIQUE;

CREATE CONSTRAINT unique_component_part IF NOT EXISTS
FOR (c:TrackComponent) REQUIRE c.partNumber IS UNIQUE;

// 2. Core Drawings
MERGE (l12:StandardDrawing {drawingNumber: "RDSO/T-6154"})
SET l12.title = "Layout of 1 in 12 Turnout B.G. (1673 mm) 60 kg (UIC) on P.S.C. Sleepers",
    l12.turnoutRatio = "1 in 12",
    l12.gaugeMm = 1673,
    l12.totalSleepers = 64,
    l12.speedMainKmph = 160,
    l12.speedLoopKmph = 50,
    l12.curveRadiusMm = 441360;

MERGE (s12:StandardDrawing {drawingNumber: "RDSO/T-6155"})
SET s12.title = "10125 mm Curved Switch with ZU-1-60/60E1A1 Thick-Web Tongue Rails for 1 in 12 Turnout",
    s12.railSection = "60 kg (UIC) / 60E1",
    s12.switchLengthMm = 10125,
    s12.throwAtToeMm = 160,
    s12.heelDivergenceMm = 175;

MERGE (bom12:StandardDrawing {drawingNumber: "RDSO/T-6155/1"})
SET bom12.title = "Particulars of Components for 10125 mm Curved Switch (ZU-1-60 Thick Web) on PSC Sleepers";

MERGE (ssd:StandardDrawing {drawingNumber: "RDSO/T-6216"})
SET ssd.title = "Spring Setting Device for Thick Web Switches on P.S.C. Sleepers (Assembly)",
    ssd.sleeperLocation = 13,
    ssd.clearanceAtJOHMm = 60;

MERGE (ssdParts:StandardDrawing {drawingNumber: "RDSO/T-6217"})
SET ssdParts.title = "Component Parts of Spring Setting Device (Items 1 to 39)";

MERGE (chk:StandardDrawing {drawingNumber: "RDSO/T-6275"})
SET chk.title = "Check Rail Arrangement and Chairs for 1 in 12 CMS Crossing 60 kg on PSC Sleepers",
    chk.lengthMm = 5000,
    chk.clearanceMinMm = 41,
    chk.clearanceMaxMm = 45,
    chk.flareOpeningMm = 89;

MERGE (cmsFab:StandardDrawing {drawingNumber: "RDSO/T-6279"})
SET cmsFab.title = "1 in 12 Cast Manganese Steel (CMS) Crossing 60 kg (UIC) on PSC Sleepers",
    cmsFab.material = "Austenitic Manganese Steel (IRS:T-29)",
    cmsFab.crossingAngle = "4° 45' 49\"";

MERGE (cmsAssy:StandardDrawing {drawingNumber: "RDSO/T-6280"})
SET cmsAssy.title = "Assembly of 1 in 12 CMS Crossing 60 kg with Fittings and Check Rails on PSC Sleepers",
    cmsAssy.sleeperSpan = "Sleepers 41 to 55";

MERGE (cmsWeld:StandardDrawing {drawingNumber: "RDSO/T-6280/1"})
SET cmsWeld.title = "1 in 12 Weldable CMS Crossing with Transition Rails";

MERGE (s85:StandardDrawing {drawingNumber: "RDSO/T-7075"})
SET s85.title = "6425 mm Curved Switch with ZU-1-60 Thick-Web Tongue Rails for 1 in 8.5 Turnout",
    s85.turnoutRatio = "1 in 8.5",
    s85.switchLengthMm = 6425,
    s85.throwAtToeMm = 115,
    s85.speedLoopKmph = 25;

MERGE (l85:StandardDrawing {drawingNumber: "RDSO/T-7076"})
SET l85.title = "Layout of 1 in 8.5 Turnout B.G. 60 kg on PSC Sleepers",
    l85.turnoutRatio = "1 in 8.5",
    l85.totalSleepers = 54;

// 3. Layout Integration Relationships
MERGE (l12)-[:INCORPORATES_SWITCH]->(s12);
MERGE (l12)-[:INCORPORATES_SSD]->(ssd);
MERGE (l12)-[:INCORPORATES_CROSSING]->(cmsAssy);
MERGE (l12)-[:INCORPORATES_CHECK_RAIL]->(chk);
MERGE (s12)-[:GOVERNED_BY_BOM]->(bom12);
MERGE (ssd)-[:CONTAINS_PARTS]->(ssdParts);
MERGE (cmsAssy)-[:INCLUDES_CASTING]->(cmsFab);
MERGE (cmsAssy)-[:HAS_WELDABLE_VARIANT]->(cmsWeld);
MERGE (l85)-[:INCORPORATES_SWITCH]->(s85);

// 4. Revisions for T-6155
MERGE (r10:DrawingRevision {revisionKey: "RDSO/T-6155/ALT-10", altNumber: 10, date: "2023-10-12"});
MERGE (r11:DrawingRevision {revisionKey: "RDSO/T-6155/ALT-11", altNumber: 11, date: "2024-05-22"});
MERGE (r12:DrawingRevision {revisionKey: "RDSO/T-6155/ALT-12", altNumber: 12, date: "2024-10-01"});
MERGE (r13:DrawingRevision {revisionKey: "RDSO/T-6155/ALT-13", altNumber: 13, date: "2025-01-27"});

MERGE (s12)-[:HAS_REVISION]->(r10);
MERGE (s12)-[:HAS_REVISION]->(r11);
MERGE (s12)-[:HAS_REVISION]->(r12);
MERGE (s12)-[:HAS_REVISION]->(r13);
MERGE (s12)-[:LATEST_REVISION]->(r13);

// 5. Critical Components & Directives
MERGE (detailB:TrackFeature {featureId: "DETAIL_B_TIE_BAR"})
SET detailB.description = "M.S. Flat Tie Bar 222 mm drop bend to clear Clamp Point Lock S-3454",
    detailB.location = "Sleepers 03 & 04",
    detailB.dropDepthMm = 222,
    detailB.bottomSpanMm = 485;

MERGE (cpl:SignalingInterlocking {drawingNumber: "RDSO/S-3454", name: "Clamp Point Lock"});
MERGE (detailB)-[:PREVENTS_FOULING_WITH]->(cpl);
MERGE (r12)-[:INTRODUCES_FEATURE]->(detailB);
MERGE (r13)-[:RETAINS_FEATURE]->(detailB);

MERGE (listA:SparesSchedule {scheduleId: "LIST_A", title: "Breakage and Wear Prone Spares Schedule"})
SET listA.totalItems = 24,
    listA.bufferPercent = 10,
    listA.governingNote = 28;

MERGE (r13)-[:ADDS_SPARES_SCHEDULE]->(listA);

MERGE (sopDowel:StandardOperatingProcedure {sopId: "SOP_EPOXY_DOWEL"})
SET sopDowel.governingNotes = "Notes 25 & 26",
    sopDowel.holeSize = "35 mm dia x 165 mm depth",
    sopDowel.resin = "IS:12994-1990 Type L-100",
    sopDowel.cureTimeHours = 24;

MERGE (r12)-[:MANDATES_SOP]->(sopDowel);
MERGE (r13)-[:MANDATES_SOP]->(sopDowel);
