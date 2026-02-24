"""MCP tool call generation for Dataiku DSS.

Generates MCP (Model Context Protocol) tool call payloads compatible with the
dataiku_factory MCP server (https://github.com/hhobin/dataiku_factory).

The dataiku_factory server exposes tools such as ``create_dataset``,
``create_recipe``, ``run_recipe``, and ``get_project_flow``. This module
converts a DataikuFlow into an ordered sequence of those tool calls.

Usage:
    >>> from py2dataiku.integrations import generate_mcp_tool_calls, format_mcp_script
    >>> tool_calls = generate_mcp_tool_calls(flow, "MY_PROJECT")
    >>> print(format_mcp_script(tool_calls))
"""

import json
from typing import Any, Dict, List

from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.flow_graph import NodeType

# Mapping from RecipeType to DSS API type strings used in MCP calls.
_MCP_RECIPE_TYPE_MAP = {
    RecipeType.PREPARE: "shaker",
    RecipeType.JOIN: "join",
    RecipeType.STACK: "vstack",
    RecipeType.SPLIT: "split",
    RecipeType.GROUPING: "grouping",
    RecipeType.WINDOW: "window",
    RecipeType.PIVOT: "pivot",
    RecipeType.SORT: "sort",
    RecipeType.DISTINCT: "distinct",
    RecipeType.TOP_N: "topn",
    RecipeType.SAMPLING: "sampling",
    RecipeType.PYTHON: "python",
    RecipeType.SQL: "sql_query",
    RecipeType.SYNC: "sync",
    RecipeType.DOWNLOAD: "download",
    RecipeType.PYSPARK: "pyspark",
    RecipeType.R: "r",
    RecipeType.HIVE: "hive",
    RecipeType.IMPALA: "impala",
    RecipeType.SPARKSQL: "sparksql",
    RecipeType.SPARK_SCALA: "spark_scala",
    RecipeType.SPARKR: "sparkr",
    RecipeType.SHELL: "shell",
}


def _dataset_to_mcp_args(dataset: DataikuDataset, project_key: str) -> Dict[str, Any]:
    """Build MCP ``create_dataset`` arguments for a dataset."""
    args: Dict[str, Any] = {
        "project_key": project_key,
        "dataset_name": dataset.name,
        "connection_type": dataset.connection_type.value,
    }

    if dataset.schema:
        args["schema"] = {
            "columns": [
                {"name": col.name, "type": col.type}
                for col in dataset.schema
            ],
        }

    return args


def _recipe_to_mcp_args(recipe: DataikuRecipe, project_key: str) -> Dict[str, Any]:
    """Build MCP ``create_recipe`` arguments for a recipe."""
    dss_type = _MCP_RECIPE_TYPE_MAP.get(recipe.recipe_type, "python")
    args: Dict[str, Any] = {
        "project_key": project_key,
        "recipe_name": recipe.name,
        "recipe_type": dss_type,
        "inputs": recipe.inputs,
        "outputs": recipe.outputs,
    }

    # Include recipe settings if available
    settings = _get_recipe_settings(recipe)
    if settings:
        args["settings"] = settings

    return args


def _get_recipe_settings(recipe: DataikuRecipe) -> Dict[str, Any]:
    """Extract recipe settings for the MCP payload."""
    if recipe.settings is not None:
        return recipe.settings.to_dict()
    return recipe._build_settings()


def generate_mcp_tool_calls(
    flow: DataikuFlow,
    project_key: str,
) -> List[Dict[str, Any]]:
    """Generate MCP tool call payloads for a DataikuFlow.

    The calls are ordered topologically so that datasets are created
    before the recipes that reference them.

    Each entry in the returned list is a dict with:
    - ``tool_name``: the MCP tool name (``"create_dataset"`` or ``"create_recipe"``)
    - ``arguments``: the keyword arguments for the tool

    Args:
        flow: The DataikuFlow to convert.
        project_key: The target DSS project key.

    Returns:
        Ordered list of MCP tool call dicts.
    """
    tool_calls: List[Dict[str, Any]] = []

    try:
        graph = flow.graph
        topo_order = graph.topological_sort()
    except ValueError:
        # Fallback: datasets first, then recipes (without topological guarantee)
        topo_order = [ds.name for ds in flow.datasets] + [
            f"recipe:{r.name}" for r in flow.recipes
        ]

    for node_name in topo_order:
        node = flow.graph.get_node(node_name) if node_name in flow.graph else None

        if node is not None and node.node_type == NodeType.DATASET:
            dataset = flow.get_dataset(node_name)
            if dataset is None:
                continue
            tool_calls.append({
                "tool_name": "create_dataset",
                "arguments": _dataset_to_mcp_args(dataset, project_key),
            })

        elif node is not None and node.node_type == NodeType.RECIPE:
            recipe_name = node_name.removeprefix("recipe:")
            recipe = flow.get_recipe(recipe_name)
            if recipe is None:
                continue
            tool_calls.append({
                "tool_name": "create_recipe",
                "arguments": _recipe_to_mcp_args(recipe, project_key),
            })

    return tool_calls


def format_mcp_script(tool_calls: List[Dict[str, Any]]) -> str:
    """Format MCP tool calls as a human-readable script.

    Produces output that can be copy-pasted into an MCP-aware client
    or used as documentation for manual recreation.

    Args:
        tool_calls: List of tool call dicts from ``generate_mcp_tool_calls``.

    Returns:
        A formatted multi-line string.
    """
    lines: List[str] = [
        "# MCP Tool Calls for Dataiku DSS",
        f"# Total calls: {len(tool_calls)}",
        "",
    ]

    for i, call in enumerate(tool_calls, start=1):
        tool_name = call["tool_name"]
        arguments = call["arguments"]
        lines.append(f"# Step {i}: {tool_name}")
        lines.append(f"tool: {tool_name}")
        lines.append(f"arguments: {json.dumps(arguments, indent=2)}")
        lines.append("")

    return "\n".join(lines)
