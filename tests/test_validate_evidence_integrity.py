import json
from pathlib import Path
import pytest
from scripts.validate_evidence_integrity import validate_record_schema, load_jsonl


def test_validate_record_schema_valid():
    schema = {
        "required": ["evidence_id", "document_id", "extraction_method", "verification_status"],
        "properties": {
            "evidence_id": {"type": "string"},
            "document_id": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "verification_status": {"type": "string", "enum": ["unverified", "machine_extracted", "reviewed", "verified", "disputed"]}
        }
    }
    record = {
        "evidence_id": "ev:test:1",
        "document_id": "DOC:TEST:1",
        "extraction_method": "text_extract",
        "confidence": 0.95,
        "verification_status": "verified"
    }
    errors = validate_record_schema(record, schema)
    assert errors == []


def test_validate_record_schema_catches_missing_and_invalid_enum():
    schema = {
        "required": ["evidence_id", "document_id", "extraction_method", "verification_status"],
        "properties": {
            "evidence_id": {"type": "string"},
            "document_id": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "verification_status": {"type": "string", "enum": ["unverified", "machine_extracted", "reviewed", "verified", "disputed"]}
        }
    }
    record = {
        "evidence_id": "ev:test:1",
        # missing document_id
        "extraction_method": "text_extract",
        "confidence": 1.5,  # > 1.0
        "verification_status": "bogus_status"
    }
    errors = validate_record_schema(record, schema)
    assert len(errors) >= 3
    assert any("missing required property 'document_id'" in e for e in errors)
    assert any("confidence" in e for e in errors)
    assert any("verification_status" in e for e in errors)


def test_load_jsonl_nonexistent(tmp_path):
    missing = tmp_path / "nonexistent.jsonl"
    records, errors = load_jsonl(missing)
    assert len(records) == 0
    assert len(errors) == 1
    assert "does not exist" in errors[0]
