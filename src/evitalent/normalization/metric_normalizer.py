from __future__ import annotations


def normalize_unit(raw_unit: str | None, text: str = "") -> str | None:
    unit = (raw_unit or "").lower()
    if unit in {"percent", "%"} or "%" in text or "百分点" in text:
        return "percent"
    if unit in {"cny", "rmb", "money"} or any(term in text for term in ("亿", "万元", "元", "GMV", "销售额", "收入")):
        return "CNY"
    if unit in {"person", "people"} or any(term in text for term in ("招聘", "人才", "到岗", "团队")) and "人" in text:
        return "person"
    if unit in {"count"} or any(term in text for term in ("套", "个", "家", "项", "门店", "品牌", "系统", "专利")):
        return "count"
    if "roi" in text.lower() or "投产比" in text:
        return "ratio"
    return raw_unit


def normalize_metric_name(raw_metric_name: str, text: str) -> str:
    return raw_metric_name.strip() or text[:20]
