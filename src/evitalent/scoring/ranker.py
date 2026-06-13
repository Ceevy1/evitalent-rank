from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from evitalent.features.achievement_features import quantified_achievement_count
from evitalent.models.extraction import CandidateExtraction
from evitalent.models.ranking import CandidateRankingResult, EvidenceSummary, RankingResult, StrengthItem
from evitalent.scoring.axis_scorer import AXES, load_domain_weight_config, score_candidate_axes
from evitalent.scoring.evidence_scorer import score_eci
from evitalent.scoring.penalty_scorer import score_penalty
from evitalent.settings import PROJECT_ROOT
from evitalent.utils import clamp


def compute_bcs(axis_scores: dict[str, float], domain: str) -> float:
    cfg = load_domain_weight_config(PROJECT_ROOT / "config" / "domain_weights.yaml")
    weights = cfg["domains"][domain]["weights"]
    return round(sum(float(axis_scores[axis]) * float(weights[axis]) for axis in AXES), 2)


def _top_strengths(axis_scores: dict[str, float], evidence_by_axis: dict[str, list[str]]) -> list[StrengthItem]:
    strengths: list[StrengthItem] = []
    for axis, score in sorted(axis_scores.items(), key=lambda item: item[1], reverse=True):
        ids = evidence_by_axis.get(axis, [])
        if ids:
            strengths.append(StrengthItem(axis=axis, label=axis, score=round(score, 2), evidence_ids=ids))
        if len(strengths) >= 3:
            break
    return strengths


def _evidence_summary(candidate: CandidateExtraction) -> EvidenceSummary:
    quantified_count, _ = quantified_achievement_count(candidate)
    return EvidenceSummary(
        evidence_count=len(candidate.evidence_items),
        scoring_evidence_count=sum(1 for item in candidate.evidence_items if item.used_for_scoring),
        achievement_event_count=len(candidate.achievement_events),
        quantified_achievement_count=quantified_count,
    )


def rank_candidates(candidates: list[CandidateExtraction], domain: str, ranking_id: str | None = None) -> RankingResult:
    cfg = load_domain_weight_config(PROJECT_ROOT / "config" / "domain_weights.yaml")
    ranking_cfg = cfg["ranking"]
    items: list[CandidateRankingResult] = []

    for candidate in candidates:
        features = score_candidate_axes(candidate, domain)
        bcs = compute_bcs(features.axis_scores, domain)
        eci, eci_parts = score_eci(candidate, features)
        penalty, penalty_flags = score_penalty(candidate)
        rank_score = bcs * (
            float(ranking_cfg["evidence_floor"]) + float(ranking_cfg["evidence_adjustment_weight"]) * eci / 100.0
        ) - penalty
        evidence_ids = sorted({eid for ids in features.evidence_ids_by_axis.values() for eid in ids})
        risk_flags = sorted(set(features.risk_flags + penalty_flags))
        if _evidence_summary(candidate).quantified_achievement_count == 0:
            risk_flags.append("量化成果缺失")
        if any("证据不足" in flag for flag in risk_flags):
            risk_flags.append("证据不足")

        computed = dict(features.metrics)
        computed["eci_parts"] = eci_parts
        items.append(
            CandidateRankingResult(
                rank=0,
                candidate_id=candidate.candidate_id,
                display_id=candidate.candidate_profile.display_id,
                bcs=round(clamp(bcs), 2),
                eci=round(clamp(eci), 2),
                penalty=round(penalty, 2),
                rank_score=round(rank_score, 2),
                axis_scores=features.axis_scores,
                computed_features=computed,
                top_strengths=_top_strengths(features.axis_scores, features.evidence_ids_by_axis),
                risk_flags=sorted(set(risk_flags)),
                evidence_summary=_evidence_summary(candidate),
                evidence_ids=evidence_ids,
            )
        )

    items.sort(key=lambda item: item.rank_score, reverse=True)
    for index, item in enumerate(items, start=1):
        item.rank = index

    return RankingResult(
        ranking_id=ranking_id or f"ranking_{uuid4().hex[:10]}",
        domain=domain,
        domain_label=cfg["domains"][domain]["label"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        ranking_method_version="stage4_v1",
        candidates=items,
        insufficient_candidates_for_ranking=len(items) < 2,
    )
