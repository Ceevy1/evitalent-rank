from __future__ import annotations

import re


SECTION_TITLES = [
    "个人信息",
    "基本信息",
    "教育经历",
    "工作经历",
    "工作经验",
    "项目经历",
    "项目经验",
    "工作业绩",
    "个人评价",
    "专业技能",
    "培训经历",
    "证书与荣誉",
]

# Backward-compatible name used by Stage 1 tests/imports.
SECTION_PATTERNS = SECTION_TITLES


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving resume business facts and paragraphs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t\u3000]+", " ", line).strip()
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_heading(line: str) -> str | None:
    stripped = line.strip().strip("：: 　\t")
    for title in SECTION_TITLES:
        if stripped == title:
            return title
        if stripped.startswith(title) and len(stripped) <= len(title) + 4:
            return title
    return None


def split_sections(text: str) -> dict[str, str]:
    cleaned = clean_text(text)
    sections: dict[str, list[str]] = {"全文": []}
    current = "全文"
    for line in cleaned.splitlines():
        heading = _normalize_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if "\n".join(lines).strip() or name != "全文"
    }
