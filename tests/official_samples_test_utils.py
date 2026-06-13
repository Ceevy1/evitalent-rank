from __future__ import annotations

from pathlib import Path

from docx import Document


DOMAINS = ["brand", "ecommerce", "hr", "production", "rd", "sales"]


def write_docx(path: Path, lines: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for line in lines or ["候选人编号：X", "工作经历：负责流程优化，完成招聘18人。"]:
        doc.add_paragraph(line)
    doc.save(path)


def make_private_tree(root: Path) -> Path:
    input_root = root / "raw" / "resumes"
    for domain in DOMAINS:
        write_docx(input_root / domain / f"{domain}_sample.docx", ["候选人编号：X", f"领域：{domain}", "工作经历：负责流程优化，完成招聘18人。"])
        (input_root / domain / f"{domain}_ignore.txt").write_text("ignore", encoding="utf-8")
    return input_root
