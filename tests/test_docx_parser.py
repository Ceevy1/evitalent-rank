from pathlib import Path

from scripts.generate_demo_resume_files import main as generate_demo_files
from evitalent.parser.docx_parser import DocxDocumentParser


def test_docx_parser_reads_paragraphs_tables_and_sections():
    generate_demo_files()
    path = Path("data/fixtures/source_documents/demo_hr_resume.docx")
    parsed = DocxDocumentParser().parse(path)

    assert parsed.parse_status == "success"
    assert parsed.cleaned_text
    assert "陆晨" in parsed.raw_text
    assert "半年完成关键岗位招聘 18 人" in parsed.cleaned_text
    assert "当前薪资" in parsed.raw_text
    assert len([name for name in parsed.detected_sections if name != "全文"]) >= 3
    assert {"个人信息", "教育经历", "工作经历", "工作业绩"} <= set(parsed.detected_sections)
