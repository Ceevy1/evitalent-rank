from __future__ import annotations

from evitalent.privacy.pii_detector import detect_pii


def assert_redacted_text_safe(text: str) -> None:
    high_risk = {"phone", "email", "id_card", "salary_current", "salary_expected"}
    leaked = [item.pii_type for item in detect_pii(text) if item.pii_type in high_risk and "已脱敏" not in item.original_text]
    if leaked:
        raise ValueError(f"脱敏文本仍疑似包含敏感字段：{sorted(set(leaked))}")
