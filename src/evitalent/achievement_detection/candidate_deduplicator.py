from __future__ import annotations

from evitalent.models.raw_achievement import AchievementCandidate


def deduplicate_candidates(candidates: list[AchievementCandidate]) -> list[AchievementCandidate]:
    seen: set[str] = set()
    unique: list[AchievementCandidate] = []
    for candidate in candidates:
        key = candidate.isolated_clause.strip()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique
