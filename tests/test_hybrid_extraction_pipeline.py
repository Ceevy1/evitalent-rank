from evitalent.demo_samples import EXPECTED_EVENTS, HR_MULTI_ACHIEVEMENT_TEXT
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline
from evitalent.scoring.ranker import rank_candidates


def test_hybrid_hr_pipeline_extracts_five_standard_events_and_scores():
    result = HybridExtractionPipeline().extract(HR_MULTI_ACHIEVEMENT_TEXT, "doc_hybrid_hr", "candidate_hybrid_hr")
    normalized = result.normalized_events
    assert len(normalized) == 5
    triples = [(event.event_type, event.direction, event.metric_value) for event in normalized]
    assert triples == EXPECTED_EVENTS["hr"]
    assert all(event.grounding_status == "passed" for event in normalized)
    assert all(event.eligible_for_core_achievement_score for event in normalized)
    assert "recruitment_completion_rate" in [event.event_type for event in normalized]
    assert normalized[0].event_type == "recruitment_delivery"
    ranking = rank_candidates([result.candidate_extraction], "hr")
    assert ranking.candidates[0].rank_score > 0
