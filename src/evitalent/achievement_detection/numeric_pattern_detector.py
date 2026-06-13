from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NumericExpression:
    text: str
    value: float | None
    unit_type: str
    unit: str
    start: int
    end: int


PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("percent", "percent", re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*%\+?|(\d+(?:\.\d+)?)\s*个百分点")),
    ("money", "CNY", re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*(亿元|亿|万元|万)(?:\\+)?")),
    ("ratio", "ratio", re.compile(r"(?:ROI|投产比)\s*(?:达到|达成|为)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)),
    ("person", "person", re.compile(r"(?<!\d)(\d+)\s*(人|名)(?![民币])")),
    ("count", "count", re.compile(r"(?<!\d)(0)\s*(?:质量安全事故|质量事故|安全事故)")),
    ("count", "count", re.compile(r"(?<!\d)(\d+)\s*(套|个(?!月)|家|项|条|款|门店|品牌|系统|专利)(?:\+)?")),
    ("period", "month", re.compile(r"(半年|三年|一年|两年|二年|四年|五年|(\d+)\s*个月|(\d+)\s*年)")),
]

CN_PERIOD_MONTHS = {"半年": 6, "一年": 12, "两年": 24, "二年": 24, "三年": 36, "四年": 48, "五年": 60}


def _value(match: re.Match[str], unit_type: str) -> float | None:
    if unit_type == "period":
        text = match.group(0)
        if text in CN_PERIOD_MONTHS:
            return float(CN_PERIOD_MONTHS[text])
        digit = re.search(r"\d+", text)
        if not digit:
            return None
        n = float(digit.group(0))
        return n if "个月" in text else n * 12
    for group in match.groups():
        if group and re.match(r"\d", group):
            return float(group)
    return None


def detect_numeric_expressions(text: str) -> list[NumericExpression]:
    items: list[NumericExpression] = []
    for unit_type, unit, pattern in PATTERNS:
        for match in pattern.finditer(text):
            items.append(
                NumericExpression(
                    text=match.group(0),
                    value=_value(match, unit_type),
                    unit_type=unit_type,
                    unit=unit,
                    start=match.start(),
                    end=match.end(),
                )
            )
    items.sort(key=lambda item: (item.start, item.end))
    accepted: list[NumericExpression] = []
    for item in items:
        if item.unit_type == "period":
            accepted.append(item)
            continue
        if not any(item.start < prev.end and prev.start < item.end and prev.unit_type != "period" for prev in accepted):
            accepted.append(item)
    return accepted


def business_numeric_expressions(text: str) -> list[NumericExpression]:
    return [item for item in detect_numeric_expressions(text) if item.unit_type != "period"]
