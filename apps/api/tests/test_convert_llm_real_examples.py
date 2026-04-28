"""Regression matrix for /convert?mode=llm against four representative scripts.

Strategy
--------
We don't talk to the real Anthropic / OpenAI API in tests (constraint). We
stub ``app.services.conversion.convert_with_llm`` with a function that runs
through ``LLMCodeAnalyzer`` + ``MockProvider`` returning a canned analysis
JSON sized to the input script. That exercises:

* the end-to-end /convert HTTP contract (key resolved, request validated,
  flow + score serialised),
* the conversion service's key-resolution ladder (file → env-var),
* every router-level audit + cost-meter side-effect — the same code path
  the real LLM takes.

Each script is a real-world py-iku Studio textbook example (V1 retail,
trade-ingestion, book-mtm-eod, forward-curve-scd) — chosen because they
exercise different recipe shapes (GROUPING / JOIN / WINDOW / PYTHON).

Two axes — {file-key, env-key, no-key} × 4 scripts.
"""

from __future__ import annotations

import json

import pytest

from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator
from py2dataiku.llm.analyzer import LLMCodeAnalyzer
from py2dataiku.llm.providers import MockProvider


# ---------------------------------------------------------------------------
# Scripts (deliberately small — they're shape fixtures, not real workloads).
# ---------------------------------------------------------------------------

V1_RETAIL = (
    "import pandas as pd\n"
    "df = pd.read_csv('transactions.csv')\n"
    "summary = df.groupby('category').agg({'amount': 'sum'}).reset_index()\n"
    "summary.to_csv('summary.csv', index=False)\n"
)

EXAMPLES_01_TRADE_INGESTION = (
    "import pandas as pd\n"
    "trades = pd.read_csv('trades.csv')\n"
    "cp = pd.read_csv('counterparties.csv')\n"
    "enriched = trades.merge(cp, on='cp_id', how='left')\n"
    "enriched.to_csv('enriched_trades.csv', index=False)\n"
)

EXAMPLES_02_BOOK_MTM_EOD = (
    "import pandas as pd\n"
    "positions = pd.read_csv('positions.csv')\n"
    "marks = pd.read_csv('marks.csv')\n"
    "joined = positions.merge(marks, on='instrument_id', how='inner')\n"
    "joined['mtm'] = joined['quantity'] * joined['price']\n"
    "book = joined.groupby('book').agg({'mtm': 'sum'}).reset_index()\n"
    "book.to_csv('book_mtm.csv', index=False)\n"
)

EXAMPLES_03_FORWARD_CURVE_SCD = (
    "import pandas as pd\n"
    "curves = pd.read_csv('curves.csv')\n"
    "curves = curves.sort_values(['curve_id', 'effective_date'])\n"
    "curves['rolling_avg'] = curves.groupby('curve_id')['value'].rolling(5).mean().reset_index(drop=True)\n"
    "curves.to_csv('curves_scd.csv', index=False)\n"
)


# ---------------------------------------------------------------------------
# Canned analyses — each one shaped to the script above.
# ---------------------------------------------------------------------------


def _canned_for(script_id: str) -> dict[str, object]:
    if script_id == "v1_retail":
        return {
            "code_summary": "Read transactions, group by category, sum.",
            "total_operations": 2,
            "complexity_score": 2,
            "datasets": [
                {"name": "transactions", "source": "transactions.csv", "is_input": True, "is_output": False},
                {"name": "summary", "source": "derived", "is_input": False, "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1, "operation": "read_data", "description": "Read transactions.csv",
                    "output_dataset": "transactions", "suggested_recipe": "sync",
                    "source_lines": [2, 2], "confidence": 0.98,
                    "reasoning": "pd.read_csv -> SYNC.",
                },
                {
                    "step_number": 2, "operation": "group_aggregate",
                    "description": "Sum amount per category",
                    "input_datasets": ["transactions"], "output_dataset": "summary",
                    "group_by_columns": ["category"],
                    "aggregations": [{"column": "amount", "function": "SUM", "output_column": "amount_sum"}],
                    "suggested_recipe": "grouping",
                    "source_lines": [3, 3], "confidence": 0.95,
                    "reasoning": "groupby + sum -> GROUPING.",
                },
            ],
            "recommendations": [], "warnings": [],
        }
    if script_id == "trade_ingestion":
        return {
            "code_summary": "Trade ingestion: read trades, enrich with counterparties.",
            "total_operations": 2, "complexity_score": 3,
            "datasets": [
                {"name": "trades", "source": "trades.csv", "is_input": True, "is_output": False},
                {"name": "cp", "source": "counterparties.csv", "is_input": True, "is_output": False},
                {"name": "enriched", "source": "derived", "is_input": False, "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1, "operation": "read_data", "description": "Read trades",
                    "output_dataset": "trades", "suggested_recipe": "sync",
                    "source_lines": [2, 2], "confidence": 0.97,
                    "reasoning": "pd.read_csv -> SYNC.",
                },
                {
                    "step_number": 2, "operation": "read_data", "description": "Read counterparties",
                    "output_dataset": "cp", "suggested_recipe": "sync",
                    "source_lines": [3, 3], "confidence": 0.97,
                    "reasoning": "pd.read_csv -> SYNC.",
                },
                {
                    "step_number": 3, "operation": "join", "description": "Left join trades + counterparties",
                    "input_datasets": ["trades", "cp"], "output_dataset": "enriched",
                    "join_conditions": [{"left_column": "cp_id", "right_column": "cp_id", "operator": "equals"}],
                    "join_type": "left", "suggested_recipe": "join",
                    "source_lines": [4, 4], "confidence": 0.88,
                    "reasoning": "merge on cp_id, how=left -> JOIN.",
                },
            ],
            "recommendations": [], "warnings": [],
        }
    if script_id == "book_mtm":
        return {
            "code_summary": "Book MTM EOD: join positions+marks, compute MTM, sum per book.",
            "total_operations": 3, "complexity_score": 4,
            "datasets": [
                {"name": "positions", "source": "positions.csv", "is_input": True, "is_output": False},
                {"name": "marks", "source": "marks.csv", "is_input": True, "is_output": False},
                {"name": "book", "source": "derived", "is_input": False, "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1, "operation": "read_data", "description": "Read positions",
                    "output_dataset": "positions", "suggested_recipe": "sync",
                    "source_lines": [2, 2], "confidence": 0.97, "reasoning": "pd.read_csv -> SYNC.",
                },
                {
                    "step_number": 2, "operation": "read_data", "description": "Read marks",
                    "output_dataset": "marks", "suggested_recipe": "sync",
                    "source_lines": [3, 3], "confidence": 0.97, "reasoning": "pd.read_csv -> SYNC.",
                },
                {
                    "step_number": 3, "operation": "join", "description": "Inner join positions+marks",
                    "input_datasets": ["positions", "marks"], "output_dataset": "joined",
                    "join_conditions": [{"left_column": "instrument_id", "right_column": "instrument_id", "operator": "equals"}],
                    "join_type": "inner", "suggested_recipe": "join",
                    "source_lines": [4, 4], "confidence": 0.92, "reasoning": "merge inner -> JOIN.",
                },
                {
                    "step_number": 4, "operation": "group_aggregate",
                    "description": "Sum MTM per book",
                    "input_datasets": ["joined"], "output_dataset": "book",
                    "group_by_columns": ["book"],
                    "aggregations": [{"column": "mtm", "function": "SUM", "output_column": "mtm_sum"}],
                    "suggested_recipe": "grouping",
                    "source_lines": [6, 6], "confidence": 0.93,
                    "reasoning": "groupby+sum -> GROUPING.",
                },
            ],
            "recommendations": [], "warnings": [],
        }
    if script_id == "forward_curve":
        return {
            "code_summary": "Forward curve SCD: sort + rolling 5d mean per curve.",
            "total_operations": 3, "complexity_score": 4,
            "datasets": [
                {"name": "curves", "source": "curves.csv", "is_input": True, "is_output": False},
                {"name": "curves_scd", "source": "derived", "is_input": False, "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1, "operation": "read_data", "description": "Read curves",
                    "output_dataset": "curves", "suggested_recipe": "sync",
                    "source_lines": [2, 2], "confidence": 0.97, "reasoning": "pd.read_csv -> SYNC.",
                },
                {
                    "step_number": 2, "operation": "sort", "description": "Sort by curve_id, effective_date",
                    "input_datasets": ["curves"], "output_dataset": "curves",
                    "sort_columns": [
                        {"column": "curve_id", "ascending": True},
                        {"column": "effective_date", "ascending": True},
                    ],
                    "suggested_recipe": "sort",
                    "source_lines": [3, 3], "confidence": 0.94, "reasoning": "sort_values -> SORT.",
                },
                {
                    "step_number": 3, "operation": "window", "description": "Rolling 5-period mean per curve",
                    "input_datasets": ["curves"], "output_dataset": "curves",
                    "window_partition_by": ["curve_id"],
                    "window_aggregations": [{"column": "value", "function": "AVG", "window": 5}],
                    "suggested_recipe": "window",
                    "source_lines": [4, 4], "confidence": 0.86,
                    "reasoning": "rolling(5).mean() -> WINDOW.",
                },
            ],
            "recommendations": [], "warnings": [],
        }
    raise ValueError(script_id)


def _stub_convert_with_llm(canned: dict[str, object]):  # type: ignore[no-untyped-def]
    """Build a stub mirroring ``convert_with_llm`` that uses MockProvider."""
    canned_text = json.dumps(canned)

    def _stub(
        code: str,
        provider: str = "anthropic",
        api_key: str | None = None,
        model: str | None = None,
        optimize: bool = True,
        flow_name: str = "converted_flow",
        on_progress=None,  # noqa: ARG001  unused
        temperature: float = 0.0,
    ):
        # MockProvider matches any prompt because the empty string is a substring.
        mock_provider = MockProvider(responses={"": canned_text})
        analyzer = LLMCodeAnalyzer(provider=mock_provider)
        analysis = analyzer.analyze(code)
        gen = LLMFlowGenerator()
        return gen.generate(analysis, flow_name=flow_name, optimize=optimize)

    return _stub


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


SCRIPTS = [
    ("v1_retail", V1_RETAIL),
    ("trade_ingestion", EXAMPLES_01_TRADE_INGESTION),
    ("book_mtm", EXAMPLES_02_BOOK_MTM_EOD),
    ("forward_curve", EXAMPLES_03_FORWARD_CURVE_SCD),
]


@pytest.mark.parametrize("script_id,code", SCRIPTS, ids=[s[0] for s in SCRIPTS])
@pytest.mark.asyncio
async def test_llm_convert_with_env_key(  # type: ignore[no-untyped-def]
    client, monkeypatch, script_id, code,
) -> None:
    """LLM mode + env-var key + canned analysis returns 200 + a flow."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-env")
    monkeypatch.setattr(
        "app.services.conversion.convert_with_llm",
        _stub_convert_with_llm(_canned_for(script_id)),
    )

    resp = await client.post("/convert", json={"code": code, "mode": "llm"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "flow" in body
    assert "score" in body
    assert body["score"]["recipe_count"] >= 1
    assert isinstance(body["flow"]["recipes"], list)


@pytest.mark.parametrize("script_id,code", SCRIPTS, ids=[s[0] for s in SCRIPTS])
@pytest.mark.asyncio
async def test_llm_convert_with_file_key_overrides_env(  # type: ignore[no-untyped-def]
    client, monkeypatch, script_id, code,
) -> None:
    """File-stored key wins over env-var; conversion still succeeds."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env-should-be-ignored")
    monkeypatch.setattr(
        "app.services.conversion.convert_with_llm",
        _stub_convert_with_llm(_canned_for(script_id)),
    )

    save = await client.post(
        "/api/settings/llm/key",
        json={"provider": "anthropic", "key": "sk-ant-on-disk-wins"},
    )
    assert save.status_code == 200
    assert save.json()["source"] == "file"

    resp = await client.post("/convert", json={"code": code, "mode": "llm"})
    assert resp.status_code == 200, resp.text


@pytest.mark.parametrize("script_id,code", SCRIPTS, ids=[s[0] for s in SCRIPTS])
@pytest.mark.asyncio
async def test_llm_convert_without_key_returns_500(  # type: ignore[no-untyped-def]
    client, monkeypatch, script_id, code,
) -> None:
    """Without any key, /convert returns 500 / ConfigurationError. The error
    message points the user at Settings → LLM Provider."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    resp = await client.post("/convert", json={"code": code, "mode": "llm"})
    assert resp.status_code == 500
    body = resp.json()
    assert "ConfigurationError" in body.get("type", "")
    detail = body.get("detail", "")
    assert "Settings" in detail or "ANTHROPIC_API_KEY" in detail
