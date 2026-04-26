"""POST /diff — compute a per-node diff between two DataikuFlow dicts."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from ..schemas.diff import DiffRequest, DiffResponse, NodeDiff

router = APIRouter(tags=["diff"])

logger = logging.getLogger(__name__)


def _recipe_signature(recipe: Any) -> dict[str, Any]:
    """Extract the comparable subset of a recipe (Pydantic model)."""
    payload = recipe.model_dump(by_alias=False, exclude_none=False)
    # Drop fields whose order/identity is irrelevant for the comparison.
    payload.pop("source_lines", None)
    payload.pop("notes", None)
    return payload


def _diff_recipes(a_rec: Any, b_rec: Any) -> dict[str, Any] | None:
    """Return field-level differences between two recipes, or None if equal."""
    sig_a = _recipe_signature(a_rec)
    sig_b = _recipe_signature(b_rec)
    if sig_a == sig_b:
        return None
    diff: dict[str, Any] = {}
    keys = set(sig_a.keys()) | set(sig_b.keys())
    for key in keys:
        if sig_a.get(key) != sig_b.get(key):
            diff[key] = {"a": sig_a.get(key), "b": sig_b.get(key)}
    return diff


@router.post(
    "/diff",
    response_model=DiffResponse,
    summary="Compute the per-node diff between two flows",
)
async def post_diff(body: DiffRequest) -> DiffResponse:
    """Compare two flows by recipe name (the node id) and return added/removed/changed.

    - **added**: recipe present in B but not in A.
    - **removed**: recipe present in A but not in B.
    - **changed**: recipe present in both with a different ``type`` or
      different settings/steps.
    """
    a_recipes = {r.name: r for r in body.a.recipes}
    b_recipes = {r.name: r for r in body.b.recipes}

    a_names = set(a_recipes)
    b_names = set(b_recipes)

    added_ids = sorted(b_names - a_names)
    removed_ids = sorted(a_names - b_names)
    common_ids = sorted(a_names & b_names)

    added = [
        NodeDiff(
            id=nid,
            recipe_type_a=None,
            recipe_type_b=b_recipes[nid].type.value,
            diff=None,
        )
        for nid in added_ids
    ]
    removed = [
        NodeDiff(
            id=nid,
            recipe_type_a=a_recipes[nid].type.value,
            recipe_type_b=None,
            diff=None,
        )
        for nid in removed_ids
    ]

    changed: list[NodeDiff] = []
    for nid in common_ids:
        a_rec = a_recipes[nid]
        b_rec = b_recipes[nid]
        field_diff = _diff_recipes(a_rec, b_rec)
        if field_diff is not None:
            changed.append(
                NodeDiff(
                    id=nid,
                    recipe_type_a=a_rec.type.value,
                    recipe_type_b=b_rec.type.value,
                    diff=field_diff,
                )
            )

    return DiffResponse(added=added, removed=removed, changed=changed)
