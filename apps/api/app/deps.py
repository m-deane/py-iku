"""FastAPI dependencies: settings, request-id."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Annotated

from fastapi import Header, Request
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All variables use the ``PY_IKU_STUDIO_`` prefix.

    Example::

        PY_IKU_STUDIO_ENV=prod
        PY_IKU_STUDIO_CORS_ORIGINS='["https://app.example.com"]'
        PY_IKU_STUDIO_SECRET_KEY=supersecret
    """

    model_config = SettingsConfigDict(
        env_prefix="PY_IKU_STUDIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    env: str = Field(default="dev", description="Runtime environment: dev or prod")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"],
        description="Allowed CORS origins",
    )
    secret_key: str = Field(
        default="change-me-in-production",
        description="HMAC secret for signed share links",
    )
    max_payload_bytes: int = Field(
        default=256 * 1024,  # 256 KB
        description="Maximum request body size in bytes",
    )
    default_llm_provider: str = Field(
        default="anthropic",
        description="Default LLM provider name",
    )
    default_llm_model: str | None = Field(
        default=None,
        description="Default LLM model name (provider default if None)",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()


def get_request_id(x_request_id: Annotated[str | None, Header()] = None) -> str:
    """Return the request-id from the incoming header, or generate a new UUID."""
    return x_request_id or str(uuid.uuid4())


def get_request_id_from_state(request: Request) -> str:
    """Return the request-id stored on ``request.state`` by the middleware."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))
