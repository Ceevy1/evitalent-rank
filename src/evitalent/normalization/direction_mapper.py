from __future__ import annotations


def map_direction(text: str, unit: str | None = None) -> tuple[str, str]:
    lower = text.lower()
    if "质量事故为0" in text or "0质量" in text or "零安全事故" in text or "0 质量" in text:
        return "maintained", "direction_maintained_zero_incident"
    if any(term in text for term in ("提升至", "达到", "达成", "完成率提升至", "回款率达到")):
        if any(term in text for term in ("招聘", "完成招聘", "上线", "新增", "获得", "授权")) and unit in {"person", "count"}:
            return "achieved_amount", "direction_achieved_amount"
        return "achieved_level", "direction_achieved_level"
    if any(term in text for term in ("下降", "降低", "减少")):
        return "decrease_by", "direction_decrease_by"
    if any(term in text for term in ("提升", "增长", "增加", "改善")):
        return "increase_by", "direction_increase_by"
    if any(term in text for term in ("完成", "招聘", "上线", "新增", "获得", "授权", "引进", "引入", "到岗")):
        return "achieved_amount", "direction_achieved_amount"
    if "roi" in lower or "投产比" in text:
        return "achieved_level", "direction_achieved_level"
    return "unknown", "direction_unknown"
