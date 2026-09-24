# EXP-01 benchmark run — USFD Manual

- Input: `usfd_new.pdf`
- SHA-256: `e4030a3edd4d3c679fb246411dd25ed263c0eec1a04843b4bc87574ed312d28f`
- Pages: 147
- PyMuPDF text pages: 147/147
- Empty pages: 0
- Extracted characters: 164,213
- Structural signals: 36 headings, 387 clause-like matches, 0 table labels, 119 figure labels
- PyMuPDF runtime: 0.644 s
- Docling: not installed in the execution environment; no comparative result recorded.

## Interpretation

This run confirms that the current PyMuPDF baseline can extract text from every page of this supplied USFD PDF. The structural counts are heuristic diagnostics only; they do not establish chapter/section/clause precision or recall. The next benchmark step is page-level ground truth plus a Docling-enabled rerun.
