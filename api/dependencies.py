"""
API bootstrap, settings, schemas, and shared dependency wiring for the observability
service.

Author: Sarala Biswal
"""

from collections.abc import AsyncIterator
from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class AppMode(StrEnum):
    DEMO = "demo"
    REAL = "real"


class Settings(BaseSettings):
    app_mode: AppMode = AppMode.DEMO
    database_url: str = "sqlite+aiosqlite:///./observability.db"
    budget_limit_usd: float = 500.0
    slo_target_ms: int = 2000
    drift_alert_threshold: float = 0.35
    quality_gate_threshold: float = 0.70
    enable_quality_scoring: bool = True
    llm_mode: str = "ollama"
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://127.0.0.1:11434"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    azure_openai_key: str = ""
    azure_openai_endpoint: str = ""
    litellm_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def has_openai_api_key(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session
