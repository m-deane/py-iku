"""Sprint-4 governance routes: lineage, schema-drift, lint, test-scaffolder."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from py2dataiku.exceptions import Py2DataikuError
from py2dataiku.models.dataiku_flow import DataikuFlow

from ..deps import get_flows_repo
from ..services.lineage_service import build_column_lineage, discover_columns
from ..services.lint_service import (
    RULE_CATALOG,
    apply_merge_adjacent_prepares,
    lint_flow,
)
from ..services.schema_drift import diff_flows, summarise
from ..services.test_scaffolder import scaffold_test
from ..store import FlowsRepo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["governance"])


# ---------------------------------------------------------------------------
# Pydantic request/response wrappers
# ---------------------------------------------------------------------------


class LintRequest(BaseModel):
    flow: dict[str, Any] = Field(..., description="Canonical DataikuFlow dict")


class LintEntry(BaseModel):
    rule_id: str
    severity: str
    recipe_id: str | None = None
    message: str
    fix: dict[str, Any] | None = None


class LintResponse(BaseModel):
    lints: list[LintEntry]
    rule_catalog: list[dict[str, str]] = Field(default_factory=lambda: list(RULE_CATALOG))


class LintFixRequest(BaseModel):
    flow: dict[str, Any]
    rule_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SchemaDriftRequest(BaseModel):
    prior: dict[str, Any]
    next: dict[str, Any] = Field(..., alias="next")

    model_config = {"populate_by_name": True}


class SchemaDriftResponse(BaseModel):
    summary: dict[str, Any]
    headline: str
    datasets_added: list[str]
    datasets_removed: list[str]
    per_dataset: list[dict[str, Any]]


class ScaffoldTestRequest(BaseModel):
    flow: dict[str, Any]
    source: str
    flow_name: str | None = None
    track_columns: list[str] = Field(default_factory=list)


class LineageResponse(BaseModel):
    column: str
    aliases: list[str]
    input_datasets: list[str]
    output_datasets: list[str]
    edges: list[dict[str, Any]]
    recipes: list[str]
    available_columns: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hydrate(flow: dict[str, Any]) -> dict[str, Any]:
    try:
        return DataikuFlow.from_dict(flow).to_dict()
    except (Py2DataikuError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail=f"Malformed flow body: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------


@router.get(
    "/flows/{flow_id}/lineage/{column_name}",
    response_model=LineageResponse,
    summary="Per-column lineage for a saved flow",
)
def get_lineage(
    flow_id: str,
    column_name: str,
    flows: FlowsRepo = Depends(get_flows_repo),
) -> LineageResponse:
    record = flows.get(flow_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"flow '{flow_id}' not found")
    flow = _hydrate(record.flow)
    lineage = build_column_lineage(flow, column_name)
    return LineageResponse(
        **lineage, available_columns=discover_columns(flow)
    )


class LineageInlineRequest(BaseModel):
    flow: dict[str, Any]
    column: str


@router.post(
    "/flows/lineage",
    response_model=LineageResponse,
    summary="Compute lineage on an inline flow (no persistence)",
)
def post_lineage_inline(body: LineageInlineRequest) -> LineageResponse:
    flow = _hydrate(body.flow)
    lineage = build_column_lineage(flow, body.column)
    return LineageResponse(**lineage, available_columns=discover_columns(flow))


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------


@router.post("/flows/lint", response_model=LintResponse, summary="Lint a flow")
def post_lint(body: LintRequest) -> LintResponse:
    flow = _hydrate(body.flow)
    lints = lint_flow(flow)
    entries = [
        LintEntry(
            rule_id=l["rule_id"],
            severity=l["severity"],
            recipe_id=l.get("recipe_id"),
            message=l["message"],
            fix=l.get("fix"),
        )
        for l in lints
    ]
    return LintResponse(lints=entries)


@router.post(
    "/flows/lint/fix",
    response_model=dict[str, Any],
    summary="Apply a fixable lint rule to a flow",
)
def post_lint_fix(body: LintFixRequest) -> dict[str, Any]:
    flow = _hydrate(body.flow)
    if body.rule_id == "merge-adjacent-prepares":
        left = body.payload.get("left")
        right = body.payload.get("right")
        if not isinstance(left, str) or not isinstance(right, str):
            raise HTTPException(
                status_code=422,
                detail="merge-adjacent-prepares requires payload.left and payload.right",
            )
        return {"flow": apply_merge_adjacent_prepares(flow, left, right)}
    raise HTTPException(
        status_code=422, detail=f"Rule '{body.rule_id}' has no automatic fixer"
    )


# ---------------------------------------------------------------------------
# Schema drift
# ---------------------------------------------------------------------------


@router.post(
    "/flows/schema-drift",
    response_model=SchemaDriftResponse,
    summary="Compute schema drift between two flow snapshots",
)
def post_schema_drift(body: SchemaDriftRequest) -> SchemaDriftResponse:
    prior = _hydrate(body.prior)
    next_ = _hydrate(body.next)
    diff = diff_flows(prior, next_)
    return SchemaDriftResponse(
        summary=diff["summary"],
        headline=summarise(diff),
        datasets_added=diff["datasets_added"],
        datasets_removed=diff["datasets_removed"],
        per_dataset=diff["per_dataset"],
    )


# ---------------------------------------------------------------------------
# Test scaffolder
# ---------------------------------------------------------------------------


@router.post(
    "/flows/scaffold-test",
    summary="Generate an integration test from a flow",
    responses={
        200: {
            "description": "A pytest module as text/x-python",
            "content": {"text/x-python": {}},
        },
    },
)
def post_scaffold_test(body: ScaffoldTestRequest) -> Response:
    flow = _hydrate(body.flow)
    filename, src = scaffold_test(
        flow=flow,
        source=body.source,
        flow_name=body.flow_name,
        track_columns=body.track_columns or None,
    )
    return Response(
        content=src,
        media_type="text/x-python",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post(
    "/flows/{flow_id}/scaffold-test",
    summary="Generate an integration test from a saved flow",
    responses={
        200: {
            "description": "A pytest module as text/x-python",
            "content": {"text/x-python": {}},
        },
    },
)
def post_scaffold_test_for_saved(
    flow_id: str,
    body: ScaffoldTestRequest,
    flows: FlowsRepo = Depends(get_flows_repo),
) -> Response:
    record = flows.get(flow_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"flow '{flow_id}' not found")
    flow = _hydrate(record.flow)
    filename, src = scaffold_test(
        flow=flow,
        source=body.source,
        flow_name=body.flow_name or record.name,
        track_columns=body.track_columns or None,
    )
    return Response(
        content=src,
        media_type="text/x-python",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


__all__ = ["router"]
