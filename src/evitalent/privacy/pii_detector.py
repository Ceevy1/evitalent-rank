from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PiiItem:
    pii_type: str
    original_text: str
    start_position: int
    end_position: int
    masked_text: str
    confidence: float
    rule_name: str

    @property
    def field_name(self) -> str:
        return self.pii_type

    @property
    def value(self) -> str:
        return self.original_text

    @property
    def start(self) -> int:
        return self.start_position

    @property
    def end(self) -> int:
        return self.end_position


# Backward-compatible alias for Stage 1 imports.
PiiFinding = PiiItem


MASKS = {
    "person_name": "[姓名已脱敏]",
    "gender": "[性别已脱敏]",
    "birth_date": "[年龄信息已脱敏]",
    "age": "[年龄信息已脱敏]",
    "marital_status": "[家庭信息已脱敏]",
    "family_status": "[家庭信息已脱敏]",
    "native_place": "[地域信息已脱敏]",
    "detailed_address": "[地域信息已脱敏]",
    "phone": "[电话已脱敏]",
    "email": "[邮箱已脱敏]",
    "id_card": "[证件信息已脱敏]",
    "salary_current": "[薪资信息已脱敏]",
    "salary_expected": "[薪资信息已脱敏]",
}


LABEL_SEP = r"\s*(?:[:：|])\s*"


RULES: list[tuple[str, str, re.Pattern[str], int, float]] = [
    ("person_name", "label_name", re.compile(rf"(姓名|候选人姓名|名字){LABEL_SEP}([\u4e00-\u9fa5A-Za-z·]{{2,20}})"), 2, 0.98),
    ("gender", "label_gender", re.compile(rf"(性别){LABEL_SEP}(男|女|male|female)", re.IGNORECASE), 2, 0.98),
    (
        "birth_date",
        "label_birth_date",
        re.compile(rf"(出生日期|出生年月|出生年份|生日){LABEL_SEP}(\d{{4}}(?:[-/.年]\d{{1,2}})?(?:[-/.月]\d{{1,2}}日?)?)"),
        2,
        0.96,
    ),
    ("age", "label_age", re.compile(rf"(年龄){LABEL_SEP}(\d{{1,2}}\s*岁?)"), 2, 0.95),
    ("marital_status", "label_marital", re.compile(rf"(婚姻状况|婚姻){LABEL_SEP}(已婚|未婚|离异|保密)", re.IGNORECASE), 2, 0.95),
    ("family_status", "label_family", re.compile(rf"(家庭情况|家庭状况){LABEL_SEP}([^\n|；;]{{2,30}})"), 2, 0.88),
    ("native_place", "label_native_place", re.compile(rf"(籍贯){LABEL_SEP}([^\n|；;]{{2,30}})"), 2, 0.9),
    ("detailed_address", "label_address", re.compile(rf"(详细住址|住址|现居住地|现居地|地址){LABEL_SEP}([^\n|；;]{{4,60}})"), 2, 0.86),
    ("phone", "mainland_phone", re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)"), 1, 0.99),
    ("email", "email", re.compile(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"), 1, 0.99),
    ("id_card", "mainland_id_card", re.compile(r"(?<!\d)(\d{17}[\dXx])(?!\d)"), 1, 0.99),
    ("salary_current", "label_current_salary", re.compile(rf"(当前薪资|目前薪资|现薪资){LABEL_SEP}([^\n|；;]{{2,30}})"), 2, 0.94),
    ("salary_expected", "label_expected_salary", re.compile(rf"(期望薪资|期待薪资){LABEL_SEP}([^\n|；;]{{2,30}})"), 2, 0.94),
]


def _overlaps(item: PiiItem, accepted: list[PiiItem]) -> bool:
    return any(item.start_position < other.end_position and other.start_position < item.end_position for other in accepted)


def detect_pii(text: str) -> list[PiiItem]:
    findings: list[PiiItem] = []
    for pii_type, rule_name, pattern, group_index, confidence in RULES:
        for match in pattern.finditer(text):
            start, end = match.span(group_index)
            original = match.group(group_index).strip()
            if not original:
                continue
            findings.append(
                PiiItem(
                    pii_type=pii_type,
                    original_text=original,
                    start_position=start,
                    end_position=end,
                    masked_text=MASKS[pii_type],
                    confidence=confidence,
                    rule_name=rule_name,
                )
            )

    findings.sort(key=lambda item: (item.start_position, -(item.end_position - item.start_position)))
    accepted: list[PiiItem] = []
    for item in findings:
        if not _overlaps(item, accepted):
            accepted.append(item)
    return accepted
