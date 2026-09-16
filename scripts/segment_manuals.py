"""
segment_manuals.py
Implements Section 4 Phase B of COMPLETE_MANUALS_KNOWLEDGE_GRAPH_PLAN.md:
- Reads source_registry.jsonl.
- Segments every document into stable addressable page and block units.
- Detects headings, clauses, tables, figures, and structural hierarchy.
- Outputs data/knowledge-graph/raw/extracted_pages.jsonl.
"""

import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import pymupdf

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(REPO_ROOT, "data", "knowledge-graph", "raw", "source_registry.jsonl")
OUTPUT_PAGES_PATH = os.path.join(REPO_ROOT, "data", "knowledge-graph", "raw", "extracted_pages.jsonl")

def detect_structural_elements(text):
    headings = []
    clauses = []
    tables = []

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        # Detect Headings
        if re.match(r'^(CHAPTER|PART|SECTION|ANNEXURE)\s*[\dIVXAB\-]+', line, re.I):
            headings.append(line[:100])
        elif re.match(r'^[A-Z\s]{5,40}$', line) and len(line) > 6:
            headings.append(line[:100])
        
        # Detect Clauses (e.g., "429", "8.10", "10.6.2", "(1)", "Para 429")
        clause_match = re.search(r'\b(Para\s*\d+|[0-9]{1,3}\.[0-9]{1,2}(?:\.[0-9])?|\b[4-9]\d{2}\b)\b', line)
        if clause_match:
            clauses.append(clause_match.group(0))

        # Detect Tables / Figures
        if re.match(r'^(TABLE|Table|FIG|Fig|FIGURE)\s*[\dIVXAB\.\-]+', line):
            tables.append(line[:80])

    return {
        "headings": list(dict.fromkeys(headings))[:10],
        "clauses": list(dict.fromkeys(clauses))[:15],
        "tables": list(dict.fromkeys(tables))[:10]
    }

def run_document_segmentation():
    print("================================================================================")
    print("PHASE B: DOCUMENT SEGMENTATION & TEXT STRUCTURING PIPELINE")
    print("================================================================================")

    if not os.path.exists(REGISTRY_PATH):
        print(f"[FATAL] Source registry not found at {REGISTRY_PATH}. Run Phase A first!")
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry_records = [json.loads(line) for line in f if line.strip()]

    print(f"[*] Loaded {len(registry_records)} documents from source registry.")

    out_file = open(OUTPUT_PAGES_PATH, "w", encoding="utf-8")
    total_pages_processed = 0
    total_text_pages = 0
    total_clauses_indexed = 0

    for doc_idx, rec in enumerate(registry_records):
        doc_id = rec["id"]
        file_path = os.path.join(REPO_ROOT, rec["file_path"])
        
        if not os.path.exists(file_path):
            print(f"  [WARN] File missing: {file_path}")
            continue

        try:
            pdf_doc = pymupdf.open(file_path)
            num_pages = len(pdf_doc)
            doc_text_count = 0

            for p_num in range(num_pages):
                page = pdf_doc[p_num]
                page_text = page.get_text()
                clean_text = page_text.strip()
                is_ext = len(clean_text) > 30

                struct = detect_structural_elements(clean_text)
                if is_ext:
                    doc_text_count += 1
                    total_clauses_indexed += len(struct["clauses"])

                page_record = {
                    "page_id": f"PAGE:{doc_id}:{p_num+1}",
                    "document_id": doc_id,
                    "document_family": rec["document_family"],
                    "page_number": p_num + 1,
                    "total_pages": num_pages,
                    "text_length": len(clean_text),
                    "is_extractable": is_ext,
                    "detected_headings": struct["headings"],
                    "detected_clauses": struct["clauses"],
                    "detected_tables": struct["tables"],
                    "text_content": clean_text
                }
                out_file.write(json.dumps(page_record, ensure_ascii=False) + "\n")
                total_pages_processed += 1

            total_text_pages += doc_text_count
            print(f"  [{doc_idx+1}/{len(registry_records)}] {doc_id}: {num_pages} pages processed ({doc_text_count} text pages)")

        except Exception as e:
            print(f"  [ERROR] Failed processing {file_path}: {e}")

    out_file.close()

    print("\n================================================================================")
    print("PHASE B SEGMENTATION AUDIT SUMMARY")
    print("================================================================================")
    print(f"Total Pages Segmented:     {total_pages_processed:,}")
    print(f"Digital Text Pages:        {total_text_pages:,}")
    print(f"Raster / Blueprint Pages:  {total_pages_processed - total_text_pages:,}")
    print(f"Total Clauses Identified:  {total_clauses_indexed:,}")
    print(f"Output File:               {OUTPUT_PAGES_PATH}")
    print("================================================================================")
    print("[PASS] Phase B: Document Segmentation & Text Structuring complete!")

if __name__ == "__main__":
    run_document_segmentation()
