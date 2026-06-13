from __future__ import annotations

from evitalent.features.timeline_features import detect_timeline_issues
from evitalent.models.extraction import CandidateExtraction
from evitalent.settings import PROJECT_ROOT
from evitalent.utils import load_yaml


def score_penalty(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    max_penalty = float(load_yaml(PROJECT_ROOT / "config" / "domain_weights.yaml")["ranking"]["max_penalty"])
    penalty = 0.0
    flags: list[str] = []

    for issue in detect_timeline_issues(candidate):
        if issue.issue_type == "date_precision":
            continue
        if issue.issue_type == "date_conflict":
            penalty += 3.0
            flags.append("时间冲突")
        elif issue.issue_type == "full_time_overlap":
            penalty += 6.0
            flags.append("明显全职岗位重叠")

    evidence_ids = candidate.evidence_ids
    career_project_ids = {eid for record in candidate.career_records for eid in record.evidence_ids}
    career_project_ids.update({eid for record in candidate.project_records for eid in record.evidence_ids})
    for event in candidate.achievement_events:
        if event.evidence_id not in evidence_ids:
            penalty += 8.0
            flags.append("重大成果无法对应证据")
        if event.evidence_grade.value in {"A", "B"} and not career_project_ids:
            penalty += 8.0
            flags.append("重大成果无法对应任职或项目经历")

    return round(min(max_penalty, penalty), 2), sorted(set(flags))
