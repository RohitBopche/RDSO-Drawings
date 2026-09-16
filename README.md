# RDSO Universal Track Infrastructure Digital Twin & Multi-Drawing Assembly Suite

**Developed for:** Track Analytical Cell, Bhusawal Division, Central Railway, Indian Railways  
**System Classification:** Offline 3D Engineering Digital Twin, Modular Component Assembly Suite & Continuous Learning Knowledge Graph

---

## 1. Executive Problem Statement: What Problem Does This Project Solve?

Indian Railways operates one of the densest and heaviest railway networks in the world. As the network transitions toward **25-tonne heavy axle freight corridors** and **160 km/h semi-high-speed passenger operations (Vande Bharat / Rajdhani)**, track turnouts (points and crossings) represent the single most critical and failure-prone operational asset:

### A. The Turnout Safety & Derailment Crisis
- **40%+ of all yard and mainline derailments** on Indian Railways occur within switch and crossing zones.
- Turnouts are dynamic mechanical structures subject to extreme horizontal lateral thrusts, wheel-impact transfer forces across crossing gaps, and tongue rail flexure under dynamic wheel flanges.

### B. The Cross-Disciplinary P-Way vs. S&T Interface Conflict
- Railway infrastructure has historically suffered from fragmented departmental coordination between **Civil Engineering (Permanent Way / P-Way)** and **Signal & Telecommunication (S&T)**:
  - **The Drive Rod Collision Issue:** In earlier revisions (Alt 10 and below of RDSO/T-6155), the M.S. Flat Tie Bar between Sleepers 03 and 04 was completely flat. When S&T installed modern **Clamp Point Locks (`RDSO/S-3454`)**, the point machine drive rod fouled directly against the flat tie bar during switch throwing. This caused intermittent point detection failure, signal failures, and manual emergency interventions.
  - **The Engineering Fix (Detail 'B'):** RDSO Alt 12 engineered **Detail 'B'**, introducing a **222 mm drop bend with a 485 mm span** and 12 mm sleeper clearance. However, field P-Way staff frequently lacked clear 3D spatial understanding of how the tie bar, dowels, and S&T lock integrated together, leading to improper field installations.

### C. The Fatigue & Dipped Joint Problem
- Early Thick-Web Switch revisions utilized a **Machined Joint ('M')** at the Junction of Rail Heads (JOH) at Sleeper 13. Under repeated 25t axle pounding, machined bolt holes elongated, resulting in severe joint dipping, high-frequency impact vibrations, and tongue rail fractures.
- Alt 11 resolved this by mandating a **Welded Joint ('W')**, but field teams needed visual guidelines on floating weld positions and thermal stress relief.

### D. The Maintenance Supply Chain & Component Cannibalization Crisis
- Turnout maintenance frequently suffered from prolonged speed restrictions because procurement orders omitted high-wear fastenings, washers, and pads. Field gangs were forced to cannibalize parts from adjacent lines.
- Alt 13 introduced **Note 28 and LIST - A (24 wear/breakage-prone items)** mandating a **statutory +10% spare procurement buffer** for every turnout purchase order. However, depot stores and field supervisors had no automated tool to compute spares across varying order sizes.

### E. The 2D Blueprint Static Barrier
- RDSO track standards are distributed as massive 2D engineering blueprint PDFs filled with microscopic notes, alteration blocks dating back decades, and multi-drawing cross-references.
- Field engineers, junior engineers (P-Way), and track maintainers under strict track possession time windows cannot easily parse interconnected tolerances or visualize how components assemble in 3D.

---

## 2. What This Project Does: The Solution Architecture

This platform is a dedicated **RDSO Railway Track Knowledge Graph Studio & Intelligent Asset Twin Platform**. Built around an enterprise-grade 3D/2D Knowledge Graph core, it provides holistic structural and operational intelligence by mapping drawings, standards, components, tolerances, interlocking interfaces, failure modes, and maintenance SOPs into a unified, interactive semantic network.

```
+------------------------------------------------------------------------------------------------+
|                    RDSO RAILWAY TRACK KNOWLEDGE GRAPH STUDIO & DIGITAL TWIN                    |
+------------------------------------+-----------------------------------+-----------------------+
|    HERO 3D/2D KNOWLEDGE GRAPH      |   EMBEDDED 3D ASSET DIGITAL TWIN  |   INTELLIGENCE TOOLS  |
| - Full-screen WebGL Viewport       | - Real-time 3D CAD Twin Viewer    | - Failure Simulator   |
| - 3D Cosmic Force Numerical Engine | - Interactive 360° Orbit Mini-CAD | - Global Fuzzy Search |
| - 2D Planar Topological Layout     | - Cast Slide Chairs & Tie Bars    | - Alteration Scrubber |
| - Hierarchical Dependency DAG      | - SSD & Monoblock CMS Crossings   | - Live Node Ingestion |
| - Concentric Radial Orbit Layout   | - Fasteners, Rails & PSC Sleepers | - W3C JSON-LD/Cypher  |
+------------------------------------+-----------------------------------+-----------------------+
```

### Key Architectural Capabilities:

### 1. Dedicated Full-Screen Knowledge Graph Studio
- **Full-Screen 3D & 2D Graph Hero Canvas:** The entire viewport is an interactive, responsive Three.js graph universe with celestial starfields, multi-tiered node geometries (planetary drawings, machined components, S&T prisms, warning octahedrons), and auto-facing 3D billboard text sprites.
- **Dynamic Multi-Mode Layout Engine:**
  - **3D Cosmic Force:** Numerical Coulomb-Hooke physics simulation with charge repulsion, spring tension, and damping.
  - **2D Planar Topological:** Forces physics into planar space for clear schematic reading.
  - **Hierarchical Dependency DAG:** Tiered architectural layout organizing entities from Master Layouts down to Components, Tolerances, and Failure Modes.
  - **Concentric Radial Orbit:** Concentric 1-hop and 2-hop radius rings centered on any selected entity.
- **Embedded 3D Physical Digital Twin Inspector:**
  - Selecting any physical component in the graph opens the slide-in **Entity Intelligence Drawer**, which embeds a dedicated interactive Three.js mini-viewport rendering the exact physical 3D asset (Slide Chair, Detail 'B' Bent Tie Bar, SSD, CMS Crossing, Check Rail, ERC Mk-V, PSC Sleeper) with full 360° orbit, pan, and zoom controls.
- **Failure Mode Stress Propagation Simulator:**
  - Selecting any defect (e.g. *Tongue Rail Chipping*, *10 mm GRSP Pad Crushing*, *Tie Bar Collision*) triggers dynamic cascading red shockwaves radiating outward along connected edges to highlight critical derailment risk pathways.
- **Global Fuzzy Search & Quick Jump (`Ctrl+K` or `/`):**
  - Instant autocomplete search for all 32+ entities with instant camera animation to target nodes.
- **Alteration Time-Travel Scrubber:**
  - Dragging the revision slider (Alt 1 to Alt 13) filters graph entities based on the revision level that introduced them.
- **Continuous Learning & Live Ingestion:**
  - Form allowing field engineers to inject new defect reports or proposals directly into the 3D physics loop, attaching structural springs and exporting to Neo4j Cypher or W3C JSON-LD.
- **Level 1: Component Studio (Macro Isolated 360° Inspection)**
  - View individual track components in macro 3D isolation with dedicated lighting and turntable controls:
    - **Cast Steel Slide Chair (`RDSO/T-9616`):** Machined slide table, stock rail check stop, plate screw holes.
    - **Detail 'B' Bent Tie Bar (`RDSO/T-9010`):** 222 mm drop bend, 485 mm span, 12 mm sleeper clearance.
    - **Spring Setting Device (`RDSO/T-6216 / T-6217`):** Helical spring, turnbuckle, mounting bracket, insulated bush.
    - **Monoblock CMS Crossing (`RDSO/T-6279`):** Monolithic austenitic manganese body, throat, vee nose (1:12 angle).
    - **Check Rail Assembly (`RDSO/T-6275`):** 5000 mm rail, 89 mm flared ends, 44 mm flangeway clearance.
    - **Elastic Rail Clip Mk-V (`RDSO/T-5919`):** Accurate double-loop spring steel geometry (1200-1500 kg toe load).
    - **Grooved Rubber Sole Pad (`RDSO/T-9630`):** 10 mm nylon-cord reinforced composite pad.
    - **ZU-1-60 Thick-Web Tongue Rail:** Asymmetrical heavy-web profile with machined knife-edge toe.
- **Level 2: Functional Sub-Assembly Linking**
  - Dynamically interlinks interacting components into focused operational sub-systems:
    - *Switch Toe & S&T Clearance Assembly* (Sleepers 1-4, Detail 'B' Tie Bar, Clamp Lock `S-3454`, slide chairs, epoxy dowels).
    - *JOH Flangeway & SSD Assembly* (Sleeper 13, SSD `T-6216`, tongue rail foot connection, welded joint).
    - *CMS Crossing Protection Assembly* (Sleepers 44-52, CMS unit `T-6279`, Check Rails `T-6275`, distance blocks).
- **Level 3: Full 64-Sleeper Infrastructure Digital Twin**
  - Complete 1 in 12 Turnout (RDSO/T-6154: Sleepers 1 to 64) with **zero floating geometry**:
    - Sleepers chamfered on all top edges with recessed rail seats.
    - 10mm GRSP pads under all rails.
    - Slide chairs on Sleepers 04 to 20 with tongue rails gliding on elevated polished slide tables.
    - 3D ERC Mk-V clips actively clamping the rail base.
    - Switch throwing animation (160 mm throw at toe) toggling between Straight and Diverging routes.

### 2. Living 3D Knowledge Graph & Continuous Learning Engine
- **Three.js WebGL Constellation Graph:** Replaces flat diagrams with an interactive, orbital 3D universe where nodes are glowing 3D spheres and edges are 3D cyber-lines with animated particle pulses.
- **Multi-Layer Railway Taxonomy:**
  - 🔵 **Standard Drawings** (`T-6154`, `T-6155`, `T-6216`, `T-6280`, `T-7075`)
  - 🟢 **Physical Components** (Tongue rails, slide chairs, tie bars, SSD, CMS crossings, check rails)
  - 🟠 **Engineering Limits & Physics** (160 mm throw, 44 mm check flangeway, 60 mm JOH heel gap, 25t axle load)
  - 🟣 **Maintenance SOPs & Directives** (Epoxy doweling Note 25/26, 24-hr curing, Note 28 LIST-A)
  - 🔴 **S&T Interlocking Interfaces** (Clamp Point Lock `S-3454`, point machine stroke)
  - 🟡 **Field Failure Modes & Historical Mitigations** (M-joint fatigue, tie bar collision)
- **Continuous Learning & Dynamic Expansion:**
  - In-app **"➕ Add Component / Field Insight"** form allows field engineers to submit new defect reports (e.g. ultrasonic flaw findings, yard fractures), design proposals, or maintenance notes.
  - Automatically positions the new 3D node, dynamically creates relationships (`INCORPORATES`, `FASTENED_BY`, `CLEARS_MECHANISM`, `CAUSES_DEFECT`, `SUPERSEDES`), and highlights impacted components in real-time.
  - **Export to Production:** One-click export to updated W3C JSON-LD (`rdso_living_knowledge_graph_exported.json`) and Neo4j Cypher (`rdso_living_knowledge_graph_exported.cypher`).

### 3. 4D Revision Lineage Scrubber
- Step backward and forward through time across **Alt 10 (Oct 2023)** $\rightarrow$ **Alt 11 (May 2024)** $\rightarrow$ **Alt 12 (Oct 2024)** $\rightarrow$ **Alt 13 (Jan 2025)**.
- Watch the 3D model physically morph: the tie bar drops from flat to bent Detail 'B', the tongue rail joint switches from Machined to Welded, and LIST - A spares indicators activate.

### 4. Automated Universal Drawing Ingestion Engine (`analyze_rdso_drawing.py`)
- Generic PyMuPDF CLI parsing engine.
- Run `python analyze_rdso_drawing.py --all` to process every RDSO PDF in the directory, extract drawing numbers, alteration numbers, categories, turnout ratios, and governing notes, and output `rdso_drawing_catalog.json`.

### 5. Dynamic Procurement Spares Calculator & Field SOPs
- Real-time calculator for the 24 wear/breakage items in **LIST - A (Note 28)** with dynamic purchase order multiplier and statutory +10% buffer targets.
- Interactive SOP modals with instructions for the Sleeper 03/04 epoxy dowel retrofit (IS: 12994-1990 Type L-100) and 24-hour curing countdown.

---

## 3. Official 14-Drawing Turnout Ecosystem Reference

| # | Drawing No. | Alt | Category | Role in Track Infrastructure |
|---|---|---|---|---|
| 1 | **RDSO/T-6154** | Alt 6 | Master Turnout Layout | General Layout of 1 in 12 Turnout 60 kg (UIC) on PSC Sleepers (Sleepers 1 to 64). |
| 2 | **RDSO/T-6155** | Alt 13 | Curved Switch Assembly | 10125 mm Curved Switch with ZU-1-60 Thick Web Rails, Detail 'B', LIST - A. |
| 3 | **RDSO/T-6155** | Alt 12 | Curved Switch Assembly | Introduced Detail 'B' bent tie bar & epoxy dowel retrofit SOP (Notes 25/26). |
| 4 | **RDSO/T-6155** | Alt 10 | Curved Switch Assembly | ERC Mk-V upgrade, cast steel slide chairs (T-9616), plate screws T-3913. |
| 5 | **RDSO/T-6155/1**| Alt 7 | Switch BOM & Particulars | Bill of Materials, fastening schedule, and particulars of components. |
| 6 | **RDSO/T-6216** | Alt 5 | Spring Setting Device (SSD) | Complete SSD assembly at Sleeper 13 (JOH) maintaining 60 mm flangeway gap. |
| 7 | **RDSO/T-6217** | Alt 4 | SSD Component Catalogue | Detailed component drawings for SSD Items 1 to 39 (springs, rods, bushes). |
| 8 | **RDSO/T-6275** | Alt 4 | Check Rail Assembly | Check rails (5000 mm) with flared ends (89 mm) & flangeway clearance 41-45 mm. |
| 9 | **RDSO/T-6279** | Alt 2 | CMS Crossing Unit | 1 in 12 Cast Manganese Steel (CMS) monoblock crossing 60 kg (UIC). |
| 10 | **RDSO/T-6280** | Alt 4 | CMS Crossing Assembly | Complete crossing assembly on Sleepers 41 to 55 with specialized base plates. |
| 11 | **RDSO/T-6280/1**| Alt 2 | Weldable CMS Crossing | CMS crossing with transition rails for direct LWR/CWR flash-butt welding. |
| 12 | **RDSO/T-7075** | Alt 1 | 1:8.5 Switch Assembly | 6425 mm Curved Switch with ZU-1-60 Thick Web Tongue Rails (115 mm throw). |
| 13 | **RDSO/T-7076** | Alt 1 | 1:8.5 Turnout Layout | Layout of 1 in 8.5 Turnout 60 kg on PSC Sleepers (54 Sleepers). |
| 14 | **RDSO/T-7076/1**| Alt 1 | 1:8.5 BOM & Particulars | Particulars of components and fittings for 1 in 8.5 Turnout. |

---

## 4. Modular Repository Architecture

The repository is organized into dedicated enterprise directories:

```text
F:\git\RDSO-Drawings\
├── drawings/                   # All 59 official RDSO PDF blueprints
├── data/                       # Canonical & extracted datasets (JSON & Cypher)
│   ├── rdso_canonical_kg.json
│   ├── rdso_extracted_knowledge.json
│   ├── rdso_drawing_catalog.json
│   ├── rdso_knowledge_graph.json
│   └── rdso_knowledge_graph.cypher
├── scripts/                    # Ingestion, extraction, compilation, and validation tools
│   ├── analyze_rdso_drawing.py
│   ├── build_updated_app.py
│   ├── extract_drawing_knowledge.py
│   ├── generate_canonical_kg.py
│   ├── validate_canonical_kg.py
│   └── visual_diff_engine.py
├── tests/                      # Automated browser and CDP test suites
│   ├── verify_kg_app.js
│   └── verify_kg_interlinking.js
├── crops/                      # High-resolution blueprint crops (used directly by index.html)
├── docs/                       # Blueprints & documentation
│   └── RDSO_Knowledge_Graph_Improvement_Blueprint.md
├── lib/                        # Offline vendor libraries (Three.js, OrbitControls.js)
├── index.html                  # Main Studio web application (kept at root for 1-click opening)
└── README.md                   # Complete system documentation
```

---

## 5. Quick Start & Offline Usage

### Running the Digital Twin & Knowledge Graph Studio
1. Simply double-click `index.html` or open it in any modern web browser:
   ```bash
   # Windows PowerShell:
   start index.html
   ```
2. **100% Offline:** The studio uses self-contained Three.js and OrbitControls libraries in `./lib/`. No internet connection or external CDN is required.

### Validating the Canonical Knowledge Core
```bash
python scripts/validate_canonical_kg.py
```

### Compiling the Standalone Web App
```bash
python scripts/build_updated_app.py
```

### Running Automated Drawing Knowledge Extraction
```bash
python scripts/extract_drawing_knowledge.py
```

### Running Automated CDP Browser Test Suite
```bash
node tests/verify_kg_interlinking.js
```
