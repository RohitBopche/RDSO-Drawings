"""P0-R.6: layout-aware clause parser."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import clause_parser as cp  # noqa: E402


def row(idx, page, text, x0=99.0, y0=100.0, size=12.0, bold=True):
    return cp.Row(page, x0, y0, x0 + 200, y0 + 12, size, bold, text, idx)


def test_lis_rejects_out_of_sequence_values():
    keys = [(101, ""), (102, ""), (5300, ""), (103, ""), (2100, ""), (104, "")]
    kept = cp._lis(keys)
    assert [keys[i][0] for i in kept] == [101, 102, 103, 104]


def test_lis_orders_decimal_keys_lexicographically():
    keys = [cp._key(n, "decimal") for n in ["8.2", "8.2.1", "8.2.4", "8.3", "8.10"]]
    assert cp._lis(keys) == [0, 1, 2, 3, 4]


def test_head_needs_bold_margin_and_sequence():
    rows = [
        row(0, 10, "101 General - the ADEN shall"),
        row(1, 10, "1500 kg per axle", bold=False),          # a value, not bold
        row(2, 10, "102 Duties -", x0=300.0),                # far from the margin
        row(3, 10, "Body sentence that is long enough to fix the page margin at ninety nine.", x0=99.0, bold=False),
        row(4, 10, "103 Records -"),
    ]
    heads, _ = cp.find_heads(rows, cp.PROFILES["DOC:IRPWM:2024:ACS14"])
    assert [h.number for h in heads] == ["101", "103"]


def test_stmm_number_without_space_is_a_head():
    m = cp.HUNDREDS_RE.match("302Types of Rail Drilling Machine")
    assert m and m.group(1) == "302" and m.group(2) == "Types of Rail Drilling Machine"
    assert cp.HUNDREDS_RE.match("1500 kg per axle")  # matches the shape; bold + margin + sequence reject it


def test_contents_pages_are_recognised():
    rows = [row(i, 8, f"10{i} Topic name {i * 3}", bold=True) for i in range(1, 8)]
    assert cp.toc_pages(rows, cp.HUNDREDS_RE) == {8}


def test_deleted_paragraph_forms():
    for t in ("(Deleted)", "Deleted", "(Deleted) (ACS – 3)", "(Deleted)."):
        assert cp.DELETED_RE.match(t), t
    assert not cp.DELETED_RE.match("Deleted items shall be recorded")


def test_banner_only_matches_short_standalone_rows():
    assert cp.BANNER_RE.match("CHAPTER – 4")
    assert cp.BANNER_RE.match("Annexure - 2/1 (Para 204)")
    assert not cp.BANNER_RE.match("Annexure - 4/8 and Annexure - 4/9. For canted turnouts the spacing shall be")
    assert cp.BANNER_TITLE_RE.match("CHAPTER - 4") and not cp.BANNER_TITLE_RE.match("Section Limit Boards -")


def test_irpwm_para_429_spans_its_page_and_is_complete():
    import json
    nodes = {json.loads(l)["id"]: json.loads(l)
             for l in (ROOT / "data/knowledge-graph/canonical/nodes.jsonl").read_text(encoding="utf-8").splitlines()}
    n = nodes["CLAUSE:IRPWM:CH_04:PARA_429"]
    assert n["page"] == 195 and len(n["text"]) > 1200          # the old extractor cut at 1,200
    assert "Annexure - 4/8" in n["text"]                        # not stopped by an inline "Annexure" phrase
