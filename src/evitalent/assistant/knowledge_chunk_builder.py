from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL

from evitalent.assistant.access_policy import AccessPolicy
from evitalent.assistant.models import AssistantKnowledgeChunk


def _chunk_id(*parts: str) -> str:
    return "chunk_" + uuid5(NAMESPACE_URL, "::".join(parts)).hex[:16]


class KnowledgeChunkBuilder:
    def __init__(self, policy: AccessPolicy | None = None) -> None:
        self.policy = policy or AccessPolicy()

    def system_help_chunks(self) -> list[AssistantKnowledgeChunk]:
        texts = [
            "综合竞争力指数由能力表现分、材料可信度和风险扣减共同形成，用于当前岗位方向内的辅助比较。",
            "能力表现分反映教育基础、领域匹配、相关经验、稳定性、成长轨迹、平台复杂度、管理跨度、专业能力、成果影响和协同领导十项指标。",
            "材料可信度反映量化证据、证据可追溯性、信息完整性、一致性和可核验程度。缺失信息不会直接判零，但会降低可信度。",
            "系统不会使用姓名、电话、邮箱、出生日期、婚姻、家庭、薪资、详细地址等敏感信息参与排序。",
        ]
        return [
            AssistantKnowledgeChunk(
                chunk_id=_chunk_id("system_help", str(index)),
                task_id=None,
                domain="system",
                candidate_id=None,
                chunk_type="system_help",
                text_safe=text,
                source_refs=["系统规则说明"],
            )
            for index, text in enumerate(texts, start=1)
        ]

    def from_ranking_summary(self, summary: dict, task_id: str | None = None) -> list[AssistantKnowledgeChunk]:
        chunks: list[AssistantKnowledgeChunk] = self.system_help_chunks()
        domains = summary.get("domains", {}) if isinstance(summary, dict) else {}
        for domain, payload in domains.items():
            ranking = payload.get("ranking", [])
            if ranking:
                order = "、".join(f"{item.get('rank')}位:{item.get('document_id')}" for item in ranking)
                text = f"{domain} 领域匿名排序为 {order}；纳入比较人数 {len(ranking)}。"
                chunks.append(self._safe_chunk(task_id, domain, None, "ranking", text, ["匿名排名结果"]))
            excluded = payload.get("excluded_counts", {})
            for item in ranking:
                cid = item.get("document_id")
                text = (
                    f"候选人 {cid} 在 {domain} 领域的综合竞争力指数 {item.get('rank_score')}，"
                    f"能力表现分 {item.get('bcs')}，材料可信度 {item.get('eci')}，风险扣减 {item.get('penalty')}；"
                    f"核心优势包括 {self._join(item.get('top_strength_labels'))}。"
                )
                chunks.append(self._safe_chunk(task_id, domain, cid, "candidate_summary", text, [f"{cid}匿名摘要"]))
                ach = f"候选人 {cid} 有依据成果数为 {item.get('grounded_achievement_count', 0)}，可用于面试中核验具体贡献、指标口径和业务场景。"
                chunks.append(self._safe_chunk(task_id, domain, cid, "achievement", ach, [f"{cid}成果统计"]))
                risks = item.get("risk_flag_types", [])
                risk_text = f"候选人 {cid} 的待核验事项包括 {self._join(risks) if risks else '暂无明显待核验事项'}。"
                chunks.append(self._safe_chunk(task_id, domain, cid, "risk", risk_text, [f"{cid}风险提示"]))
            if excluded:
                text = f"{domain} 领域排除或待处理文档状态统计：{', '.join(f'{k}:{v}' for k, v in excluded.items())}。"
                chunks.append(self._safe_chunk(task_id, domain, None, "risk", text, ["排除原因统计"]))
        return chunks

    def from_mock_ranking(self, ranking, task_id: str = "fixture_task") -> list[AssistantKnowledgeChunk]:
        summary = {"domains": {ranking.domain: {"ranking": [], "excluded_counts": {}}}}
        for item in ranking.candidates:
            summary["domains"][ranking.domain]["ranking"].append(
                {
                    "rank": item.rank,
                    "document_id": item.candidate_id,
                    "rank_score": item.rank_score,
                    "bcs": item.bcs,
                    "eci": item.eci,
                    "penalty": item.penalty,
                    "top_strength_labels": [s.label for s in item.top_strengths],
                    "risk_flag_types": item.risk_flags,
                    "grounded_achievement_count": item.evidence_summary.quantified_achievement_count,
                }
            )
        return self.from_ranking_summary(summary, task_id)

    def _safe_chunk(self, task_id: str | None, domain: str, candidate_id: str | None, chunk_type: str, text: str, refs: list[str]) -> AssistantKnowledgeChunk:
        violations = self.policy.find_text_violations(text)
        return AssistantKnowledgeChunk(
            chunk_id=_chunk_id(task_id or "none", domain, candidate_id or "none", chunk_type, text),
            task_id=task_id,
            domain=domain,
            candidate_id=candidate_id,
            chunk_type=chunk_type,  # type: ignore[arg-type]
            text_safe=text,
            source_refs=refs,
            display_allowed=not violations,
            safety_passed=not violations,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _join(values) -> str:
        return "、".join(str(v) for v in values or []) or "暂无"
