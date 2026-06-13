from __future__ import annotations

from copy import deepcopy
from typing import Any

from evitalent.models.audit import AuditIssue, FairnessAuditResult
from evitalent.models.extraction import CandidateExtraction
from evitalent.models.ranking import RankingResult
from evitalent.scoring.ranker import rank_candidates


FORBIDDEN_FIELDS = {
    "name",
    "person_name",
    "gender",
    "birth_year",
    "birth_date",
    "age",
    "marital_status",
    "family_status",
    "salary_current",
    "salary_expected",
    "phone",
    "email",
    "id_card",
}


def _contains_forbidden_key(value: Any) -> list[str]:
    found: set[str] = set()
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        for key, item in value.items():
            lower = str(key).lower()
            if lower in FORBIDDEN_FIELDS:
                found.add(lower)
            found.update(_contains_forbidden_key(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_contains_forbidden_key(item))
    return sorted(found)


def _rank_map(result: RankingResult) -> dict[str, int]:
    return {item.candidate_id: item.rank for item in result.candidates}


def _score_map(result: RankingResult) -> dict[str, float]:
    return {item.candidate_id: item.rank_score for item in result.candidates}


def _counterfactual_candidates(candidates: list[CandidateExtraction], variant: str) -> list[CandidateExtraction]:
    changed = deepcopy(candidates)
    for candidate in changed:
        sensitive = candidate.sensitive_information
        if variant == "gender":
            sensitive.gender = "counterfactual_gender"
        elif variant == "birth_year":
            sensitive.birth_year = 1988 if sensitive.birth_year != 1988 else 1992
        elif variant == "marital_status":
            sensitive.marital_status = "counterfactual_marital_status"
        elif variant == "salary":
            sensitive.salary_current = "[薪资信息已脱敏]"
            sensitive.salary_expected = "[薪资信息已脱敏]"
    return changed


def run_fairness_audit(
    candidates: list[CandidateExtraction],
    domain: str,
    baseline_ranking: RankingResult | None = None,
) -> dict:
    baseline = baseline_ranking or rank_candidates(candidates, domain)
    issues: list[AuditIssue] = []

    for candidate in candidates:
        if candidate.sensitive_information.masked_for_scoring is not True:
            issues.append(
                AuditIssue(
                    issue_type="masked_for_scoring_false",
                    severity="critical",
                    description="sensitive_information.masked_for_scoring 不是 true。",
                    candidate_id=candidate.candidate_id,
                )
            )
        forbidden = _contains_forbidden_key(candidate.domain_assessment_inputs)
        if forbidden:
            issues.append(
                AuditIssue(
                    issue_type="sensitive_field_in_scoring_input",
                    severity="critical",
                    description=f"domain_assessment_inputs 出现禁止字段：{', '.join(forbidden)}。",
                    candidate_id=candidate.candidate_id,
                )
            )

    ranking_blob = baseline.model_dump(mode="json")
    forbidden_ranking = _contains_forbidden_key(ranking_blob)
    if forbidden_ranking:
        issues.append(
            AuditIssue(
                issue_type="sensitive_field_in_ranking_result",
                severity="critical",
                description=f"ranking result 出现禁止字段：{', '.join(forbidden_ranking)}。",
            )
        )

    base_ranks = _rank_map(baseline)
    base_scores = _score_map(baseline)
    max_score_shift_by_candidate = {cid: 0.0 for cid in base_scores}
    max_rank_shift_by_candidate = {cid: 0 for cid in base_ranks}

    for variant in ("gender", "birth_year", "marital_status", "salary"):
        changed = rank_candidates(_counterfactual_candidates(candidates, variant), domain, ranking_id=f"{baseline.ranking_id}_{variant}")
        changed_ranks = _rank_map(changed)
        changed_scores = _score_map(changed)
        for cid, score in base_scores.items():
            max_score_shift_by_candidate[cid] = max(max_score_shift_by_candidate[cid], abs(score - changed_scores[cid]))
            max_rank_shift_by_candidate[cid] = max(max_rank_shift_by_candidate[cid], abs(base_ranks[cid] - changed_ranks[cid]))

    tolerance = 1e-9
    if any(value > tolerance for value in max_score_shift_by_candidate.values()) or any(max_rank_shift_by_candidate.values()):
        issues.append(
            AuditIssue(
                issue_type="counterfactual_rank_score_shift",
                severity="critical",
                description="敏感字段反事实变更导致 RankScore 或排名变化，应视为评分配置泄露。",
            )
        )

    max_score_shift = max(max_score_shift_by_candidate.values(), default=0.0)
    max_rank_shift = max(max_rank_shift_by_candidate.values(), default=0)
    mean_score_shift = sum(max_score_shift_by_candidate.values()) / max(1, len(max_score_shift_by_candidate))
    mean_rank_shift = sum(max_rank_shift_by_candidate.values()) / max(1, len(max_rank_shift_by_candidate))
    failed = any(issue.severity == "critical" for issue in issues)
    result = FairnessAuditResult(
        fairness_audit_status="failed" if failed else "passed",
        sensitive_field_isolation_passed=not any(issue.issue_type != "counterfactual_rank_score_shift" for issue in issues),
        counterfactual_invariance_passed=max_score_shift <= tolerance and max_rank_shift == 0,
        candidate_score_shift={cid: round(value, 8) for cid, value in max_score_shift_by_candidate.items()},
        candidate_rank_shift=max_rank_shift_by_candidate,
        mean_score_shift=round(mean_score_shift, 8),
        max_score_shift=round(max_score_shift, 8),
        mean_rank_shift=round(mean_rank_shift, 8),
        max_rank_shift=max_rank_shift,
        detected_issues=issues,
    )
    data = result.model_dump(mode="json")
    # Backward-compatible fields used by earlier tests and scripts.
    data["domain"] = domain
    data["sensitive_rank_shift"] = data["candidate_rank_shift"]
    data["warning"] = result.fairness_audit_status != "passed"
    return data
