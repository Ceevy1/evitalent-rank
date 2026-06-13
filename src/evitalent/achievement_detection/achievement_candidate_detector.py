from __future__ import annotations

from evitalent.achievement_detection.candidate_deduplicator import deduplicate_candidates
from evitalent.achievement_detection.numeric_pattern_detector import business_numeric_expressions, detect_numeric_expressions
from evitalent.achievement_detection.sentence_segmenter import split_achievement_clauses, split_sentences
from evitalent.models.raw_achievement import AchievementCandidate


class AchievementCandidateDetector:
    def detect(self, redacted_text: str) -> list[AchievementCandidate]:
        candidates: list[AchievementCandidate] = []
        counter = 1
        section = "resume_text"
        for sentence in split_sentences(redacted_text):
            clauses = split_achievement_clauses(sentence)
            for clause in clauses:
                business_nums = business_numeric_expressions(clause)
                if not business_nums:
                    continue
                all_nums = detect_numeric_expressions(clause)
                period = next((int(item.value) for item in all_nums if item.unit_type == "period" and item.value), None)
                candidates.append(
                    AchievementCandidate(
                        candidate_event_id=f"AC{counter:03d}",
                        source_section=section,
                        source_sentence=sentence,
                        isolated_clause=clause,
                        detected_numeric_expressions=[item.text for item in business_nums],
                        linked_career_context=None,
                        detection_reason="contains_business_numeric_metric",
                        period_months=period,
                    )
                )
                counter += 1
        return deduplicate_candidates(candidates)
