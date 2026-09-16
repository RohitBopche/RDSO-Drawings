// ==============================================================================
// RDSO Track Infrastructure Knowledge Graph - Neo4j Cypher DDL & Data Ingestion
// Standard: RDSO/T-6155 (10125 mm Curved Switch with ZU-1-60 Thick-Web Tongue Rails)
// ==============================================================================

// Create Constraints
CREATE CONSTRAINT unique_drawing_number IF NOT EXISTS FOR (d:Drawing) REQUIRE d.number IS UNIQUE;
CREATE CONSTRAINT unique_component_part IF NOT EXISTS FOR (c:Component) REQUIRE c.partNumber IS UNIQUE;
CREATE CONSTRAINT unique_revision_id IF NOT EXISTS FOR (r:Revision) REQUIRE r.id IS UNIQUE;

// Create Drawing Nodes
MERGE (d:Drawing {number: 'RDSO/T-6155'})
SET d.title = '10125 mm Curved Switch with ZU-1-60/60E1A1 Thick-Web Tongue Rails for 1 in 12 Turnout B.G. on P.S.C. Sleepers',
    d.specification = 'IRS: T 10',
    d.railSection = '60 kg (UIC) / 60E1',
    d.gaugeMm = 1673,
    d.switchAngleAtToe = '0° 20\' 00"',
    d.divergenceAtHeelMm = 175,
    d.throwAtToeMm = 160,
    d.radiusMm = 441360,
    d.tongueRailLengthMm = 12480,
    d.stockRailLengthMm = 13000;

MERGE (layout:Drawing {number: 'RDSO/T-6154'})
SET layout.title = 'Layout of 1 in 12 Turnout B.G. with 10125 mm Curved Switch';

MERGE (crossing:Drawing {number: 'RDSO/T-4220'})
SET crossing.title = '1 in 12 CMS Crossing 60 kg';

MERGE (clampLock:Drawing {number: 'RDSO/S-3454'})
SET clampLock.title = 'Clamp Point Lock for Thick Web Switch';

MERGE (d)-[:REQUIRES_LAYOUT]->(layout);
MERGE (d)-[:USED_WITH_CROSSING]->(crossing);
MERGE (d)-[:INTEGRATES_SIGNALING]->(clampLock);

// Create Revisions
MERGE (r10:Revision {id: 'RDSO_T_6155_ALT_10'})
SET r10.number = 10, r10.date = date('2023-10-12'), r10.type = 'REVISED & REDRAWN',
    r10.summary = 'ERC Mk-V adoption, cast steel chairs/bearing plates, nylon-cord GRSP';

MERGE (r11:Revision {id: 'RDSO_T_6155_ALT_11'})
SET r11.number = 11, r11.date = date('2024-05-22'), r11.type = 'REVISED & REDRAWN',
    r11.summary = 'Tongue rail machined joint replaced with welded joint';

MERGE (r12:Revision {id: 'RDSO_T_6155_ALT_12'})
SET r12.number = 12, r12.date = date('2024-10-01'), r12.type = 'REVISED & REDRAWN',
    r12.summary = 'Detail B added (222 mm drop bent tie bar), Notes 23-27 added';

MERGE (r13:Revision {id: 'RDSO_T_6155_ALT_13'})
SET r13.number = 13, r13.date = date('2025-01-27'), r13.type = 'REVISED & REDRAWN',
    r13.summary = 'LIST - A added, Note 28 enforces mandatory 10% wear/breakage spares buffer';

MERGE (d)-[:HAS_REVISION]->(r10);
MERGE (d)-[:HAS_REVISION]->(r11);
MERGE (d)-[:HAS_REVISION]->(r12);
MERGE (d)-[:HAS_REVISION]->(r13);
MERGE (d)-[:LATEST_REVISION]->(r13);

MERGE (r10)-[:SUPERSEDED_BY]->(r11);
MERGE (r11)-[:SUPERSEDED_BY]->(r12);
MERGE (r12)-[:SUPERSEDED_BY]->(r13);

// Key Components
MERGE (cTieBar:Component {partNumber: 'RDSO/T-9010'})
SET cTieBar.description = 'M.S. Flat Tie Bar (Non-Point Machine End)',
    cTieBar.material = 'Mild Steel',
    cTieBar.detail = 'Detail B 222 mm drop bend to clear Clamp Point Lock';

MERGE (cTieBarPM:Component {partNumber: 'RDSO/T-9010/1'})
SET cTieBarPM.description = 'M.S. Flat Tie Bar (Point Machine End)';

MERGE (cSlideChair:Component {partNumber: 'RDSO/T-9616'})
SET cSlideChair.description = 'Cast Steel Slide Chair',
    cSlideChair.material = 'Cast Steel',
    cSlideChair.quantity = 34,
    cSlideChair.sleeperRange = 'Sleepers 04 to 20';

MERGE (cERCMkV:Component {partNumber: 'RDSO/T-5919'})
SET cERCMkV.description = 'Elastic Rail Clip MK-V',
    cERCMkV.material = 'Spring Steel 55Si7 / 60Si7',
    cERCMkV.toeLoadKg = '1200 - 1500 kg',
    cERCMkV.quantity = 84;

MERGE (cSSD:Component {partNumber: 'RDSO/T-6216'})
SET cSSD.description = 'Spring Setting Device (SSD)',
    cSSD.sleeperLocation = 'Sleeper No. 13 (Junction of Rail Heads - JOH)';

MERGE (dowel:Component {partNumber: 'RDSO/T-3002'})
SET dowel.description = 'Polyethylene Dowel for Sleeper Retrofit',
    dowel.diameterMm = 35,
    dowel.depthMm = 165;

MERGE (screw:Component {partNumber: 'RDSO/T-3913'})
SET screw.description = 'Plate Screw for PSC Sleeper',
    screw.quantity = 215;

MERGE (sparesList:SparesSchedule {name: 'LIST - A'})
SET sparesList.description = 'Breakage-prone and wear-prone spare parts schedule',
    sparesList.mandatoryBufferPct = 10,
    sparesList.totalItems = 24;

// Directives & SOPs
MERGE (sopDowel:FieldSOP {code: 'SOP-DOWEL-T6155'})
SET sopDowel.name = 'Sleeper 03 & 04 Field Doweling SOP',
    sopDowel.notes = 'Notes 25 & 26',
    sopDowel.drillHole = '35 mm dia x 165 mm depth',
    sopDowel.resin = 'IS: 12994:1990 Type L-100 Epoxy',
    sopDowel.mandatoryCureTimeHours = 24;

MERGE (ruleSpares:FieldSOP {code: 'RULE-SPARES-10PCT'})
SET ruleSpares.name = 'Mandatory 10% Spares Procurement Rule',
    ruleSpares.note = 'Note 28';

// Link Relationships
MERGE (r12)-[:INTRODUCES_DETAIL_B]->(cTieBar);
MERGE (r12)-[:DEFINES_SOP]->(sopDowel);
MERGE (r13)-[:ADDS_SCHEDULE]->(sparesList);
MERGE (r13)-[:ENFORCES_RULE]->(ruleSpares);
MERGE (sparesList)-[:MANDATES_SPARE {qty: 215}]->(screw);
MERGE (sparesList)-[:MANDATES_SPARE {qty: 12}]->(:Component {partNumber: 'RDSO/T-9630', description: 'Nylon Cord Reinforced GRSP'});
MERGE (sparesList)-[:MANDATES_SPARE {qty: 34}]->(:Component {partNumber: 'RDSO/T-6305', description: 'Wedge'});
MERGE (sparesList)-[:MANDATES_SPARE {qty: 36}]->(:Component {partNumber: 'RDSO/T-6310', description: 'Leaf Spring'});
