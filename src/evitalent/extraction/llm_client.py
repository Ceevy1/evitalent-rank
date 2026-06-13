from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from evitalent.settings import get_settings


class LLMClientError(RuntimeError):
    pass


class LLMConfigurationError(LLMClientError):
    pass


class LLMResponseFormatError(LLMClientError):
    def __init__(self, message: str, raw_response: str = "") -> None:
        super().__init__(message)
        self.raw_response = raw_response


@dataclass(frozen=True)
class LLMHealthResult:
    ok: bool
    provider: str
    mode: str
    message: str


class LLMClient:
    def __init__(
        self,
        provider: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        seed: int | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self.provider = provider or settings.llm_provider or "mock"
        configured_provider = provider or settings.llm_provider or "mock"
        default_base_url = "http://127.0.0.1:11434" if configured_provider == "local_ollama" else ""
        default_api_key = "ollama" if configured_provider == "local_ollama" else ""
        default_model = "evitalent-extractor:7b" if configured_provider == "local_ollama" else ""
        self.base_url = self._normalize_base_url((base_url if base_url is not None else settings.llm_base_url) or default_base_url, configured_provider)
        self.api_key = (api_key if api_key is not None else settings.llm_api_key) or default_api_key
        self.model = (model if model is not None else settings.llm_model) or default_model
        self.temperature = settings.llm_temperature if temperature is None else temperature
        self.timeout_seconds = settings.llm_timeout_seconds if timeout_seconds is None else timeout_seconds
        self.max_retries = settings.llm_max_retries if max_retries is None else max_retries
        self.seed = settings.llm_seed if seed is None else seed
        self.transport = transport

    def is_configured(self) -> bool:
        if self.provider == "mock":
            return True
        return bool(self.base_url and self.api_key and self.model)

    def health_check(self) -> LLMHealthResult:
        if self.provider == "mock":
            return LLMHealthResult(True, self.provider, "mock", "mock 模式无需模型连接。")
        if self.provider not in {"local_ollama", "compatible_api"}:
            return LLMHealthResult(False, self.provider, self.provider, "不支持的 LLM_PROVIDER。")
        if not self.is_configured():
            return LLMHealthResult(False, self.provider, self.provider, "LLM_BASE_URL、LLM_API_KEY 或 LLM_MODEL 未配置。")
        try:
            with self._client() as client:
                response = client.get(self._url("/models"), headers=self._headers())
                response.raise_for_status()
            return LLMHealthResult(True, self.provider, self.provider, "模型接口连接正常。")
        except Exception as exc:  # pragma: no cover - exact httpx subclasses vary by backend.
            return LLMHealthResult(False, self.provider, self.provider, f"模型接口连接失败：{type(exc).__name__}")

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.is_configured() or self.provider == "mock":
            raise LLMConfigurationError("当前模式未配置真实模型，请使用 mock 或配置 local_ollama/compatible_api。")

        raw = self._post_chat(system_prompt, user_prompt)
        try:
            return self._parse_json(raw)
        except LLMResponseFormatError as first_error:
            if self.max_retries <= 0:
                raise
            repair_system = "你只负责把上一轮模型输出修复为严格 JSON。不要补充事实，不要加入排名，不要输出 Markdown。"
            repair_user = (
                "上一轮输出无法解析为 JSON。请只返回修复后的 JSON。\n"
                f"错误摘要：{first_error}\n"
                "上一轮输出：\n"
                f"{raw[:12000]}"
            )
            repaired = self._post_chat(repair_system, repair_user)
            return self._parse_json(repaired)

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout_seconds, transport=self.transport)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _url(self, suffix: str) -> str:
        return self.base_url.rstrip("/") + suffix

    @staticmethod
    def _normalize_base_url(base_url: str, provider: str) -> str:
        cleaned = base_url.rstrip("/")
        if provider == "local_ollama" and cleaned and not cleaned.endswith("/v1"):
            return cleaned + "/v1"
        return cleaned

    def _post_chat(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        if self.seed is not None:
            payload["seed"] = self.seed
        try:
            with self._client() as client:
                response = client.post(self._url("/chat/completions"), headers=self._headers(), json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.TimeoutException as exc:
            raise LLMClientError("模型请求超时。") from exc
        except httpx.HTTPError as exc:
            raise LLMClientError(f"模型请求失败：{type(exc).__name__}") from exc
        except json.JSONDecodeError as exc:
            raise LLMResponseFormatError("模型接口返回体不是 JSON。") from exc

        if "choices" in body:
            return str(body["choices"][0]["message"]["content"])
        if "output_text" in body:
            return str(body["output_text"])
        if "output" in body:
            chunks: list[str] = []
            for item in body["output"]:
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"}:
                        chunks.append(str(content.get("text", "")))
            if chunks:
                return "\n".join(chunks)
        raise LLMResponseFormatError("模型接口返回缺少可解析文本字段。", json.dumps(body, ensure_ascii=False)[:1000])

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMResponseFormatError("模型输出不是严格 JSON。", raw[:1000]) from exc
        if not isinstance(payload, dict):
            raise LLMResponseFormatError("模型输出 JSON 顶层必须是对象。", raw[:1000])
        return payload
