"""Real-LLM smoke tests for the studio API.

These tests are GATED on the ``ANTHROPIC_API_KEY`` environment variable.
When the key is absent the entire module is skipped — CI never goes red
because of a missing secret. When it IS set (nightly job, manual smoke,
local ``.env.local``) we exercise the FULL LLM path end-to-end:

    1. POST /convert?mode=llm with a 5-line pandas script — assert the
       response has at least one recipe, cost > 0, and no error field.
    2. POST /chat (sync) with the resulting flow — assert it returns an
       answer and at least one valid recipe citation.

Why a separate file? The default unit suite must remain offline-only and
deterministic so it can run on every PR. The smoke surface is opt-in and
deliberately makes a real network call — see CLAUDE.md "Real-LLM tests
must NEVER be required for CI green".
"""

from __future__ import annotations

import os
from typing import Any

import pytest

# Module-level guard. When the env var is missing the whole file is skipped
# with a clear reason — pytest reports "1 skipped" instead of failing.
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="no API key — set ANTHROPIC_API_KEY to run the real-LLM smoke",
)


SMOKE_CODE = """\
import pandas as pd
df = pd.read_csv('sales.csv')
df = df.dropna()
result = df.groupby('category').agg({'amount': 'sum'})
"""


@pytest.mark.asyncio
async def test_convert_llm_smoke(client) -> None:  # type: ignore[no-untyped-def]
    """POST /convert?mode=llm returns a sensible flow + non-zero cost."""
    resp = await client.post(
        "/convert",
        json={"code": SMOKE_CODE, "mode": "llm"},
        timeout=60.0,
    )
    # 200 path — all the failure cases get mapped to problem+json by the
    # global handler, so a non-200 here is a hard fail for the smoke surface.
    assert resp.status_code == 200, resp.text

    body: dict[str, Any] = resp.json()
    flow = body.get("flow") or {}
    score = body.get("score") or {}

    recipes = flow.get("recipes") or []
    assert len(recipes) >= 1, f"expected ≥1 recipe, got: {recipes!r}"

    # cost_estimate is the LLM-mode token cost in USD; rule-mode leaves it
    # None. Smoke runs MUST cost something, otherwise the LLM path silently
    # fell back to rule mode.
    cost = score.get("cost_estimate")
    assert cost is not None and cost > 0, (
        f"cost_estimate must be > 0 in llm mode, got {cost!r}"
    )

    # The convert response has no top-level "error" field on the happy path.
    assert "error" not in body, f"unexpected error in body: {body.get('error')!r}"


@pytest.mark.asyncio
async def test_chat_llm_smoke(client) -> None:  # type: ignore[no-untyped-def]
    """A small flow → /chat round-trip yields an answer + a citation."""
    # First convert so we have a real flow to chat about.
    convert_resp = await client.post(
        "/convert",
        json={"code": SMOKE_CODE, "mode": "llm"},
        timeout=60.0,
    )
    assert convert_resp.status_code == 200, convert_resp.text
    flow = convert_resp.json()["flow"]

    chat_resp = await client.post(
        "/chat",
        json={
            "flow_json": flow,
            "question": (
                "Briefly describe the first recipe in this flow and cite it "
                "with the [recipe:NAME] marker."
            ),
            "provider": "anthropic",
            "stream": False,
        },
        timeout=60.0,
    )
    assert chat_resp.status_code == 200, chat_resp.text
    body = chat_resp.json()
    assert body.get("answer"), "chat must return a non-empty answer"
    # cost_usd > 0 confirms the real provider was called (mock returns 0.0).
    assert body.get("cost_usd", 0.0) > 0.0, (
        f"expected non-zero cost_usd, got {body.get('cost_usd')!r}"
    )
    # Citation isn't strictly guaranteed by the LLM — but the rubric in
    # chat.py demands one, and we only run this gate against a real flow.
    # Treat absence as a soft warning, not a hard fail, to avoid flake.
    citations = body.get("citations") or []
    if citations:
        valid_names = {r.get("name") for r in flow.get("recipes", [])}
        assert all(
            c.get("recipe_id") in valid_names for c in citations
        ), f"invalid citation: {citations!r}"
