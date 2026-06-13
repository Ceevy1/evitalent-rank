from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.assistant.embedding_client import EmbeddingClient, EmbeddingClientError
from evitalent.assistant.knowledge_chunk_builder import KnowledgeChunkBuilder
from evitalent.assistant.knowledge_repository import KnowledgeRepository
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import rank_candidates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["fixtures", "official_safe_results"], default="fixtures")
    args = parser.parse_args()
    if args.source != "fixtures":
        raise SystemExit("official_safe_results 尚未完成安全批处理，暂不建立助手索引。")
    candidates = MockExtractor().load_all()
    builder = KnowledgeChunkBuilder()
    chunks = []
    for domain in ["hr", "production", "ecommerce", "brand", "sales", "rd"]:
        selected = [c for c in candidates if any(item.domain == domain for item in c.candidate_profile.target_domain_candidates)]
        if selected:
            chunks.extend(builder.from_mock_ranking(rank_candidates(selected, domain), task_id="fixture_task"))
    repo = KnowledgeRepository()
    repo.clear()
    repo.upsert_chunks(chunks)
    embedded = 0
    client = EmbeddingClient()
    for chunk in chunks:
        if not (chunk.safety_passed and chunk.display_allowed):
            continue
        try:
            repo.save_embedding(chunk.chunk_id, client.model, client.embed(chunk.text_safe))
            embedded += 1
        except EmbeddingClientError:
            break
    print(f"indexed_chunk_count={len(chunks)}")
    print(f"embedded_chunk_count={embedded}")
    print(f"safety_passed={all(chunk.safety_passed for chunk in chunks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
