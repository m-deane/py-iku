"""Route aggregator — collects all sub-routers into a single ``router``."""

from __future__ import annotations

from fastapi import APIRouter

from .catalog import router as catalog_router
from .convert import router as convert_router
from .flows import router as flows_router
from .health import router as health_router
from .score import router as score_router
from .version import router as version_router

router = APIRouter()
router.include_router(health_router)
router.include_router(version_router)
router.include_router(convert_router)
router.include_router(catalog_router)
router.include_router(score_router)
router.include_router(flows_router)
