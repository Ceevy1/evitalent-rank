from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.demo_samples import HR_MULTI_ACHIEVEMENT_TEXT
from evitalent.extraction.llm_client import LLMClient
from evitalent.extraction.llm_single_event_extractor import LLMSingleEventExtractor
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline
from evitalent.scoring.ranker import rank_candidates
from evitalent.settings import get_settings


def main() -> None:
    settings = get_settings()
    use_llm = settings.llm_provider in {"local_ollama", "compatible_api"} and bool(settings.llm_model)
    single_event = LLMSingleEventExtractor(client=LLMClient(provider=settings.llm_provider), use_llm=use_llm)
    result = HybridExtractionPipeline(single_event_extractor=single_event).extract(HR_MULTI_ACHIEVEMENT_TEXT, "doc_demo_hybrid_hr", "candidate_demo_hybrid_hr")
    print(result.summary)
    for event in result.normalized_events:
        print(
            {
                "evidence_quote": event.evidence_quote,
                "metric_value": event.metric_value,
                "unit": event.unit,
                "event_type": event.event_type,
                "direction": event.direction,
                "normalization_rule_id": event.normalization_rule_id,
                "grounding_status": event.grounding_status,
                "eligible_for_scoring": event.eligible_for_core_achievement_score,
            }
        )
    ranking = rank_candidates([result.candidate_extraction], "hr")
    print(f"rank_score={ranking.candidates[0].rank_score}")


if __name__ == "__main__":
    main()
