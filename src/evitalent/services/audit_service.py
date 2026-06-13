from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from evitalent.audit.audit_report_builder import build_audit_result
from evitalent.audit.fairness_audit import run_fairness_audit
from evitalent.audit.robustness_audit import run_robustness_audit
from evitalent.audit.timeline_audit import run_timeline_audit
from evitalent.db import AuditRecord
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.audit import AuditResult
from evitalent.models.extraction import CandidateExtraction
from evitalent.models.ranking import RankingResult
from evitalent.repositories import AuditRepository, CandidateRepository, RankingRepository
from evitalent.services.extraction_service import ExtractionService
from evitalent.services.ranking_service import RankingService
from evitalent.settings import PROJECT_ROOT


class AuditServiceError(RuntimeError):
    pass


class AuditService:
    def __init__(
        self,
        audit_repository: AuditRepository | None = None,
        ranking_repository: RankingRepository | None = None,
        candidate_repository: CandidateRepository | None = None,
    ) -> None:
        self.audit_repository = audit_repository
        self.ranking_repository = ranking_repository
        self.candidate_repository = candidate_repository
        self.mock_extractor = MockExtractor()

    def run_timeline(self, domain: str, candidate_ids: list[str] | None = None) -> AuditResult:
        candidates = self._load_candidates_by_domain(domain, candidate_ids)
        timeline = run_timeline_audit(candidates)
        audit = build_audit_result(f"timeline_{domain}", domain, timeline_audit=timeline)
        return self._save(audit, "timeline")

    def run_fairness(self, ranking_id: str, audit_mode: str = "deterministic_counterfactual") -> AuditResult:
        ranking = self._load_ranking(ranking_id)
        candidates = self._load_candidates_by_ids([item.candidate_id for item in ranking.candidates])
        fairness = run_fairness_audit(candidates, ranking.domain, ranking)
        timeline = run_timeline_audit(candidates)
        audit = build_audit_result(ranking_id, ranking.domain, timeline_audit=timeline, fairness_audit=fairness)
        return self._save(audit, "fairness")

    def run_robustness(self, ranking_id: str, audit_mode: str = "mock_equivalent_versions", top_k: int = 3) -> AuditResult:
        ranking = self._load_ranking(ranking_id)
        candidates = self._load_candidates_by_ids([item.candidate_id for item in ranking.candidates])
        fact_only = deepcopy(candidates)
        compressed = deepcopy(candidates)
        robustness = run_robustness_audit(candidates, fact_only, compressed, ranking.domain, top_k)
        timeline = run_timeline_audit(candidates)
        audit = build_audit_result(ranking_id, ranking.domain, timeline_audit=timeline, robustness_audit=robustness)
        return self._save(audit, "robustness")

    def get_audit(self, audit_id: str) -> AuditResult | None:
        record = self.audit_repository.get(audit_id) if self.audit_repository else None
        path = Path(record.result_json_path) if record else PROJECT_ROOT / "data" / "outputs" / "audit_reports" / f"{audit_id}.json"
        if not path.exists():
            return None
        return AuditResult.model_validate_json(path.read_text(encoding="utf-8"))

    def _load_ranking(self, ranking_id: str) -> RankingResult:
        result = RankingService(self.ranking_repository, candidate_repository=self.candidate_repository).get_ranking(ranking_id)
        if result:
            return result
        raise AuditServiceError("排名结果不存在，无法审计。")

    def _load_candidates_by_domain(self, domain: str, candidate_ids: list[str] | None = None) -> list[CandidateExtraction]:
        candidates = self.mock_extractor.load_all()
        if candidate_ids:
            candidates = [candidate for candidate in candidates if candidate.candidate_id in set(candidate_ids)]
        return [candidate for candidate in candidates if any(item.domain == domain for item in candidate.candidate_profile.target_domain_candidates)]

    def _load_candidates_by_ids(self, candidate_ids: list[str]) -> list[CandidateExtraction]:
        found: dict[str, CandidateExtraction] = {}
        for candidate in self.mock_extractor.load_all():
            if candidate.candidate_id in candidate_ids:
                found[candidate.candidate_id] = candidate
        if self.candidate_repository:
            for record in self.candidate_repository.list_by_ids(candidate_ids):
                if record.extraction_json_path and Path(record.extraction_json_path).exists():
                    candidate = ExtractionService.load_extracted_candidate(record.extraction_json_path)
                    found[candidate.candidate_id] = candidate
        ordered = [found[cid] for cid in candidate_ids if cid in found]
        if not ordered:
            raise AuditServiceError("无法加载审计所需候选人。")
        return ordered

    def _save(self, audit: AuditResult, audit_type: str) -> AuditResult:
        output_dir = PROJECT_ROOT / "data" / "outputs" / "audit_reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{audit.audit_id}.json"
        path.write_text(audit.model_dump_json(indent=2), encoding="utf-8")
        if self.audit_repository:
            self.audit_repository.add(
                AuditRecord(
                    audit_id=audit.audit_id,
                    ranking_id=audit.ranking_id,
                    audit_type=audit_type,
                    result_json_path=str(path),
                )
            )
        return audit
