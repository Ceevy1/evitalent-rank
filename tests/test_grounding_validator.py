from evitalent.extraction.grounding_validator import GroundingValidator
from evitalent.models.raw_achievement import AchievementCandidate, RawAchievementEvent
from evitalent.normalization import build_normalized_achievement


def _candidate_and_raw(clause="完成一线员工招聘120人", value=120, quote=None):
    candidate = AchievementCandidate(candidate_event_id="AC001", source_sentence=clause, isolated_clause=clause, detected_numeric_expressions=["120人"], detection_reason="test")
    raw = RawAchievementEvent(raw_achievement_id="RAW001", raw_metric_name="招聘人数", raw_achievement_text=clause, metric_value=value, metric_value_upper=None, unit="person", evidence_quote=clause if quote is None else quote)
    return candidate, raw


def test_grounding_passes_when_value_in_quote():
    candidate, raw = _candidate_and_raw()
    normalized = build_normalized_achievement(raw, 1)
    result = GroundingValidator().validate(candidate.isolated_clause, candidate, raw, normalized)
    assert result.grounding_status == "passed"


def test_grounding_fails_when_value_bound_to_wrong_quote():
    candidate, raw = _candidate_and_raw(value=120, quote="招聘完成率提升至88%")
    normalized = build_normalized_achievement(raw, 1)
    result = GroundingValidator().validate(candidate.isolated_clause, candidate, raw, normalized)
    assert result.grounding_status == "failed"


def test_grounding_fails_when_quote_missing():
    candidate, raw = _candidate_and_raw(quote="")
    normalized = build_normalized_achievement(raw, 1)
    result = GroundingValidator().validate(candidate.isolated_clause, candidate, raw, normalized)
    assert result.grounding_status == "failed"
