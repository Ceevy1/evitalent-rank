from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from evitalent.parser.base import BaseDocumentParser, ParsedDocument
from evitalent.parser.text_cleaner import clean_text, split_sections


def _iter_block_items(document: DocxDocument):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _table_to_lines(table: Table) -> list[str]:
    lines: list[str] = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
        if cells:
            lines.append(" | ".join(cells))
    return lines


class DocxDocumentParser(BaseDocumentParser):
    def parse(self, file_path: Path) -> ParsedDocument:
        path = Path(file_path)
        document = Document(str(path))
        parts: list[str] = []
        warnings: list[str] = []

        for block in _iter_block_items(document):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    parts.append(text)
            elif isinstance(block, Table):
                parts.extend(_table_to_lines(block))

        raw_text = "\n".join(parts)
        cleaned_text = clean_text(raw_text)
        if not cleaned_text:
            warnings.append("DOCX 未提取到有效文本。")

        return ParsedDocument(
            document_id=path.stem,
            source_filename=path.name,
            file_type="docx",
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            detected_sections=split_sections(cleaned_text),
            parse_status="success" if cleaned_text else "warning",
            warnings=warnings,
        )


def parse_docx(path: str | Path) -> str:
    return DocxDocumentParser().parse(Path(path)).cleaned_text
