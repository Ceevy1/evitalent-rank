from __future__ import annotations

from evitalent.assistant.assistant_prompt_builder import AssistantPromptBuilder
from evitalent.assistant.models import ContextScope


def test_prompt_builder_contains_privacy_and_decision_rules():
    prompt = AssistantPromptBuilder().system_prompt()
    assert "不得输出姓名" in prompt
    assert "不得直接给出" in prompt
    assert "不得猜测" in prompt
    messages = AssistantPromptBuilder().build_messages("解释排名", "匿名上下文", [], ContextScope.current_task)
    assert "匿名上下文" in messages[-1]["content"]


def test_prompt_builder_general_chat_mode_allows_non_context_questions():
    messages = AssistantPromptBuilder().build_general_chat_messages("人才排名与对比在不同领域对不同指标的权重一样吗？")
    assert "本地 Ollama 对话助手" in messages[0]["content"]
    assert "不要套用" in messages[0]["content"]
    assert "当前简历材料不足" in messages[0]["content"]
    assert "人才排名与对比" in messages[-1]["content"]
