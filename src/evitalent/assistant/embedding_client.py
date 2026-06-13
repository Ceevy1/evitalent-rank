from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from evitalent.assistant.access_policy import AccessPolicy
from evitalent.settings import get_settings


class EmbeddingClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingHealth:
    ok: bool
    message: str


class EmbeddingClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, timeout_seconds: float | None = None, transport: httpx.BaseTransport | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.assistant_base_url).rstrip("/")
        self.ollama_root_url = self.base_url.removesuffix("/v1")
        if not self.base_url.endswith("/v1"):
            self.base_url += "/v1"
        self.model = model or settings.assistant_embedding_model
        self.timeout_seconds = timeout_seconds or settings.assistant_timeout_seconds
        self.transport = transport
        self.policy = AccessPolicy()

    def health_check(self) -> EmbeddingHealth:
        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.get(self.base_url + "/models")
                response.raise_for_status()
                body = response.json()
            model_names = {item.get("id") or item.get("name") for item in body.get("data", [])}
            if self.model not in model_names:
                return EmbeddingHealth(False, "embedding 模型尚未配置")
            return EmbeddingHealth(True, "embedding 模型接口可访问")
        except Exception as exc:
            return EmbeddingHealth(False, type(exc).__name__)

    def embed(self, text: str) -> list[float]:
        self.policy.validate_text(text)
        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.post(self.base_url + "/embeddings", json={"model": self.model, "input": text})
                if response.status_code >= 400 and self.transport is None:
                    response = client.post(self.ollama_root_url + "/api/embed", json={"model": self.model, "input": text})
                if response.status_code >= 400 and self.transport is None:
                    response = client.post(self.ollama_root_url + "/api/embeddings", json={"model": self.model, "prompt": text})
                response.raise_for_status()
                body: dict[str, Any] = response.json()
        except httpx.HTTPError as exc:
            raise EmbeddingClientError(type(exc).__name__) from exc
        data = body.get("data") or []
        if data and "embedding" in data[0]:
            return [float(v) for v in data[0]["embedding"]]
        if "embedding" in body:
            return [float(v) for v in body["embedding"]]
        if "embeddings" in body and body["embeddings"]:
            return [float(v) for v in body["embeddings"][0]]
        raise EmbeddingClientError("embedding response missing vector")
