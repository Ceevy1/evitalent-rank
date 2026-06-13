from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from evitalent.privacy.pii_detector import MASKS, PiiItem, detect_pii


@dataclass
class RedactionResult:
    redacted_text: str
    pii_items: list[PiiItem]
    masked_count: int
    redaction_summary: dict[str, int] = field(default_factory=dict)

    def __iter__(self):
        # Backward-compatible unpacking: redacted, findings = redact_text(text)
        yield self.redacted_text
        yield self.pii_items


def redact_text(text: str) -> RedactionResult:
    pii_items = detect_pii(text)
    redacted = text
    for item in sorted(pii_items, key=lambda finding: finding.start_position, reverse=True):
        redacted = redacted[: item.start_position] + item.masked_text + redacted[item.end_position :]

    summary: dict[str, int] = {}
    for item in pii_items:
        summary[item.pii_type] = summary.get(item.pii_type, 0) + 1

    return RedactionResult(
        redacted_text=redacted,
        pii_items=pii_items,
        masked_count=len(pii_items),
        redaction_summary=summary,
    )


def redact_to_file(text: str, output_path: str | Path) -> tuple[Path, list[PiiItem]]:
    result = redact_text(text)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.redacted_text, encoding="utf-8")
    return path, result.pii_items


def mask_for_type(pii_type: str) -> str:
    return MASKS.get(pii_type, "[敏感信息已脱敏]")
