from __future__ import annotations

from evitalent.models.normalized_achievement import NormalizedAchievementEvent
from evitalent.models.raw_achievement import RawAchievementEvent
from evitalent.normalization.direction_mapper import map_direction
from evitalent.normalization.event_type_mapper import map_event_type
from evitalent.normalization.metric_normalizer import normalize_metric_name, normalize_unit


def build_normalized_achievement(raw: RawAchievementEvent, index: int) -> NormalizedAchievementEvent:
    text = raw.raw_achievement_text or raw.evidence_quote
    unit = normalize_unit(raw.unit, text)
    event_type, normalized_metric_name, event_rule = map_event_type(text, unit)
    direction, direction_rule = map_direction(text, unit)
    eligible = not (event_type == "other" or direction == "unknown")
    return NormalizedAchievementEvent(
        achievement_id=f"ACH{index:03d}",
        raw_achievement_id=raw.raw_achievement_id,
        raw_achievement_text=raw.raw_achievement_text,
        raw_metric_name=raw.raw_metric_name,
        normalized_metric_name=normalize_metric_name(normalized_metric_name, text),
        metric_value=raw.metric_value,
        metric_value_upper=raw.metric_value_upper,
        unit=unit,
        event_type=event_type,
        direction=direction,
        period_months=raw.period_months,
        approximate=raw.approximate,
        lower_bound=raw.lower_bound,
        evidence_quote=raw.evidence_quote,
        evidence_id=f"ev_ach_{index:03d}",
        normalization_rule_id=f"{event_rule}+{direction_rule}",
        normalization_status="normalized" if eligible else "needs_review",
        eligible_for_core_achievement_score=eligible,
    )
