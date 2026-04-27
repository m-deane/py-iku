"""Recipe-pattern linter.

A small pure-function rule engine that flags suboptimal flow shapes. Each rule
takes a flow dict (canonical :meth:`DataikuFlow.to_dict` shape) and yields
``Lint`` records; rules are completely independent and pure (no I/O).

Rule severities:
    - ``blocker``  : the flow will not run as intended.
    - ``warning``  : likely-suboptimal; worth fixing before deploy.
    - ``info``     : style nudge.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypedDict


class Lint(TypedDict, total=False):
    rule_id: str
    severity: str  # "blocker" | "warning" | "info"
    recipe_id: str | None
    message: str
    fix: dict[str, Any] | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _recipes_by_name(flow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        r.get("name"): r
        for r in flow.get("recipes") or []
        if isinstance(r, dict) and isinstance(r.get("name"), str)
    }


def _adjacency(flow: dict[str, Any]) -> dict[str, list[str]]:
    """Build a recipe → downstream-recipes adjacency, keyed by recipe name.

    We connect ``A → B`` when an output dataset of A is an input of B.
    """
    by_input: dict[str, list[str]] = {}
    for r in flow.get("recipes") or []:
        for inp in r.get("inputs") or []:
            by_input.setdefault(inp, []).append(r.get("name"))
    out: dict[str, list[str]] = {}
    for r in flow.get("recipes") or []:
        rname = r.get("name")
        downstream: list[str] = []
        for outp in r.get("outputs") or []:
            downstream.extend(by_input.get(outp, []))
        # de-dup, preserve order
        seen: set[str] = set()
        deduped: list[str] = []
        for n in downstream:
            if n and n not in seen:
                seen.add(n)
                deduped.append(n)
        out[rname] = deduped
    return out


# ---------------------------------------------------------------------------
# Individual rules
# ---------------------------------------------------------------------------


def rule_filter_before_groupby(flow: dict[str, Any]) -> list[Lint]:
    """A GROUPBY *upstream* of a FILTER processes more rows than needed."""
    out: list[Lint] = []
    adj = _adjacency(flow)
    by_name = _recipes_by_name(flow)
    for rname, recipe in by_name.items():
        if recipe.get("type") != "grouping":
            continue
        for downstream in adj.get(rname, []):
            d = by_name.get(downstream)
            if d is None:
                continue
            if d.get("type") == "prepare" and any(
                (s.get("type") or "").startswith("Filter") for s in d.get("steps") or []
            ):
                out.append(
                    Lint(
                        rule_id="filter-before-groupby",
                        severity="warning",
                        recipe_id=rname,
                        message=(
                            f"GROUPING '{rname}' is followed by a FILTER in "
                            f"'{downstream}'. Reordering filter → group is "
                            f"usually cheaper for high-cardinality data."
                        ),
                        fix=None,
                    )
                )
    return out


def rule_adjacent_prepares(flow: dict[str, Any]) -> list[Lint]:
    """Two PREPARE recipes connected by a single intermediate dataset can merge."""
    out: list[Lint] = []
    adj = _adjacency(flow)
    by_name = _recipes_by_name(flow)
    # Build reverse-adj for "single producer" check.
    rev: dict[str, list[str]] = {}
    for src, dests in adj.items():
        for d in dests:
            rev.setdefault(d, []).append(src)

    for rname, recipe in by_name.items():
        if recipe.get("type") != "prepare":
            continue
        downstream = adj.get(rname, [])
        # Only one downstream and the only producer of *its* sole input is us.
        for dn in downstream:
            d = by_name.get(dn)
            if d is None or d.get("type") != "prepare":
                continue
            # Is `dn` connected only from `rname`?
            ins = d.get("inputs") or []
            if len(ins) != 1:
                continue
            producers = rev.get(dn, [])
            if producers != [rname]:
                continue
            outs = recipe.get("outputs") or []
            if len(outs) != 1:
                continue
            out.append(
                Lint(
                    rule_id="merge-adjacent-prepares",
                    severity="warning",
                    recipe_id=rname,
                    message=(
                        f"PREPARE '{rname}' feeds straight into PREPARE "
                        f"'{dn}'. Merging them removes an intermediate "
                        f"dataset and one I/O round-trip."
                    ),
                    fix={
                        "kind": "merge_adjacent_prepares",
                        "left": rname,
                        "right": dn,
                    },
                )
            )
    return out


def rule_grouping_no_aggs(flow: dict[str, Any]) -> list[Lint]:
    """A GROUPING recipe with no aggregations is a no-op (just keys)."""
    out: list[Lint] = []
    for r in flow.get("recipes") or []:
        if r.get("type") != "grouping":
            continue
        # py2dataiku composes settings onto the recipe at to_dict() time.
        # Look at common shapes: aggregations / values / aggs.
        settings = r.get("settings") or {}
        aggs = (
            r.get("aggregations")
            or r.get("values")
            or settings.get("aggregations")
            or settings.get("values")
            or []
        )
        if not aggs:
            out.append(
                Lint(
                    rule_id="grouping-no-aggregations",
                    severity="warning",
                    recipe_id=r.get("name"),
                    message=(
                        f"GROUPING '{r.get('name')}' has no aggregations — "
                        f"this collapses to a SELECT DISTINCT on the keys."
                    ),
                    fix=None,
                )
            )
    return out


def rule_window_empty_partitions(flow: dict[str, Any]) -> list[Lint]:
    """WINDOW with no partition columns scans the entire dataset per row."""
    out: list[Lint] = []
    for r in flow.get("recipes") or []:
        if r.get("type") != "window":
            continue
        settings = r.get("settings") or {}
        parts = (
            r.get("partition_columns")
            or r.get("partitionColumns")
            or settings.get("partition_columns")
            or settings.get("partitionColumns")
            or []
        )
        if not parts:
            out.append(
                Lint(
                    rule_id="window-empty-partitions",
                    severity="warning",
                    recipe_id=r.get("name"),
                    message=(
                        f"WINDOW '{r.get('name')}' has empty "
                        f"partition_columns. Performance degrades on large "
                        f"datasets — partition by something, e.g. "
                        f"`book` or `instrument_id` for trade tapes."
                    ),
                    fix=None,
                )
            )
    return out


def rule_split_single_output(flow: dict[str, Any]) -> list[Lint]:
    """SPLIT with one or zero outputs is dead code — the second branch is missing."""
    out: list[Lint] = []
    for r in flow.get("recipes") or []:
        if r.get("type") != "split":
            continue
        outs = r.get("outputs") or []
        if len(outs) <= 1:
            out.append(
                Lint(
                    rule_id="split-single-output",
                    severity="blocker",
                    recipe_id=r.get("name"),
                    message=(
                        f"SPLIT '{r.get('name')}' has only "
                        f"{len(outs)} output(s). A SPLIT needs at least two "
                        f"branches — collapse to a FILTER processor instead."
                    ),
                    fix=None,
                )
            )
    return out


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


RULES: tuple[Callable[[dict[str, Any]], list[Lint]], ...] = (
    rule_filter_before_groupby,
    rule_adjacent_prepares,
    rule_grouping_no_aggs,
    rule_window_empty_partitions,
    rule_split_single_output,
)


RULE_CATALOG: list[dict[str, str]] = [
    {
        "rule_id": "filter-before-groupby",
        "severity": "warning",
        "title": "Filter before groupby is cheaper",
    },
    {
        "rule_id": "merge-adjacent-prepares",
        "severity": "warning",
        "title": "Two adjacent PREPAREs can merge",
    },
    {
        "rule_id": "grouping-no-aggregations",
        "severity": "warning",
        "title": "GROUPING with no aggregations is a no-op",
    },
    {
        "rule_id": "window-empty-partitions",
        "severity": "warning",
        "title": "WINDOW with empty partition_columns may degrade",
    },
    {
        "rule_id": "split-single-output",
        "severity": "blocker",
        "title": "SPLIT with one output is dead code",
    },
]


def lint_flow(
    flow: dict[str, Any],
    rules: Iterable[Callable[[dict[str, Any]], list[Lint]]] | None = None,
) -> list[Lint]:
    """Run every rule against *flow* and return a flat list of findings."""
    rs = tuple(rules) if rules is not None else RULES
    out: list[Lint] = []
    for rule in rs:
        out.extend(rule(flow))
    return out


# ---------------------------------------------------------------------------
# Fixers
# ---------------------------------------------------------------------------


def apply_merge_adjacent_prepares(
    flow: dict[str, Any],
    left: str,
    right: str,
) -> dict[str, Any]:
    """Merge PREPARE *right* into PREPARE *left*, returning a new flow dict.

    Pre-conditions are the same as the rule's emit conditions: ``left`` and
    ``right`` are both PREPARE; ``right`` has exactly one input, equal to
    ``left``'s sole output; nothing else consumes that intermediate dataset.
    """
    new = {**flow, "recipes": list(flow.get("recipes") or []), "datasets": list(flow.get("datasets") or [])}
    by_name = _recipes_by_name(new)
    if left not in by_name or right not in by_name:
        return flow
    L = by_name[left]
    R = by_name[right]
    if L.get("type") != "prepare" or R.get("type") != "prepare":
        return flow
    intermediate = (R.get("inputs") or [None])[0]
    if intermediate is None or intermediate not in (L.get("outputs") or []):
        return flow

    # Concatenate steps; keep L's name and inputs; take R's outputs.
    merged_steps = list(L.get("steps") or []) + list(R.get("steps") or [])
    merged: dict[str, Any] = {
        **L,
        "steps": merged_steps,
        "step_count": len(merged_steps),
        "outputs": list(R.get("outputs") or []),
        "notes": list(L.get("notes") or []) + [f"merged with {right}"],
    }

    # Drop both old recipes; insert the merged one at L's position.
    recipes_in = list(new.get("recipes") or [])
    out_recipes: list[dict[str, Any]] = []
    inserted = False
    for r in recipes_in:
        if r.get("name") == left:
            out_recipes.append(merged)
            inserted = True
        elif r.get("name") == right:
            continue
        else:
            out_recipes.append(r)
    if not inserted:
        out_recipes.append(merged)
    new["recipes"] = out_recipes

    # Drop the now-orphaned intermediate dataset.
    new["datasets"] = [
        d for d in new.get("datasets") or [] if d.get("name") != intermediate
    ]
    new["total_recipes"] = len(out_recipes)
    new["total_datasets"] = len(new["datasets"])
    return new


__all__ = [
    "Lint",
    "RULES",
    "RULE_CATALOG",
    "lint_flow",
    "apply_merge_adjacent_prepares",
    "rule_filter_before_groupby",
    "rule_adjacent_prepares",
    "rule_grouping_no_aggs",
    "rule_window_empty_partitions",
    "rule_split_single_output",
]
