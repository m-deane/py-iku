"""Column-level lineage service.

Builds a per-flow column-lineage graph from a converted flow's recipe metadata
and dataset schemas, using the existing :mod:`py2dataiku.parser.dataflow_tracker`
DataFrameState model as the canonical column carrier.

The graph we expose is a small, JSON-serialisable view tailored to UI
highlighting:

    {
      "column": "px",
      "input_datasets": [...],     # datasets that *originate* the column
      "output_datasets": [...],    # datasets where the column *exists*
      "edges": [                   # recipe-edges that operate on / derive
        {
          "recipe_id": "prepare_1",
          "input_dataset": "df",
          "output_dataset": "df_prepared",
          "kind": "rename" | "derive" | "passthrough" | "drop" | "split" | "join",
          "details": {...}
        },
        ...
      ],
      "recipes": ["prepare_1", "split_2"]   # convenient flat set
    }

Front-office trading flows commonly rename/derive columns inside long PREPARE
chains (e.g. ``price`` -> ``px`` -> ``notional``); we resolve those rename
chains so the user can click any *current* name and still see upstream history.

This service is pure: it operates on the flow dict (the same shape returned by
:meth:`DataikuFlow.to_dict`) and never touches the LLM or filesystem.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


# ---------------------------------------------------------------------------
# Step / recipe analysis
# ---------------------------------------------------------------------------

# PREPARE processor types that explicitly rename a column.
RENAME_PROCESSORS = {"ColumnRenamer", "ColumnsSelector"}

# PREPARE processor types that explicitly add / derive a column.
DERIVE_PROCESSORS = {
    "CreateColumnWithGREL",
    "FormulaProcessor",
    "FillEmptyWithValue",
    "FillEmptyWithMean",
    "FillEmptyWithMedian",
    "ConcatenateColumns",
    "GenerateBigData",
    "AbsoluteValue",
    "RoundProcessor",
    "ClipProcessor",
    "MathProcessor",
    "NumericalCombinator",
}

# PREPARE processor types that drop columns.
DROP_PROCESSORS = {"ColumnRemover", "ColumnsSelector"}


def _step_renames(step: dict[str, Any]) -> list[tuple[str, str]]:
    """Return ``[(old, new), ...]`` rename pairs for a PREPARE step, if any."""
    if step.get("type") not in RENAME_PROCESSORS:
        return []
    params = step.get("params") or {}
    out: list[tuple[str, str]] = []
    # ColumnRenamer style.
    for r in params.get("renamings", []) or []:
        if isinstance(r, dict) and "from" in r and "to" in r:
            out.append((str(r["from"]), str(r["to"])))
    # Some processors store rename mappings differently — be permissive.
    mapping = params.get("mapping") or params.get("rename_mapping")
    if isinstance(mapping, dict):
        for k, v in mapping.items():
            out.append((str(k), str(v)))
    return out


def _step_derives(step: dict[str, Any]) -> list[str]:
    """Return columns produced by a derive-style processor."""
    if step.get("type") not in DERIVE_PROCESSORS:
        return []
    params = step.get("params") or {}
    out: list[str] = []
    # CreateColumnWithGREL / FormulaProcessor put the new col in `column` /
    # `output_column`.
    for k in ("column", "output_column", "new_column", "target", "outputColumn"):
        v = params.get(k)
        if isinstance(v, str):
            out.append(v)
    # Concatenate often writes to `output_column` and reads `columns`.
    return out


def _step_drops(step: dict[str, Any]) -> list[str]:
    """Return columns removed by a step."""
    if step.get("type") not in DROP_PROCESSORS:
        return []
    params = step.get("params") or {}
    cols: list[str] = []
    for k in ("columns", "removed", "dropped"):
        v = params.get(k)
        if isinstance(v, list):
            cols.extend(str(x) for x in v)
    return cols


def _step_inputs(step: dict[str, Any]) -> list[str]:
    """Best-effort list of input columns referenced by this step."""
    params = step.get("params") or {}
    cols: list[str] = []
    for k in ("columns", "inputColumns", "input_columns", "source_columns"):
        v = params.get(k)
        if isinstance(v, list):
            cols.extend(str(x) for x in v)
    for k in ("column", "inputColumn", "input_column", "source_column"):
        v = params.get(k)
        if isinstance(v, str):
            cols.append(v)
    return cols


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_column_lineage(flow: dict[str, Any], column: str) -> dict[str, Any]:
    """Build a lineage view for *column* across *flow*.

    Resolves rename chains so a query for the *current* name (e.g. ``px``)
    also matches edges that operated on the *original* name (``price``).
    """
    if not column:
        raise ValueError("column must be a non-empty string")

    # Walk recipes in declared order to resolve rename chains across the flow.
    # Maintain a set of all names that, at some point, *were* this column.
    aliases: set[str] = {column}
    edges: list[dict[str, Any]] = []
    touched_recipes: list[str] = []
    input_datasets: list[str] = []
    output_datasets: list[str] = []

    datasets = flow.get("datasets") or []
    dataset_index = {d.get("name"): d for d in datasets if isinstance(d, dict)}

    # Datasets where the column appears in the declared schema.
    for ds in datasets:
        schema = ds.get("schema") or []
        names = {c.get("name") for c in schema if isinstance(c, dict)}
        if names & aliases:
            kind = ds.get("type")
            if kind == "input":
                input_datasets.append(ds["name"])
            elif kind == "output":
                output_datasets.append(ds["name"])

    for recipe in flow.get("recipes") or []:
        rname = recipe.get("name")
        rtype = recipe.get("type")
        rin = list(recipe.get("inputs") or [])
        rout = list(recipe.get("outputs") or [])
        steps = list(recipe.get("steps") or [])

        recipe_touched = False

        # PREPARE → step-level analysis.
        if rtype == "prepare":
            local_aliases = set(aliases)
            for step in steps:
                renames = _step_renames(step)
                derives = _step_derives(step)
                drops = _step_drops(step)
                step_inputs = _step_inputs(step)

                # Renames: if any old name is in our alias set, the new name
                # becomes a fresh alias. Conversely, if the *new* name is
                # already an alias (the user clicked the renamed column), the
                # old name is upstream history.
                for old, new in renames:
                    if old in local_aliases:
                        local_aliases.add(new)
                        recipe_touched = True
                    if new in local_aliases:
                        local_aliases.add(old)
                        recipe_touched = True

                # Derives: only counts if the derived column *is* this column,
                # OR if our column appears in the step's input expressions.
                if any(d in local_aliases for d in derives):
                    recipe_touched = True
                if any(c in local_aliases for c in step_inputs):
                    recipe_touched = True

                # Drops: drops *also* count as touching the column, for the
                # downstream "this column was dropped here" UX.
                if any(c in local_aliases for c in drops):
                    recipe_touched = True

            # Merge any new aliases we picked up walking this recipe's steps.
            aliases |= local_aliases

            if recipe_touched:
                kind = _classify_prepare(recipe)
                for src in rin:
                    for dst in rout:
                        edges.append(
                            {
                                "recipe_id": rname,
                                "input_dataset": src,
                                "output_dataset": dst,
                                "kind": kind,
                                "details": {"steps": len(steps)},
                            }
                        )

        # SPLIT — column passthroughs to every output.
        elif rtype == "split":
            recipe_touched = True
            for src in rin:
                for dst in rout:
                    edges.append(
                        {
                            "recipe_id": rname,
                            "input_dataset": src,
                            "output_dataset": dst,
                            "kind": "split",
                            "details": {},
                        }
                    )

        # JOIN — column passthroughs to the single output for any input that
        # carries the column.
        elif rtype == "join":
            recipe_touched = True
            for src in rin:
                for dst in rout:
                    edges.append(
                        {
                            "recipe_id": rname,
                            "input_dataset": src,
                            "output_dataset": dst,
                            "kind": "join",
                            "details": {},
                        }
                    )

        # Default: assume passthrough on every input/output edge.
        else:
            recipe_touched = True
            for src in rin:
                for dst in rout:
                    edges.append(
                        {
                            "recipe_id": rname,
                            "input_dataset": src,
                            "output_dataset": dst,
                            "kind": "passthrough",
                            "details": {"recipe_type": rtype},
                        }
                    )

        if recipe_touched and rname not in touched_recipes:
            touched_recipes.append(rname)

    # Promote any datasets that carry an alias and whose type is input/output.
    for name, ds in dataset_index.items():
        kind = ds.get("type")
        if kind == "input" and name not in input_datasets:
            # Already filled above from explicit schema.
            pass
        if kind == "output" and name not in output_datasets:
            pass

    # If we have *no* schema info but the recipe analysis touched edges,
    # promote the connected datasets: the leaf inputs / outputs of the touched
    # subgraph give the user a useful starting/ending point.
    if not input_datasets:
        srcs = {e["input_dataset"] for e in edges}
        dsts = {e["output_dataset"] for e in edges}
        leaves_in = sorted(srcs - dsts)
        for n in leaves_in:
            ds = dataset_index.get(n)
            if ds is not None:
                input_datasets.append(n)
    if not output_datasets:
        srcs = {e["input_dataset"] for e in edges}
        dsts = {e["output_dataset"] for e in edges}
        leaves_out = sorted(dsts - srcs)
        for n in leaves_out:
            ds = dataset_index.get(n)
            if ds is not None:
                output_datasets.append(n)

    return {
        "column": column,
        "aliases": sorted(aliases),
        "input_datasets": input_datasets,
        "output_datasets": output_datasets,
        "edges": edges,
        "recipes": touched_recipes,
    }


def _classify_prepare(recipe: dict[str, Any]) -> str:
    """Heuristically classify a PREPARE recipe by what its steps do."""
    steps = recipe.get("steps") or []
    types = {s.get("type") for s in steps}
    if types & RENAME_PROCESSORS:
        return "rename"
    if types & DERIVE_PROCESSORS:
        return "derive"
    if types & DROP_PROCESSORS:
        return "drop"
    return "passthrough"


def discover_columns(flow: dict[str, Any]) -> list[str]:
    """Return a deduplicated list of every column name surfaced by *flow*.

    Sources:
      - Each dataset's declared schema.
      - Every PREPARE step's params (column / columns / renamings.from / .to).
    """
    out: set[str] = set()
    for ds in flow.get("datasets") or []:
        for col in ds.get("schema") or []:
            if isinstance(col, dict) and isinstance(col.get("name"), str):
                out.add(col["name"])
    for recipe in flow.get("recipes") or []:
        for step in recipe.get("steps") or []:
            params = step.get("params") or {}
            for k in ("column", "output_column", "new_column"):
                v = params.get(k)
                if isinstance(v, str):
                    out.add(v)
            for k in ("columns",):
                v = params.get(k)
                if isinstance(v, list):
                    for x in v:
                        if isinstance(x, str):
                            out.add(x)
            for r in params.get("renamings") or []:
                if isinstance(r, dict):
                    for kk in ("from", "to"):
                        vv = r.get(kk)
                        if isinstance(vv, str):
                            out.add(vv)
    return sorted(out)


__all__ = ["build_column_lineage", "discover_columns"]


# Back-compat: surface a thin Iterable signature for callers that want
# to pre-validate a list of columns. (Used from the route layer.)
def filter_known_columns(flow: dict[str, Any], columns: Iterable[str]) -> list[str]:
    known = set(discover_columns(flow))
    return [c for c in columns if c in known]
