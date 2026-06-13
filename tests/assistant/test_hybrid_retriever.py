from __future__ import annotations

from evitalent.assistant.hybrid_retriever import HybridRetriever
from evitalent.assistant.knowledge_repository import KnowledgeRepository
from evitalent.assistant.models import AssistantKnowledgeChunk, ContextScope


def test_hybrid_retriever_filters_candidate_and_task():
    repo = KnowledgeRepository()
    repo.clear()
    chunks = [
        AssistantKnowledgeChunk(chunk_id="r1", task_id="task1", domain="hr", candidate_id="a", chunk_type="achievement", text_safe="候选人 a 有依据成果 3 项。"),
        AssistantKnowledgeChunk(chunk_id="r2", task_id="task1", domain="hr", candidate_id="b", chunk_type="achievement", text_safe="候选人 b 有依据成果 1 项。"),
        AssistantKnowledgeChunk(chunk_id="r3", task_id="task2", domain="hr", candidate_id="c", chunk_type="achievement", text_safe="候选人 c 有依据成果 2 项。"),
    ]
    repo.upsert_chunks(chunks)
    result = HybridRetriever(repository=repo).retrieve("成果", ContextScope.current_candidate, task_id="task1", domain="hr", candidate_id="a")
    assert [chunk.candidate_id for chunk in result.chunks] == ["a"]
    empty = HybridRetriever(repository=repo).retrieve("成果", ContextScope.current_candidate, task_id="task1", domain="hr", candidate_id="x")
    assert empty.insufficient_context is True
    repo.clear()


def test_hybrid_retriever_uses_safe_fallback_when_index_is_empty():
    repo = KnowledgeRepository()
    repo.clear()
    retriever = HybridRetriever(repository=repo)
    help_result = retriever.retrieve("综合竞争力指数如何计算？", ContextScope.system_help, task_id="fixture_task")
    assert help_result.insufficient_context is False
    assert help_result.chunks
    assert any(chunk.chunk_type == "system_help" for chunk in help_result.chunks)

    ranking_result = retriever.retrieve("为什么当前 HR 第一名排名靠前？", ContextScope.current_task, task_id="fixture_task", domain="hr")
    assert ranking_result.insufficient_context is False
    assert ranking_result.chunks
    assert any(chunk.chunk_type in {"ranking", "candidate_summary"} for chunk in ranking_result.chunks)
    repo.clear()
