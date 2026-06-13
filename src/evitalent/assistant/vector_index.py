from __future__ import annotations

import numpy as np


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def top_k_by_similarity(query_vector: list[float], vectors: dict[str, list[float]], k: int = 5) -> list[tuple[str, float]]:
    scored = [(chunk_id, cosine_similarity(query_vector, vector)) for chunk_id, vector in vectors.items()]
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
