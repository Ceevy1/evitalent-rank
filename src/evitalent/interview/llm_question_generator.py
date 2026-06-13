from __future__ import annotations

import os
from typing import Optional


class LLMQuestionGenerator:
    def __init__(self, enabled: Optional[bool] = None) -> None:
        self.enabled = bool(enabled) if enabled is not None else os.getenv("INTERVIEW_LLM_REWRITE_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
        self.model = os.getenv("INTERVIEW_LLM_MODEL", "evitalent-assistant:7b")

    def rewrite(self, question: str, evidence_basis: str) -> str:
        # V1 keeps LLM rewriting disabled by default. Returning the template
        # preserves evidence basis and avoids adding unsupported facts.
        return question
