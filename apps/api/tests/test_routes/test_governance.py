"""Tests for the Sprint-4 governance routes (lineage, lint, drift, scaffolder)."""

from __future__ import annotations

import pytest

# A V5-style SPLIT example — long PREPARE chain ending in a complementary
# split that produces both branches (the canonical front-office trade-tape
# pattern: rename → derive notional → split into in/out-of-policy).
V5_SPLIT_SOURCE = """
import pandas as pd

df = pd.read_csv('trades.csv')
df = df.rename(columns={'price': 'px'})
df['notional'] = df['px'] * df['qty']
big = df[df.notional > 1000]
small = df[~(df.notional > 1000)]
big.to_csv('big.csv')
small.to_csv('small.csv')
"""


@pytest.fixture()
def v5_flow() -> dict:
    """Build the V5-SPLIT flow once via the real py2dataiku.convert."""
    from py2dataiku import convert

    return convert(V5_SPLIT_SOURCE).to_dict()


# ---------------------------------------------------------------------------
# Lineage — round-trip on the V5 SPLIT example
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lineage_inline_post_resolves_rename_chain(client, v5_flow) -> None:  # noqa: D401
    response = await client.post(
        "/flows/lineage", json={"flow": v5_flow, "column": "px"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # The user clicked "px" (the renamed name); we should still see "price"
    # in the resolved alias set.
    assert "price" in body["aliases"]
    assert "px" in body["aliases"]
    # The PREPARE recipe (rename + derive notional) and the SPLIT both
    # operate on this column.
    assert any(r.startswith("prepare") for r in body["recipes"])
    assert any(r.startswith("split") for r in body["recipes"])
    # At least one edge per touched recipe.
    assert len(body["edges"]) >= 2


@pytest.mark.asyncio
async def test_lineage_for_saved_flow(client, v5_flow) -> None:
    saved = await client.post(
        "/flows", json={"flow": v5_flow, "name": "v5-split", "tags": []}
    )
    flow_id = saved.json()["id"]
    response = await client.get(f"/flows/{flow_id}/lineage/px")
    assert response.status_code == 200, response.text
    body = response.json()
    # `px` is the renamed `price`; the PREPARE that renames it should appear.
    assert any("prepare" in r for r in body["recipes"])
    # The rename chain should resolve "price" as an alias.
    assert "price" in body["aliases"]
    # available_columns covers the catalog the inspector renders.
    assert "px" in body["available_columns"]


@pytest.mark.asyncio
async def test_lineage_unknown_column_is_safe(client, v5_flow) -> None:
    """An unknown column returns an empty result, not a crash."""
    response = await client.post(
        "/flows/lineage", json={"flow": v5_flow, "column": "this_column_doesnt_exist"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["aliases"] == ["this_column_doesnt_exist"]
    # Edges are produced because the linter still walks the graph; that's fine.
    # The important contract is that the call completes without error.
    assert isinstance(body["edges"], list)


# ---------------------------------------------------------------------------
# Lint — V5 example shape + happy-path rule firings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lint_v5_split_is_clean(client, v5_flow) -> None:
    response = await client.post("/flows/lint", json={"flow": v5_flow})
    assert response.status_code == 200, response.text
    body = response.json()
    # The V5 SPLIT example is well-formed: SPLIT has 2 outputs, PREPARE
    # is the only one in the chain, no GROUPING / WINDOW. So lints == [].
    assert body["lints"] == []
    # But the catalog is always returned for the UI to render the rule list.
    assert any(
        r["rule_id"] == "split-single-output" for r in body["rule_catalog"]
    )


@pytest.mark.asyncio
async def test_lint_split_single_output_blocker(client) -> None:
    bad_flow = {
        "flow_name": "bad",
        "total_recipes": 1,
        "total_datasets": 2,
        "datasets": [
            {"name": "a", "type": "input", "connection_type": "Filesystem", "schema": []},
            {"name": "b", "type": "output", "connection_type": "Filesystem", "schema": []},
        ],
        "recipes": [
            {
                "name": "split_solo",
                "type": "split",
                "inputs": ["a"],
                "outputs": ["b"],
            },
        ],
    }
    response = await client.post("/flows/lint", json={"flow": bad_flow})
    assert response.status_code == 200, response.text
    lints = response.json()["lints"]
    assert any(
        l["rule_id"] == "split-single-output" and l["severity"] == "blocker"
        for l in lints
    )


# ---------------------------------------------------------------------------
# Schema drift — synthetic before/after
# ---------------------------------------------------------------------------


def _flow_with_schema(cols: list[tuple[str, str]]) -> dict:
    return {
        "flow_name": "x",
        "total_recipes": 0,
        "total_datasets": 1,
        "datasets": [
            {
                "name": "trades",
                "type": "input",
                "connection_type": "Filesystem",
                "schema": [{"name": n, "type": t} for n, t in cols],
            }
        ],
        "recipes": [],
    }


@pytest.mark.asyncio
async def test_schema_drift_detects_added_removed_renamed_typed(client) -> None:
    prior = _flow_with_schema(
        [("price", "double"), ("qty", "int"), ("ccy", "string"), ("legacy_id", "int")]
    )
    next_ = _flow_with_schema(
        [
            # legacy_id removed (no add of same type → real removal)
            ("px", "double"),  # rename of price (only one double on each side)
            ("qty", "string"),  # type-changed
            ("ccy", "string"),  # unchanged
            ("trade_book", "string"),  # net-new, no type partner → real add
        ]
    )
    response = await client.post(
        "/flows/schema-drift", json={"prior": prior, "next": next_}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    s = body["summary"]
    assert s["columns_renamed"] == 1
    assert s["columns_type_changed"] == 1
    # legacy_id removed and trade_book added (separate types, no rename match).
    assert s["columns_added"] == 1
    assert s["columns_removed"] == 1
    assert s["has_drift"] is True
    assert "since last run" in body["headline"]


@pytest.mark.asyncio
async def test_schema_drift_no_changes(client) -> None:
    schema = _flow_with_schema([("a", "int"), ("b", "string")])
    response = await client.post(
        "/flows/schema-drift", json={"prior": schema, "next": schema}
    )
    assert response.status_code == 200, response.text
    assert response.json()["summary"]["has_drift"] is False


# ---------------------------------------------------------------------------
# Test scaffolder — generate a test from V5, run it via subprocess
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scaffold_test_returns_python(client, v5_flow) -> None:
    response = await client.post(
        "/flows/scaffold-test",
        json={
            "flow": v5_flow,
            "source": V5_SPLIT_SOURCE,
            "flow_name": "v5_split",
            "track_columns": ["px", "notional"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/x-python")
    cd = response.headers["content-disposition"]
    assert "test_v5_split_integration.py" in cd
    # Body has the structural assertions and the column-lineage block.
    body = response.text
    assert "from py2dataiku import convert" in body
    assert "EXPECTED_RECIPE_TYPES" in body
    assert "EXPECTED_LINEAGE_COLUMNS" in body


def test_scaffolder_subprocess_round_trip(tmp_path) -> None:
    """Generate a test from V5, run pytest in-process via subprocess."""
    import subprocess
    import sys

    from app.services.test_scaffolder import scaffold_test
    from py2dataiku import convert

    flow = convert(V5_SPLIT_SOURCE).to_dict()
    filename, src = scaffold_test(
        flow=flow,
        source=V5_SPLIT_SOURCE,
        flow_name="v5_split",
        # `px` is the rename target — the only column the rule-based path
        # materialises in a step's params for this V5 example.
        track_columns=["px"],
    )
    test_path = tmp_path / filename
    test_path.write_text(src)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-xvs", str(test_path)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        "Generated test failed:\n"
        + result.stdout
        + "\n---STDERR---\n"
        + result.stderr
    )
