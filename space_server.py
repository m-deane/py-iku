"""Hugging Face Space entrypoint.

Wraps the existing ``apps.api.app.main:app`` FastAPI application by mounting the
built React SPA (``apps/web/dist``) at the root path. Every API route defined by
the FastAPI app (``/health``, ``/convert``, ``/convert/stream``, ``/catalog``,
``/diff``, ``/score``, ``/export``, ``/flows``, ``/share``, ``/audit``) is
reachable on the same origin and same port as the SPA, eliminating CORS for
in-browser calls. A SPA fallback returns ``index.html`` for any unknown GET that
isn't an API path, so client-side routing works on hard refresh.

Run with::

    uvicorn space_server:app --host 0.0.0.0 --port 7860
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure the API picks up Space-friendly defaults BEFORE create_app() runs.
# On HF Spaces the SPA and API share an origin, so CORS preflights are
# uncommon, but configure a sane allow-list for the platform to be safe.
os.environ.setdefault(
    "PY_IKU_STUDIO_CORS_ORIGINS",
    '["https://huggingface.co", "https://*.hf.space", "https://helwyr55-py-iku.hf.space"]',
)
os.environ.setdefault("PY_IKU_STUDIO_ENV", "prod")
# Persist saved flows + audit log inside the writable working directory.
os.environ.setdefault("PY_IKU_STUDIO_FLOWS_DIR", "/tmp/py-iku-flows")

from app.main import app  # noqa: E402  — must run after env defaults

# ---------------------------------------------------------------------------
# Static SPA mount
# ---------------------------------------------------------------------------

# /workspace/apps/web/dist is populated by the Node build stage in the Dockerfile.
_SPA_DIR = Path(os.environ.get("SPA_DIST_DIR", "/workspace/apps/web/dist"))
_INDEX_HTML = _SPA_DIR / "index.html"

# These prefixes belong to the FastAPI app and must not be served as SPA pages.
_API_PREFIXES: tuple[str, ...] = (
    "/health",
    "/convert",
    "/catalog",
    "/diff",
    "/score",
    "/export",
    "/flows",
    "/share",
    "/audit",
    "/openapi.json",
    "/docs",
    "/redoc",
)


if _SPA_DIR.exists():
    # Mount asset files (everything under dist/assets/, plus icons, manifests, etc.)
    # at the root, but defer index.html serving to the catch-all so we can do SPA
    # fallback routing.
    app.mount(
        "/assets",
        StaticFiles(directory=str(_SPA_DIR / "assets")) if (_SPA_DIR / "assets").exists() else StaticFiles(directory=str(_SPA_DIR)),
        name="spa-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str, request: Request) -> FileResponse:
        """Serve static files from dist/ when present, else fall back to index.html."""
        # Reject API paths — they should have already matched a real route.
        path_with_slash = "/" + full_path
        for prefix in _API_PREFIXES:
            if path_with_slash == prefix or path_with_slash.startswith(prefix + "/"):
                raise HTTPException(status_code=404, detail="Not Found")

        candidate = _SPA_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        if _INDEX_HTML.is_file():
            return FileResponse(_INDEX_HTML)
        raise HTTPException(status_code=404, detail="SPA bundle missing")

else:
    # When the SPA hasn't been built (e.g. local Python-only smoke test), expose
    # a friendly root so /health and /convert still work and the user knows why.
    @app.get("/", include_in_schema=False)
    async def _no_spa() -> dict[str, str]:
        return {
            "status": "API only",
            "detail": (
                f"SPA bundle not found at {_SPA_DIR!s}. The FastAPI routes "
                "(/health, /convert, /catalog, ...) are still available."
            ),
        }
