from __future__ import annotations

from pathlib import Path

from evitalent.db import CandidateRecord
from evitalent.extraction.llm_client import LLMClient
from evitalent.extraction.llm_extractor import LLMExtractionError, LLMExtractor
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline
from evitalent.extraction.llm_single_event_extractor import LLMSingleEventExtractor
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction
from evitalent.repositories import CandidateRepository, DocumentRepository
from evitalent.settings import PROJECT_ROOT


class ExtractionServiceError(RuntimeError):
    pass


class ExtractionService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        candidate_repository: CandidateRepository | None = None,
    ) -> None:
        self.document_repository = document_repository
        self.candidate_repository = candidate_repository

    def extract_document(self, document_id: str, mode: str = "mock") -> dict:
        if mode == "mock":
            candidate = MockExtractor().extract(document_id)
            return self._summary(candidate, "completed", eligible_for_scoring=True)
        if mode not in {"local_ollama", "compatible_api"}:
            raise ExtractionServiceError("抽取模式仅支持 mock、local_ollama 或 compatible_api。")

        record = self.document_repository.get(document_id) if self.document_repository else None
        fallback_redacted = PROJECT_ROOT / "data" / "redacted" / f"{document_id}.txt"
        has_redacted = bool(record and record.redacted_path and Path(record.redacted_path).exists()) or fallback_redacted.exists()
        if not has_redacted:
            raise ExtractionServiceError("真实简历尚未完成脱敏，禁止调用模型抽取。")

        client = LLMClient(provider=mode)
        try:
            redacted_text = Path(record.redacted_path).read_text(encoding="utf-8") if record and record.redacted_path else (PROJECT_ROOT / "data" / "redacted" / f"{document_id}.txt").read_text(encoding="utf-8")
            hybrid = HybridExtractionPipeline(single_event_extractor=LLMSingleEventExtractor(client=client, use_llm=True))
            hybrid_result = hybrid.extract(redacted_text, document_id, f"candidate_{document_id}")
            candidate = hybrid_result.candidate_extraction
            extra_summary = hybrid_result.summary
            (PROJECT_ROOT / "data" / "extracted").mkdir(parents=True, exist_ok=True)
            (PROJECT_ROOT / "data" / "extracted" / f"{candidate.candidate_id}.json").write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
        except Exception as hybrid_exc:
            extractor = LLMExtractor(client=client, document_repository=self.document_repository, mode=mode)
            try:
                candidate = extractor.extract(document_id)
                extra_summary = self._hybrid_count_defaults(candidate)
            except LLMExtractionError as exc:
                self._write_safe_error(document_id, str(exc))
                raise ExtractionServiceError("结构化抽取失败，请重试、检查模型配置或改用 Mock 模式。") from exc

        path = PROJECT_ROOT / "data" / "extracted" / f"{candidate.candidate_id}.json"
        if self.candidate_repository:
            self.candidate_repository.add(
                CandidateRecord(
                    candidate_id=candidate.candidate_id,
                    document_id=document_id,
                    masked_display_name=candidate.candidate_id,
                    extraction_json_path=str(path),
                    extraction_mode=mode,
                )
            )
        summary = self._summary(candidate, "completed", eligible_for_scoring=True)
        summary.update(extra_summary)
        return summary

    @staticmethod
    def load_extracted_candidate(path: str | Path) -> CandidateExtraction:
        return CandidateExtraction.model_validate_json(Path(path).read_text(encoding="utf-8"))

    @staticmethod
    def _summary(candidate: CandidateExtraction, status: str, eligible_for_scoring: bool) -> dict:
        detected_domains = [item.domain for item in candidate.candidate_profile.target_domain_candidates]
        return {
            "extraction_status": status,
            "candidate_id": candidate.candidate_id,
            "detected_domains": detected_domains,
            "career_count": len(candidate.career_records),
            "achievement_count": len(candidate.achievement_events),
            "evidence_count": len(candidate.evidence_items),
            "quality_flags": [flag.description for flag in candidate.quality_flags],
            "eligible_for_scoring": eligible_for_scoring,
            **ExtractionService._hybrid_count_defaults(candidate),
        }

    @staticmethod
    def _hybrid_count_defaults(candidate: CandidateExtraction) -> dict:
        count = len(candidate.achievement_events)
        return {
            "structure_extraction_status": "completed",
            "achievement_candidate_count": count,
            "raw_event_count": count,
            "normalized_event_count": count,
            "grounded_event_count": count,
            "needs_review_event_count": 0,
            "achievement_validation_rows": [],
        }

    @staticmethod
    def _write_safe_error(document_id: str, message: str) -> None:
        output_dir = PROJECT_ROOT / "data" / "outputs" / "extraction_errors"
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_message = message[:800]
        (output_dir / f"{document_id}.txt").write_text(safe_message, encoding="utf-8")
