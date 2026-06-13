from __future__ import annotations

from evitalent.assistant.knowledge_chunk_builder import KnowledgeChunkBuilder


def test_knowledge_chunk_builder_generates_safe_chunk_types():
    summary = {
        "domains": {
            "hr": {
                "ranking": [
                    {
                        "rank": 1,
                        "document_id": "hr_abc",
                        "rank_score": 90,
                        "bcs": 86,
                        "eci": 95,
                        "penalty": 0,
                        "top_strength_labels": ["招聘交付"],
                        "risk_flag_types": ["待核验"],
                        "grounded_achievement_count": 3,
                    }
                ],
                "excluded_counts": {"failed_safety": 1},
            }
        }
    }
    chunks = KnowledgeChunkBuilder().from_ranking_summary(summary, task_id="task1")
    types = {chunk.chunk_type for chunk in chunks}
    assert {"candidate_summary", "achievement", "risk", "ranking", "system_help"} <= types
    assert all(chunk.safety_passed for chunk in chunks)
    assert "original_filename" not in "\n".join(chunk.text_safe for chunk in chunks)
