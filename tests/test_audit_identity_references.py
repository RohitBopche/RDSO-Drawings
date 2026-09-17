import json
from pathlib import Path

from scripts.audit_identity_references import build_report, load_alias_map, scan


def make_repo(tmp_path: Path) -> Path:
    (tmp_path / "data/knowledge-graph/canonical").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data/knowledge-graph/canonical/identity_aliases.json").write_text(
        json.dumps({"version": 1, "mappings": [{
            "canonical_id": "DOC:TEST:1",
            "aliases": ["doc_test_1"],
        }]}),
        encoding="utf-8",
    )
    return tmp_path


def test_inventory_is_machine_readable_and_classified(tmp_path):
    root = make_repo(tmp_path)
    (root / "data/knowledge-graph/canonical/nodes.jsonl").write_text(
        '{"id":"doc_test_1","type":"DOCUMENT"}\n', encoding="utf-8"
    )
    (root / "index.html").write_text(
        'const id = "doc_test_1";\n', encoding="utf-8"
    )
    aliases = load_alias_map(root / "data/knowledge-graph/canonical/identity_aliases.json")
    findings = scan(root, aliases, {
        (root / "data/knowledge-graph/canonical/identity_aliases.json").resolve()
    })
    report = build_report(root, aliases, findings)

    assert report["schema_version"] == 1
    assert report["non_destructive"] is True
    assert report["reference_count"] == 2
    assert report["summary"]["files_with_references"] == 2
    assert {item["reference_kind"] for item in report["references"]} == {
        "canonical_data_identity", "application_reference"
    }


def test_token_matching_rejects_substrings(tmp_path):
    root = make_repo(tmp_path)
    (root / "notes.md").write_text(
        "doc_test_10 should not match\n doc_test_1 is exact\n", encoding="utf-8"
    )
    aliases = load_alias_map(root / "data/knowledge-graph/canonical/identity_aliases.json")
    findings = scan(root, aliases, {
        (root / "data/knowledge-graph/canonical/identity_aliases.json").resolve()
    })
    assert len(findings) == 1
    assert findings[0].alias == "doc_test_1"
