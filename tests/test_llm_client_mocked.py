import json

import httpx
import pytest

from evitalent.extraction.llm_client import LLMClient, LLMClientError, LLMResponseFormatError


def _client_with_handler(handler, max_retries=0):
    return LLMClient(
        provider="local_ollama",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="qwen2.5:7b",
        max_retries=max_retries,
        transport=httpx.MockTransport(handler),
    )


def test_llm_client_success_response():
    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"ok": True})}}]})

    data = _client_with_handler(handler).generate_json("system", "user")
    assert data == {"ok": True}


def test_llm_client_connection_failure():
    def handler(request):
        raise httpx.ConnectError("no server", request=request)

    with pytest.raises(LLMClientError):
        _client_with_handler(handler).generate_json("system", "user")


def test_llm_client_non_json_response():
    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})

    with pytest.raises(LLMResponseFormatError):
        _client_with_handler(handler, max_retries=0).generate_json("system", "user")


def test_llm_client_timeout():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(LLMClientError):
        _client_with_handler(handler).generate_json("system", "user")


def test_llm_client_health_check_success():
    def handler(request):
        return httpx.Response(200, json={"data": []})

    result = _client_with_handler(handler).health_check()
    assert result.ok is True
