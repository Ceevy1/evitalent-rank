from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from evitalent.extraction.base import BaseExtractor
from evitalent.extraction.extraction_pipeline import ExtractionPipeline, ExtractionPipelineError
from evitalent.extraction.llm_client import LLMClient, LLMClientError
from evitalent.extraction.prompt_builder import PromptBuilder, PromptSecurityError, RedactedResumeInput
from evitalent.models.extraction import CandidateExtraction
from evitalent.repositories import DocumentRepository
from evitalent.settings import PROJECT_ROOT


class LLMExtractionError(RuntimeError):
    pass


class LLMExtractor(BaseExtractor):
    def __init__(
        self,
        client: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        pipeline: ExtractionPipeline | None = None,
        document_repository: DocumentRepository | None = None,
        output_dir: str | Path | None = None,
        mode: str = "local_ollama",
    ) -> None:
        self.client = client or LLMClient(provider=mode)
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.pipeline = pipeline or ExtractionPipeline()
        self.document_repository = document_repository
        self.output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "data" / "extracted"
        self.mode = mode

    def extract(self, document_id: str, redacted_text: Optional[str] = None) -> CandidateExtraction:
        text = redacted_text if redacted_text is not None else self._load_redacted_text(document_id)
        try:
            system_prompt, user_prompt = self.prompt_builder.build(
                RedactedResumeInput(document_id=document_id, redacted_text=text, redaction_completed=True)
            )
        except PromptSecurityError as exc:
            raise LLMExtractionError(f"安全检查失败：{exc}") from exc
        try:
            payload = self.client.generate_json(system_prompt, user_prompt)
        except LLMClientError as exc:
            raise LLMExtractionError(f"模型抽取失败：{exc}") from exc

        payload.setdefault("document_id", document_id)
        payload.setdefault("schema_version", "1.0.0")
        payload.setdefault("llm_metadata", {})
        payload["llm_metadata"].update(
            {
                "provider": self.mode,
                "model_name": self.client.model or self.mode,
                "temperature": self.client.temperature,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        candidate_id = str(payload.get("candidate_id") or f"candidate_{document_id}")
        save_path = self.output_dir / f"{candidate_id}.json"
        try:
            return self.pipeline.validate_or_raise(payload, save_path=save_path)
        except ExtractionPipelineError as exc:
            raise LLMExtractionError(f"抽取结果校验失败：{exc}") from exc

    def _load_redacted_text(self, document_id: str) -> str:
        redacted_path: Path | None = None
        if self.document_repository:
            record = self.document_repository.get(document_id)
            if record and record.redacted_path:
                redacted_path = Path(record.redacted_path)
        if redacted_path is None:
            candidate = PROJECT_ROOT / "data" / "redacted" / f"{document_id}.txt"
            if candidate.exists():
                redacted_path = candidate
        if redacted_path is None or not redacted_path.exists():
            raise LLMExtractionError("未找到脱敏文本，请先完成解析与脱敏。")
        return redacted_path.read_text(encoding="utf-8")
