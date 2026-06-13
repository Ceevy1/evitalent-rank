from __future__ import annotations

from evitalent.assistant.knowledge_repository import KnowledgeRepository
from evitalent.assistant.models import AssistantKnowledgeChunk


def test_knowledge_repository_saves_chunks_and_embeddings():
    repo = KnowledgeRepository()
    repo.clear()
    chunk = AssistantKnowledgeChunk(chunk_id="test_chunk_repo", task_id="task1", domain="hr", candidate_id="hr_abc", chunk_type="candidate_summary", text_safe="候选人 hr_abc 材料可信度较高。")
    repo.upsert_chunks([chunk])
    assert repo.list_chunks(task_id="task1", candidate_id="hr_abc")[0].chunk_id == "test_chunk_repo"
    repo.save_embedding(chunk.chunk_id, "mock-embedding", [1.0, 0.0])
    assert repo.list_embeddings("mock-embedding")[chunk.chunk_id] == [1.0, 0.0]
    repo.clear()
