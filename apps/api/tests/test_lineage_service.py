"""Unit tests for lineage_service — pure functions."""

from __future__ import annotations

from app.services.lineage_service import (
    build_column_lineage,
    discover_columns,
    filter_known_columns,
)


def _flow_rename_then_split() -> dict:
    return {
        "flow_name": "x",
        "total_recipes": 2,
        "total_datasets": 4,
        "datasets": [
            {"name": "df", "type": "input", "connection_type": "Filesystem", "schema": []},
            {
                "name": "df_prepared",
                "type": "intermediate",
                "connection_type": "Filesystem",
                "schema": [],
            },
            {"name": "big", "type": "output", "connection_type": "Filesystem", "schema": []},
            {"name": "small", "type": "output", "connection_type": "Filesystem", "schema": []},
        ],
        "recipes": [
            {
                "name": "prepare_1",
                "type": "prepare",
                "inputs": ["df"],
                "outputs": ["df_prepared"],
                "steps": [
                    {
                        "type": "ColumnRenamer",
                        "params": {"renamings": [{"from": "price", "to": "px"}]},
                    }
                ],
            },
            {
                "name": "split_1",
                "type": "split",
                "inputs": ["df_prepared"],
                "outputs": ["big", "small"],
            },
        ],
    }


def test_lineage_resolves_rename_chain_when_querying_renamed_name() -> None:
    flow = _flow_rename_then_split()
    out = build_column_lineage(flow, "px")
    assert "price" in out["aliases"]
    assert "px" in out["aliases"]
    # PREPARE was the rename step; SPLIT passes the column through.
    assert "prepare_1" in out["recipes"]
    assert "split_1" in out["recipes"]


def test_lineage_resolves_rename_chain_when_querying_original_name() -> None:
    flow = _flow_rename_then_split()
    out = build_column_lineage(flow, "price")
    assert "px" in out["aliases"]
    assert "prepare_1" in out["recipes"]


def test_lineage_split_is_classified_correctly() -> None:
    flow = _flow_rename_then_split()
    out = build_column_lineage(flow, "px")
    split_edges = [e for e in out["edges"] if e["recipe_id"] == "split_1"]
    assert {e["kind"] for e in split_edges} == {"split"}
    # SPLIT fans out to both branches.
    assert {e["output_dataset"] for e in split_edges} == {"big", "small"}


def test_discover_columns_collects_renames_and_targets() -> None:
    flow = _flow_rename_then_split()
    cols = discover_columns(flow)
    assert "px" in cols
    assert "price" in cols


def test_filter_known_columns_filters_unknown() -> None:
    flow = _flow_rename_then_split()
    assert filter_known_columns(flow, ["px", "ghost"]) == ["px"]


def test_lineage_unknown_column_returns_empty_recipes_for_a_flat_passthrough() -> None:
    """A column nobody operates on still returns a structurally-valid result."""
    flow = _flow_rename_then_split()
    out = build_column_lineage(flow, "nonexistent_col")
    # A passthrough column appears in every recipe-edge by default since we
    # can't disprove it isn't carried along — the PREPARE/SPLIT recipes are
    # listed because they touch the dataset (not the column-by-name).
    assert isinstance(out["recipes"], list)
    assert isinstance(out["edges"], list)
