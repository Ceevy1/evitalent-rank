from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.parser.docx_parser import DocxDocumentParser
from evitalent.privacy.redactor import redact_text
from scripts.generate_demo_resume_files import OUTPUT_DIR, main as generate_demo_files


REDACTED_DIR = ROOT / "data" / "redacted"
DEMO_FILES = ["demo_hr_resume.docx", "demo_production_resume.docx"]


def _safe_preview(text: str, max_chars: int = 420) -> str:
    preview = text[:max_chars].strip()
    return preview + ("..." if len(text) > max_chars else "")


def main() -> None:
    missing = [filename for filename in DEMO_FILES if not (OUTPUT_DIR / filename).exists()]
    if missing:
        generate_demo_files()

    parser = DocxDocumentParser()
    REDACTED_DIR.mkdir(parents=True, exist_ok=True)
    for filename in DEMO_FILES:
        path = OUTPUT_DIR / filename
        parsed = parser.parse(path)
        result = redact_text(parsed.cleaned_text)
        out_path = REDACTED_DIR / f"{path.stem}.txt"
        out_path.write_text(result.redacted_text, encoding="utf-8")
        counts = Counter(item.pii_type for item in result.pii_items)

        print(f"文件名: {path.name}")
        print(f"解析状态: {parsed.parse_status}")
        print(f"敏感字段类别数量: {dict(sorted(counts.items()))}")
        print(f"脱敏文件保存路径: {out_path}")
        print("脱敏后的安全文本预览:")
        print(_safe_preview(result.redacted_text))
        print("-" * 60)


if __name__ == "__main__":
    main()
