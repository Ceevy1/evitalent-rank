from __future__ import annotations

from typing import Any

from evitalent.assistant.access_policy import AccessPolicy
from evitalent.assistant.models import AssistantKnowledgeChunk, ContextScope


class SafeContextBuilder:
    def __init__(self, policy: AccessPolicy | None = None, max_chars: int = 6000) -> None:
        self.policy = policy or AccessPolicy()
        self.max_chars = max_chars

    def build(self, chunks: list[AssistantKnowledgeChunk], scope: ContextScope) -> str:
        parts: list[str] = [f"当前安全作用范围：{scope.value}"]
        for chunk in chunks:
            if not chunk.display_allowed or not chunk.safety_passed:
                continue
            self.policy.validate_text(chunk.text_safe)
            parts.append(f"[{chunk.chunk_type}] {chunk.text_safe}")
        context = "\n".join(parts)
        return context[: self.max_chars]

    def validate_context_payload(self, payload: Any) -> None:
        self.policy.validate_payload(payload)
