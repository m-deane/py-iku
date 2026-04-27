"""Route aggregator — collects all sub-routers into a single ``router``."""

from __future__ import annotations

from fastapi import APIRouter

from .audit import router as audit_router
from .catalog import router as catalog_router
from .chat import router as chat_router
from .comments import router as comments_router
from .convert import router as convert_router
from .diff import router as diff_router
from .explain import router as explain_router
from .export import router as export_router
from .flows import router as flows_router
from .github import router as github_router
from .governance import router as governance_router
from .health import router as health_router
from .llm_history import router as llm_history_router
from .market_calendar import router as market_calendar_router
from .plugins import router as plugins_router
from .score import router as score_router
from .share import router as share_router
from .suggest import router as suggest_router
from .templates import router as templates_router
from .version import router as version_router

router = APIRouter()
router.include_router(health_router)
router.include_router(version_router)
router.include_router(convert_router)
router.include_router(catalog_router)
router.include_router(diff_router)
router.include_router(score_router)
router.include_router(export_router)
router.include_router(flows_router)
router.include_router(comments_router)
router.include_router(share_router)
router.include_router(github_router)
router.include_router(audit_router)
router.include_router(templates_router)
router.include_router(chat_router)
router.include_router(explain_router)
router.include_router(suggest_router)
router.include_router(llm_history_router)
router.include_router(governance_router)
router.include_router(market_calendar_router)
router.include_router(plugins_router)
