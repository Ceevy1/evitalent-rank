from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.extraction.llm_client import LLMClient
from evitalent.extraction.llm_single_event_extractor import LLMSingleEventExtractor
from evitalent.models.raw_achievement import AchievementCandidate
from evitalent.settings import get_settings


def main() -> None:
    candidate = AchievementCandidate(
        candidate_event_id="AC001",
        source_sentence="某候选人担任生产经理，主导工艺优化，使原料损耗下降0.6%。",
        isolated_clause="使原料损耗下降0.6%",
        detected_numeric_expressions=["0.6%"],
        linked_career_context="生产经理",
        detection_reason="contains_business_numeric_metric",
    )
    settings = get_settings()
    use_llm = settings.llm_provider in {"local_ollama", "compatible_api"} and bool(settings.llm_model)
    extractor = LLMSingleEventExtractor(client=LLMClient(provider=settings.llm_provider), use_llm=use_llm)
    raw = extractor.extract(candidate)
    print(raw.model_dump_json(indent=2))
    print("standard_event_type_is_not_generated=true")


if __name__ == "__main__":
    main()
