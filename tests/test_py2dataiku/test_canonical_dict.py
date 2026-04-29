"""Tests for ``DataikuFlow.to_canonical_dict()`` — Bug #7 fix.

The canonical view strips free-text drift sources (notes, reasoning,
optimization_notes, recommendations, generation_timestamp) so a SHA-256
of ``json.dumps(canonical, sort_keys=True)`` is byte-stable across
identical-input deterministic conversions.
"""
import hashlib
import json

from py2dataiku import convert


SRC = """
import pandas as pd
df = pd.read_csv("trades.csv")
df = df.dropna(subset=["trade_id"])
df["mtm"] = (df["mid_price"] - df["price"]) * df["notional"]
agg = df.groupby("book").agg({"mtm": "sum"})
agg.to_csv("out.csv")
"""


def _hash(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


def test_canonical_dict_strips_free_text_fields() -> None:
    flow = convert(SRC)
    canonical = flow.to_canonical_dict()

    assert "optimization_notes" not in canonical
    assert "recommendations" not in canonical
    assert "generation_timestamp" not in canonical
    for recipe in canonical["recipes"]:
        assert "notes" not in recipe, f"recipe {recipe.get('name')} kept notes"
        assert "reasoning" not in recipe, (
            f"recipe {recipe.get('name')} kept reasoning"
        )


def test_canonical_dict_preserves_structure() -> None:
    flow = convert(SRC)
    canonical = flow.to_canonical_dict()

    # Core structure preserved
    assert canonical["flow_name"] == flow.name
    assert canonical["total_recipes"] == len(flow.recipes)
    assert canonical["total_datasets"] == len(flow.datasets)
    assert len(canonical["recipes"]) == len(flow.recipes)
    assert len(canonical["datasets"]) == len(flow.datasets)

    # Per-recipe structural fields preserved
    for recipe in canonical["recipes"]:
        assert "type" in recipe
        assert "name" in recipe
        # inputs/outputs are part of the DAG structure
        assert "inputs" in recipe or "outputs" in recipe


def test_canonical_dict_byte_stable_across_repeat_conversions() -> None:
    """Two identical convert() calls produce byte-identical canonical
    dicts. (Rule mode is fully deterministic; this test pins that
    property and protects against future free-text leakage into the
    canonical structure.)"""
    flow_a = convert(SRC)
    flow_b = convert(SRC)
    assert _hash(flow_a.to_canonical_dict()) == _hash(flow_b.to_canonical_dict())


def test_full_to_dict_still_has_free_text() -> None:
    """Sanity: the regular to_dict still carries the prose so callers
    that want it (Inspector panel, audit log, etc.) aren't broken."""
    flow = convert(SRC)
    full = flow.to_dict(include_timestamp=False)
    assert "optimization_notes" in full
    assert "recommendations" in full
