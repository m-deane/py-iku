"""Health-check endpoint."""

from __future__ import annotations

import importlib.metadata

import py2dataiku
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


def _api_version() -> str:
    try:
        return importlib.metadata.version("py-iku-studio-api")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


class HealthResponse(BaseModel):
    status: str
    version: str
    py_iku_version: str


@router.get("/health", response_model=HealthResponse, summary="Service liveness check")
async def health() -> HealthResponse:
    """Return service status, API version, and the underlying py2dataiku version."""
    return HealthResponse(
        status="ok",
        version=_api_version(),
        py_iku_version=py2dataiku.__version__,
    )
