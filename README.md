# RDSO Track Infrastructure Intelligence & 3D Turnout Digital Twin

An end-to-end engineering intelligence and digital twin suite for Indian Railways (RDSO) standard track drawings, developed for **Track Analytical Cell, Bhusawal Division, Central Railway**.

The suite models the complete **1 in 12 Broad Gauge (1673 mm) 60 kg (UIC) Turnout on PSC Sleepers (RDSO/T-6154)**, the **10125 mm Curved Switch with ZU-1-60/60E1A1 Thick-Web Tongue Rails (RDSO/T-6155 Alt 10, 11, 12, 13)**, the **Spring Setting Device (RDSO/T-6216/T-6217)**, the **Check Rail Arrangement (RDSO/T-6275)**, the **1:12 CMS Crossing (RDSO/T-6279/T-6280/T-6280/1)**, and the **1 in 8.5 Turnout Suite (RDSO/T-7075/T-7076)**.

---

## Deliverables & Architecture

### 1. Offline 3D Turnout Asset Digital Twin (`index.html`)
- **Self-contained & 100% Offline:** Packaged with local Three.js and OrbitControls in `./lib/`. Operates anywhere without internet access.
- **Complete 64-Sleeper Turnout Layout (RDSO/T-6154):**
  - **Switch Zone (Sleepers 01 to 27):** Thick-Web Tongue Rails (12.48m), Stock Rails (13.0m), Cast Steel Slide Chairs (Sleepers 04 to 20), Fanshape Layout (Sleepers 21 to 27).
  - **Detail 'B' Bent Tie Bar (RDSO/T-9010):** Modeled with exact 222 mm drop bend between Sleepers 03 & 04 to guarantee clearance with Clamp Point Lock drive rod (RDSO/S-3454).
  - **Spring Setting Device (SSD):** Modeled at Sleeper 13 (JOH) per RDSO/T-6216 to ensure 60 mm flangeway clearance.
  - **Lead Curve Zone (Sleepers 28 to 40):** Graduated PSC sleeper lengths (3.1m to 4.0m) following the 441.36 m curve radius.
  - **Crossing Zone (Sleepers 41 to 55):** 1 in 12 Cast Manganese Steel (CMS) Monoblock Crossing (RDSO/T-6279 & T-6280) with Theoretical Nose of Crossing (TNC) at Sleeper 48.
  - **Check Rails (RDSO/T-6275):** Modeled with flared ends (89 mm opening) and nominal 44 mm flangeway clearance (41 mm - 45 mm) on both running rails.
  - **Exit Zone (Sleepers 56 to 64):** Transition to straight and diverging lines.
- **Interactive Capabilities:**
  - **Layout Scope Selector:** Switch between Full Turnout (Sleepers 1-64), Switch Zone (Sleepers 1-27), Crossing Zone (Sleepers 41-55), and 1:8.5 Switch (RDSO/T-7075).
  - **Switch Throwing:** Toggle between Straight and Diverging route (160 mm stroke at toe).
  - **4D Revision Evolution Scrubber:** Step through Alt 10, Alt 11, Alt 12, and Alt 13 with dynamic 3D morphing.
  - **LIST - A Mandatory Spares Calculator:** Dynamic computation of statutory 10% wear/breakage spares buffer per Note 28.
  - **Embedded Knowledge Graph Visualizer:** 2D interactive canvas network connecting standards, sub-assemblies, and field directives.
  - **Field SOP Modals:** Complete instructions for Sleeper 03/04 epoxy dowel retrofit (IS: 12994-1990 L-100) with 24-hr curing countdown.

### 2. Universal Drawing Ingestion Engine (`analyze_rdso_drawing.py`)
- Automated PyMuPDF CLI parsing tool that automatically detects drawing numbers, alteration numbers, categories, turnout ratios, and engineering directives across any RDSO standard PDF.
- **Batch Processing Mode:**
  ```bash
  python analyze_rdso_drawing.py --all
  ```
  Generates `rdso_drawing_catalog.json` indexing all drawings in the repository.

### 3. Knowledge Graph Datasets
- **JSON-LD Semantic Graph (`rdso_knowledge_graph.json`):** W3C RDF/JSON-LD dataset connecting layouts, switches, SSD, CMS crossings, and maintenance notes.
- **Neo4j Cypher DDL (`rdso_knowledge_graph.cypher`):** Ready-to-import Cypher graph schema with nodes, constraints, and relationships.

### 4. Automated Visual Diff Engine (`visual_diff_engine.py`)
- Generates high-resolution comparative side-by-side PNG panels in `crops/` (Detail 'B' clearance, Alteration tables, and Spares schedules).

---

## 14-Drawing Turnout Ecosystem Reference

| # | Drawing No. | Alt | Category | Description |
|---|---|---|---|---|
| 1 | **RDSO/T-6154** | Alt 6 | Master Turnout Layout | Layout of 1 in 12 Turnout 60 kg (UIC) on PSC Sleepers (Sleepers 1 to 64). |
| 2 | **RDSO/T-6155** | Alt 13 | Curved Switch Assembly | 10125 mm Curved Switch with ZU-1-60 Thick Web Rails, Detail 'B', LIST - A. |
| 3 | **RDSO/T-6155** | Alt 12 | Curved Switch Assembly | Introduced Detail 'B' bent tie bar & epoxy dowel retrofit SOP (Notes 25/26). |
| 4 | **RDSO/T-6155** | Alt 10 | Curved Switch Assembly | ERC Mk-V upgrade, cast steel slide chairs (T-9616), plate screws T-3913. |
| 5 | **RDSO/T-6155/1**| Alt 7 | Switch BOM & Particulars | Bill of Materials, fastening schedule, and particulars of components. |
| 6 | **RDSO/T-6216** | Alt 5 | Spring Setting Device (SSD) | Complete SSD assembly at Sleeper 13 (JOH) maintaining 60 mm flangeway gap. |
| 7 | **RDSO/T-6217** | Alt 4 | SSD Component Catalogue | Detailed component drawings for SSD Items 1 to 39. |
| 8 | **RDSO/T-6275** | Alt 4 | Check Rail Assembly | Check rails (5000 mm) with flared ends (89 mm) & flangeway clearance 41-45 mm. |
| 9 | **RDSO/T-6279** | Alt 2 | CMS Crossing Unit | 1 in 12 Cast Manganese Steel (CMS) monoblock crossing 60 kg (UIC). |
| 10 | **RDSO/T-6280** | Alt 4 | CMS Crossing Assembly | Complete crossing assembly on Sleepers 41 to 55 with fittings. |
| 11 | **RDSO/T-6280/1**| Alt 2 | Weldable CMS Crossing | CMS crossing with transition rails for direct LWR/CWR flash-butt welding. |
| 12 | **RDSO/T-7075** | Alt 1 | 1:8.5 Switch Assembly | 6425 mm Curved Switch with ZU-1-60 Thick Web Tongue Rails (115 mm throw). |
| 13 | **RDSO/T-7076** | Alt 1 | 1:8.5 Turnout Layout | Layout of 1 in 8.5 Turnout 60 kg on PSC Sleepers (54 Sleepers). |
| 14 | **RDSO/T-7076/1**| Alt 1 | 1:8.5 BOM & Particulars | Particulars of components and fittings for 1 in 8.5 Turnout. |

---

## Critical Field Engineering Highlights

1. **Alt 13 (27-01-2025):** Mandatory procurement buffer of **+10% on all 24 wear/breakage prone items in LIST - A** (Note 28).
2. **Alt 12 (01-10-2024):** Introduction of **Detail 'B'** (222 mm drop bend in M.S. Flat Tie Bar RDSO/T-9010) to clear Clamp Point Lock RDSO/S-3454, plus **Notes 25 & 26** enforcing the 35 mm dia $\times$ 165 mm depth dowel retrofit SOP (IS: 12994 Type L-100 epoxy resin with 24-hr curing).
3. **Alt 11 (22-05-2024):** Machined Joint `'M'` replaced by **Welded Joint `'W'`** on tongue rails to eliminate joint fatigue under 25t axle loads.
4. **Alt 10 (12-10-2023):** Upgraded to **ERC Mk-V (RDSO/T-5919)**, **Cast Steel Slide Chairs (RDSO/T-9616)**, and **Special Bearing Plates (RDSO/T-9617 to 9629)**.
