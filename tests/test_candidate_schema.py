from copy import deepcopy

import pytest

from evitalent.extraction.schema_validator import SchemaValidationError, SchemaValidator
from evitalent.settings import PROJECT_ROOT


def _fixture_payload():
    import json

    path = PROJECT_ROOT / "data" / "fixtures" / "extracted" / "demo_hr_001.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_extracted_fixtures_pass_schema():
    validator = SchemaValidator()
    paths = sorted((PROJECT_ROOT / "data" / "fixtures" / "extracted").glob("*.json"))
    assert len(paths) >= 8
    for path in paths:
        validator.validate_file_or_raise(path)


def test_masked_for_scoring_false_fails_schema():
    payload = _fixture_payload()
    payload["sensitive_information"]["masked_for_scoring"] = False
    with pytest.raises(SchemaValidationError):
        SchemaValidator().validate_or_raise(payload)


def test_missing_required_arrays_fail_schema():
    payload = _fixture_payload()
    del payload["achievement_events"]
    with pytest.raises(SchemaValidationError):
        SchemaValidator().validate_or_raise(payload)

    payload = _fixture_payload()
    del payload["evidence_items"]
    with pytest.raises(SchemaValidationError):
        SchemaValidator().validate_or_raise(payload)


def test_invalid_event_type_fails_schema():
    payload = _fixture_payload()
    payload["achievement_events"][0]["event_type"] = "invalid_event"
    with pytest.raises(SchemaValidationError):
        SchemaValidator().validate_or_raise(payload)
