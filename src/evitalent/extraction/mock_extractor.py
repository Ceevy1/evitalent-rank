from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from evitalent.extraction.base import BaseExtractor
from evitalent.extraction.evidence_linker import check_evidence_links
from evitalent.extraction.schema_validator import SchemaValidationError, SchemaValidator
from evitalent.models.extraction import CandidateExtraction
from evitalent.settings import PROJECT_ROOT, get_settings


class MockExtractionError(RuntimeError):
    pass


class MockExtractor(BaseExtractor):
    def __init__(self, fixture_dir: str | Path | None = None) -> None:
        default_dir = PROJECT_ROOT / "data" / "fixtures" / "extracted"
        self.fixture_dir = Path(fixture_dir) if fixture_dir else default_dir
        self.schema_validator = SchemaValidator()

    def _candidate_files(self) -> list[Path]:
        return sorted(self.fixture_dir.glob("*.json"))

    def _resolve_fixture_path(self, document_id: str) -> Path:
        direct = self.fixture_dir / document_id
        if direct.suffix == ".json" and direct.exists():
            return direct
        by_stem = self.fixture_dir / f"{document_id}.json"
        if by_stem.exists():
            return by_stem
        for path in self._candidate_files():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if payload.get("document_id") == document_id or payload.get("candidate_id") == document_id:
                return path
        raise FileNotFoundError(f"Mock fixture not found for document_id='{document_id}' in {self.fixture_dir}")

    def extract(self, document_id: str, redacted_text: Optional[str] = None, **legacy_kwargs) -> CandidateExtraction:
        if legacy_kwargs.get("candidate_id"):
            document_id = legacy_kwargs["candidate_id"]
        if legacy_kwargs.get("target_domain") and not document_id:
            document_id = legacy_kwargs["target_domain"]
        path = self._resolve_fixture_path(document_id)
        try:
            payload = self.schema_validator.validate_file_or_raise(path)
            candidate = CandidateExtraction.model_validate(payload)
        except SchemaValidationError:
            raise
        except ValidationError as exc:
            raise MockExtractionError(f"Pydantic validation failed for {path.name}: {exc}") from exc

        link_result = check_evidence_links(candidate)
        if not link_result["passed"]:
            raise MockExtractionError(f"Evidence link validation failed for {path.name}: {link_result}")
        return candidate

    def load_all(self) -> list[CandidateExtraction]:
        if not self.fixture_dir.exists():
            raise FileNotFoundError(f"Fixture directory not found: {self.fixture_dir}")
        files = self._candidate_files()
        if not files:
            raise FileNotFoundError(f"No fixture JSON files found in {self.fixture_dir}")
        return [self.extract(path.stem) for path in files]
