# Repository Structure

This repository is organized into five logical areas while preserving the existing application entrypoint and drawing files.

```text
RDSO-Drawings/
├── index.html                         # Current offline web application entrypoint
├── README.md                          # Project overview and quick start
├── docs/                              # Architecture, product and engineering documentation
│   ├── RDSO_Knowledge_Graph_Improvement_Blueprint.md
│   └── REPO_STRUCTURE.md
├── scripts/                           # Python/JavaScript utilities and validation tools
│   └── README.md
├── data/                              # Generated and canonical knowledge datasets
│   └── knowledge-graph/
│       └── README.md
├── lib/                               # Vendored browser libraries used offline
│   ├── three.min.js
│   └── OrbitControls.js
├── crops/                             # Generated drawing crops and visual-diff outputs
└── *.pdf                              # Source RDSO drawing documents
```

## Current migration policy

- The root `index.html` remains unchanged to avoid breaking offline usage or deployment.
- Existing PDFs remain unchanged until references and download workflows are audited.
- Existing generated datasets remain at the root temporarily for backward compatibility.
- New code should be added under `scripts/` and new canonical datasets under `data/knowledge-graph/`.
- A later migration can move legacy files after all application and documentation references are updated.
