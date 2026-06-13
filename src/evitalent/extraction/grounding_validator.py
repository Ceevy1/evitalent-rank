from __future__ import annotations

import re

from evitalent.models.normalized_achievement import NormalizedAchievementEvent
from evitalent.models.raw_achievement import AchievementCandidate, RawAchievementEvent


class GroundingValidator:
    def validate(
        self,
        redacted_text: str,
        candidate: AchievementCandidate,
        raw: RawAchievementEvent,
        normalized: NormalizedAchievementEvent,
    ) -> NormalizedAchievementEvent:
        errors: list[str] = []
        if candidate.isolated_clause not in redacted_text:
            errors.append("isolated_clause_not_in_redacted_text")
        if not raw.evidence_quote or (raw.evidence_quote not in candidate.isolated_clause and raw.evidence_quote not in redacted_text):
            errors.append("evidence_quote_not_grounded")
        if raw.metric_value is None:
            errors.append("metric_value_missing")
        elif not self._value_in_quote(raw.metric_value, raw.evidence_quote):
            errors.append("metric_value_not_found_in_evidence_quote")
        if normalized.metric_value != raw.metric_value:
            errors.append("normalized_value_changed")
        if normalized.event_type != "other" and not normalized.normalization_rule_id:
            errors.append("normalization_rule_missing")
        if errors:
            normalized.grounding_status = "failed"
            normalized.grounding_errors = errors
            normalized.eligible_for_core_achievement_score = False
        return normalized

    @staticmethod
    def _value_in_quote(value: float, quote: str) -> bool:
        candidates = {str(int(value)) if float(value).is_integer() else str(value), str(value)}
        numbers = set(re.findall(r"\d+(?:\.\d+)?", quote))
        return bool(candidates & numbers)
