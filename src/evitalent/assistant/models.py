from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ContextScope(str, Enum):
    system_help = "system_help"
    current_candidate = "current_candidate"
    current_task = "current_task"
    current_domain = "current_domain"


ChunkType = Literal["candidate_summary", "ranking", "achievement", "risk", "scoring_explanation", "system_help"]


class AssistantKnowledgeChunk(BaseModel):
    chunk_id: str
    task_id: Optional[str] = None
    domain: str
    candidate_id: Optional[str] = None
    chunk_type: ChunkType
    text_safe: str = Field(min_length=1)
    source_refs: List[str] = Field(default_factory=list)
    display_allowed: bool = True
    safety_passed: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssistantChatRequest(BaseModel):
    session_id: Optional[str] = None
    question: str
    scope: ContextScope = ContextScope.system_help
    task_id: Optional[str] = None
    domain: Optional[str] = None
    candidate_id: Optional[str] = None
    include_displayable_evidence: bool = False


class AssistantChatResponse(BaseModel):
    session_id: str
    answer: str
    source_labels: List[str] = Field(default_factory=list)
    safety_passed: bool = True
    blocked: bool = False
    retrieved_chunk_count: int = 0


class RetrievalResult(BaseModel):
    chunks: List[AssistantKnowledgeChunk] = Field(default_factory=list)
    insufficient_context: bool = False
    source_labels: List[str] = Field(default_factory=list)
