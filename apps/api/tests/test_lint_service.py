"""Unit tests for lint rules — pure functions, no I/O, no fixtures from app."""

from __future__ import annotations

from app.services.lint_service import (
    apply_merge_adjacent_prepares,
    lint_flow,
    rule_adjacent_prepares,
    rule_filter_before_groupby,
    rule_grouping_no_aggs,
    rule_split_single_output,
    rule_window_empty_partitions,
)


def _flow(*, recipes: list[dict], datasets: list[dict] | None = None) -> dict:
    datasets = datasets or [
        {"name": n, "type": "intermediate", "connection_type": "Filesystem", "schema": []}
        for r in recipes
        for n in (r.get("inputs") or []) + (r.get("outputs") or [])
    ]
    return {
        "flow_name": "x",
        "total_recipes": len(recipes),
        "total_datasets": len(datasets),
        "datasets": datasets,
        "recipes": recipes,
    }


# ---------------------------------------------------------------------------
# rule_split_single_output
# ---------------------------------------------------------------------------


def test_rule_split_single_output_fires() -> None:
    flow = _flow(recipes=[{"name": "split_x", "type": "split", "inputs": ["a"], "outputs": ["b"]}])
    out = rule_split_single_output(flow)
    assert len(out) == 1
    assert out[0]["severity"] == "blocker"


def test_rule_split_single_output_silent_when_two() -> None:
    flow = _flow(
        recipes=[{"name": "split_x", "type": "split", "inputs": ["a"], "outputs": ["b", "c"]}]
    )
    assert rule_split_single_output(flow) == []


# ---------------------------------------------------------------------------
# rule_grouping_no_aggs
# ---------------------------------------------------------------------------


def test_rule_grouping_no_aggs_fires_when_aggs_empty() -> None:
    flow = _flow(
        recipes=[
            {
                "name": "g1",
                "type": "grouping",
                "inputs": ["a"],
                "outputs": ["b"],
                "aggregations": [],
            }
        ]
    )
    out = rule_grouping_no_aggs(flow)
    assert len(out) == 1


def test_rule_grouping_no_aggs_silent_when_present() -> None:
    flow = _flow(
        recipes=[
            {
                "name": "g1",
                "type": "grouping",
                "inputs": ["a"],
                "outputs": ["b"],
                "aggregations": [{"column": "x", "function": "sum"}],
            }
        ]
    )
    assert rule_grouping_no_aggs(flow) == []


# ---------------------------------------------------------------------------
# rule_window_empty_partitions
# ---------------------------------------------------------------------------


def test_rule_window_empty_partitions_fires() -> None:
    flow = _flow(
        recipes=[
            {
                "name": "w1",
                "type": "window",
                "inputs": ["a"],
                "outputs": ["b"],
                "partition_columns": [],
            }
        ]
    )
    out = rule_window_empty_partitions(flow)
    assert len(out) == 1


def test_rule_window_empty_partitions_silent_when_set() -> None:
    flow = _flow(
        recipes=[
            {
                "name": "w1",
                "type": "window",
                "inputs": ["a"],
                "outputs": ["b"],
                "partition_columns": ["book"],
            }
        ]
    )
    assert rule_window_empty_partitions(flow) == []


# ---------------------------------------------------------------------------
# rule_filter_before_groupby
# ---------------------------------------------------------------------------


def test_rule_filter_before_groupby_detects_filter_after_groupby() -> None:
    flow = _flow(
        recipes=[
            {"name": "g1", "type": "grouping", "inputs": ["a"], "outputs": ["b"]},
            {
                "name": "p1",
                "type": "prepare",
                "inputs": ["b"],
                "outputs": ["c"],
                "steps": [{"type": "FilterOnValue", "params": {}}],
            },
        ]
    )
    out = rule_filter_before_groupby(flow)
    assert len(out) == 1
    assert out[0]["recipe_id"] == "g1"


def test_rule_filter_before_groupby_silent_when_no_filter_downstream() -> None:
    flow = _flow(
        recipes=[
            {"name": "g1", "type": "grouping", "inputs": ["a"], "outputs": ["b"]},
            {
                "name": "p1",
                "type": "prepare",
                "inputs": ["b"],
                "outputs": ["c"],
                "steps": [{"type": "ColumnRenamer", "params": {"renamings": []}}],
            },
        ]
    )
    assert rule_filter_before_groupby(flow) == []


# ---------------------------------------------------------------------------
# rule_adjacent_prepares — also test the fix
# ---------------------------------------------------------------------------


def test_rule_adjacent_prepares_fires_for_chained_prepares() -> None:
    flow = _flow(
        recipes=[
            {
                "name": "p1",
                "type": "prepare",
                "inputs": ["a"],
                "outputs": ["mid"],
                "steps": [{"type": "ColumnRenamer", "params": {"renamings": []}}],
            },
            {
                "name": "p2",
                "type": "prepare",
                "inputs": ["mid"],
                "outputs": ["c"],
                "steps": [{"type": "ColumnRenamer", "params": {"renamings": []}}],
            },
        ]
    )
    out = rule_adjacent_prepares(flow)
    assert len(out) == 1
    assert out[0]["fix"]["kind"] == "merge_adjacent_prepares"


def test_apply_merge_adjacent_prepares_concatenates_steps() -> None:
    flow = _flow(
        recipes=[
            {
                "name": "p1",
                "type": "prepare",
                "inputs": ["a"],
                "outputs": ["mid"],
                "steps": [{"type": "ColumnRenamer", "params": {}}],
            },
            {
                "name": "p2",
                "type": "prepare",
                "inputs": ["mid"],
                "outputs": ["c"],
                "steps": [{"type": "ColumnRemover", "params": {}}],
            },
        ]
    )
    fixed = apply_merge_adjacent_prepares(flow, "p1", "p2")
    assert len(fixed["recipes"]) == 1
    merged = fixed["recipes"][0]
    assert merged["name"] == "p1"
    assert [s["type"] for s in merged["steps"]] == ["ColumnRenamer", "ColumnRemover"]
    assert merged["outputs"] == ["c"]
    # Intermediate dataset is gone.
    assert "mid" not in {d["name"] for d in fixed["datasets"]}


# ---------------------------------------------------------------------------
# Engine-level
# ---------------------------------------------------------------------------


def test_lint_flow_returns_a_combined_list() -> None:
    flow = _flow(
        recipes=[
            {"name": "split_x", "type": "split", "inputs": ["a"], "outputs": ["b"]},
            {"name": "g1", "type": "grouping", "inputs": ["b"], "outputs": ["c"]},
        ]
    )
    out = lint_flow(flow)
    rule_ids = {l["rule_id"] for l in out}
    # Both rules should fire on this flow.
    assert "split-single-output" in rule_ids
    assert "grouping-no-aggregations" in rule_ids
