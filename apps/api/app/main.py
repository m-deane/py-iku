"""FastAPI application factory for py-iku Studio API."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from py2dataiku.exceptions import Py2DataikuError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .deps import get_settings
from .errors import problem_dict
from .routes import router

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(
        "py-iku Studio API starting up",
        extra={"env": settings.env, "cors_origins": settings.cors_origins},
    )
    yield
    logger.info("py-iku Studio API shutting down")


# ---------------------------------------------------------------------------
# Request-ID middleware
# ---------------------------------------------------------------------------


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generate a UUID request-id, store on ``request.state``, echo in response header."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Propagate to log context
        logger.debug("Request received", extra={"request_id": request_id, "path": request.url.path})

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="py-iku Studio API",
        description="FastAPI wrapper around py2dataiku for py-iku Studio",
        version="0.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request-ID (add after CORS so it runs first in the stack)
    app.add_middleware(RequestIDMiddleware)

    # Error handler — Py2DataikuError hierarchy → RFC 7807 problem+json
    @app.exception_handler(Py2DataikuError)
    async def py2dataiku_error_handler(
        request: Request, exc: Py2DataikuError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        body = problem_dict(exc, instance=str(request.url), request_id=request_id)
        logger.warning(
            "Py2DataikuError handled",
            extra={
                "exc_type": type(exc).__name__,
                "status": body["status"],
                "detail": str(exc),
                "request_id": request_id,
            },
        )
        return JSONResponse(
            status_code=body["status"],
            content=body,
            media_type="application/problem+json",
        )

    # Mount all routes
    app.include_router(router)

    return app


app = create_app()
