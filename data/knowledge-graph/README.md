# Knowledge Graph Data

This folder is the target home for canonical and intermediate knowledge-graph datasets.

## Recommended layout

```text
data/knowledge-graph/
├── raw/            # Direct extraction outputs; do not manually edit
├── intermediate/   # Normalized facts, OCR, regions and review queues
├── canonical/      # Validated entities, facts, revisions and relationships
├── exports/        # JSON-LD, Cypher and other exchange formats
└── schemas/        # JSON Schema and controlled vocabularies
```

The existing root-level JSON and Cypher files are retained temporarily because the current `index.html` may reference them. Move them only after those references are updated and tested.
