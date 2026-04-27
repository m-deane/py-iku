"""Inline comment routes for recipes within a flow.

Endpoints (single-user mode for v1; multi-user collab is Wave 5+):

* ``GET    /flows/{flow_id}/comments``                    — list all
* ``POST   /flows/{flow_id}/recipes/{recipe_id}/comments`` — append one
* ``DELETE /flows/{flow_id}/comments/{comment_id}``       — delete one
"""

from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..deps import get_settings
from ..services.comments_store import CommentsStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["comments"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreateCommentRequest(BaseModel):
    """Body for ``POST /flows/{flow_id}/recipes/{recipe_id}/comments``."""

    body: str = Field(min_length=1, max_length=4000)
    author: str | None = Field(default=None, max_length=120)


class CommentResponse(BaseModel):
    id: str
    flow_id: str
    recipe_id: str
    author: str
    body: str
    timestamp: str
    edited_at: str | None = None


class CommentListResponse(BaseModel):
    comments: list[CommentResponse]


# ---------------------------------------------------------------------------
# Store dependency
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _get_store_singleton() -> CommentsStore:
    settings = get_settings()
    return CommentsStore(base_dir=settings.flows_dir)


def reset_comments_store() -> None:
    """Test seam — drop the cached singleton so the next call rebinds."""
    _get_store_singleton.cache_clear()


def get_comments_store() -> CommentsStore:
    return _get_store_singleton()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/{flow_id}/comments",
    response_model=CommentListResponse,
    summary="List inline comments on a flow",
)
def list_comments(
    flow_id: str,
    store: CommentsStore = Depends(get_comments_store),
) -> CommentListResponse:
    items = store.list(flow_id)
    return CommentListResponse(
        comments=[
            CommentResponse(
                id=c.id,
                flow_id=c.flow_id,
                recipe_id=c.recipe_id,
                author=c.author,
                body=c.body,
                timestamp=c.timestamp,
                edited_at=c.edited_at,
            )
            for c in items
        ]
    )


@router.post(
    "/{flow_id}/recipes/{recipe_id}/comments",
    response_model=CommentResponse,
    status_code=201,
    summary="Append a comment to a recipe",
)
def post_comment(
    flow_id: str,
    recipe_id: str,
    body: CreateCommentRequest,
    store: CommentsStore = Depends(get_comments_store),
) -> CommentResponse:
    try:
        c = store.add(
            flow_id=flow_id,
            recipe_id=recipe_id,
            body=body.body,
            author=body.author,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CommentResponse(
        id=c.id,
        flow_id=c.flow_id,
        recipe_id=c.recipe_id,
        author=c.author,
        body=c.body,
        timestamp=c.timestamp,
        edited_at=c.edited_at,
    )


@router.delete(
    "/{flow_id}/comments/{comment_id}",
    status_code=204,
    summary="Delete a comment",
)
def delete_comment(
    flow_id: str,
    comment_id: str,
    store: CommentsStore = Depends(get_comments_store),
) -> None:
    if not store.delete(flow_id, comment_id):
        raise HTTPException(status_code=404, detail=f"comment {comment_id!r} not found")
    return None
