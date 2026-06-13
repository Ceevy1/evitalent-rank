from __future__ import annotations

from fastapi import APIRouter, HTTPException

from evitalent.assistant.assistant_client import AssistantClient
from evitalent.assistant.chat_service import ChatService
from evitalent.assistant.embedding_client import EmbeddingClient
from evitalent.assistant.knowledge_chunk_builder import KnowledgeChunkBuilder
from evitalent.assistant.knowledge_repository import KnowledgeRepository
from evitalent.assistant.models import AssistantChatRequest
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import rank_candidates
from evitalent.settings import get_settings

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


@router.get("/status")
def assistant_status() -> dict:
    settings = get_settings()
    status = AssistantClient().status()
    return {
        "enabled": settings.assistant_enabled,
        "provider_display_name": "本地智能分析服务",
        "model_display_name": settings.assistant_model,
        "connected": status.connected,
        "knowledge_index_ready": bool(KnowledgeRepository().list_chunks()),
        "embedding_enabled": bool(settings.assistant_embedding_model),
        "sensitive_access_disabled": not settings.assistant_allow_sensitive_field_access,
        "available_scopes": ["system_help", "current_candidate", "current_task", "current_domain"],
    }


@router.post("/index/rebuild")
def rebuild_index(scope: str = "fixture_safe_data") -> dict:
    if scope != "fixture_safe_data":
        raise HTTPException(status_code=400, detail="official_safe_results 尚未完成安全批处理，暂不允许建立索引。")
    candidates = MockExtractor().load_all()
    chunks = []
    builder = KnowledgeChunkBuilder()
    for domain in ["hr", "production", "ecommerce", "brand", "sales", "rd"]:
        domain_candidates = [c for c in candidates if any(item.domain == domain for item in c.candidate_profile.target_domain_candidates)]
        if domain_candidates:
            chunks.extend(builder.from_mock_ranking(rank_candidates(domain_candidates, domain), task_id="fixture_task"))
    repo = KnowledgeRepository()
    repo.clear()
    repo.upsert_chunks(chunks)
    return {
        "status": "completed",
        "indexed_chunk_count": len(chunks),
        "indexed_candidate_count": len({chunk.candidate_id for chunk in chunks if chunk.candidate_id}),
        "embedding_model_display_name": get_settings().assistant_embedding_model,
        "sensitive_chunk_count": sum(1 for chunk in chunks if not chunk.safety_passed),
        "safety_passed": all(chunk.safety_passed for chunk in chunks),
    }


@router.post("/chat")
def assistant_chat(request: AssistantChatRequest) -> dict:
    return ChatService().ask(request).model_dump()


@router.post("/session/clear")
def clear_session(session_id: str) -> dict:
    ChatService().clear(session_id)
    return {"status": "cleared"}
