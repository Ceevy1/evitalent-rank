from __future__ import annotations

import pytest

from evitalent.assistant.access_policy import AccessPolicyError
from evitalent.assistant.models import AssistantKnowledgeChunk, ContextScope
from evitalent.assistant.safe_context_builder import SafeContextBuilder


def test_safe_context_builder_builds_safe_context_and_rejects_sensitive_text():
    builder = SafeContextBuilder()
    chunk = AssistantKnowledgeChunk(chunk_id="c1", domain="hr", chunk_type="system_help", text_safe="综合竞争力指数用于辅助比较。")
    context = builder.build([chunk], ContextScope.system_help)
    assert "综合竞争力指数" in context

    bad = AssistantKnowledgeChunk(chunk_id="c2", domain="hr", chunk_type="system_help", text_safe="电话：13900001111")
    with pytest.raises(AccessPolicyError):
        builder.build([bad], ContextScope.system_help)
