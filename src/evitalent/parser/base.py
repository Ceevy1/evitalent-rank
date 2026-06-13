from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedDocument:
    document_id: str
    source_filename: str
    file_type: str
    raw_text: str
    cleaned_text: str
    detected_sections: dict[str, str]
    parse_status: str
    warnings: list[str] = field(default_factory=list)


class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        raise NotImplementedError
