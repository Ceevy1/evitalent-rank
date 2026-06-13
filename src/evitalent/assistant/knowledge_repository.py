from __future__ import annotations

import json

from sqlalchemy.orm import Session

from evitalent.assistant.models import AssistantKnowledgeChunk
from evitalent.db import AssistantEmbeddingRecord, AssistantKnowledgeChunkRecord, get_session


class KnowledgeRepository:
    def __init__(self, session: Session | None = None) -> None:
        self.session = session or get_session()

    def clear(self) -> None:
        self.session.query(AssistantEmbeddingRecord).delete()
        self.session.query(AssistantKnowledgeChunkRecord).delete()
        self.session.commit()

    def upsert_chunks(self, chunks: list[AssistantKnowledgeChunk]) -> None:
        unique_chunks = {}
        for chunk in chunks:
            unique_chunks[chunk.chunk_id] = chunk
        for chunk in unique_chunks.values():
            record = self.session.query(AssistantKnowledgeChunkRecord).filter_by(chunk_id=chunk.chunk_id).one_or_none()
            payload = {
                "task_id": chunk.task_id,
                "domain": chunk.domain,
                "candidate_id": chunk.candidate_id,
                "chunk_type": chunk.chunk_type,
                "text_safe": chunk.text_safe,
                "source_refs_json": json.dumps(chunk.source_refs, ensure_ascii=False),
                "display_allowed": int(chunk.display_allowed),
                "safety_passed": int(chunk.safety_passed),
            }
            if record:
                for key, value in payload.items():
                    setattr(record, key, value)
            else:
                self.session.add(AssistantKnowledgeChunkRecord(chunk_id=chunk.chunk_id, **payload))
        self.session.commit()

    def list_chunks(self, task_id: str | None = None, domain: str | None = None, candidate_id: str | None = None) -> list[AssistantKnowledgeChunk]:
        query = self.session.query(AssistantKnowledgeChunkRecord).filter_by(display_allowed=1, safety_passed=1)
        if task_id:
            query = query.filter(AssistantKnowledgeChunkRecord.task_id == task_id)
        if domain:
            query = query.filter(AssistantKnowledgeChunkRecord.domain == domain)
        if candidate_id:
            query = query.filter(AssistantKnowledgeChunkRecord.candidate_id == candidate_id)
        return [self._to_model(record) for record in query.all()]

    def save_embedding(self, chunk_id: str, model: str, vector: list[float]) -> None:
        record = self.session.query(AssistantEmbeddingRecord).filter_by(chunk_id=chunk_id).one_or_none()
        payload = {"embedding_model": model, "vector_json": json.dumps(vector)}
        if record:
            record.embedding_model = model
            record.vector_json = payload["vector_json"]
        else:
            self.session.add(AssistantEmbeddingRecord(chunk_id=chunk_id, **payload))
        self.session.commit()

    def list_embeddings(self, model: str | None = None) -> dict[str, list[float]]:
        query = self.session.query(AssistantEmbeddingRecord)
        if model:
            query = query.filter_by(embedding_model=model)
        return {record.chunk_id: json.loads(record.vector_json) for record in query.all()}

    @staticmethod
    def _to_model(record: AssistantKnowledgeChunkRecord) -> AssistantKnowledgeChunk:
        return AssistantKnowledgeChunk(
            chunk_id=record.chunk_id,
            task_id=record.task_id,
            domain=record.domain,
            candidate_id=record.candidate_id,
            chunk_type=record.chunk_type,
            text_safe=record.text_safe,
            source_refs=json.loads(record.source_refs_json),
            display_allowed=bool(record.display_allowed),
            safety_passed=bool(record.safety_passed),
            created_at=record.created_at.isoformat() if record.created_at else "",
        )
