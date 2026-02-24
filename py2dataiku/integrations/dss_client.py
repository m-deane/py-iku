"""Dataiku DSS API client for deploying py2dataiku flows.

This module provides the DSSFlowDeployer class which deploys a DataikuFlow
to a running DSS instance via the dataikuapi Python client.

The dataikuapi package is an optional dependency. If not installed, a helpful
error message is shown when attempting to connect to DSS. The dry_run mode
works without dataikuapi.

Usage:
    >>> from py2dataiku.integrations import DSSFlowDeployer
    >>> deployer = DSSFlowDeployer(
    ...     host="https://dss.example.com",
    ...     api_key="your-api-key",
    ...     project_key="MY_PROJECT",
    ... )
    >>> result = deployer.deploy(flow)
    >>> print(result)

    >>> # Dry-run mode (no DSS connection required)
    >>> deployer = DSSFlowDeployer("", "", "MY_PROJECT", dry_run=True)
    >>> result = deployer.deploy(flow)
    >>> print(result.datasets_created, result.recipes_created)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from py2dataiku.exceptions import ExportError
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.flow_graph import NodeType

logger = logging.getLogger(__name__)

# DSS recipe type strings used by the dataikuapi builder API.
_DSS_RECIPE_TYPE_MAP = {
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


@dataclass
class DeploymentResult:
    """Result of deploying a DataikuFlow to DSS."""

    datasets_created: List[str] = field(default_factory=list)
    recipes_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def success(self) -> bool:
        """Whether the deployment completed without errors."""
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "datasets_created": self.datasets_created,
            "recipes_created": self.recipes_created,
            "errors": self.errors,
            "warnings": self.warnings,
            "dry_run": self.dry_run,
            "success": self.success,
        }

    def __repr__(self) -> str:
        status = "DRY RUN" if self.dry_run else ("OK" if self.success else "FAILED")
        return (
            f"DeploymentResult({status}: "
            f"{len(self.datasets_created)} datasets, "
            f"{len(self.recipes_created)} recipes, "
            f"{len(self.errors)} errors)"
        )


def _get_dss_recipe_type(recipe_type: RecipeType) -> str:
    """Map a RecipeType enum to the DSS API type string."""
    return _DSS_RECIPE_TYPE_MAP.get(recipe_type, "python")


class DSSFlowDeployer:
    """Deploy a DataikuFlow to a Dataiku DSS instance.

    This class uses the ``dataikuapi`` package to create datasets and recipes
    in a DSS project. When ``dry_run=True``, it validates the flow and returns
    what *would* be created without making any API calls (no ``dataikuapi``
    required).

    Args:
        host: DSS instance URL (e.g. ``"https://dss.example.com"``)
        api_key: Personal API key for authentication
        project_key: Target DSS project key
        dry_run: If True, validate only without creating resources
    """

    def __init__(
        self,
        host: str,
        api_key: str,
        project_key: str,
        dry_run: bool = False,
    ):
        self.host = host.rstrip("/") if host else ""
        self.api_key = api_key
        self.project_key = project_key
        self.dry_run = dry_run
        self._client = None
        self._project = None

    def _ensure_connected(self) -> None:
        """Lazily initialise the dataikuapi client and project handle."""
        if self._client is not None:
            return

        try:
            import dataikuapi  # type: ignore[import-untyped]
        except ImportError:
            raise ExportError(
                "The 'dataikuapi' package is required to deploy to DSS. "
                "Install it with: pip install dataiku-api-client\n"
                "See https://doc.dataiku.com/dss/latest/python-api/outside-usage.html"
            )

        self._client = dataikuapi.DSSClient(self.host, self.api_key)
        self._project = self._client.get_project(self.project_key)

    def deploy(self, flow: DataikuFlow) -> DeploymentResult:
        """Deploy an entire DataikuFlow to DSS.

        Datasets are created first, followed by recipes in topological
        order so that each recipe's inputs already exist.

        Args:
            flow: The DataikuFlow to deploy.

        Returns:
            A DeploymentResult summarising what was created.
        """
        result = DeploymentResult(dry_run=self.dry_run)

        # Validate flow first
        validation = flow.validate()
        if not validation["valid"]:
            for error in validation["errors"]:
                result.errors.append(error["message"])
            return result

        for warning in validation.get("warnings", []):
            if isinstance(warning, dict):
                result.warnings.append(warning.get("message", str(warning)))
            else:
                result.warnings.append(str(warning))

        # Use topological sort for correct creation order
        try:
            graph = flow.graph
            topo_order = graph.topological_sort()
        except ValueError as exc:
            result.errors.append(f"Flow contains a cycle: {exc}")
            return result

        # Deploy datasets first (in topological order), then recipes
        for node_name in topo_order:
            node = graph.get_node(node_name)
            if node is None:
                continue

            if node.node_type == NodeType.DATASET:
                dataset = flow.get_dataset(node_name)
                if dataset is None:
                    continue
                try:
                    self.deploy_dataset(dataset)
                    result.datasets_created.append(dataset.name)
                except Exception as exc:
                    result.errors.append(
                        f"Failed to create dataset '{dataset.name}': {exc}"
                    )

            elif node.node_type == NodeType.RECIPE:
                # FlowGraph prefixes recipe names with "recipe:"
                recipe_name = node_name.removeprefix("recipe:")
                recipe = flow.get_recipe(recipe_name)
                if recipe is None:
                    continue
                try:
                    self.deploy_recipe(recipe)
                    result.recipes_created.append(recipe.name)
                except Exception as exc:
                    result.errors.append(
                        f"Failed to create recipe '{recipe.name}': {exc}"
                    )

        return result

    def deploy_dataset(self, dataset: DataikuDataset) -> Dict[str, Any]:
        """Create a single dataset in DSS.

        Args:
            dataset: The DataikuDataset to create.

        Returns:
            A summary dict with ``name`` and ``type`` keys.
        """
        info = {
            "name": dataset.name,
            "type": dataset.dataset_type.value,
            "connection_type": dataset.connection_type.value,
        }

        if self.dry_run:
            logger.info("DRY RUN: would create dataset '%s'", dataset.name)
            return info

        self._ensure_connected()
        builder = self._project.new_managed_dataset(dataset.name)

        # Set connection type
        connection_type = dataset.connection_type.value
        builder.with_store_into(connection_type)

        ds_handle = builder.create()

        # Apply schema if available
        if dataset.schema:
            ds_def = ds_handle.get_definition()
            ds_def["schema"] = {
                "columns": [
                    {"name": col.name, "type": col.type}
                    for col in dataset.schema
                ],
                "userModified": False,
            }
            ds_handle.set_definition(ds_def)

        return info

    def deploy_recipe(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Create a single recipe in DSS.

        Uses the dataikuapi builder pattern::

            project.new_recipe(type)
                   .with_input(dataset)
                   .with_output(dataset)
                   .create()

        Args:
            recipe: The DataikuRecipe to create.

        Returns:
            A summary dict with ``name``, ``type``, ``inputs``, and ``outputs``.
        """
        dss_type = _get_dss_recipe_type(recipe.recipe_type)
        info = {
            "name": recipe.name,
            "type": dss_type,
            "inputs": recipe.inputs,
            "outputs": recipe.outputs,
        }

        if self.dry_run:
            logger.info("DRY RUN: would create recipe '%s' (%s)", recipe.name, dss_type)
            info["builder_args"] = self._get_recipe_builder_args(recipe)
            return info

        self._ensure_connected()
        builder = self._project.new_recipe(dss_type, recipe.name)

        # Wire inputs and outputs
        for inp in recipe.inputs:
            builder.with_input(inp)
        for out in recipe.outputs:
            builder.with_output(out)

        recipe_handle = builder.create()

        # Apply recipe-specific settings
        builder_args = self._get_recipe_builder_args(recipe)
        if builder_args:
            recipe_def = recipe_handle.get_definition()
            recipe_def.get_json_payload().update(builder_args)
            recipe_handle.set_definition(recipe_def)

        return info

    def _get_recipe_builder_args(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Extract dataikuapi builder arguments from a DataikuRecipe.

        If the recipe has a composed ``settings`` object with a
        ``to_dss_builder_args`` method, that is used. Otherwise falls
        back to ``recipe._build_settings()``.

        Args:
            recipe: The recipe to extract builder args from.

        Returns:
            Dictionary of settings suitable for the DSS API payload.
        """
        if recipe.settings is not None and hasattr(recipe.settings, "to_dss_builder_args"):
            return recipe.settings.to_dss_builder_args()

        return recipe._build_settings()
