from __future__ import annotations

from evitalent.assistant.answer_guardrail import AnswerGuardrail, DECISION_LIMIT, PRIVACY_REFUSAL
from evitalent.assistant.assistant_client import AssistantClient, AssistantClientError
from evitalent.assistant.assistant_prompt_builder import AssistantPromptBuilder
from evitalent.assistant.hybrid_retriever import HybridRetriever
from evitalent.assistant.models import AssistantChatRequest, AssistantChatResponse
from evitalent.assistant.safe_context_builder import SafeContextBuilder
from evitalent.assistant.session_repository import SessionRepository

FALLBACK_SUFFIX = "\n\n回答用于招聘分析辅助，不构成最终录用结论。"
MODEL_UNAVAILABLE_ANSWER = "本地智能分析助手暂时不可用，未能调用 evitalent 模型完成回答。请确认 Ollama 已启动，并且已加载助手模型。"


class ChatService:
    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        client: AssistantClient | None = None,
        sessions: SessionRepository | None = None,
        guardrail: AnswerGuardrail | None = None,
        prompt_builder: AssistantPromptBuilder | None = None,
    ) -> None:
        self.retriever = retriever or HybridRetriever()
        self.client = client or AssistantClient()
        self.sessions = sessions or SessionRepository()
        self.guardrail = guardrail or AnswerGuardrail()
        self.prompt_builder = prompt_builder or AssistantPromptBuilder()

    def ask(self, request: AssistantChatRequest) -> AssistantChatResponse:
        sid = self.sessions.ensure_session(request.session_id, request.task_id, request.domain, request.candidate_id, request.scope.value)
        question_guard = self.guardrail.check_user_question(request.question)
        if not question_guard.passed:
            return AssistantChatResponse(session_id=sid, answer=question_guard.text, blocked=True, safety_passed=False)
        retrieval = self.retriever.retrieve(request.question, request.scope, request.task_id, request.domain, request.candidate_id)
        context = SafeContextBuilder().build(retrieval.chunks, request.scope)
        messages = (
            self.prompt_builder.build_general_chat_messages(request.question, self.sessions.history(sid))
            if retrieval.insufficient_context
            else self.prompt_builder.build_messages(request.question, context, self.sessions.history(sid), request.scope)
        )
        self.sessions.add_message(sid, "user", request.question)
        try:
            answer = self.client.chat(messages)
        except Exception:
            answer = MODEL_UNAVAILABLE_ANSWER if retrieval.insufficient_context else self._structured_fallback(request.question, retrieval.chunks)
        checked = self.guardrail.check_answer(answer)
        final_answer = (checked.text if checked.passed else checked.text) + FALLBACK_SUFFIX
        self.sessions.add_message(sid, "assistant", final_answer)
        return AssistantChatResponse(
            session_id=sid,
            answer=final_answer,
            source_labels=retrieval.source_labels,
            safety_passed=checked.passed,
            blocked=not checked.passed,
            retrieved_chunk_count=len(retrieval.chunks),
        )

    @staticmethod
    def _structured_fallback(question: str, chunks) -> str:
        joined = "\n".join(chunk.text_safe for chunk in chunks[:5])
        if any(word in question for word in ["录用", "淘汰", "晋升决定"]):
            return DECISION_LIMIT
        if not joined:
            return "当前简历材料不足以支持这一判断，建议在面试或背景调查中进一步确认。"
        return "1. 综合判断\n可根据当前匿名安全结果进行辅助分析。\n\n2. 主要依据\n" + joined[:1200] + "\n\n3. 待核验事项\n建议在面试中核实成果口径、个人贡献和业务场景。\n\n4. 使用边界说明\n本回答不构成最终录用结论。"

    def clear(self, session_id: str) -> None:
        self.sessions.clear(session_id)
