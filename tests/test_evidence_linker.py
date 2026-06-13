from copy import deepcopy

from evitalent.extraction.evidence_linker import check_evidence_links
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction


def test_valid_evidence_links_pass():
    candidate = MockExtractor().extract("demo_hr_001")
    result = check_evidence_links(candidate)
    assert result["passed"] is True
    assert result["missing_evidence_ids"] == []
    assert result["invalid_scoring_links"] == []


def test_missing_evidence_id_is_reported():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["achievement_events"][0]["evidence_id"] = "ev_missing"
    broken = CandidateExtraction.model_validate(payload)
    result = check_evidence_links(broken)
    assert result["passed"] is False
    assert "ev_missing" in result["missing_evidence_ids"]


def test_grade_d_evidence_cannot_be_used_for_main_scoring():
    candidate = MockExtractor().extract("demo_hr_003")
    payload = candidate.model_dump(mode="json")
    for item in payload["evidence_items"]:
        if item["evidence_id"] == "ev_hr3_ach2":
            item["used_for_scoring"] = True
    broken = CandidateExtraction.model_validate(payload)
    result = check_evidence_links(broken)
    assert result["passed"] is False
    assert any(link["reason"] == "grade_d_evidence_cannot_enter_main_scoring" for link in result["invalid_scoring_links"])


def test_scorable_achievement_links_back_to_quote():
    candidate = MockExtractor().extract("demo_ecommerce_001")
    evidence_by_id = {item.evidence_id: item for item in candidate.evidence_items}
    for event in candidate.achievement_events:
        if event.evidence_grade.value in {"A", "B"}:
            assert evidence_by_id[event.evidence_id].quote
            assert evidence_by_id[event.evidence_id].used_for_scoring is True
