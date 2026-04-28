"""LLM credentials & provider settings — server-side persistence + status.

Routes
------
* ``GET    /api/settings/llm``         → ``{provider, model, has_key, source}``
* ``POST   /api/settings/llm/key``     → persist a provider's key
* ``DELETE /api/settings/llm/key``     → remove the key for a given provider

The key is persisted as JSON to ``Settings.flows_dir / llm-credentials.json``
(0600 permissions on POSIX, gitignored alongside the rest of
``.py-iku-flows/``). The file holds plain text; this is acceptable for the
single-user, local-only Studio use case but is documented honestly in the
prompt+UI copy. The key is **never** echoed back over the wire — ``has_key``
is the only signal the frontend ever sees.

The conversion service consults
:func:`app.services.llm_credentials.resolve_api_key` at request time so the
file always wins over the environment variable, but the env var remains a
zero-config fallback when the file is absent.
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from ..deps import get_settings
from ..services.llm_credentials import (
    LlmCredentialStore,
    SUPPORTED_PROVIDERS,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LlmStatusResponse(BaseModel):
    """Status payload — what the frontend learns about the current LLM config."""

    provider: Literal["anthropic", "openai"] = Field(
        description="The provider currently selected as the default."
    )
    model: str | None = Field(
        default=None,
        description=(
            "The default model name for this provider, when one is configured. "
            "Null falls back to the provider's library default."
        ),
    )
    has_key: bool = Field(
        description=(
            "True when a usable key is reachable — either persisted via "
            "POST /api/settings/llm/key or set as an environment variable."
        ),
    )
    source: Literal["file", "env", "none"] = Field(
        description=(
            "Where the active key came from. 'file' wins over 'env' so users "
            "see the persisted credential's effect immediately."
        ),
    )
    supported_providers: list[str] = Field(
        default_factory=lambda: list(SUPPORTED_PROVIDERS),
        description="Providers the server knows how to dispatch to.",
    )


class SaveKeyRequest(BaseModel):
    """Payload for POST /api/settings/llm/key."""

    provider: Literal["anthropic", "openai"] = Field(
        description="Provider the key belongs to."
    )
    key: str = Field(
        min_length=1,
        max_length=512,
        description=(
            "API key. Stored plaintext on disk in single-user Studio mode — "
            "see /api/settings/llm response copy."
        ),
    )


class DeleteKeyRequest(BaseModel):
    """Payload for DELETE /api/settings/llm/key (body is optional, but
    when supplied lets the caller pick which provider's key to clear)."""

    provider: Literal["anthropic", "openai"] = Field(default="anthropic")


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


def get_credential_store() -> LlmCredentialStore:
    """Return a credential store bound to the current ``Settings.flows_dir``.

    Re-resolved per request because tests rebind ``flows_dir`` via
    ``conftest.py`` and we want each test to operate on its own tmp dir.
    """
    settings = get_settings()
    return LlmCredentialStore(base_dir=settings.flows_dir)


CredentialStoreDep = Annotated[LlmCredentialStore, Depends(get_credential_store)]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/llm", response_model=LlmStatusResponse)
async def get_llm_settings(store: CredentialStoreDep) -> LlmStatusResponse:
    """Return the current LLM provider/model/key status.

    The key is **never** included in the response. Use ``has_key`` and
    ``source`` to drive the UI 🟢/🔴 indicator.
    """
    settings = get_settings()
    provider = settings.default_llm_provider  # "anthropic" / "openai"
    if provider not in SUPPORTED_PROVIDERS:
        provider = "anthropic"
    state = store.status(provider)  # type: ignore[arg-type]
    return LlmStatusResponse(
        provider=provider,  # type: ignore[arg-type]
        model=state.model or settings.default_llm_model,
        has_key=state.has_key,
        source=state.source,
    )


@router.post(
    "/llm/key",
    response_model=LlmStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def save_llm_key(
    body: SaveKeyRequest,
    store: CredentialStoreDep,
) -> LlmStatusResponse:
    """Persist the API key for a given provider.

    The key is stored on disk under ``Settings.flows_dir`` with 0600
    permissions. We log only the provider — never the key value or its length.
    """
    if body.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider {body.provider!r}",
        )
    store.set_key(body.provider, body.key)
    logger.info("LLM key saved", extra={"provider": body.provider})
    state = store.status(body.provider)
    settings = get_settings()
    return LlmStatusResponse(
        provider=body.provider,
        model=state.model or settings.default_llm_model,
        has_key=state.has_key,
        source=state.source,
    )


@router.delete("/llm/key")
async def delete_llm_key(
    store: CredentialStoreDep,
    provider: Literal["anthropic", "openai"] = "anthropic",
) -> dict[str, bool]:
    """Remove the persisted key for *provider* (env-var fallback still applies).

    Returns a small JSON body — explicit and easy to assert on. We do not use a
    bare 204 here because some HTTP clients hang waiting for the closing
    chunked-encoding terminator when the response body is empty.
    """
    removed = store.clear_key(provider)
    logger.info("LLM key cleared", extra={"provider": provider, "removed": removed})
    return {"removed": removed}
