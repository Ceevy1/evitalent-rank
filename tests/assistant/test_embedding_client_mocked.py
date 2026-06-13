from __future__ import annotations

import httpx
import pytest

from evitalent.assistant.embedding_client import EmbeddingClient, EmbeddingClientError


def test_embedding_client_mocked_success():
    def handler(request):
        return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}]})

    client = EmbeddingClient(transport=httpx.MockTransport(handler))
    assert client.embed("匿名安全文本") == [0.1, 0.2]


def test_embedding_client_connection_failure_and_forbidden_content():
    def handler(request):
        return httpx.Response(500, json={})

    client = EmbeddingClient(transport=httpx.MockTransport(handler))
    with pytest.raises(EmbeddingClientError):
        client.embed("匿名安全文本")
    with pytest.raises(Exception):
        client.embed("电话：13900001111")
