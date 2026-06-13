from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from evitalent.privacy.pii_detector import detect_pii

FORBIDDEN_KEYS = {
    "name",
    "person_name",
    "phone",
    "email",
    "id_card",
    "salary",
    "salary_current",
    "salary_expected",
    "marital_status",
    "family_status",
    "birth_date",
    "birth_year",
    "age",
    "native_place",
    "detailed_address",
    "original_filename",
    "private_relative_path",
}

FORBIDDEN_PATH_HINTS = {"data/raw", "raw_manifest_private", "document_id_map_private", "extraction_results_private"}


class AccessPolicyError(RuntimeError):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


class AccessPolicy:
    def validate_payload(self, payload: Any) -> None:
        reasons = self.find_violations(payload)
        if reasons:
            raise AccessPolicyError(reasons)

    def validate_text(self, text: str) -> None:
        reasons = self.find_text_violations(text)
        if reasons:
            raise AccessPolicyError(reasons)

    def find_violations(self, payload: Any) -> list[str]:
        reasons: list[str] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                if str(key).lower() in FORBIDDEN_KEYS:
                    reasons.append(f"forbidden_key:{key}")
                reasons.extend(self.find_violations(value))
        elif isinstance(payload, list):
            for value in payload:
                reasons.extend(self.find_violations(value))
        elif isinstance(payload, (str, Path)):
            reasons.extend(self.find_text_violations(str(payload)))
        return sorted(set(reasons))

    def find_text_violations(self, text: str) -> list[str]:
        lowered = text.lower().replace("\\", "/")
        reasons = [f"forbidden_path:{hint}" for hint in FORBIDDEN_PATH_HINTS if hint in lowered]
        high_risk = {"phone", "email", "id_card", "salary_current", "salary_expected", "birth_date", "marital_status", "family_status", "detailed_address"}
        pii_types = sorted({item.pii_type for item in detect_pii(text) if item.pii_type in high_risk})
        reasons.extend(f"pii:{item}" for item in pii_types)
        if re.search(r"\b[\w.-]+\.(docx|pdf)\b", text, re.IGNORECASE):
            reasons.append("private_filename")
        return sorted(set(reasons))


def sanitize_json_for_context(payload: Any) -> str:
    AccessPolicy().validate_payload(payload)
    return json.dumps(payload, ensure_ascii=False)
