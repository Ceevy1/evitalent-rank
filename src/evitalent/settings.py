from functools import lru_cache
import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:
    BaseSettings = object
    SettingsConfigDict = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "local"
    app_mode: str = "development"
    default_extraction_mode: str = "mock"
    database_url: str = "sqlite:///./data/evitalent.db"
    mock_fixture_dir: str = "./data/fixtures"
    llm_provider: str = "mock"
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: float = 0.0
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 1
    llm_seed: Optional[int] = None
    assistant_enabled: bool = True
    assistant_provider: str = "local_ollama"
    assistant_model: str = "evitalent-extractor:7b"
    assistant_base_url: str = "http://127.0.0.1:11434"
    assistant_temperature: float = 0.2
    assistant_seed: int = 9
    assistant_num_ctx: int = 8192
    assistant_num_predict: int = 1200
    assistant_timeout_seconds: float = 180.0
    assistant_embedding_model: str = "qwen3-embedding:0.6b"
    assistant_retrieval_top_k: int = 5
    assistant_max_context_chars: int = 6000
    assistant_allow_raw_resume_access: bool = False
    assistant_allow_private_filename_access: bool = False
    assistant_allow_sensitive_field_access: bool = False
    assistant_store_chat_history: bool = True
    assistant_store_safe_responses_only: bool = True

    if SettingsConfigDict:
        model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8")

    def __init__(self, **kwargs):
        if BaseSettings is object:
            for field, default in {
                "app_env": "local",
                "app_mode": "development",
                "default_extraction_mode": "mock",
                "database_url": "sqlite:///./data/evitalent.db",
                "mock_fixture_dir": "./data/fixtures",
                "llm_provider": "mock",
                "llm_base_url": None,
                "llm_api_key": None,
                "llm_model": None,
                "llm_temperature": 0.0,
                "llm_timeout_seconds": 60.0,
                "llm_max_retries": 1,
                "llm_seed": None,
                "assistant_enabled": True,
                "assistant_provider": "local_ollama",
                "assistant_model": "evitalent-extractor:7b",
                "assistant_base_url": "http://127.0.0.1:11434",
                "assistant_temperature": 0.2,
                "assistant_seed": 9,
                "assistant_num_ctx": 8192,
                "assistant_num_predict": 1200,
                "assistant_timeout_seconds": 180.0,
                "assistant_embedding_model": "qwen3-embedding:0.6b",
                "assistant_retrieval_top_k": 5,
                "assistant_max_context_chars": 6000,
                "assistant_allow_raw_resume_access": False,
                "assistant_allow_private_filename_access": False,
                "assistant_allow_sensitive_field_access": False,
                "assistant_store_chat_history": True,
                "assistant_store_safe_responses_only": True,
            }.items():
                env_name = field.upper()
                value = kwargs.get(field, os.getenv(env_name, default))
                if field in {"llm_temperature", "llm_timeout_seconds", "assistant_temperature", "assistant_timeout_seconds"}:
                    value = float(value)
                if field in {"llm_max_retries", "assistant_seed", "assistant_num_ctx", "assistant_num_predict", "assistant_retrieval_top_k", "assistant_max_context_chars"}:
                    value = int(value)
                if field == "llm_seed" and value not in {None, ""}:
                    value = int(value)
                if field.startswith("assistant_") and isinstance(default, bool):
                    value = str(value).lower() in {"1", "true", "yes", "on"}
                setattr(self, field, value)
        else:
            super().__init__(**kwargs)

    @property
    def resolved_database_url(self) -> str:
        if self.database_url.startswith("sqlite:///./"):
            return "sqlite:///" + str(PROJECT_ROOT / self.database_url.removeprefix("sqlite:///./"))
        return self.database_url

    @property
    def fixture_path(self) -> Path:
        return (PROJECT_ROOT / self.mock_fixture_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
