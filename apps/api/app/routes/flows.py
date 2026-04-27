"""POST /flows, GET /flows/{id}, PATCH /flows/{id}, POST /flows/{id}/share."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from py2dataiku.exceptions import Py2DataikuError
from py2dataiku.models.dataiku_flow import DataikuFlow

from ..deps import Settings, get_audit_repo, get_flows_repo, get_settings
from ..schemas.flows import (
    CreatedFlowResponse,
    SavedFlowResponse,
    SaveFlowRequest,
    ShareFlowRequest,
    ShareFlowResponse,
    UpdateFlowRequest,
)
from ..security.share_links import sign as sign_share_token
from ..store import AuditEvent, AuditRepo, FlowsRepo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["flows"])


def _client_actor(request: Request) -> str:
    """Best-effort actor identity for audit purposes."""
    return request.headers.get("X-Actor") or (
        request.client.host if request.client else "anonymous"
    )


def _build_share_url(request: Request, token: str) -> str:
    """Construct an absolute /share/{token} URL from the inbound request."""
    base = str(request.base_url).rstrip("/")
    return f"{base}/share/{token}"


def _hydrate(flow_dict: dict) -> dict:
    """Round-trip *flow_dict* through ``DataikuFlow.from_dict`` to validate.

    Raises ``HTTPException(422)`` on a malformed flow body.
    """
    try:
        flow = DataikuFlow.from_dict(flow_dict)
    except (Py2DataikuError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail=f"Malformed flow body: {exc}"
        ) from exc
    return flow.to_dict()


@router.post(
    "",
    response_model=CreatedFlowResponse,
    status_code=201,
    summary="Persist a flow",
)
def post_flow(
    body: SaveFlowRequest,
    request: Request,
    flows: FlowsRepo = Depends(get_flows_repo),
    audit: AuditRepo = Depends(get_audit_repo),
) -> CreatedFlowResponse:
    flow_dict = body.flow.model_dump(by_alias=True)
    _hydrate(flow_dict)  # validate, but persist the raw dict
    record = flows.save(flow=flow_dict, name=body.name, tags=list(body.tags or []))
    audit.append(
        AuditEvent(
            actor=_client_actor(request),
            action="flow.create",
            resource_type="flow",
            resource_id=record.id,
            details={"name": record.name, "tags": list(record.tags)},
        )
    )
    return CreatedFlowResponse(id=record.id, created_at=record.created_at)


@router.get("/{flow_id}", response_model=SavedFlowResponse, summary="Read a saved flow")
def get_flow(
    flow_id: str,
    flows: FlowsRepo = Depends(get_flows_repo),
) -> SavedFlowResponse:
    record = flows.get(flow_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"flow '{flow_id}' not found")
    # Round-trip through DataikuFlow to keep parity with /convert responses.
    hydrated = _hydrate(record.flow)
    return SavedFlowResponse(
        id=record.id,
        name=record.name,
        flow=hydrated,  # type: ignore[arg-type]
        created_at=record.created_at,
        updated_at=record.updated_at,
        tags=list(record.tags),
    )


@router.patch(
    "/{flow_id}", response_model=SavedFlowResponse, summary="Patch a saved flow"
)
def patch_flow(
    flow_id: str,
    body: UpdateFlowRequest,
    request: Request,
    flows: FlowsRepo = Depends(get_flows_repo),
    audit: AuditRepo = Depends(get_audit_repo),
) -> SavedFlowResponse:
    if body.flow is None and body.name is None and body.tags is None:
        raise HTTPException(
            status_code=422, detail="At least one of flow, name, tags must be set"
        )
    new_flow_dict: dict | None = None
    if body.flow is not None:
        candidate = body.flow.model_dump(by_alias=True)
        new_flow_dict = _hydrate(candidate)
    try:
        record = flows.update(
            flow_id,
            flow=new_flow_dict,
            name=body.name,
            tags=body.tags,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"flow '{flow_id}' not found"
        ) from exc
    audit.append(
        AuditEvent(
            actor=_client_actor(request),
            action="flow.update",
            resource_type="flow",
            resource_id=record.id,
            details={
                "name": record.name,
                "tags": list(record.tags),
                "fields": [
                    k
                    for k, v in {
                        "flow": body.flow,
                        "name": body.name,
                        "tags": body.tags,
                    }.items()
                    if v is not None
                ],
            },
        )
    )
    return SavedFlowResponse(
        id=record.id,
        name=record.name,
        flow=record.flow,  # type: ignore[arg-type]
        created_at=record.created_at,
        updated_at=record.updated_at,
        tags=list(record.tags),
    )


@router.post(
    "/{flow_id}/share",
    response_model=ShareFlowResponse,
    summary="Mint a signed share token for a flow",
)
def post_share(
    flow_id: str,
    body: ShareFlowRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    flows: FlowsRepo = Depends(get_flows_repo),
    audit: AuditRepo = Depends(get_audit_repo),
) -> ShareFlowResponse:
    record = flows.get(flow_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"flow '{flow_id}' not found")
    ttl = body.ttl_seconds or settings.share_default_ttl_seconds
    scopes = list(body.scopes or ["read"])
    token = sign_share_token(
        flow_id, ttl_seconds=ttl, scopes=scopes, secret=settings.secret_key
    )
    expires_at = datetime.fromtimestamp(
        datetime.now(tz=UTC).timestamp() + ttl, tz=UTC
    ).isoformat()

    # Sprint 4D follow-up: inline fixtures in the share record so the
    # recipient can Run-with-embedded-fixtures without a side-channel bundle
    # download. The payload is compressed (gzip+base64) before being persisted.
    if body.include_fixtures:
        from ..services.share_service import (
            build_share_bundle,
            encode_bundle_gzip_b64,
        )

        bundle = build_share_bundle(record.flow, n_rows=body.fixtures_n_rows)
        encoded = encode_bundle_gzip_b64(bundle)
        flows.update(flow_id, fixtures_b64=encoded)

    audit.append(
        AuditEvent(
            actor=_client_actor(request),
            action="flow.share",
            resource_type="flow",
            resource_id=flow_id,
            details={
                "ttl_seconds": ttl,
                "scopes": scopes,
                "include_fixtures": body.include_fixtures,
            },
        )
    )
    return ShareFlowResponse(
        token=token,
        url=_build_share_url(request, token),
        expires_at=expires_at,
    )
