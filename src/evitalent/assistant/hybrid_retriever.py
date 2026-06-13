from __future__ import annotations

from evitalent.assistant.embedding_client import EmbeddingClient, EmbeddingClientError
from evitalent.assistant.knowledge_chunk_builder import KnowledgeChunkBuilder
from evitalent.assistant.knowledge_repository import KnowledgeRepository
from evitalent.assistant.models import AssistantKnowledgeChunk, ContextScope, RetrievalResult
from evitalent.assistant.vector_index import top_k_by_similarity
from evitalent.settings import get_settings


class HybridRetriever:
    def __init__(self, repository: KnowledgeRepository | None = None, embedding_client: EmbeddingClient | None = None) -> None:
        self.repository = repository or KnowledgeRepository()
        self.embedding_client = embedding_client
        self.settings = get_settings()

    def retrieve(self, question: str, scope: ContextScope, task_id: str | None = None, domain: str | None = None, candidate_id: str | None = None, top_k: int | None = None) -> RetrievalResult:
        chunks = self._filtered_chunks(scope, task_id, domain, candidate_id)
        if not chunks:
            chunks = self._fallback_chunks(scope, task_id, domain, candidate_id)
        if not chunks:
            return RetrievalResult(chunks=[], insufficient_context=True)
        structured = self._structured_match(question, chunks)
        if structured:
            selected = structured[: top_k or self.settings.assistant_retrieval_top_k]
            return RetrievalResult(chunks=selected, source_labels=self._labels(selected))
        if self.embedding_client:
            try:
                query_vector = self.embedding_client.embed(question)
                vectors = self.repository.list_embeddings(self.embedding_client.model)
                wanted_ids = {chunk.chunk_id for chunk in chunks}
                vectors = {key: value for key, value in vectors.items() if key in wanted_ids}
                if vectors:
                    ranked_ids = [chunk_id for chunk_id, _ in top_k_by_similarity(query_vector, vectors, top_k or self.settings.assistant_retrieval_top_k)]
                    by_id = {chunk.chunk_id: chunk for chunk in chunks}
                    selected = [by_id[item] for item in ranked_ids if item in by_id]
                    return RetrievalResult(chunks=selected, insufficient_context=not selected, source_labels=self._labels(selected))
            except EmbeddingClientError:
                pass
        selected = chunks[: top_k or self.settings.assistant_retrieval_top_k]
        return RetrievalResult(chunks=selected, source_labels=self._labels(selected))

    def _filtered_chunks(self, scope: ContextScope, task_id: str | None, domain: str | None, candidate_id: str | None):
        if scope == ContextScope.system_help:
            return [chunk for chunk in self.repository.list_chunks() if chunk.chunk_type in {"system_help", "scoring_explanation"}]
        if scope == ContextScope.current_candidate:
            if not candidate_id:
                return []
            return self.repository.list_chunks(task_id=task_id, domain=domain, candidate_id=candidate_id)
        if scope == ContextScope.current_task:
            return self.repository.list_chunks(task_id=task_id, domain=domain)
        if scope == ContextScope.current_domain:
            return self.repository.list_chunks(domain=domain)
        return []

    def _fallback_chunks(self, scope: ContextScope, task_id: str | None, domain: str | None, candidate_id: str | None) -> list[AssistantKnowledgeChunk]:
        builder = KnowledgeChunkBuilder()
        if scope == ContextScope.system_help:
            return builder.system_help_chunks()
        if task_id == "fixture_task":
            return self._fixture_task_chunks(scope, domain, candidate_id)
        return []

    @staticmethod
    def _fixture_task_chunks(scope: ContextScope, domain: str | None, candidate_id: str | None) -> list[AssistantKnowledgeChunk]:
        from evitalent.extraction.mock_extractor import MockExtractor
        from evitalent.scoring.ranker import rank_candidates

        target_domains = [domain] if domain else ["hr", "production", "ecommerce", "brand", "sales", "rd"]
        builder = KnowledgeChunkBuilder()
        chunks: list[AssistantKnowledgeChunk] = []
        candidates = MockExtractor().load_all()
        for target_domain in target_domains:
            selected = [
                candidate
                for candidate in candidates
                if any(item.domain == target_domain for item in candidate.candidate_profile.target_domain_candidates)
            ]
            if selected:
                chunks.extend(builder.from_mock_ranking(rank_candidates(selected, target_domain), task_id="fixture_task"))
        business_chunks = [chunk for chunk in chunks if chunk.chunk_type != "system_help"]
        chunks = business_chunks + builder.system_help_chunks()
        if scope == ContextScope.current_candidate:
            return [chunk for chunk in chunks if chunk.candidate_id == candidate_id]
        if scope == ContextScope.current_domain and domain:
            return [chunk for chunk in chunks if chunk.domain == domain]
        return chunks

    @staticmethod
    def _structured_match(question: str, chunks):
        hits = []
        for chunk in chunks:
            if chunk.candidate_id and chunk.candidate_id in question:
                hits.append(chunk)
            elif "排名" in question and chunk.chunk_type == "ranking":
                hits.append(chunk)
            elif ("第一" in question or "前三" in question or "靠前" in question) and chunk.chunk_type in {"ranking", "candidate_summary"}:
                hits.append(chunk)
            elif ("指数" in question or "评分" in question or "规则" in question or "隐私" in question or "如何" in question or "怎么" in question) and chunk.chunk_type in {"system_help", "scoring_explanation"}:
                hits.append(chunk)
            elif ("风险" in question or "核验" in question) and chunk.chunk_type == "risk":
                hits.append(chunk)
            elif ("成果" in question or "面试" in question) and chunk.chunk_type == "achievement":
                hits.append(chunk)
        return hits

    @staticmethod
    def _labels(chunks) -> list[str]:
        labels = []
        for chunk in chunks:
            if chunk.candidate_id:
                labels.append(f"依据：{chunk.candidate_id} 匿名{chunk.chunk_type}")
            else:
                labels.append(f"依据：{chunk.domain} {chunk.chunk_type}")
        return labels
