import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from resolve_manual_hierarchy import heading_kind, numeric_parent, resolve_heading_sequence


def test_heading_depth_and_kind():
    assert heading_kind("2") == ("SECTION", 1)
    assert heading_kind("2.1") == ("SUBSECTION", 2)
    assert heading_kind("2.1.1") == ("SUBSECTION", 3)
    assert heading_kind("ANNEXURE-II") == ("ANNEXURE", 1)


def test_numeric_parent():
    assert numeric_parent("2.1") == "2"
    assert numeric_parent("2.1.1") == "2.1"
    assert numeric_parent("2") is None


def test_valid_nested_heading_sequence():
    headings, errors = resolve_heading_sequence([
        {"reference": "2", "title": "Track Structure", "source_page": 10},
        {"reference": "2.1", "title": "Rails", "source_page": 11},
        {"reference": "2.1.1", "title": "Rail Selection", "source_page": 11},
        {"reference": "2.2", "title": "Sleepers", "source_page": 12},
        {"reference": "ANNEXURE-I", "title": "Inspection Form", "source_page": 13},
    ], [10, 20])
    assert not errors
    assert headings[2]["parent_heading_ref"] == "2.1"
    assert headings[4]["heading_kind"] == "ANNEXURE"


def test_missing_parent_is_preserved_as_chapter_fallback():
    headings, errors = resolve_heading_sequence([
        {"reference": "2", "title": "Track Structure", "source_page": 10},
        {"reference": "2.1.1", "title": "Rail Selection", "source_page": 11},
    ], [10, 20])
    assert not errors
    assert headings[1]["parent_heading_ref"] == "2.1"
    assert headings[1]["parent_resolution"] == "CHAPTER_FALLBACK"
    assert headings[1]["parent_available_in_source"] is False


def test_reject_duplicate_and_out_of_range_heading():
    _, errors = resolve_heading_sequence([
        {"reference": "2", "title": "Track Structure", "source_page": 10},
        {"reference": "2", "title": "Duplicate", "source_page": 11},
        {"reference": "3", "title": "Outside", "source_page": 21},
    ], [10, 20])
    assert any("duplicate heading reference: 2" in e for e in errors)
    assert any("outside chapter range" in e for e in errors)


def test_canonical_graph_materializes_authoritative_nested_headings_and_deepest_clause_owner():
    from resolve_manual_hierarchy import resolve_canonical_graph

    chapter_id = "CHAPTER:TEST:CH_02"
    clause_id = "CLAUSE:TEST:PARA_2_1_1"
    canonical = {
        "entities": [
            {"id": chapter_id, "type": "CHAPTER", "domain": "manual", "universe": "manuals"},
            {"id": clause_id, "type": "CLAUSE", "domain": "manual", "universe": "manuals"},
        ],
        "edges": [
            {"from": chapter_id, "to": clause_id, "rel": "HAS_CLAUSE"},
        ],
        "facts": [],
        "metadata": {},
    }
    intermediate = {
        "manuals": [{
            "document_id": "DOC:TEST:2026",
            "alias": "TEST",
            "chapters": [{
                "chapter_id": chapter_id,
                "title": "Test Chapter",
                "page_range": [10, 20],
                "headings": [
                    {"reference": "2", "title": "Track Structure", "source_page": 10},
                    {"reference": "2.1", "title": "Rails", "source_page": 11},
                    {"reference": "2.1.1", "title": "Rail Selection", "source_page": 12},
                ],
                "clauses": [{
                    "clause_id": clause_id,
                    "para_number": "2.1.1",
                    "source_page": 12,
                }],
            }],
        }],
    }
    result, errors = resolve_canonical_graph(intermediate, canonical)
    assert not errors
    entities = {e["id"]: e for e in result["entities"]}
    assert entities["SECTION:TEST:CHAPTER_TEST_CH_02:SEC_2"]["heading_kind"] == "SECTION"
    assert entities["SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1_1"]["heading_kind"] == "SUBSECTION"
    assert any(e["from"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1" and e["to"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1_1" and e["rel"] == "HAS_SECTION" for e in result["edges"])
    assert any(e["from"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1_1" and e["to"] == clause_id and e["rel"] == "HAS_CLAUSE" for e in result["edges"])
    assert not any(e["from"] == "SUBSECTION:TEST:CHAPTER_TEST_CH_02:SEC_2_1" and e["to"] == clause_id and e["rel"] == "HAS_CLAUSE" for e in result["edges"])
    assert result["metadata"]["manual_hierarchy_resolved_headings"] == 3


def test_canonical_graph_materializes_orphan_heading_under_chapter():
    from resolve_manual_hierarchy import resolve_canonical_graph

    chapter_id = "CHAPTER:TEST:CH_08"
    canonical = {
        "entities": [{"id": chapter_id, "type": "CHAPTER", "domain": "manual", "universe": "manuals"}],
        "edges": [],
        "facts": [],
        "metadata": {},
    }
    intermediate = {
        "manuals": [{
            "document_id": "DOC:TEST:2026",
            "alias": "TEST",
            "chapters": [{
                "chapter_id": chapter_id,
                "title": "Test Chapter",
                "page_range": [10, 20],
                "headings": [
                    {"reference": "8.5.2", "title": "Detailed Requirement", "source_page": 12},
                ],
                "clauses": [],
            }],
        }],
    }
    result, errors = resolve_canonical_graph(intermediate, canonical)
    assert not errors
    hid = "SUBSECTION:TEST:CHAPTER_TEST_CH_08:SEC_8_5_2"
    entity = next(e for e in result["entities"] if e["id"] == hid)
    assert entity["specs"]["Structure Status"] == "AUTHORITATIVE_SOURCE_HEADING_ORPHAN"
    assert entity["parent_resolution"] == "CHAPTER_FALLBACK"
    assert any(
        e["from"] == chapter_id and e["to"] == hid and e["rel"] == "HAS_SECTION"
        for e in result["edges"]
    )


def test_coverage_audit_flags_sparse_chapters_as_warnings():
    from validate_manual_hierarchy import _coverage_audit
    errors, warnings, metrics = _coverage_audit({
        "chapter_id": "CHAPTER:TEST:CH_01",
        "page_range": [10, 12],
        "pages_seen": [10],
        "headings": [{"reference": "2.1", "source_page": 10, "title": "Heading"}],
        "clauses": [],
        "tables": [],
        "figures": [],
        "evidence": [],
    })
    assert errors == []
    assert metrics["pages_expected"] == 3
    assert metrics["pages_seen"] == 1
    assert metrics["headings"] == 1
    assert any("not observed" in warning for warning in warnings)


def test_coverage_audit_rejects_malformed_heading_references():
    from validate_manual_hierarchy import _coverage_audit
    errors, warnings, metrics = _coverage_audit({
        "chapter_id": "CHAPTER:TEST:CH_01",
        "page_range": [10, 10],
        "pages_seen": [10],
        "headings": [{"reference": "not-a-reference", "source_page": 10, "title": "Bad"}],
    })
    assert any("malformed heading reference" in error for error in errors)


def test_coverage_audit_classifies_health_states():
    from validate_manual_hierarchy import _coverage_audit

    base = {
        "chapter_id": "CHAPTER:TEST:CH_01",
        "page_range": [10, 10],
        "pages_seen": [10],
        "clauses": [],
    }
    errors, warnings, metrics = _coverage_audit({**base, "headings": []})
    assert not errors
    assert metrics["coverage_class"] == "NO_SOURCE_HEADINGS"

    errors, warnings, metrics = _coverage_audit({
        **base,
        "headings": [
            {"reference": "2", "source_page": 10, "title": "Section"},
            {"reference": "2.1", "source_page": 10, "title": "Subsection"},
        ],
    })
    assert not errors
    assert metrics["coverage_class"] == "HEALTHY"

    errors, warnings, metrics = _coverage_audit({
        **base,
        "headings": [{"reference": "2", "source_page": 10, "title": "Section"}],
    })
    assert not errors
    assert metrics["coverage_class"] == "SPARSE"

    errors, warnings, metrics = _coverage_audit({
        **base,
        "headings": [{"reference": "bad", "source_page": 10, "title": "Bad"}],
    })
    assert errors
    assert metrics["coverage_class"] == "MALFORMED"


def test_audit_manual_corpus_aggregates_machine_readable_report():
    from validate_manual_hierarchy import audit_manual_corpus
    payload = {"manuals": [{"document_id": "DOC:TEST:2026", "alias": "TEST", "chapters": [
        {"chapter_id": "CHAPTER:TEST:CH_01", "page_range": [10, 10], "pages_seen": [10], "headings": [
            {"reference": "2", "source_page": 10, "title": "Section"},
            {"reference": "2.1", "source_page": 10, "title": "Subsection"}], "clauses": []},
        {"chapter_id": "CHAPTER:TEST:CH_02", "page_range": [20, 20], "pages_seen": [20], "headings": [], "clauses": []},
    ]}]}
    report = audit_manual_corpus(payload)
    assert report["schema_version"] == "manual_hierarchy_audit_v1"
    assert report["checked_chapters"] == 2
    assert report["class_counts"]["HEALTHY"] == 1
    assert report["class_counts"]["NO_SOURCE_HEADINGS"] == 1
    assert report["manuals"][0]["chapters"] == 2
    assert report["status"] == "PASS"


def test_coverage_audit_builds_complete_page_matrix():
    from validate_manual_hierarchy import _coverage_audit

    errors, warnings, metrics = _coverage_audit({
        "chapter_id": "CHAPTER:TEST:CH_03",
        "page_range": [30, 34],
        "pages_seen": [30, 31, 33],
        "headings": [{"reference": "3", "source_page": 30, "title": "Section"}],
        "clauses": [{"clause_id": "C1", "source_page": 31}],
        "tables": [{"id": "T1", "source_page": 33}],
        "figures": [],
        "evidence": [],
    }, [99])

    assert not errors
    assert metrics["pages_expected"] == 5
    assert metrics["pages_seen"] == 3
    assert metrics["missing_pages"] == [32, 34]
    assert metrics["unmapped_pages"] == [99]
    assert metrics["pages_with_headings"] == 1
    assert metrics["pages_with_clauses"] == 1
    assert metrics["content_empty_pages"] == []
    assert metrics["coverage_ratio"] == 0.6


def test_coverage_audit_identifies_observed_content_empty_pages():
    from validate_manual_hierarchy import _coverage_audit

    errors, warnings, metrics = _coverage_audit({
        "chapter_id": "CHAPTER:TEST:CH_04",
        "page_range": [40, 42],
        "pages_seen": [40, 41, 42],
        "headings": [{"reference": "4", "source_page": 40, "title": "Section"}],
        "clauses": [{"clause_id": "C1", "source_page": 42}],
        "tables": [],
        "figures": [],
        "evidence": [],
    })

    assert not errors
    assert metrics["content_empty_pages"] == [41]


def test_audit_manual_corpus_aggregates_manual_page_completeness():
    from validate_manual_hierarchy import audit_manual_corpus

    payload = {"manuals": [{
        "document_id": "DOC:TEST:2026",
        "alias": "TEST",
        "unmapped_pages": [99],
        "chapters": [{
            "chapter_id": "CHAPTER:TEST:CH_01",
            "page_range": [10, 12],
            "pages_seen": [10, 12],
            "headings": [{"reference": "2", "source_page": 10, "title": "Section"}],
            "clauses": [{"clause_id": "C1", "source_page": 12}],
        }]
    }]}

    report = audit_manual_corpus(payload)
    row = report["manuals"][0]
    assert row["pages_expected"] == 3
    assert row["pages_seen"] == 2
    assert row["observed_page_owner_count"] == 2
    assert row["observed_pages_with_multiple_chapters"] == []
    assert row["missing_pages"] == [11]
    assert row["unmapped_pages"] == [99]
    assert row["pages_with_headings"] == 1
    assert row["pages_with_clauses"] == 1
    assert row["content_empty_pages"] == []
    assert row["coverage_ratio"] == 2 / 3


def test_audit_manual_corpus_uses_union_of_overlapping_chapter_ranges():
    from validate_manual_hierarchy import audit_manual_corpus

    payload = {"manuals": [{
        "document_id": "DOC:TEST:2026",
        "alias": "TEST",
        "chapters": [
            {
                "chapter_id": "CHAPTER:TEST:CH_01",
                "page_range": [10, 12],
                "pages_seen": [10, 11, 12],
                "headings": [],
            },
            {
                "chapter_id": "CHAPTER:TEST:CH_02",
                "page_range": [12, 14],
                "pages_seen": [12, 13, 14],
                "headings": [],
            },
        ],
    }]}

    report = audit_manual_corpus(payload)
    row = report["manuals"][0]
    assert row["pages_expected"] == 5
    assert row["pages_seen"] == 4
    assert row["missing_pages"] == []
    assert row["observed_page_owner_count"] == 4
    assert row["observed_pages_with_multiple_chapters"] == [12]
    assert row["coverage_ratio"] == 0.8


def test_corpus_audit_exposes_registry_page_ownership_metrics():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    first = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{first['num']:02d}"
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "chapters": [{
            "chapter_id": chapter_id,
            "page_range": [first["page_start"], first["page_end"]],
            "pages_seen": [first["page_start"]],
            "headings": [],
            "clauses": [],
        }]
    }]}

    report = audit_manual_corpus(payload)
    row = report["manuals"][0]
    audit = row["registry_page_audit"]
    assert audit["registered_pages"] == first["page_end"] - first["page_start"] + 1
    assert audit["observed_pages"] == 1
    assert audit["missing_pages"]
    assert audit["unmapped_pages"] == []
    assert audit["ownership_mismatches"] == []


def test_corpus_audit_emits_chapter_and_manual_readiness_status():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}"
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "unmapped_pages": [],
        "chapters": [{
            "chapter_id": chapter_id,
            "page_range": [spec["page_start"], spec["page_end"]],
            "pages_seen": [spec["page_start"]],
            "headings": [],
            "clauses": [],
        }]
    }]}

    report = audit_manual_corpus(payload)
    assert report["chapters"][0]["status"] == "ATTENTION"
    assert report["manuals"][0]["status"] == "ATTENTION"
    assert report["chapters"][0]["readiness_status"] == "ATTENTION"
    assert report["chapters"][0]["readiness_reasons"] == ["no_source_headings"]
    assert report["chapters"][0]["ownership_status"] == "CLEAN"


def test_corpus_audit_summary_aggregates_readiness_and_page_gaps():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}"
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "unmapped_pages": [999],
        "chapters": [{
            "chapter_id": chapter_id,
            "page_range": [spec["page_start"], spec["page_end"]],
            "pages_seen": [spec["page_start"]],
            "headings": [],
            "clauses": [],
        }]
    }]}

    report = audit_manual_corpus(payload)
    summary = report["summary"]
    assert summary["manuals_total"] == 1
    assert summary["chapters_total"] == 1
    assert summary["manuals_by_status"]["ATTENTION"] == 1
    assert summary["chapters_by_status"]["ATTENTION"] == 1
    assert chapter_id in summary["chapters_requiring_attention"]
    assert summary["pages"]["unmapped"] == 1


def test_corpus_audit_attributes_registry_ownership_mismatch_to_affected_chapter():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    first, second = registry["chapters"][:2]
    first_id = f"CHAPTER:{registry['alias']}:CH_{first['num']:02d}"
    second_id = f"CHAPTER:{registry['alias']}:CH_{second['num']:02d}"
    boundary = first["page_end"]
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "chapters": [
            {
                "chapter_id": first_id,
                "page_range": [first["page_start"], first["page_end"]],
                "pages_seen": [first["page_start"], boundary],
                "headings": [],
                "clauses": [],
            },
            {
                "chapter_id": second_id,
                "page_range": [second["page_start"], second["page_end"]],
                "pages_seen": [second["page_start"]],
                "headings": [],
                "clauses": [],
            },
        ],
    }]}

    # Deliberately place the boundary page under the wrong chapter as well.
    payload["manuals"][0]["chapters"][1]["pages_seen"].append(boundary)

    report = audit_manual_corpus(payload)
    second_row = next(c for c in report["chapters"] if c["chapter_id"] == second_id)
    assert second_row["ownership_status"] == "BLOCKED"
    assert second_row["ownership_issue_pages"] == [boundary]
    assert second_row["readiness_status"] == "BLOCKED"
    assert any("ownership mismatch" in e for e in second_row["errors"])
    assert report["error_count"] > 0


def test_manual_readiness_aggregates_explicit_chapter_states():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    first, second = registry["chapters"][:2]
    first_id = f"CHAPTER:{registry['alias']}:CH_{first['num']:02d}"
    second_id = f"CHAPTER:{registry['alias']}:CH_{second['num']:02d}"
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "chapters": [
            {
                "chapter_id": first_id,
                "page_range": [first["page_start"], first["page_start"] + 1],
                "pages_seen": [first["page_start"], first["page_start"] + 1],
                "headings": [
                    {"reference": "1", "source_page": first["page_start"], "title": "SECTION ONE"},
                    {"reference": "1.1", "source_page": first["page_start"] + 1, "title": "SUBSECTION ONE"},
                ],
                "clauses": [],
            },
            {
                "chapter_id": second_id,
                "page_range": [second["page_start"], second["page_start"] + 1],
                "pages_seen": [second["page_start"], second["page_start"] + 1],
                "headings": [
                    {"reference": "not-a-heading", "source_page": second["page_start"], "title": "INVALID"},
                ],
                "clauses": [],
            },
        ],
    }]}

    report = audit_manual_corpus(payload)
    manual = report["manuals"][0]
    assert manual["status"] == "BLOCKED"
    assert manual["chapter_status_counts"]["HEALTHY"] == 1
    assert manual["chapter_status_counts"]["BLOCKED"] == 1
    assert manual["chapter_status_counts"]["ATTENTION"] == 0


def test_manual_readiness_treats_unmapped_pages_as_manual_attention_not_ownership_block():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}"
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "unmapped_pages": [9999],
        "chapters": [{
            "chapter_id": chapter_id,
            "page_range": [spec["page_start"], spec["page_start"] + 1],
            "pages_seen": [spec["page_start"], spec["page_start"] + 1],
            "headings": [
                {"reference": "1", "source_page": spec["page_start"], "title": "SECTION ONE"},
                {"reference": "1.1", "source_page": spec["page_start"] + 1, "title": "SUBSECTION ONE"},
            ],
            "clauses": [],
        }]
    }]}

    report = audit_manual_corpus(payload)
    manual = report["manuals"][0]
    chapter = report["chapters"][0]
    assert chapter["readiness_status"] == "HEALTHY"
    assert chapter["ownership_status"] == "CLEAN"
    assert manual["status"] == "ATTENTION"
    assert manual["unmapped_pages"] == [9999]


def test_chapter_readiness_includes_content_empty_reason():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}"
    payload = {"manuals": [{"document_id": doc_id, "alias": registry["alias"], "chapters": [{
        "chapter_id": chapter_id,
        "page_range": [spec["page_start"], spec["page_start"] + 2],
        "pages_seen": [spec["page_start"], spec["page_start"] + 1, spec["page_start"] + 2],
        "headings": [{"reference": "1", "source_page": spec["page_start"], "title": "SECTION ONE"}],
        "clauses": [{"clause_id": "C1", "source_page": spec["page_start"] + 2}],
        "tables": [], "figures": [], "evidence": [],
    }]}]}

    report = audit_manual_corpus(payload)
    row = report["chapters"][0]
    assert row["readiness_status"] == "ATTENTION"
    assert row["readiness_reasons"] == ["sparse", "content_empty_pages"]
    assert row["content_empty_pages"] == [spec["page_start"] + 1]


def test_manual_readiness_reasons_explain_status_precedence():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    first, second = registry["chapters"][:2]
    first_id = f"CHAPTER:{registry['alias']}:CH_{first['num']:02d}"
    second_id = f"CHAPTER:{registry['alias']}:CH_{second['num']:02d}"
    boundary = first["page_end"]
    payload = {"manuals": [{"document_id": doc_id, "alias": registry["alias"], "chapters": [
        {
            "chapter_id": first_id,
            "page_range": [first["page_start"], first["page_start"]],
            "pages_seen": [first["page_start"]],
            "headings": [{"reference": "1", "source_page": first["page_start"], "title": "SECTION ONE"}],
            "clauses": [],
        },
        {
            "chapter_id": second_id,
            "page_range": [second["page_start"], second["page_start"] + 1],
            "pages_seen": [second["page_start"], second["page_start"] + 1],
            "headings": [{"reference": "2.1", "source_page": second["page_start"], "title": "SUBSECTION WITHOUT PARENT"}],
            "clauses": [],
        },
    ], "unmapped_pages": [9999]}]}
    payload["manuals"][0]["chapters"][1]["pages_seen"].append(boundary)

    report = audit_manual_corpus(payload)
    manual = report["manuals"][0]
    assert manual["readiness_status"] == "BLOCKED"
    assert manual["readiness_reasons"] == ["chapter_blocked", "unmapped_pages"]


def test_manual_readiness_is_healthy_only_when_no_signals_apply():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}"
    payload = {"manuals": [{"document_id": doc_id, "alias": registry["alias"], "chapters": [{
        "chapter_id": chapter_id,
        "page_range": [spec["page_start"], spec["page_start"] + 1],
        "pages_seen": [spec["page_start"], spec["page_start"] + 1],
        "headings": [
            {"reference": "1", "source_page": spec["page_start"], "title": "SECTION ONE"},
            {"reference": "1.1", "source_page": spec["page_start"] + 1, "title": "SUBSECTION ONE"},
        ],
        "clauses": [],
    }]}]}

    report = audit_manual_corpus(payload)
    manual = report["manuals"][0]
    assert manual["readiness_status"] == "HEALTHY"
    assert manual["readiness_reasons"] == ["complete_manual_readiness"]



def test_manual_validator_reports_empty_corpus_artifact_as_blocker(tmp_path, monkeypatch, capsys):
    import validate_manual_hierarchy as validator

    empty = tmp_path / "all_chapters_extracted.json"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    result = validator.main()
    output = capsys.readouterr().out
    assert result == 2
    assert "BLOCKED: Manual corpus artifact is empty" in output



def test_manual_validator_rejects_empty_manual_list(tmp_path, monkeypatch, capsys):
    import validate_manual_hierarchy as validator

    artifact = tmp_path / "all_chapters_extracted.json"
    artifact.write_text(json.dumps({"manuals": []}), encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    result = validator.main()
    output = capsys.readouterr().out
    assert result == 2
    assert "BLOCKED: Manual corpus artifact contains no manuals" in output


def test_manual_validator_rejects_invalid_top_level_schema(tmp_path, monkeypatch, capsys):
    import validate_manual_hierarchy as validator

    artifact = tmp_path / "all_chapters_extracted.json"
    artifact.write_text(json.dumps({"chapters": []}), encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    result = validator.main()
    output = capsys.readouterr().out
    assert result == 2
    assert "BLOCKED: Manual corpus artifact has invalid top-level schema" in output



def test_manual_hierarchy_script_has_cli_entrypoint():
    import validate_manual_hierarchy as validator

    assert callable(validator.main)
    source = validator.__file__
    text = open(source, encoding="utf-8").read()
    assert 'if __name__ == "__main__":' in text
    assert "raise SystemExit(main())" in text



def test_chapter_readiness_preserves_multiple_attention_reasons():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}"
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "chapters": [{
            "chapter_id": chapter_id,
            "page_range": [spec["page_start"], spec["page_start"] + 2],
            "pages_seen": [spec["page_start"]],
            "headings": [],
            "clauses": [],
        }]
    }]}

    report = audit_manual_corpus(payload)
    row = report["chapters"][0]
    assert row["readiness_status"] == "ATTENTION"
    assert row["readiness_reasons"] == ["no_source_headings", "missing_pages"]


def test_blocked_chapter_preserves_structural_error_and_coverage_reason():
    from validate_manual_hierarchy import audit_manual_corpus, MANUAL_CHAPTER_REGISTRY

    doc_id, registry = next(iter(MANUAL_CHAPTER_REGISTRY.items()))
    spec = registry["chapters"][0]
    chapter_id = f"CHAPTER:{registry['alias']}:CH_{spec['num']:02d}"
    payload = {"manuals": [{
        "document_id": doc_id,
        "alias": registry["alias"],
        "chapters": [{
            "chapter_id": chapter_id,
            "page_range": [spec["page_start"], spec["page_start"] + 1],
            "pages_seen": [spec["page_start"]],
            "headings": [{
                "reference": "2.1",
                "source_page": spec["page_start"],
                "title": "SUBSECTION WITHOUT PARENT",
            }],
            "clauses": [],
        }]
    }]}

    report = audit_manual_corpus(payload)
    row = report["chapters"][0]
    assert row["readiness_status"] == "BLOCKED"
    assert row["readiness_reasons"] == [
        "structural_or_ownership_error",
        "sparse",
        "missing_pages",
    ]
