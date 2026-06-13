from __future__ import annotations

from evitalent.assistant.vector_index import cosine_similarity, top_k_by_similarity


def test_vector_index_cosine_and_top_k():
    assert round(cosine_similarity([1, 0], [1, 0]), 4) == 1.0
    ranked = top_k_by_similarity([1, 0], {"a": [1, 0], "b": [0, 1]}, k=1)
    assert ranked[0][0] == "a"
