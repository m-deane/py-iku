"""FastAPI dependencies: settings, request-id, repositories."""

from __future__ import annotations

import uuid
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Header, Request
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .store import AuditRepo, FlowsRepo


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
    flows_dir: Path = Field(
        default=Path("./.py-iku-flows"),
        description="Directory used to persist saved flows and audit log",
    )
    share_default_ttl_seconds: int = Field(
        default=24 * 60 * 60,
        description="Default share-link TTL (24 hours)",
    )
    share_rate_limit_per_minute: int = Field(
        default=10,
        description="Per-IP rate limit for GET /share/{token}",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()


@lru_cache(maxsize=1)
def get_flows_repo() -> FlowsRepo:
    """Return the singleton ``FlowsRepo`` rooted under ``settings.flows_dir``."""
    settings = get_settings()
    return FlowsRepo(base_dir=settings.flows_dir)


@lru_cache(maxsize=1)
def get_audit_repo() -> AuditRepo:
    """Return the singleton ``AuditRepo`` rooted under ``settings.flows_dir``."""
    settings = get_settings()
    return AuditRepo(base_dir=settings.flows_dir)


def reset_repo_singletons() -> None:
    """Clear the cached repo singletons.  Used by the test suite to re-bind to
    a freshly created ``flows_dir`` per test.
    """
    get_flows_repo.cache_clear()
    get_audit_repo.cache_clear()


def get_request_id(x_request_id: Annotated[str | None, Header()] = None) -> str:
    """Return the request-id from the incoming header, or generate a new UUID."""
    return x_request_id or str(uuid.uuid4())


def get_request_id_from_state(request: Request) -> str:
    """Return the request-id stored on ``request.state`` by the middleware."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))
