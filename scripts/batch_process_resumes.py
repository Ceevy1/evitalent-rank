from __future__ import annotations

from pathlib import Path

from evitalent.parser.docx_parser import parse_docx
from evitalent.parser.pdf_parser import parse_pdf
from evitalent.privacy.redactor import redact_to_file
from evitalent.settings import PROJECT_ROOT


def main() -> None:
    raw_dir = PROJECT_ROOT / "data" / "raw"
    for path in raw_dir.glob("*"):
        if path.suffix.lower() == ".docx":
            text = parse_docx(path)
        elif path.suffix.lower() == ".pdf":
            text = parse_pdf(path)
        elif path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            continue
        output_path = PROJECT_ROOT / "data" / "redacted" / f"{path.stem}.txt"
        redacted_path, findings = redact_to_file(text, output_path)
        print(f"redacted={redacted_path} pii_fields={sorted({item.field_name for item in findings})}")


if __name__ == "__main__":
    main()

