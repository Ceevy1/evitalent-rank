from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from evitalent.parser.base import BaseDocumentParser, ParsedDocument
from evitalent.parser.text_cleaner import clean_text, split_sections


SCAN_WARNING = "PDF 可能为扫描件，V1 当前不支持 OCR，请转换为可复制文本的 PDF 或 DOCX。"


class PdfDocumentParser(BaseDocumentParser):
    min_text_length = 30

    def parse(self, file_path: Path) -> ParsedDocument:
        path = Path(file_path)
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        raw_text = "\n".join(pages)
        cleaned_text = clean_text(raw_text)
        warnings: list[str] = []
        if len(cleaned_text) < self.min_text_length:
            warnings.append(SCAN_WARNING)

        return ParsedDocument(
            document_id=path.stem,
            source_filename=path.name,
            file_type="pdf",
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            detected_sections=split_sections(cleaned_text),
            parse_status="success" if cleaned_text and not warnings else "warning",
            warnings=warnings,
        )


def parse_pdf(path: str | Path) -> str:
    return PdfDocumentParser().parse(Path(path)).cleaned_text
