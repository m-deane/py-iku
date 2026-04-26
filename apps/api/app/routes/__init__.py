"""Route aggregator — collects all sub-routers into a single ``router``."""

from __future__ import annotations

from fastapi import APIRouter

from .catalog import router as catalog_router
from .convert import router as convert_router
from .diff import router as diff_router
from .health import router as health_router
from .score import router as score_router

# Placeholders for future milestones (M6, M7).  Each is an empty
# APIRouter so this file can import them without errors; they will be filled
# in their respective milestones.
export_router: APIRouter = APIRouter()   # M6
flows_router: APIRouter = APIRouter()    # M7
audit_router: APIRouter = APIRouter()    # M7

router = APIRouter()
router.include_router(health_router)
router.include_router(convert_router)
router.include_router(catalog_router)
router.include_router(diff_router)
router.include_router(score_router)
router.include_router(export_router)
router.include_router(flows_router)
router.include_router(audit_router)
