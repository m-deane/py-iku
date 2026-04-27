"""Unit tests for schema_drift — pure functions."""

from __future__ import annotations

from app.services.schema_drift import diff_dataset_schemas, diff_flows, summarise


def _ds(name: str, cols: list[tuple[str, str]]) -> dict:
    return {
        "name": name,
        "type": "input",
        "connection_type": "Filesystem",
        "schema": [{"name": n, "type": t} for n, t in cols],
    }


def _flow(datasets: list[dict]) -> dict:
    return {
        "flow_name": "x",
        "total_datasets": len(datasets),
        "total_recipes": 0,
        "datasets": datasets,
        "recipes": [],
    }


def test_diff_dataset_added_and_removed() -> None:
    prior = _ds("d", [("a", "int"), ("b", "string")])
    next_ = _ds("d", [("a", "int"), ("c", "double")])
    out = diff_dataset_schemas(prior, next_, "d")
    assert {c["name"] for c in out["removed"]} == {"b"}
    assert {c["name"] for c in out["added"]} == {"c"}
    assert out["renamed"] == []
    assert out["type_changed"] == []


def test_diff_dataset_rename_heuristic() -> None:
    prior = _ds("d", [("price", "double"), ("qty", "int")])
    next_ = _ds("d", [("px", "double"), ("qty", "int")])
    out = diff_dataset_schemas(prior, next_, "d")
    assert out["renamed"] == [{"from": "price", "to": "px", "type": "double"}]
    assert out["added"] == []
    assert out["removed"] == []


def test_diff_dataset_rename_ambiguous_falls_back_to_add_remove() -> None:
    """Two doubles renamed → ambiguous, surface as add+remove."""
    prior = _ds("d", [("price", "double"), ("foo", "double")])
    next_ = _ds("d", [("px", "double"), ("bar", "double")])
    out = diff_dataset_schemas(prior, next_, "d")
    assert out["renamed"] == []
    assert {c["name"] for c in out["removed"]} == {"price", "foo"}
    assert {c["name"] for c in out["added"]} == {"px", "bar"}


def test_diff_dataset_type_changed() -> None:
    prior = _ds("d", [("qty", "int")])
    next_ = _ds("d", [("qty", "string")])
    out = diff_dataset_schemas(prior, next_, "d")
    assert out["type_changed"] == [
        {"name": "qty", "from_type": "int", "to_type": "string"}
    ]


def test_diff_flows_dataset_level_adds_and_removes() -> None:
    prior = _flow([_ds("a", [("x", "int")])])
    next_ = _flow([_ds("b", [("y", "int")])])
    out = diff_flows(prior, next_)
    assert out["datasets_added"] == ["b"]
    assert out["datasets_removed"] == ["a"]
    assert out["per_dataset"] == []
    assert out["summary"]["has_drift"] is True


def test_summarise_no_drift() -> None:
    assert summarise({"summary": {}}) == "No schema drift detected."


def test_summarise_combo() -> None:
    s = summarise(
        {
            "summary": {
                "columns_added": 3,
                "columns_removed": 1,
                "columns_renamed": 0,
                "columns_type_changed": 0,
                "datasets_added": 0,
                "datasets_removed": 0,
            }
        }
    )
    assert s == "3 added, 1 removed since last run."
