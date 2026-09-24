#!/usr/bin/env python3
"""
Research EXP-01: benchmark the current PyMuPDF extraction against Docling.

This is intentionally a research harness. It does not modify production
ingestion and does not publish benchmark output into canonical data.

Example:
    python scripts/research/benchmark_docling.py --input manuals --limit 1

Outputs:
    research/benchmarks/docling/<timestamp>/results.json
    research/benchmarks/docling/<timestamp>/README.md

Docling is optional. If it is unavailable, the benchmark records that state
and exits successfully without changing production code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import time
from pathlib import Path
from typing import Any

try:
    import pymupdf
except ImportError as exc:
    raise SystemExit("PyMuPDF is required for EXP-01") from exc


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def structural_signals(text: str) -> dict[str, int]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    headings = 0
    clauses = 0
    tables = 0
    figures = 0
    for line in lines:
        if re.match(r"^(CHAPTER|PART|SECTION|ANNEXURE)\s*[\dIVXAB\-]+", line, re.I):
            headings += 1
        elif re.match(r"^[A-Z\s]{5,40}$", line) and len(line) > 6:
            headings += 1
        if re.search(r"\b(Para\s*\d+|[0-9]{1,3}\.[0-9]{1,2}(?:\.[0-9])?|\b[4-9]\d{2}\b)\b", line):
            clauses += 1
        if re.match(r"^(TABLE|Table)\s*[\dIVXAB\.\-]+", line):
            tables += 1
        if re.match(r"^(FIG|Fig|FIGURE)\s*[\dIVXAB\.\-]+", line):
            figures += 1
    return {
        "headings": headings,
        "clauses": clauses,
        "tables": tables,
        "figures": figures,
    }


def benchmark_pymupdf(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    doc = pymupdf.open(path)
    page_lengths: list[int] = []
    signals = {"headings": 0, "clauses": 0, "tables": 0, "figures": 0}
    for page in doc:
        text = page.get_text()
        page_lengths.append(len(text.strip()))
        for key, value in structural_signals(text).items():
            signals[key] += value
    elapsed = time.perf_counter() - started
    return {
        "pages": len(doc),
        "text_pages": sum(x > 30 for x in page_lengths),
        "empty_pages": sum(x <= 30 for x in page_lengths),
        "characters": sum(page_lengths),
        "signals": signals,
        "seconds": round(elapsed, 4),
    }


def benchmark_docling(path: Path) -> dict[str, Any]:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        return {"available": False, "reason": "docling is not installed"}

    started = time.perf_counter()
    converter = DocumentConverter()
    result = converter.convert(str(path))
    document = result.document

    # Exported markdown is used only as a common comparison representation.
    markdown = document.export_to_markdown()
    elapsed = time.perf_counter() - started

    lines = [x.strip() for x in markdown.splitlines() if x.strip()]
    headings = sum(1 for x in lines if x.startswith("#"))
    tables = sum(1 for x in lines if "|" in x)
    return {
        "available": True,
        "characters": len(markdown),
        "markdown_lines": len(lines),
        "headings": headings,
        "table_like_lines": tables,
        "seconds": round(elapsed, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "manuals")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--output-root", type=Path, default=ROOT / "research" / "benchmarks" / "docling")
    args = parser.parse_args()

    pdfs = sorted(args.input.glob("*.pdf"))[: args.limit]
    if not pdfs:
        raise SystemExit(f"No PDFs found under {args.input}")

    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    output = args.output_root / stamp
    output.mkdir(parents=True, exist_ok=True)

    records = []
    for pdf in pdfs:
        current = benchmark_pymupdf(pdf)
        docling = benchmark_docling(pdf)
        records.append({
            "file": str(pdf.relative_to(ROOT)),
            "sha256": sha256(pdf),
            "current_pymupdf": current,
            "docling": docling,
        })
        print(json.dumps(records[-1], ensure_ascii=False))

    result = {
        "experiment": "EXP-01",
        "question": "Can structured PDF parsing improve manual extraction without damaging deterministic hierarchy?",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": records,
        "note": "Automated signals are diagnostic only. Hierarchy accuracy requires a manually verified ground-truth sample.",
    }
    (output / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (output / "README.md").write_text(
        "# EXP-01 Benchmark Run\n\n"
        "This directory contains an immutable benchmark snapshot. "
        "Do not copy results into canonical production data.\n\n"
        "Interpret results together with manually verified hierarchy ground truth.\n",
        encoding="utf-8",
    )
    print(f"Results written to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
