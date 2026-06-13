from evitalent.extraction.llm_single_event_extractor import LLMSingleEventExtractor
from evitalent.models.raw_achievement import AchievementCandidate


def test_single_event_extractor_returns_raw_event_without_standard_fields():
    candidate = AchievementCandidate(
        candidate_event_id="AC001",
        source_sentence="将招聘完成率提升至91%",
        isolated_clause="将招聘完成率提升至91%",
        detected_numeric_expressions=["91%"],
        detection_reason="contains_business_numeric_metric",
    )
    raw = LLMSingleEventExtractor().extract(candidate)
    dumped = raw.model_dump()
    assert dumped["metric_value"] == 91
    assert dumped["unit"] == "percent"
    assert "event_type" not in dumped
    assert "direction" not in dumped


def test_single_event_extractor_sanitizes_empty_llm_metric_value_to_candidate_fallback():
    class FakeClient:
        provider = "local_ollama"

        def generate_json(self, system_prompt, user_prompt):
            return {
                "raw_achievement_id": "RAW001",
                "raw_metric_name": "招聘完成率",
                "raw_achievement_text": "将招聘完成率提升至91%",
                "metric_value": "",
                "unit": "percent",
                "period_months": "",
                "approximate": "false",
                "lower_bound": "",
                "evidence_quote": "将招聘完成率提升至91%",
            }

    candidate = AchievementCandidate(
        candidate_event_id="AC001",
        source_sentence="将招聘完成率提升至91%",
        isolated_clause="将招聘完成率提升至91%",
        detected_numeric_expressions=["91%"],
        detection_reason="contains_business_numeric_metric",
    )
    raw = LLMSingleEventExtractor(client=FakeClient(), use_llm=True).extract(candidate)
    assert raw.metric_value == 91
    assert raw.unit == "percent"
    assert raw.period_months is None
    assert raw.approximate is False
    assert raw.lower_bound is False
