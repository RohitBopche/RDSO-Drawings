# Indian Railways Codes, Manuals & Standards Repository

Place your official PDF manuals, IRS specifications, and Indian Standard (IS) codes in this directory (`manuals/`).

---

## Recommended Organization / Naming Convention

You can drop PDF files directly into `manuals/` or organize them by category:

### 1. Permanent Way & Engineering Manuals
- `IRPWM_2020.pdf` — Indian Railways Permanent Way Manual (June 2020 / latest slip revisions)
- `USFD_Manual.pdf` — Manual for Ultrasonic Testing of Rails and Welds
- `LWR_Manual.pdf` — Manual for Instructions on Long Welded Rails
- `AT_Welding_Manual.pdf` — Manual for Fusion Welding of Rails by Alumino-Thermic Process
- `Track_Tamping_Manual.pdf` — Manual for Maintenance of Track by Track Machines

### 2. IRS Technical Specifications (Track & Signaling)
- `IRS_T_10.pdf` — IRS Specification for Thick Web Curved Switches (ZU-1-60 & 60E1A1)
- `IRS_T_29.pdf` — IRS Specification for Cast Manganese Steel (CMS) Crossings
- `IRS_S_3454.pdf` — IRS Specification for Clamp Point Lock Assemblies & Interlocking
- `IRS_T_12.pdf` — Specification for Elastic Rail Clips & Fastenings

### 3. Bureau of Indian Standards (IS Codes)
- `IS_2062.pdf` — Hot Rolled Medium and High Tensile Structural Steel (governs Tie Bars Detail 'B')
- `IS_1030.pdf` — Carbon Steel Castings for General Engineering Purposes (governs Slide Chairs T-9616)
- `IS_12994.pdf` — Epoxy Resin System for In-situ Grouting of Concrete Inserts (governs Dowels Note 25/26)

### 4. Schedule of Dimensions (IRSOD)
- `IRSOD_BG_2004.pdf` — Indian Railways Schedule of Dimensions 1676 mm Gauge (Revised 2004 / 2022)

---

## How the Ingestion Pipeline Connects These to the Knowledge Graph

When files are uploaded here:
1. The ingestion scripts in `scripts/` will parse chapters, tables, and clauses (e.g. IRPWM Chapter 4 Turnout Tolerances, Annexure 4/6 Versine Tables).
2. Specific paragraphs (e.g. *Para 405(2) Switch Opening*, *Para 408 Check Rail Clearances*) will be mapped as first-class `STANDARD` and `SOP` nodes.
3. They will automatically link to the corresponding blueprint drawings in `drawings/` via typed relationships (`GOVERNS`, `SPECIFIES`, `INSPECTED_BY`, `MITIGATED_BY`).
