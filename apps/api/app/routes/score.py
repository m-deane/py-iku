"""POST /score — compute a complexity score for a DataikuFlow."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from py2dataiku.models.dataiku_flow import DataikuFlow

from ..schemas.convert import ComplexityScore
from ..schemas.flow import DataikuFlowModel
from ..services.score import score_flow

router = APIRouter(tags=["score"])

logger = logging.getLogger(__name__)


class ScoreRequest(DataikuFlowModel):
    """Request body for POST /score — a DataikuFlowModel directly."""

    pass


@router.post(
    "/score",
    response_model=ComplexityScore,
    summary="Compute a complexity score for a flow",
)
async def post_score(body: DataikuFlowModel) -> ComplexityScore:
    """Compute the complexity score from a flow payload.

    The flow is hydrated into a real ``DataikuFlow`` via ``from_dict`` so
    the FlowGraph metrics computed by ``score_flow`` are accurate.
    """
    flow_dict = body.model_dump(by_alias=True)
    flow = DataikuFlow.from_dict(flow_dict)
    return score_flow(flow)
