"""End-to-end test that LLM-mode confidence + reasoning + source_lines flow
through to the /convert response.

Strategy:

* Stub ``app.services.conversion.convert_with_llm`` with a function that
  drives ``LLMCodeAnalyzer`` against a ``MockProvider`` returning a canned
  analysis JSON. The MockProvider keeps us off the real Anthropic /
  OpenAI APIs (constraint: never hit real APIs in tests) and lets us
  assert the precise per-recipe metadata the UI reads.
* The canned analysis exercises three confidence bands so the UI's
  shading bands are validated end-to-end:
    - high (>=0.85): a SYNC + GROUPING + SORT chain.
    - medium (0.60–0.84): a JOIN with judgement-call key inference.
    - low (<0.60): a Python-recipe fallback for a custom UDF.
"""

from __future__ import annotations

import json
import os

import pytest

from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator
from py2dataiku.llm.analyzer import LLMCodeAnalyzer
from py2dataiku.llm.providers import MockProvider


# --- canned LLM analysis ----------------------------------------------------

# This dict is the EXACT JSON the LLM is expected to emit for the test code
# below. Each step exercises a different confidence band so the response
# contract carries them through unchanged. The Studio UI bands are:
#   confidence >= 0.85  -> "high" (no shade)
#   0.60–0.84            -> "medium" (warn border + ⚠)
#   < 0.60              -> "low" (danger border + ⚠ + pulse)
#   confidence is None  -> rule-based ("R" badge)
CANNED_ANALYSIS_JSON: dict[str, object] = {
    "code_summary": "Read trades, join with counterparties, group + sort, custom UDF.",
    "total_operations": 5,
    "complexity_score": 5,
    "datasets": [
        {"name": "trades", "source": "trades.csv", "is_input": True, "is_output": False},
        {"name": "cp", "source": "cp.csv", "is_input": True, "is_output": False},
        {"name": "out", "source": "derived", "is_input": False, "is_output": True},
    ],
    "steps": [
        {
            "step_number": 1,
            "operation": "read_data",
            "description": "Read trades.csv",
            "output_dataset": "trades",
            "suggested_recipe": "sync",
            "source_lines": [1, 1],
            "confidence": 0.97,
            "reasoning": "pd.read_csv -> SYNC; trivial mapping.",
        },
        {
            "step_number": 2,
            "operation": "read_data",
            "description": "Read cp.csv",
            "output_dataset": "cp",
            "suggested_recipe": "sync",
            "source_lines": [2, 2],
            "confidence": 0.96,
            "reasoning": "pd.read_csv -> SYNC; trivial mapping.",
        },
        {
            "step_number": 3,
            "operation": "join",
            "description": "Left join trades with cp on cpid",
            "input_datasets": ["trades", "cp"],
            "output_dataset": "enriched",
            "join_conditions": [
                {"left_column": "cpid", "right_column": "cpid", "operator": "equals"}
            ],
            "join_type": "left",
            "suggested_recipe": "join",
            "source_lines": [3, 3],
            "confidence": 0.72,
            "reasoning": (
                "df.merge(..., on='cpid', how='left') -> JOIN with EXACT key; "
                "judgement call on the column rename inferred from context."
            ),
        },
        {
            "step_number": 4,
            "operation": "group_aggregate",
            "description": "Sum notional per region",
            "input_datasets": ["enriched"],
            "output_dataset": "out",
            "group_by_columns": ["region"],
            "aggregations": [
                {"column": "notional", "function": "SUM", "output_column": "notional_sum"}
            ],
            "suggested_recipe": "grouping",
            "source_lines": [4, 4],
            "confidence": 0.93,
            "reasoning": "groupby+sum -> GROUPING; canonical SUM aggregation.",
        },
        {
            "step_number": 5,
            "operation": "custom_function",
            "description": "Apply user-defined risk_metric(),  no visual recipe.",
            "input_datasets": ["out"],
            "output_dataset": "out",
            "suggested_recipe": "python",
            "requires_python_recipe": True,
            "source_lines": [5, 7],
            "confidence": 0.42,
            "reasoning": (
                "df.apply(my_risk_metric) — UDF with no visual equivalent; "
                "fell back to Python recipe."
            ),
        },
    ],
    "recommendations": [],
    "warnings": [],
}


# --- monkeypatch helper -----------------------------------------------------


def _stub_convert_with_llm(*, expected_recipe_count: int) -> "callable":
    """Build a stub that mirrors the real ``convert_with_llm`` signature but
    routes through a ``MockProvider``-backed ``LLMCodeAnalyzer``. Returns the
    callable suitable for ``monkeypatch.setattr``.
    """

    canned_text = json.dumps(CANNED_ANALYSIS_JSON)

    def _stub(
        code: str,
        provider: str = "anthropic",
        api_key: str | None = None,
        model: str | None = None,
        optimize: bool = True,
        flow_name: str = "converted_flow",
        on_progress=None,
        temperature: float = 0.0,
    ):
        # Match all prompts — MockProvider returns the canned response when
        # the prompt contains any key in `responses`. We use the empty
        # string so every prompt matches.
        mock_provider = MockProvider(responses={"": canned_text})
        analyzer = LLMCodeAnalyzer(provider=mock_provider)
        analysis = analyzer.analyze(code)
        gen = LLMFlowGenerator()
        flow = gen.generate(analysis, flow_name=flow_name, optimize=optimize)
        # Sanity check the canned analysis produced the expected recipe count.
        # Defensive: if optimize merges further it's fine, the test below
        # just inspects per-recipe metadata.
        assert len(flow.recipes) >= expected_recipe_count
        return flow

    return _stub


@pytest.mark.asyncio
async def test_convert_llm_confidence_round_trip(client, monkeypatch) -> None:
    """LLM-mode /convert response carries per-recipe confidence/reasoning/
    source_lines for the trader-engineer Studio UI to render.
    """
    # Provide a fake API key so the conversion service's env-var precondition
    # passes — the real provider is stubbed out below.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")

    # py-iku models sync-style READ_DATA steps as input datasets, not
    # recipes — so the canned 5-step analysis collapses to 3 recipes.
    stub = _stub_convert_with_llm(expected_recipe_count=3)
    monkeypatch.setattr("app.services.conversion.convert_with_llm", stub)

    code = (
        "import pandas as pd\n"
        "trades = pd.read_csv('trades.csv')\n"
        "cp = pd.read_csv('cp.csv')\n"
        "enriched = trades.merge(cp, on='cpid', how='left')\n"
        "out = enriched.groupby('region').agg({'notional': 'sum'})\n"
        "def my_risk_metric(row):\n"
        "    return row['notional'] * 0.05\n"
        "out['risk'] = out.apply(my_risk_metric, axis=1)\n"
    )

    response = await client.post(
        "/convert",
        json={"code": code, "mode": "llm"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    recipes = body["flow"]["recipes"]
    assert len(recipes) >= 3

    by_type = {r["type"]: r for r in recipes}

    # SYNC isn't generated as a recipe in py-iku (it's modelled by an INPUT
    # dataset, not a recipe), so the four expected recipe bands are:
    #   join   -> medium   (0.72)
    #   grouping -> high   (0.93)
    #   python   -> low    (0.42)
    # plus optionally a prepare for the trailing apply assignment.

    # --- join recipe (medium band) -----------------------------------------
    assert "join" in by_type, f"expected a join recipe, got {sorted(by_type)}"
    join_recipe = by_type["join"]
    assert join_recipe["confidence"] == pytest.approx(0.72)
    assert "judgement call" in (join_recipe.get("reasoning") or "")
    assert join_recipe["source_lines"] == [3]

    # --- grouping recipe (high band) ---------------------------------------
    assert "grouping" in by_type
    grouping_recipe = by_type["grouping"]
    assert grouping_recipe["confidence"] == pytest.approx(0.93)
    assert grouping_recipe["source_lines"] == [4]

    # --- python recipe (low band) ------------------------------------------
    assert "python" in by_type
    python_recipe = by_type["python"]
    assert python_recipe["confidence"] == pytest.approx(0.42)
    assert "Python recipe" in (python_recipe.get("reasoning") or "")
    # Source lines preserve the analyzer's [start, end] span exactly — the
    # backend never expands ranges (the UI does that when calling
    # Monaco.deltaDecorations).
    assert python_recipe["source_lines"] == [5, 7]


@pytest.mark.asyncio
async def test_convert_rule_mode_omits_confidence(client) -> None:
    """Rule-based /convert response MUST NOT include confidence on recipes
    (preserves byte-shape parity with the pre-confidence /convert contract).
    """
    code = (
        "import pandas as pd\n"
        "df = pd.read_csv('x.csv')\n"
        "g = df.groupby('k').agg({'v': 'sum'})\n"
    )
    response = await client.post(
        "/convert", json={"code": code, "mode": "rule"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for recipe in body["flow"]["recipes"]:
        # The Pydantic model defaults confidence/reasoning to None and the
        # API serializer is permitted to either omit None values or emit
        # them as null. Both are valid backward-compat behaviour; the UI
        # treats None / missing identically.
        assert recipe.get("confidence") is None
        assert recipe.get("reasoning") is None
