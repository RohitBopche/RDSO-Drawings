# RDSO Track Infrastructure Intelligence & 3D Asset Digital Twin

This repository contains an end-to-end engineering intelligence suite for Indian Railways (RDSO) standard track drawings, focusing on **RDSO/T-6155** (10125 mm Curved Switch with ZU-1-60/60E1A1 Thick-Web Tongue Rails for 1 in 12 Turnout B.G. on PSC Sleepers) across revisions **Alt 10 (12-10-2023)**, **Alt 12 (01-10-2024)**, and **Alt 13 (27-01-2025)**.

---

## Deliverables Summary

### 1. Offline 3D Turnout Asset Dashboard (`index.html`)
- **Self-contained & 100% Offline:** Packaged with local Three.js and OrbitControls in `./lib/`. No internet connection required.
- **Interactive 3D Switch Model:**
  - 27 PSC Sleepers (with fanshape layout from Sleeper 21 to 27).
  - Stock Rails (13.0m) and Thick-Web Tongue Rails (12.48m).
  - Cast Steel Slide Chairs (Sleepers 04 to 20) and Special Bearing Plates (Sleepers 21 to 27).
  - **Detail 'B' Bent Tie Bar:** Accurate 3D modeling of the 222 mm drop bend between Sleepers 03 & 04 to clear the Clamp Point Lock (RDSO/S-3454).
  - Spring Setting Device (SSD) modeled at Sleeper 13 (JOH).
- **Interactive Features:**
  - **Switch Throwing:** Toggle between Straight and Diverging route (160 mm throw at toe).
  - **Revision Differential Lenses:** Switch between Alt 10, Alt 12, Alt 13, and Diff Highlighter mode.
  - **LIST - A Mandatory Spares Calculator:** Dynamic computation of 10% wear/breakage spares buffer per Note 28.
  - **Embedded Knowledge Graph Visualizer:** 2D canvas network graph of standards and dependencies.
  - **Field SOP Modals:** Step-by-step instructions for Sleeper 03/04 epoxy doweling (IS: 12994 L-100) with 24-hr curing countdown.

### 2. Knowledge Graph Datasets
- **JSON-LD Schema (`rdso_knowledge_graph.json`):** W3C RDF/JSON-LD semantic dataset connecting drawings, revisions, components, and field directives.
- **Neo4j Cypher DDL (`rdso_knowledge_graph.cypher`):** Ready-to-import Cypher scripts with constraints, nodes, and relationships.

### 3. Automated Drawing Ingestion CLI (`analyze_rdso_drawing.py`)
- Automated Python tool using `pymupdf` to parse drawing metadata, detect alteration numbers, and extract key engineering differences when new drawings are dropped into the directory.

```bash
# Example usage:
python analyze_rdso_drawing.py 2025-01-28-RDSO_T_6155_ALT_13.pdf
```

---

## Field Implementation Highlights (Alt 10 $\rightarrow$ Alt 12 $\rightarrow$ Alt 13)

1. **Alt 13 (27-01-2025):** Mandatory procurement buffer of **10% on all 24 wear/breakage prone items in LIST - A** (Note 28).
2. **Alt 12 (01-10-2024):** Introduction of **Detail 'B'** (222 mm drop bend in M.S. Flat Tie Bar RDSO/T-9010) and **Notes 25 & 26** for field doweling SOP (35 mm dia $\times$ 165 mm depth hole with IS:12994 Type L-100 Epoxy Resin and 24-hour cure).
3. **Alt 11 (22-05-2024):** Machined Joint `'M'` replaced by **Welded Joint `'W'`** on tongue rails to eliminate joint fatigue.
4. **Alt 10 (12-10-2023):** Upgraded from ERC Mk-III to **ERC Mk-V (RDSO/T-5919)**, and from fabricated M.S. to **Cast Steel Slide Chairs (RDSO/T-9616)** and **Special Bearing Plates (RDSO/T-9617 to 9629)**.
