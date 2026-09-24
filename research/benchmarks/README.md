# Research Benchmarks

This directory contains reproducible research experiment outputs and manifests.

## EXP-01

EXP-01 compares the current PyMuPDF-based extraction path with Docling on representative RDSO manuals.

The benchmark is deliberately separate from production data:

- no canonical graph mutation;
- no source replacement;
- no automatic architecture change;
- outputs remain research evidence.

A result can only change production architecture after manual review, comparison against ground truth, and an explicit update to docs/PROJECT_MASTER.md.

Run from the repository root:

    python scripts/research/benchmark_docling.py --input manuals --limit 1

For a broader sample:

    python scripts/research/benchmark_docling.py --input manuals --limit 3
