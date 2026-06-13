from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction
from evitalent.scoring.penalty_scorer import score_penalty


def test_date_conflict_penalty():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["career_records"][1]["start_date"] = "2019-06"
    broken = CandidateExtraction.model_validate(payload)
    penalty, flags = score_penalty(broken)
    assert penalty >= 3
    assert penalty <= 8
    assert flags


def test_severe_overlap_penalty():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["career_records"][1]["start_date"] = "2018-01"
    broken = CandidateExtraction.model_validate(payload)
    penalty, _ = score_penalty(broken)
    assert penalty >= 6
    assert penalty <= 8


def test_missing_achievement_evidence_caps_at_eight():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["achievement_events"][0]["evidence_id"] = "missing_achievement_evidence"
    broken = CandidateExtraction.model_validate(payload)
    penalty, flags = score_penalty(broken)
    assert penalty == 8
    assert "重大成果无法对应证据" in flags
