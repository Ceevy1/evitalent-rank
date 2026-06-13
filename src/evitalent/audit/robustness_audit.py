from __future__ import annotations

from evitalent.models.extraction import CandidateExtraction
from evitalent.models.ranking import RankingResult
from evitalent.scoring.ranker import rank_candidates


def top_k_consistency(a: RankingResult, b: RankingResult, top_k: int = 3) -> float | None:
    k = min(top_k, len(a.candidates), len(b.candidates))
    if k <= 1:
        return None
    top_a = {item.candidate_id for item in a.candidates[:k]}
    top_b = {item.candidate_id for item in b.candidates[:k]}
    return round(len(top_a & top_b) / k, 4)


def rank_shift_metrics(a: RankingResult, b: RankingResult) -> tuple[float, int]:
    ranks_a = {item.candidate_id: item.rank for item in a.candidates}
    ranks_b = {item.candidate_id: item.rank for item in b.candidates}
    common = sorted(set(ranks_a) & set(ranks_b))
    if not common:
        return 0.0, 0
    shifts = [abs(ranks_a[cid] - ranks_b[cid]) for cid in common]
    return round(sum(shifts) / len(shifts), 4), max(shifts)


def score_stability(rankings: dict[str, RankingResult]) -> dict[str, float]:
    values: dict[str, list[float]] = {}
    for result in rankings.values():
        for item in result.candidates:
            values.setdefault(item.candidate_id, []).append(item.rank_score)
    return {cid: round(max(scores) - min(scores), 4) for cid, scores in values.items() if scores}


def run_robustness_audit(
    full_text_candidates: list[CandidateExtraction],
    fact_only_candidates: list[CandidateExtraction],
    compressed_candidates: list[CandidateExtraction],
    domain: str,
    top_k: int = 3,
) -> dict:
    rankings = {
        "full_text": rank_candidates(full_text_candidates, domain, ranking_id=f"robust_{domain}_full"),
        "fact_only_text": rank_candidates(fact_only_candidates, domain, ranking_id=f"robust_{domain}_fact"),
        "compressed_text": rank_candidates(compressed_candidates, domain, ranking_id=f"robust_{domain}_compressed"),
    }
    baseline = rankings["full_text"]
    comparisons = {}
    warnings: list[str] = []
    for name, result in rankings.items():
        consistency = top_k_consistency(baseline, result, top_k)
        mean_shift, max_shift = rank_shift_metrics(baseline, result)
        comparisons[name] = {
            "top_k_consistency": consistency,
            "mean_rank_shift": mean_shift,
            "max_rank_shift": max_shift,
        }
        if consistency is not None and consistency < 0.8:
            warnings.append(f"{name} Top-{top_k} consistency 低于 0.80")
        if mean_shift > 1.5:
            warnings.append(f"{name} mean_rank_shift 超过 1.50")
        if max_shift > 2:
            warnings.append(f"{name} max_rank_shift 超过 2")

    stability = score_stability(rankings)
    for cid, shift in stability.items():
        if shift > 5:
            warnings.append(f"{cid} RankScore 差值超过 5")

    rankings_by_version = {name: [item.candidate_id for item in result.candidates] for name, result in rankings.items()}
    return {
        "domain": domain,
        "robustness_audit_status": "warning" if warnings else "passed",
        "top_k": top_k,
        "comparisons": comparisons,
        "rankings_by_version": rankings_by_version,
        "score_stability": stability,
        "warnings": warnings,
        "warning": bool(warnings),
    }
