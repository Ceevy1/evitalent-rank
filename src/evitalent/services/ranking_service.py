from __future__ import annotations

import json
from pathlib import Path

from evitalent.db import RankingRecord
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction
from evitalent.models.ranking import RankingResult
from evitalent.repositories import CandidateRepository, RankingRepository
from evitalent.services.extraction_service import ExtractionService
from evitalent.scoring.ranker import rank_candidates
from evitalent.settings import PROJECT_ROOT


REAL_DOC_NOT_READY_MESSAGE = "真实简历尚未完成结构化抽取，请在 Stage 6 接入 LLM 后评分，或选择 Mock 演示数据。"


class RankingService:
    def __init__(
        self,
        repository: RankingRepository | None = None,
        extractor: MockExtractor | None = None,
        candidate_repository: CandidateRepository | None = None,
    ) -> None:
        self.repository = repository
        self.extractor = extractor or MockExtractor()
        self.candidate_repository = candidate_repository

    def list_fixtures(self) -> list[dict]:
        rows = []
        for candidate in self.extractor.load_all():
            domains = [item.domain for item in candidate.candidate_profile.target_domain_candidates]
            rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "domain": domains[0] if domains else None,
                    "domains": domains,
                    "achievement_count": len(candidate.achievement_events),
                    "evidence_count": len(candidate.evidence_items),
                }
            )
        return rows

    def create_ranking(self, domain: str, candidate_ids: list[str] | None = None, mode: str = "mock") -> RankingResult:
        if mode == "mock":
            candidates = self._load_mock_candidates(domain, candidate_ids)
        elif mode == "extracted":
            candidates = self._load_extracted_candidates(domain, candidate_ids)
        else:
            raise ValueError(REAL_DOC_NOT_READY_MESSAGE)
        if not candidates:
            raise ValueError(REAL_DOC_NOT_READY_MESSAGE)
        result = rank_candidates(candidates, domain)
        path = self._save_result(result)
        if self.repository:
            self.repository.add(
                RankingRecord(
                    ranking_id=result.ranking_id,
                    domain=domain,
                    method_version=result.ranking_method_version,
                    result_json_path=str(path),
                )
            )
        return result

    def get_ranking(self, ranking_id: str) -> RankingResult | None:
        record = self.repository.get(ranking_id) if self.repository else None
        path = Path(record.result_json_path) if record else PROJECT_ROOT / "data" / "outputs" / "rankings" / f"{ranking_id}.json"
        if not path.exists():
            return None
        return RankingResult.model_validate_json(path.read_text(encoding="utf-8"))

    def _load_mock_candidates(self, domain: str, candidate_ids: list[str] | None) -> list[CandidateExtraction]:
        candidates = self.extractor.load_all()
        if candidate_ids:
            candidates = [candidate for candidate in candidates if candidate.candidate_id in set(candidate_ids)]
        return [candidate for candidate in candidates if any(item.domain == domain for item in candidate.candidate_profile.target_domain_candidates)]

    def _load_extracted_candidates(self, domain: str, candidate_ids: list[str] | None) -> list[CandidateExtraction]:
        if not self.candidate_repository:
            raise ValueError("缺少候选人仓储，无法加载真实抽取结果。")
        records = self.candidate_repository.list_by_ids(candidate_ids)
        candidates: list[CandidateExtraction] = []
        for record in records:
            if not record.extraction_json_path:
                continue
            path = Path(record.extraction_json_path)
            if not path.exists():
                continue
            candidate = ExtractionService.load_extracted_candidate(path)
            if any(item.domain == domain for item in candidate.candidate_profile.target_domain_candidates):
                candidates.append(candidate)
        return candidates

    def _save_result(self, result: RankingResult) -> Path:
        output_dir = PROJECT_ROOT / "data" / "outputs" / "rankings"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{result.ranking_id}.json"
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return path
