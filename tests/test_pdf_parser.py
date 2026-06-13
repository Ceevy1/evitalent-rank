from pathlib import Path

from evitalent.parser import pdf_parser
from evitalent.parser.pdf_parser import PdfDocumentParser, SCAN_WARNING


class _FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _FakeTextPdfReader:
    def __init__(self, path):
        self.pages = [
            _FakePage("个人信息\n候选人编号：CAND-PDF-001"),
            _FakePage("工作业绩\nGMV 1亿，转化率提升 30%。"),
        ]


class _FakeEmptyPdfReader:
    def __init__(self, path):
        self.pages = [_FakePage(""), _FakePage(None)]


def test_pdf_parser_extracts_text_pdf(monkeypatch):
    monkeypatch.setattr(pdf_parser, "PdfReader", _FakeTextPdfReader)
    parsed = PdfDocumentParser().parse(Path("demo_text.pdf"))

    assert parsed.parse_status == "success"
    assert "GMV 1亿" in parsed.cleaned_text
    assert "工作业绩" in parsed.detected_sections
    assert not parsed.warnings


def test_pdf_parser_warns_for_scanned_pdf(monkeypatch):
    monkeypatch.setattr(pdf_parser, "PdfReader", _FakeEmptyPdfReader)
    parsed = PdfDocumentParser().parse(Path("demo_scanned.pdf"))

    assert parsed.parse_status == "warning"
    assert SCAN_WARNING in parsed.warnings
