from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from evitalent.achievement_detection import AchievementCandidateDetector
from evitalent.extraction.extraction_assembler import assemble_candidate_extraction
from evitalent.extraction.grounding_validator import GroundingValidator
from evitalent.extraction.llm_single_event_extractor import LLMSingleEventExtractor
from evitalent.extraction.llm_structure_extractor import LLMStructureExtractor
from evitalent.extraction.safety_validator import assert_redacted_text_safe
from evitalent.models.extraction import CandidateExtraction
from evitalent.models.normalized_achievement import NormalizedAchievementEvent
from evitalent.models.raw_achievement import AchievementCandidate, RawAchievementEvent
from evitalent.normalization import build_normalized_achievement


@dataclass
class HybridExtractionResult:
    candidate_extraction: CandidateExtraction
    achievement_candidates: list[AchievementCandidate]
    raw_events: list[RawAchievementEvent]
    normalized_events: list[NormalizedAchievementEvent]
    latency_seconds: float

    @property
    def summary(self) -> dict:
        grounded = [event for event in self.normalized_events if event.grounding_status == "passed"]
        needs_review = [event for event in self.normalized_events if not event.eligible_for_core_achievement_score]
        return {
            "structure_extraction_status": "completed",
            "achievement_candidate_count": len(self.achievement_candidates),
            "raw_event_count": len(self.raw_events),
            "normalized_event_count": len(self.normalized_events),
            "grounded_event_count": len(grounded),
            "needs_review_event_count": len(needs_review),
            "eligible_for_scoring": bool(self.candidate_extraction.achievement_events),
            "achievement_validation_rows": [
                {
                    "原文证据": event.evidence_quote,
                    "数值": event.metric_value,
                    "单位": event.unit,
                    "系统标准事件": event.event_type,
                    "方向": event.direction,
                    "校验状态": event.grounding_status,
                    "是否计分": event.eligible_for_core_achievement_score and event.grounding_status == "passed",
                }
                for event in self.normalized_events
            ],
        }


class HybridExtractionPipeline:
    def __init__(
        self,
        detector: AchievementCandidateDetector | None = None,
        structure_extractor: LLMStructureExtractor | None = None,
        single_event_extractor: LLMSingleEventExtractor | None = None,
        grounding_validator: GroundingValidator | None = None,
    ) -> None:
        self.detector = detector or AchievementCandidateDetector()
        self.structure_extractor = structure_extractor or LLMStructureExtractor()
        self.single_event_extractor = single_event_extractor or LLMSingleEventExtractor()
        self.grounding_validator = grounding_validator or GroundingValidator()

    def extract(self, redacted_text: str, document_id: str = "hybrid_demo_doc", candidate_id: str = "hybrid_demo_candidate") -> HybridExtractionResult:
        started = perf_counter()
        assert_redacted_text_safe(redacted_text)
        structure = self.structure_extractor.extract(redacted_text, document_id)
        domain = structure.target_domains[0] if structure.target_domains else "hr"
        candidates = self.detector.detect(redacted_text)
        raw_events = [self.single_event_extractor.extract(candidate, redaction_completed=True) for candidate in candidates]
        normalized_events: list[NormalizedAchievementEvent] = []
        for index, (candidate, raw) in enumerate(zip(candidates, raw_events), start=1):
            normalized = build_normalized_achievement(raw, index)
            normalized_events.append(self.grounding_validator.validate(redacted_text, candidate, raw, normalized))
        extraction = assemble_candidate_extraction(document_id, candidate_id, domain, redacted_text, normalized_events)
        return HybridExtractionResult(extraction, candidates, raw_events, normalized_events, round(perf_counter() - started, 4))
