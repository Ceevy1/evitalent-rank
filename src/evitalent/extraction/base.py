from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from evitalent.models.extraction import CandidateExtraction


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, document_id: str, redacted_text: Optional[str] = None) -> CandidateExtraction:
        raise NotImplementedError
