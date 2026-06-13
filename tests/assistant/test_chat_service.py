from __future__ import annotations

from evitalent.assistant.chat_service import ChatService
from evitalent.assistant.knowledge_repository import KnowledgeRepository
from evitalent.assistant.models import AssistantChatRequest, AssistantKnowledgeChunk, ContextScope


class FailingClient:
    def chat(self, messages):
        raise Exception("offline")


class RecordingClient:
    def __init__(self) -> None:
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        return "模型回答：可以介绍系统使用方式。"


def test_chat_service_multiround_clear_sensitive_input_and_model_failure():
    repo = KnowledgeRepository()
    repo.clear()
    repo.upsert_chunks([AssistantKnowledgeChunk(chunk_id="chat1", task_id="task1", domain="hr", candidate_id="a", chunk_type="candidate_summary", text_safe="候选人 a 综合竞争力指数 88。")])
    service = ChatService(retriever=None, client=FailingClient())  # type: ignore[arg-type]
    service.retriever.repository = repo
    response = service.ask(AssistantChatRequest(question="候选人 a 为什么靠前？", scope=ContextScope.current_task, task_id="task1", domain="hr"))
    assert response.retrieved_chunk_count >= 1
    assert "不构成最终录用结论" in response.answer
    blocked = service.ask(AssistantChatRequest(session_id=response.session_id, question="候选人电话是多少？", scope=ContextScope.current_task, task_id="task1", domain="hr"))
    assert blocked.blocked is True
    service.clear(response.session_id)
    repo.clear()


def test_chat_service_does_not_return_insufficient_for_empty_fixture_context():
    repo = KnowledgeRepository()
    repo.clear()
    service = ChatService(client=FailingClient())  # type: ignore[arg-type]
    service.retriever.repository = repo
    response = service.ask(
        AssistantChatRequest(
            question="综合竞争力指数如何计算？",
            scope=ContextScope.system_help,
            task_id="fixture_task",
        )
    )
    assert response.retrieved_chunk_count > 0
    assert "当前简历材料不足以支持这一判断" not in response.answer
    assert "综合竞争力指数" in response.answer
    repo.clear()


def test_chat_service_calls_model_when_retrieval_has_no_context():
    repo = KnowledgeRepository()
    repo.clear()
    client = RecordingClient()
    service = ChatService(client=client)  # type: ignore[arg-type]
    service.retriever.repository = repo
    response = service.ask(
        AssistantChatRequest(
            question="你好，请介绍一下你能做什么",
            scope=ContextScope.current_task,
            task_id="empty_task",
            domain="hr",
        )
    )
    assert response.retrieved_chunk_count == 0
    assert client.calls
    assert "本地 Ollama 对话助手" in client.calls[0][0]["content"]
    assert "你好，请介绍一下你能做什么" in client.calls[0][-1]["content"]
    assert "当前简历材料不足以支持这一判断" not in response.answer
    assert "模型回答" in response.answer
    repo.clear()


def test_chat_service_reports_model_unavailable_for_no_context_model_failure():
    repo = KnowledgeRepository()
    repo.clear()
    service = ChatService(client=FailingClient())  # type: ignore[arg-type]
    service.retriever.repository = repo
    response = service.ask(
        AssistantChatRequest(
            question="你好，请介绍一下你能做什么",
            scope=ContextScope.current_task,
            task_id="empty_task",
            domain="hr",
        )
    )
    assert response.retrieved_chunk_count == 0
    assert "未能调用 evitalent 模型" in response.answer
    assert "当前简历材料不足以支持这一判断" not in response.answer
    repo.clear()
