from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from evitalent.models.extraction import CandidateExtraction
from evitalent.official_samples.batch_state_store import COMPLETED_ELIGIBLE
from evitalent.official_samples.batch_state_store import BatchStateStore
from evitalent.official_samples.private_manifest import read_json, write_json
from evitalent.official_samples.settings import OfficialSampleSettings
from evitalent.scoring.ranker import rank_candidates


class DomainRankingRunner:
    def __init__(self, settings: OfficialSampleSettings) -> None:
        self.settings = settings
        self.state = BatchStateStore(settings.batch_state_path)

    def run(self, include_partial: bool = True) -> dict[str, Any]:
        state = self.state.load()
        all_safe: dict[str, Any] = {"domains": {}, "notes": {}}
        for domain in self.settings.domains:
            eligible = [item for item in state.get("documents", {}).values() if item.get("domain") == domain and item.get("status") == COMPLETED_ELIGIBLE]
            candidates: list[CandidateExtraction] = []
            private_rows = []
            for item in eligible:
                result_path = Path(item["result_path"])
                payload = read_json(result_path)
                candidates.append(CandidateExtraction.model_validate(payload["candidate_extraction"]))
            if candidates:
                ranking = rank_candidates(candidates, domain=domain, ranking_id=f"official_{domain}_v1")
                for row in ranking.candidates:
                    private_rows.append(row.model_dump(mode="json"))
                write_json(self.settings.rankings_dir / f"{domain}_ranking_private.json", {"domain": domain, "candidates": private_rows})
                safe_rows = [
                    {
                        "rank": row.rank,
                        "document_id": row.candidate_id,
                        "folder_domain": domain,
                        "detected_domains": [domain],
                        "domain_match_status": "matched",
                        "bcs": row.bcs,
                        "eci": row.eci,
                        "penalty": row.penalty,
                        "rank_score": row.rank_score,
                        "top_strength_labels": [strength.label for strength in row.top_strengths],
                        "risk_flag_types": row.risk_flags,
                        "grounded_achievement_count": row.evidence_summary.quantified_achievement_count,
                        "needs_review_count": 0,
                    }
                    for row in ranking.candidates
                ]
            else:
                safe_rows = []
            statuses = Counter(item.get("status") for item in state.get("documents", {}).values() if item.get("domain") == domain)
            all_safe["domains"][domain] = {
                "candidate_count": len(safe_rows),
                "excluded_counts": dict(statuses),
                "ranking": safe_rows,
            }
            if domain in {"sales", "rd"}:
                all_safe["notes"][domain] = "当前评分规则为 V1 模板规则，后续仍需更多专家标注进行领域权重校准，本次结果用于赛题样本测试与系统展示。"
        write_json(self.settings.rankings_dir / "all_domains_safe_summary.json", all_safe)
        return all_safe
