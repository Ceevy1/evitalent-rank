from __future__ import annotations

import re

from evitalent.achievement_detection.numeric_pattern_detector import business_numeric_expressions
from evitalent.extraction.llm_client import LLMClient, LLMClientError
from evitalent.models.raw_achievement import AchievementCandidate, RawAchievementEvent
from evitalent.normalization.metric_normalizer import normalize_unit
from evitalent.settings import PROJECT_ROOT


class LLMSingleEventExtractor:
    def __init__(self, client: LLMClient | None = None, use_llm: bool = False) -> None:
        self.client = client
        self.use_llm = use_llm

    def extract(self, candidate: AchievementCandidate, redaction_completed: bool = True) -> RawAchievementEvent:
        if not redaction_completed:
            raise ValueError("未完成脱敏，禁止单事件抽取。")
        if self.use_llm and self.client is not None and self.client.provider != "mock":
            system = (PROJECT_ROOT / "prompts" / "single_achievement_extraction_system_v1.txt").read_text(encoding="utf-8")
            template = (PROJECT_ROOT / "prompts" / "single_achievement_extraction_user_template_v1.txt").read_text(encoding="utf-8")
            payload = self.client.generate_json(
                system,
                template.format(
                    isolated_clause=candidate.isolated_clause,
                    linked_career_context=candidate.linked_career_context or "",
                ),
            )
            payload = self._sanitize_payload(payload, candidate)
            return RawAchievementEvent.model_validate(payload)
        return self._rule_fallback(candidate)

    def _sanitize_payload(self, payload: dict, candidate: AchievementCandidate) -> dict:
        allowed = {
            "raw_achievement_id",
            "raw_metric_name",
            "raw_achievement_text",
            "metric_value",
            "metric_value_upper",
            "unit",
            "period_months",
            "approximate",
            "lower_bound",
            "evidence_quote",
        }
        cleaned = {key: payload.get(key) for key in allowed}
        fallback = self._rule_fallback(candidate)
        defaults = fallback.model_dump()
        for key, value in list(cleaned.items()):
            if value is None and key in {"raw_achievement_id", "raw_metric_name", "raw_achievement_text", "unit", "evidence_quote"}:
                cleaned[key] = defaults[key]
        cleaned["raw_achievement_id"] = cleaned.get("raw_achievement_id") or defaults["raw_achievement_id"]
        cleaned["raw_metric_name"] = cleaned.get("raw_metric_name") or defaults["raw_metric_name"]
        cleaned["raw_achievement_text"] = cleaned.get("raw_achievement_text") or candidate.isolated_clause
        cleaned["metric_value"] = self._coerce_float(cleaned.get("metric_value"))
        if cleaned["metric_value"] is None or not self._value_appears_in_text(cleaned["metric_value"], candidate.isolated_clause):
            cleaned["metric_value"] = defaults["metric_value"]
        cleaned["metric_value_upper"] = self._coerce_float(cleaned.get("metric_value_upper"))
        cleaned["unit"] = normalize_unit(cleaned.get("unit") or defaults["unit"], candidate.isolated_clause)
        cleaned["period_months"] = self._coerce_int(cleaned.get("period_months"))
        if cleaned["period_months"] is None:
            cleaned["period_months"] = candidate.period_months
        cleaned["approximate"] = self._coerce_bool(cleaned.get("approximate"))
        cleaned["lower_bound"] = self._coerce_bool(cleaned.get("lower_bound"))
        cleaned["evidence_quote"] = cleaned.get("evidence_quote") or candidate.isolated_clause
        return cleaned

    @staticmethod
    def _coerce_float(value) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return abs(float(value))
        text = str(value).strip()
        if not text:
            return None
        match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
        if not match:
            return None
        return abs(float(match.group(0)))

    @staticmethod
    def _coerce_int(value) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        if isinstance(value, float):
            return int(value) if value >= 0 else None
        text = str(value).strip()
        if not text:
            return None
        match = re.search(r"\d+", text.replace(",", ""))
        return int(match.group(0)) if match else None

    @staticmethod
    def _coerce_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        text = str(value).strip().lower()
        return text in {"true", "1", "yes", "y", "是", "约", "大约", "左右"}

    @staticmethod
    def _value_appears_in_text(value: float, text: str) -> bool:
        value_text = str(int(value)) if float(value).is_integer() else str(value)
        return value_text in text

    def _rule_fallback(self, candidate: AchievementCandidate) -> RawAchievementEvent:
        text = candidate.isolated_clause
        value = self._first_value(text)
        return RawAchievementEvent(
            raw_achievement_id=candidate.candidate_event_id.replace("AC", "RAW"),
            raw_metric_name=self._metric_name(text),
            raw_achievement_text=text,
            metric_value=value,
            metric_value_upper=None,
            unit=self._unit(text),
            period_months=candidate.period_months,
            approximate="约" in text or "+" in text,
            lower_bound="+" in text,
            evidence_quote=text,
        )

    @staticmethod
    def _first_value(text: str) -> float | None:
        business = business_numeric_expressions(text)
        if business:
            return business[0].value
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(match.group(1)) if match else None

    @staticmethod
    def _unit(text: str) -> str | None:
        if "%" in text or "百分点" in text:
            return "percent"
        if any(term in text for term in ("亿", "万", "元")):
            return "CNY"
        if "人" in text or "人才" in text or "到岗" in text:
            return "person"
        if any(term in text for term in ("套", "个", "家", "项", "门店", "品牌", "系统", "专利")):
            return "count"
        if "ROI" in text or "投产比" in text:
            return "ratio"
        return None

    @staticmethod
    def _metric_name(text: str) -> str:
        for key in ("招聘完成率", "招聘达成率", "到岗率", "离职率", "流失率", "原料损耗", "损耗率", "产出率", "生产效率", "转化率", "GMV", "ROI", "回款率"):
            if key in text:
                return key
        if "招聘" in text:
            return "招聘人数"
        if "自动化" in text or "系统" in text:
            return "自动化系统"
        if "质量" in text:
            return "质量安全事故"
        return text[:12]
