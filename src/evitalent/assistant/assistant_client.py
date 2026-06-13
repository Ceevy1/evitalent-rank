from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from evitalent.settings import get_settings


class AssistantClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class AssistantStatus:
    enabled: bool
    connected: bool
    provider_display_name: str
    model_display_name: str
    message: str


class AssistantClient:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        settings = get_settings()
        self.enabled = settings.assistant_enabled
        self.provider = settings.assistant_provider
        self.model = settings.assistant_model
        self.base_url = settings.assistant_base_url.rstrip("/")
        if self.provider == "local_ollama" and not self.base_url.endswith("/v1"):
            self.base_url += "/v1"
        self.temperature = settings.assistant_temperature
        self.timeout_seconds = settings.assistant_timeout_seconds
        self.seed = settings.assistant_seed
        self.num_ctx = settings.assistant_num_ctx
        self.num_predict = settings.assistant_num_predict
        self.transport = transport

    def status(self) -> AssistantStatus:
        if not self.enabled:
            return AssistantStatus(False, False, "本地智能分析服务", self.model, "助手未启用")
        try:
            with httpx.Client(timeout=10, transport=self.transport) as client:
                response = client.get(self.base_url + "/models")
                response.raise_for_status()
                body = response.json()
            model_names = {item.get("id") or item.get("name") for item in body.get("data", [])}
            if self.model not in model_names:
                return AssistantStatus(True, False, "本地智能分析服务", self.model, "本地智能分析助手尚未配置")
            return AssistantStatus(True, True, "本地智能分析服务", self.model, "助手服务可用")
        except Exception as exc:
            return AssistantStatus(True, False, "本地智能分析服务", self.model, f"本地智能分析助手尚未配置或暂不可用：{type(exc).__name__}")

    def chat(self, messages: list[dict]) -> str:
        if not self.enabled:
            raise AssistantClientError("本地智能分析助手尚未配置")
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "seed": self.seed,
            "num_ctx": self.num_ctx,
            "num_predict": self.num_predict,
            "messages": messages,
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.post(self.base_url + "/chat/completions", json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise AssistantClientError(type(exc).__name__) from exc
        if "choices" in body:
            return str(body["choices"][0]["message"]["content"])
        if "message" in body and "content" in body["message"]:
            return str(body["message"]["content"])
        raise AssistantClientError("助手模型返回格式不完整")
