from __future__ import annotations

import re

from evitalent.achievement_detection.numeric_pattern_detector import business_numeric_expressions


SENTENCE_SPLIT_RE = re.compile(r"[。；;\n]+")
CLAUSE_SPLIT_RE = re.compile(r"[，,、；;]|(?:并|且|同时)(?=(?:将|推动|实现|完成|上线|保持|使|把|达到|ROI|GMV))")


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_SPLIT_RE.split(text) if part.strip()]


def split_achievement_clauses(sentence: str) -> list[str]:
    raw_parts = [part.strip() for part in CLAUSE_SPLIT_RE.split(sentence) if part and part.strip()]
    clauses: list[str] = []
    prefix = ""
    for part in raw_parts:
        nums = business_numeric_expressions(part)
        if nums:
            clauses.append((prefix + part).strip())
            prefix = ""
        else:
            prefix = (prefix + part).strip()
            if prefix and not prefix.endswith("，"):
                prefix += "，"
    return clauses
