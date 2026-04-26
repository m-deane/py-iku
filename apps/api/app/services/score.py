"""Flow complexity scoring service.

Score formula: complexity = recipe_count + 0.1*processor_count + 0.5*max_depth + 0.2*fan_out_max
"""

from __future__ import annotations

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import RecipeType

from ..schemas.convert import ComplexityScore


def score_flow(flow: DataikuFlow) -> ComplexityScore:
    """Compute a ComplexityScore from FlowGraph metrics.

    complexity = recipe_count + 0.1 * processor_count + 0.5 * max_depth + 0.2 * fan_out_max
    """
    graph = flow.graph

    recipe_count = len(flow.recipes)

    # Count total prepare steps across all PREPARE recipes
    processor_count = sum(
        len(r.steps)
        for r in flow.recipes
        if r.recipe_type == RecipeType.PREPARE
    )

    # Compute longest path from any root to any leaf (node hops)
    max_depth = _compute_max_depth(graph)

    # Maximum out-degree across all nodes
    fan_out_max = max(
        (len(graph.get_successors(n.name)) for n in graph.nodes),
        default=0,
    )

    complexity = recipe_count + 0.1 * processor_count + 0.5 * max_depth + 0.2 * fan_out_max

    return ComplexityScore(
        recipe_count=recipe_count,
        processor_count=processor_count,
        max_depth=max_depth,
        fan_out_max=fan_out_max,
        complexity=round(complexity, 4),
        cost_estimate=None,  # Only set for LLM mode (not available here)
    )


def _compute_max_depth(graph) -> int:  # type: ignore[type-arg]
    """Return the length (in edges) of the longest path in the DAG."""
    if not graph.nodes:
        return 0

    # Dynamic programming on topological order
    try:
        topo = graph.topological_sort()
    except ValueError:
        # Cycle detected — return 0 as fallback
        return 0

    dist: dict[str, int] = {name: 0 for name in topo}
    for name in topo:
        for successor in graph.get_successors(name):
            if dist[name] + 1 > dist.get(successor, 0):
                dist[successor] = dist[name] + 1

    return max(dist.values(), default=0)
