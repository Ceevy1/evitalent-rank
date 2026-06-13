import os

import pytest

from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction


def test_mock_extractor_loads_specified_fixture():
    candidate = MockExtractor().extract("demo_hr_001")
    assert isinstance(candidate, CandidateExtraction)
    assert candidate.candidate_id == "demo_hr_001"
    assert candidate.sensitive_information.masked_for_scoring is True


def test_mock_extractor_missing_fixture_has_clear_error():
    with pytest.raises(FileNotFoundError, match="Mock fixture not found"):
        MockExtractor().extract("not_existing_fixture")


def test_mock_extractor_does_not_require_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    assert "LLM_API_KEY" not in os.environ
    candidate = MockExtractor().extract("demo_brand_001")
    assert candidate.llm_metadata.provider == "mock"


def test_mock_extractor_load_all_returns_all_fixtures():
    candidates = MockExtractor().load_all()
    assert len(candidates) >= 8
    assert {candidate.candidate_id for candidate in candidates} >= {"demo_hr_001", "demo_hr_002", "demo_hr_003"}
