"""Static regression checks for the Manuals Knowledge Graph UI contract.

These checks intentionally validate the browser-side hierarchy contract without
requiring a WebGL/browser runner. They protect the production invariants that
must hold at runtime:
  Manual -> authoritative Chapters only
  Chapter -> structural content only
  Manual/Drawing edges remain hidden
  Manuals entry resets to a collapsed chapter-first view
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


def _source() -> str:
    assert INDEX.exists(), f"missing {INDEX}"
    return INDEX.read_text(encoding="utf-8")


def test_manual_frontend_uses_authoritative_structure():
    source = _source()
    assert "window.RDSO_MANUAL_STRUCTURE" in source
    assert "window.RDSO_MANUAL_CONTENT_INDEX" in source
    assert "Structure: 'AUTHORITATIVE'" in source
    assert "Authoritative manual chapter registry" in source


def test_manual_hierarchy_allows_only_structural_relationships():
    source = _source()
    match = re.search(
        r"const MANUAL_STRUCTURAL_RELS = new Set\(\[(.*?)\]\);",
        source,
        flags=re.DOTALL,
    )
    assert match, "manual structural relationship allowlist is missing"

    relations = set(re.findall(r"'([A-Z_]+)'", match.group(1)))
    assert relations == {
        "HAS_CHAPTER",
        "HAS_SECTION",
        "HAS_CLAUSE",
        "HAS_TABLE",
        "HAS_FIGURE",
        "HAS_EVIDENCE",
    }

    assert "if (parentEntry.universe === 'manuals' && !MANUAL_STRUCTURAL_RELS.has(e.rel)) return;" in source


def test_manual_frontend_hard_blocks_cross_universe_edges():
    source = _source()
    assert "function addEdgeToGraph(edgeData)" in source
    assert "getNodeUniverse(sourceData) !== getNodeUniverse(targetData)" in source
    assert "Manual and Drawing universes remain hard-isolated" in source


def test_manual_entry_resets_descendants_and_selects_canonical_root():
    source = _source()
    assert "Array.from(expandedNodeIds).forEach" in source
    assert "h && h.universe === 'manuals'" in source
    assert "DOC:IRPWM:2024:ACS14" in source
    assert "switchDrawerTab('manuals')" in source


def test_single_click_drills_down_through_hierarchy():
    source = _source()
    click_block = source[source.index("// Node Click Selection") : source.index("function inspectNode")]
    assert "inspectNode(hit);" in click_block
    assert "toggleNodeExpansion(hit.data.id);" in click_block


def test_manual_layout_is_chapter_then_content():
    source = _source()
    assert "function layoutManualChildren(manualId)" in source
    assert "function layoutManualChapterChildren(chapterId)" in source
    assert "entry.id.startsWith('DOC:')" in source
    assert "entry.id.startsWith('CHAPTER:')" in source


def test_manual_frontend_prefers_authoritative_source_heading_tree():
    source = _source()
    assert "authoritativeHeadingByChapter" in source
    assert "heading_kind" in source
    assert "parent_heading_ref" in source
    assert "Authoritative source-heading hierarchy" in source
    assert "if (chapterAuthoritativeHeadings.length === 0)" in source
    assert "EXTRACTED_HEADING_UNVERIFIED" in source


def test_manual_frontend_preserves_structural_heading_relationships():
    source = _source()
    assert "const parentRef = n.parent_heading_ref || n.provenance?.parent_heading_ref;" in source
    assert "const parentId = parent ? parent.id : chapterId;" in source
    assert "rel: 'HAS_SECTION'" in source


def test_manual_frontend_consumes_readiness_as_qa_metadata_only():
    source = _source()
    assert "manualReadinessAudit" in source
    assert "manual_hierarchy_audit_v1" in source
    assert "readiness_status" in source
    assert "readiness_reasons" in source
    assert "ownership_status" in source
    assert "ownership_issue_pages" in source
    assert "Manual readiness is a QA signal only. It never participates in hierarchy construction." in source
    assert "manual-readiness-card" in source


def test_manual_readiness_does_not_replace_authoritative_hierarchy():
    source = _source()
    hierarchy_start = source.index("function buildHierarchyStructure()")
    readiness_start = source.index("function renderManualReadiness(data)")
    assert readiness_start < hierarchy_start
    assert "MANUAL_STRUCTURAL_RELS" in source
    assert "authoritativeHeadingByChapter" in source
