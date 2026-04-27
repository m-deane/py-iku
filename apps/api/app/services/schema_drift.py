"""Schema-drift detection service.

Compares two flow snapshots' dataset schemas and emits a structured diff.

Algorithm
---------
We treat each *dataset* as a (name, schema) pair where schema is a list of
``{name, type}`` columns. For every dataset present in *both* the prior and
the next snapshot:

1. Index columns by ``(dataset_name, column_name)``.
2. **Removed**: in prior but not in next.
3. **Added**: in next but not in prior.
4. **Renamed** (heuristic): a removed and an added column where the *types*
   match exactly *and* there is exactly one such pair per type for that
   dataset. This avoids false positives in flat tables with many string
   columns; if it isn't confident we leave them as add+remove.
5. **Type changed**: same column name, different ``type``.

We also surface dataset-level adds/removes for completeness — a dataset that
appears in one snapshot but not the other is a structural change a trader
will want to see.

The output is intentionally JSON-friendly (no enums, no ``None``-only fields)
because it round-trips through the API and into a Zustand store.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any


def _columns(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise a dataset's schema into ``[{name, type}, ...]``."""
    raw = dataset.get("schema") or []
    out: list[dict[str, Any]] = []
    for col in raw:
        if not isinstance(col, dict):
            continue
        name = col.get("name")
        if not isinstance(name, str):
            continue
        out.append({"name": name, "type": col.get("type") or "unknown"})
    return out


def _index_datasets(flow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        d.get("name"): d
        for d in (flow.get("datasets") or [])
        if isinstance(d, dict) and isinstance(d.get("name"), str)
    }


def _detect_renames(
    removed: list[dict[str, Any]],
    added: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Greedy 1:1 rename detection by *type*.

    Only treats a (removed, added) pair as a rename when there is exactly one
    of each for a given type within the same dataset — otherwise we surface
    them as separate removes and adds.
    """
    by_type_rem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_type_add: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in removed:
        by_type_rem[c["type"]].append(c)
    for c in added:
        by_type_add[c["type"]].append(c)

    renamed: list[dict[str, Any]] = []
    rem_left: list[dict[str, Any]] = []
    add_left: list[dict[str, Any]] = []
    for t, rems in by_type_rem.items():
        adds = by_type_add.get(t, [])
        if len(rems) == 1 and len(adds) == 1:
            renamed.append(
                {
                    "from": rems[0]["name"],
                    "to": adds[0]["name"],
                    "type": t,
                }
            )
        else:
            rem_left.extend(rems)
            add_left.extend(adds)
    # Types that only appear on the *added* side were never iterated above.
    for t, adds in by_type_add.items():
        if t not in by_type_rem:
            add_left.extend(adds)
    return renamed, rem_left, add_left


def diff_dataset_schemas(
    prior: dict[str, Any],
    next_: dict[str, Any],
    dataset_name: str,
) -> dict[str, Any]:
    """Diff a single dataset's schema between two flow snapshots."""
    p = _columns(prior)
    n = _columns(next_)
    p_by_name = {c["name"]: c for c in p}
    n_by_name = {c["name"]: c for c in n}

    type_changed: list[dict[str, Any]] = []
    for name in set(p_by_name) & set(n_by_name):
        if p_by_name[name]["type"] != n_by_name[name]["type"]:
            type_changed.append(
                {
                    "name": name,
                    "from_type": p_by_name[name]["type"],
                    "to_type": n_by_name[name]["type"],
                }
            )
    removed_raw = [c for c in p if c["name"] not in n_by_name]
    added_raw = [c for c in n if c["name"] not in p_by_name]

    renamed, removed, added = _detect_renames(removed_raw, added_raw)

    return {
        "dataset": dataset_name,
        "added": added,
        "removed": removed,
        "renamed": renamed,
        "type_changed": type_changed,
    }


def diff_flows(prior: dict[str, Any], next_: dict[str, Any]) -> dict[str, Any]:
    """Return a structured diff of two flows' dataset schemas.

    ``prior`` and ``next_`` are flow dicts in the canonical
    :meth:`DataikuFlow.to_dict` shape.
    """
    p_idx = _index_datasets(prior)
    n_idx = _index_datasets(next_)

    common = sorted(set(p_idx) & set(n_idx))
    only_prior = sorted(set(p_idx) - set(n_idx))
    only_next = sorted(set(n_idx) - set(p_idx))

    per_dataset: list[dict[str, Any]] = []
    totals_added = 0
    totals_removed = 0
    totals_renamed = 0
    totals_type_changed = 0
    for name in common:
        d = diff_dataset_schemas(p_idx[name], n_idx[name], name)
        if (
            d["added"]
            or d["removed"]
            or d["renamed"]
            or d["type_changed"]
        ):
            per_dataset.append(d)
            totals_added += len(d["added"])
            totals_removed += len(d["removed"])
            totals_renamed += len(d["renamed"])
            totals_type_changed += len(d["type_changed"])

    return {
        "datasets_added": only_next,
        "datasets_removed": only_prior,
        "per_dataset": per_dataset,
        "summary": {
            "datasets_added": len(only_next),
            "datasets_removed": len(only_prior),
            "columns_added": totals_added,
            "columns_removed": totals_removed,
            "columns_renamed": totals_renamed,
            "columns_type_changed": totals_type_changed,
            "has_drift": bool(
                only_next
                or only_prior
                or per_dataset
            ),
        },
    }


def summarise(diff: dict[str, Any]) -> str:
    """Human-readable one-liner for the banner — `"3 added, 1 removed since last run"`."""
    s = diff.get("summary", {})
    bits: list[str] = []
    if s.get("columns_added"):
        bits.append(f"{s['columns_added']} added")
    if s.get("columns_removed"):
        bits.append(f"{s['columns_removed']} removed")
    if s.get("columns_renamed"):
        bits.append(f"{s['columns_renamed']} renamed")
    if s.get("columns_type_changed"):
        bits.append(f"{s['columns_type_changed']} type-changed")
    if s.get("datasets_added"):
        bits.append(f"{s['datasets_added']} new dataset(s)")
    if s.get("datasets_removed"):
        bits.append(f"{s['datasets_removed']} dataset(s) gone")
    if not bits:
        return "No schema drift detected."
    return ", ".join(bits) + " since last run."


__all__ = ["diff_dataset_schemas", "diff_flows", "summarise"]


def schemas_only(flow: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Project a flow snapshot down to ``{dataset_name: [columns]}`` for storage."""
    return {
        name: _columns(d) for name, d in _index_datasets(flow).items()
    }
