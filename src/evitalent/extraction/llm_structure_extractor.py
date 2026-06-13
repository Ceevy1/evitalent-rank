from __future__ import annotations

from dataclasses import dataclass

from evitalent.extraction.llm_client import LLMClient


@dataclass(frozen=True)
class StructureExtractionResult:
    target_domains: list[str]
    candidate_summary_tags: list[str]
    highest_role_level: str
    education_records: list[dict]
    career_records: list[dict]
    project_records: list[dict]
    quality_flags: list[dict]


class LLMStructureExtractor:
    """Macro-structure extractor placeholder.

    The hybrid pipeline can accept real structure payloads later; the deterministic
    demo path uses safe defaults so achievement extraction can be validated first.
    """

    def __init__(self, client: LLMClient | None = None, use_llm: bool = False) -> None:
        self.client = client
        self.use_llm = use_llm

    def extract(self, redacted_text: str, document_id: str) -> StructureExtractionResult:
        if self.use_llm and self.client is not None and self.client.provider != "mock":
            payload = self.client.generate_json(
                "你只抽取简历宏观结构，输出 JSON，不要输出成果事件、评分或排名。",
                (
                    "请从以下脱敏文本抽取宏观结构。JSON 字段：target_domains, candidate_summary_tags, "
                    "highest_role_level, education_records, career_records, project_records, quality_flags。\n"
                    f"document_id={document_id}\n"
                    f"text={redacted_text[:4000]}"
                ),
            )
            return StructureExtractionResult(
                target_domains=self._normalize_domains(payload.get("target_domains")) or self._infer_domains(redacted_text),
                candidate_summary_tags=payload.get("candidate_summary_tags") or [],
                highest_role_level=payload.get("highest_role_level") or "manager",
                education_records=payload.get("education_records") or [],
                career_records=payload.get("career_records") or [],
                project_records=payload.get("project_records") or [],
                quality_flags=payload.get("quality_flags") or [],
            )
        return self._fallback(redacted_text)

    def _fallback(self, redacted_text: str) -> StructureExtractionResult:
        domain = "hr"
        domains = self._infer_domains(redacted_text)
        domain = domains[0] if domains else domain
        return StructureExtractionResult(
            target_domains=[domain],
            candidate_summary_tags=[],
            highest_role_level="manager",
            education_records=[],
            career_records=[],
            project_records=[],
            quality_flags=[],
        )

    @staticmethod
    def _infer_domains(redacted_text: str) -> list[str]:
        if any(term in redacted_text for term in ("产出率", "损耗", "自动化", "生产")):
            return ["production"]
        if any(term in redacted_text for term in ("GMV", "ROI", "转化率")):
            return ["ecommerce"]
        return ["hr"]

    @staticmethod
    def _normalize_domains(values) -> list[str]:
        mapping = {
            "人力资源": "hr",
            "hr": "hr",
            "生产": "production",
            "production": "production",
            "电商": "ecommerce",
            "ecommerce": "ecommerce",
            "品牌": "brand",
            "brand": "brand",
            "销售": "sales",
            "sales": "sales",
            "研发": "rd",
            "rd": "rd",
        }
        if not isinstance(values, list):
            return []
        result = []
        for value in values:
            key = str(value).strip().lower()
            normalized = mapping.get(key) or mapping.get(str(value).strip())
            if normalized and normalized not in result:
                result.append(normalized)
        return result
