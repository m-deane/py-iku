"""Dataiku DSS project exporter.

This module exports py2dataiku flows to Dataiku DSS-compatible project format
that can be imported directly into a DSS instance.

DSS Project Structure:
    project/
    ├── project.json           # Project metadata
    ├── params.json            # Project parameters
    ├── datasets/
    │   ├── dataset1.json      # Dataset configurations
    │   └── dataset2.json
    ├── recipes/
    │   ├── recipe1.json       # Recipe configurations
    │   └── recipe2.json
    └── flow/
        └── zones.json         # Flow zone configuration

Usage:
    >>> from py2dataiku.exporters import DSSExporter, export_to_dss
    >>> exporter = DSSExporter(flow, project_key="MY_PROJECT")
    >>> exporter.export("./output")
    >>>
    >>> # Or use convenience function
    >>> export_to_dss(flow, "./output", project_key="MY_PROJECT")
"""

import json
import os
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType


@dataclass
class DSSProjectConfig:
    """Configuration for DSS project export."""

    project_key: str = "CONVERTED_PROJECT"
    project_name: str = "Converted Python Pipeline"
    owner: str = "py2dataiku"
    description: str = "Auto-generated from Python code using py2dataiku"
    tags: List[str] = field(default_factory=lambda: ["py2dataiku", "auto-generated"])

    # Dataset defaults
    default_connection: str = "filesystem_managed"
    default_format: str = "csv"

    # Recipe defaults
    include_code_comments: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "projectKey": self.project_key,
            "name": self.project_name,
            "owner": self.owner,
            "description": self.description,
            "tags": self.tags,
        }


class DSSExporter:
    """
    Export py2dataiku flows to Dataiku DSS project format.

    This exporter generates all necessary configuration files for a
    DSS project that can be imported via the DSS UI or API.
    """

    def __init__(
        self,
        flow: DataikuFlow,
        project_key: str = None,
        config: DSSProjectConfig = None,
    ):
        """
        Initialize the exporter.

        Args:
            flow: DataikuFlow to export
            project_key: DSS project key (letters, numbers, underscores)
            config: Full project configuration
        """
        self.flow = flow
        self.config = config or DSSProjectConfig()
        if project_key:
            self.config.project_key = project_key.upper().replace("-", "_")

    def export(self, output_dir: str, create_zip: bool = False) -> str:
        """
        Export the flow to DSS project format.

        Args:
            output_dir: Directory to create the project in
            create_zip: Whether to create a zip file for import

        Returns:
            Path to the exported project (directory or zip file)
        """
        project_dir = os.path.join(output_dir, self.config.project_key)
        os.makedirs(project_dir, exist_ok=True)

        # Create directory structure
        dirs = ["datasets", "recipes", "flow"]
        for d in dirs:
            os.makedirs(os.path.join(project_dir, d), exist_ok=True)

        # Export project metadata
        self._export_project_json(project_dir)
        self._export_params_json(project_dir)

        # Export datasets
        for dataset in self.flow.datasets:
            self._export_dataset(project_dir, dataset)

        # Export recipes
        for recipe in self.flow.recipes:
            self._export_recipe(project_dir, recipe)

        # Export flow zones
        self._export_flow_zones(project_dir)

        # Export summary
        self._export_summary(project_dir)

        if create_zip:
            zip_path = f"{project_dir}.zip"
            self._create_zip(project_dir, zip_path)
            return zip_path

        return project_dir

    def _export_project_json(self, project_dir: str) -> None:
        """Export project.json metadata file."""
        project_json = {
            "projectKey": self.config.project_key,
            "name": self.config.project_name,
            "owner": self.config.owner,
            "permissions": [],
            "additionalDashboardUsers": {"users": []},
            "projectStatus": "Sandbox",
            "projectAppType": "REGULAR",
            "disableAutomaticTriggers": False,
            "integrations": {},
            "exposedObjects": {"objects": []},
            "settings": {
                "flowAnchorSourcesAndSinks": True,
                "flowDisplaySettings": {
                    "zonesGraphRenderingAlgorithm": "DOT_LAYOUT"
                },
                "gitCommitMode": "AUTO",
                "gitMode": "PROJECT_ONLY"
            },
            "versionTag": {
                "versionNumber": 1,
                "lastModifiedBy": {"login": self.config.owner},
                "lastModifiedOn": int(datetime.now().timestamp() * 1000),
            },
            "creationTag": {
                "versionNumber": 0,
                "lastModifiedBy": {"login": self.config.owner},
                "lastModifiedOn": int(datetime.now().timestamp() * 1000),
            },
            "description": self.config.description,
            "shortDesc": f"Generated by py2dataiku from {self.flow.name}",
            "tags": self.config.tags,
            "customFields": {},
            "checklists": {"checklists": []},
        }

        path = os.path.join(project_dir, "project.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(project_json, f, indent=2)

    def _export_params_json(self, project_dir: str) -> None:
        """Export params.json for project variables."""
        params = {
            "projectVariables": {
                "standard": {},
                "local": {},
            },
            "projectResourcesStorage": {"cleanPolicy": "KEEP_ALL"},
        }

        path = os.path.join(project_dir, "params.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)

    def _export_dataset(self, project_dir: str, dataset: DataikuDataset) -> None:
        """Export a single dataset configuration."""
        dataset_json = self._build_dataset_config(dataset)

        path = os.path.join(project_dir, "datasets", f"{dataset.name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dataset_json, f, indent=2)

    def _build_dataset_config(self, dataset: DataikuDataset) -> Dict[str, Any]:
        """Build DSS-compatible dataset configuration."""
        # Determine managed vs filesystem
        is_input = dataset.dataset_type == DatasetType.INPUT

        dataset_json = {
            "type": "Filesystem" if is_input else "Managed",
            "managed": not is_input,
            "name": dataset.name,
            "projectKey": self.config.project_key,
            "formatType": self.config.default_format,
            "formatParams": self._get_format_params(self.config.default_format),
            "partitioning": {"dimensions": []},
            "flowOptions": {
                "virtualizable": False,
                "rebuildBehavior": "NORMAL",
                "crossProjectBuildBehavior": "DEFAULT",
            },
            "readWriteOptions": {},
            "versionTag": {
                "versionNumber": 1,
                "lastModifiedBy": {"login": self.config.owner},
                "lastModifiedOn": int(datetime.now().timestamp() * 1000),
            },
            "creationTag": {
                "versionNumber": 0,
                "lastModifiedBy": {"login": self.config.owner},
                "lastModifiedOn": int(datetime.now().timestamp() * 1000),
            },
            "tags": [],
            "params": {},
        }

        # Add connection settings
        if is_input:
            dataset_json["params"] = {
                "connection": self.config.default_connection,
                "path": f"/{dataset.name}",
                "filesSelectionRules": {
                    "mode": "ALL",
                    "excludeRules": [],
                    "includeRules": [],
                    "explicitFiles": [],
                }
            }
        else:
            dataset_json["params"] = {
                "connection": self.config.default_connection,
            }

        # Add schema if available
        if dataset.schema:
            dataset_json["schema"] = {
                "columns": [
                    {"name": col.get("name", ""), "type": col.get("type", "string")}
                    for col in dataset.schema
                ],
                "userModified": False,
            }

        return dataset_json

    def _get_format_params(self, format_type: str) -> Dict[str, Any]:
        """Get format parameters for a dataset."""
        if format_type.lower() == "csv":
            return {
                "style": "unix",
                "charset": "utf8",
                "separator": ",",
                "quoteChar": '"',
                "escapeChar": "\\",
                "dateSerializationFormat": "ISO",
                "arrayMapFormat": "json",
                "hiveSeparators": ["\x02", "\x03", "\x04", "\x05", "\x06", "\x07", "\x08"],
                "skipRowsBeforeHeader": 0,
                "parseHeaderRow": True,
                "skipRowsAfterHeader": 0,
                "probableNumberOfRecords": 0,
                "normalizeBooleans": False,
                "normalizeDoubles": True,
                "readAdditionalColumnsBehavior": "INSERT_IN_DATA_WARNING",
                "readMissingColumnsBehavior": "DISCARD_SILENT",
                "readDataTypeMismatchBehavior": "DISCARD_WARNING",
                "writeDataTypeMismatchBehavior": "DISCARD_WARNING",
                "fileReadFailureBehavior": "FAIL",
                "compress": "",
            }
        elif format_type.lower() == "parquet":
            return {
                "compression": "SNAPPY",
                "readDataTypeMismatchBehavior": "DISCARD_WARNING",
            }
        return {}

    def _export_recipe(self, project_dir: str, recipe: DataikuRecipe) -> None:
        """Export a single recipe configuration."""
        recipe_json = self._build_recipe_config(recipe)

        path = os.path.join(project_dir, "recipes", f"{recipe.name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(recipe_json, f, indent=2)

    def _build_recipe_config(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build DSS-compatible recipe configuration."""
        base_config = {
            "name": recipe.name,
            "projectKey": self.config.project_key,
            "type": self._get_dss_recipe_type(recipe.recipe_type),
            "inputs": {self._get_input_role(recipe.recipe_type): self._format_io_items(recipe.inputs)},
            "outputs": {self._get_output_role(recipe.recipe_type): self._format_io_items(recipe.outputs)},
            "versionTag": {
                "versionNumber": 1,
                "lastModifiedBy": {"login": self.config.owner},
                "lastModifiedOn": int(datetime.now().timestamp() * 1000),
            },
            "creationTag": {
                "versionNumber": 0,
                "lastModifiedBy": {"login": self.config.owner},
                "lastModifiedOn": int(datetime.now().timestamp() * 1000),
            },
            "tags": [],
            "customMeta": {
                "kpiByLabels": {}
            },
        }

        # Add recipe-specific payload
        payload = self._build_recipe_payload(recipe)
        if payload:
            base_config["params"] = payload

        return base_config

    def _get_dss_recipe_type(self, recipe_type: RecipeType) -> str:
        """Map RecipeType to DSS recipe type string."""
        type_map = {
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
        }
        return type_map.get(recipe_type, "python")

    def _get_input_role(self, recipe_type: RecipeType) -> str:
        """Get the input role name for a recipe type."""
        if recipe_type == RecipeType.JOIN:
            return "main"
        return "main"

    def _get_output_role(self, recipe_type: RecipeType) -> str:
        """Get the output role name for a recipe type."""
        return "main"

    def _format_io_items(self, names: List[str]) -> Dict[str, Any]:
        """Format input/output items for DSS recipe."""
        return {
            "items": [{"ref": name, "deps": []} for name in names]
        }

    def _build_recipe_payload(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build the recipe-specific payload."""
        if recipe.recipe_type == RecipeType.PREPARE:
            return self._build_prepare_payload(recipe)
        elif recipe.recipe_type == RecipeType.JOIN:
            return self._build_join_payload(recipe)
        elif recipe.recipe_type == RecipeType.GROUPING:
            return self._build_grouping_payload(recipe)
        elif recipe.recipe_type == RecipeType.SORT:
            return self._build_sort_payload(recipe)
        elif recipe.recipe_type == RecipeType.DISTINCT:
            return self._build_distinct_payload(recipe)
        elif recipe.recipe_type == RecipeType.PYTHON:
            return self._build_python_payload(recipe)
        return {}

    def _build_prepare_payload(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build Prepare recipe payload with steps."""
        steps = []
        for step in recipe.steps:
            step_config = {
                "metaType": step.meta_type,
                "type": step.processor_type.value if hasattr(step.processor_type, 'value') else str(step.processor_type),
                "disabled": step.disabled,
                "params": step.params,
            }
            steps.append(step_config)

        return {
            "mode": "BATCH",
            "steps": steps,
            "maxJobsPerCategory": {
                "PREPARE_FILTERING": 1,
                "PREPARE_PARSING": 1,
                "PREPARE_OTHERS": 1,
                "PREPARE_MERGE_COLUMNS": 1,
                "PREPARE_RESHAPING": 1,
                "PREPARE_EXPLODE": 1,
            },
            "engineParams": {
                "hive": {
                    "skipPrerunValidate": False,
                    "hiveconf": [],
                    "inheritConf": "default",
                    "addDkuUdf": False,
                    "executionEngine": "HIVESERVER2",
                },
                "sqlPipelineParams": {"pipelineAllowMerge": True, "pipelineAllowStart": True},
                "impala": {"forceStreamMode": True},
                "spark": {
                    "inheritConf": "default",
                    "sparkConf": [],
                },
                "dkuHadoop": {
                    "inheritConf": "default",
                },
            },
            "columnsSelection": {
                "mode": "ALL",
            },
            "virtualInputs": [],
            "filterExpression": {},
        }

    def _build_join_payload(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build Join recipe payload."""
        join_params = recipe.parameters if hasattr(recipe, 'parameters') else {}
        return {
            "mode": "LEFT",
            "engineParams": {
                "hive": {"skipPrerunValidate": False, "hiveconf": [], "inheritConf": "default"},
                "sqlPipelineParams": {"pipelineAllowMerge": True, "pipelineAllowStart": True},
                "impala": {"forceStreamMode": True},
                "spark": {"inheritConf": "default", "sparkConf": []},
            },
            "virtualInputs": [
                {"index": i, "computedColumns": [], "originLabel": f"input_{i}"}
                for i in range(len(recipe.inputs))
            ],
            "joins": [{
                "table1": 0,
                "table2": 1,
                "conditionsMode": "AND",
                "type": join_params.get("how", "LEFT").upper(),
                "on": join_params.get("on", []),
                "outerJoinOnTheLeft": True,
            }] if len(recipe.inputs) > 1 else [],
            "preFilter": {},
            "postFilter": {},
            "enableAutoCastInJoinConditions": False,
            "computedColumns": [],
            "selectedColumns": [],
            "outputColumnsSelectionMode": "MANUAL",
        }

    def _build_grouping_payload(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build Grouping recipe payload."""
        params = recipe.parameters if hasattr(recipe, 'parameters') else {}
        keys = params.get("keys", [])
        aggregations = params.get("aggregations", {})

        return {
            "engineParams": {
                "hive": {"skipPrerunValidate": False, "hiveconf": [], "inheritConf": "default"},
                "sqlPipelineParams": {"pipelineAllowMerge": True, "pipelineAllowStart": True},
                "impala": {"forceStreamMode": True},
                "spark": {"inheritConf": "default", "sparkConf": []},
            },
            "keys": [{"column": k, "type": "string"} for k in keys],
            "values": [
                {"column": col, "type": "string", "$idx": i, "function": agg.upper()}
                for i, (col, agg) in enumerate(aggregations.items())
            ],
            "globalCount": False,
            "preFilter": {},
            "postFilter": {},
            "computedColumns": [],
        }

    def _build_sort_payload(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build Sort recipe payload."""
        params = recipe.parameters if hasattr(recipe, 'parameters') else {}
        return {
            "engineParams": {
                "hive": {"skipPrerunValidate": False, "hiveconf": [], "inheritConf": "default"},
                "sqlPipelineParams": {"pipelineAllowMerge": True, "pipelineAllowStart": True},
                "impala": {"forceStreamMode": True},
                "spark": {"inheritConf": "default", "sparkConf": []},
            },
            "orders": [
                {"column": col, "desc": not params.get("ascending", True)}
                for col in params.get("columns", [])
            ],
            "preFilter": {},
            "computedColumns": [],
        }

    def _build_distinct_payload(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build Distinct recipe payload."""
        return {
            "engineParams": {
                "hive": {"skipPrerunValidate": False, "hiveconf": [], "inheritConf": "default"},
                "sqlPipelineParams": {"pipelineAllowMerge": True, "pipelineAllowStart": True},
                "impala": {"forceStreamMode": True},
                "spark": {"inheritConf": "default", "sparkConf": []},
            },
            "columns": [],
            "preFilter": {},
            "computedColumns": [],
            "postFilter": {},
        }

    def _build_python_payload(self, recipe: DataikuRecipe) -> Dict[str, Any]:
        """Build Python recipe payload."""
        code = recipe.parameters.get("code", "") if hasattr(recipe, 'parameters') else ""

        # Add py2dataiku comment if enabled
        if self.config.include_code_comments and recipe.notes:
            comment_lines = ["# Generated by py2dataiku"]
            comment_lines.extend([f"# {note}" for note in recipe.notes])
            code = "\n".join(comment_lines) + "\n\n" + code

        return {
            "code": code,
            "envSelection": {"envMode": "INHERIT"},
            "pythonParams": {
                "pythonVersion": "python3",
                "runAsUser": False,
            },
        }

    def _export_flow_zones(self, project_dir: str) -> None:
        """Export flow zone configuration."""
        zones = {
            "zones": [{
                "id": "default",
                "name": "Default",
                "color": "#2980b9",
                "items": [],
            }],
            "zonesOrder": ["default"],
        }

        path = os.path.join(project_dir, "flow", "zones.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(zones, f, indent=2)

    def _export_summary(self, project_dir: str) -> None:
        """Export a human-readable summary."""
        summary = [
            f"# DSS Project Export: {self.config.project_key}",
            "",
            f"Generated: {datetime.now().isoformat()}",
            f"Source: {self.flow.source_file or 'Python code'}",
            "",
            "## Contents",
            "",
            f"- Datasets: {len(self.flow.datasets)}",
            f"- Recipes: {len(self.flow.recipes)}",
            "",
            "## Import Instructions",
            "",
            "### Via DSS UI",
            "1. Go to Administration > Projects",
            "2. Click 'Import project from a bundle'",
            "3. Upload the zip file or select the folder",
            "4. Configure project settings if needed",
            "",
            "### Via DSS API",
            "```python",
            "import dataiku",
            "client = dataiku.Client()",
            f"client.create_project_from_bundle('{self.config.project_key}')",
            "```",
            "",
        ]

        if self.flow.recommendations:
            summary.extend([
                "## Recommendations",
                "",
            ])
            for rec in self.flow.recommendations:
                summary.append(f"- [{rec.priority}] {rec.message}")
            summary.append("")

        path = os.path.join(project_dir, "README.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(summary))

    def _create_zip(self, source_dir: str, zip_path: str) -> None:
        """Create a zip file from the project directory."""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)

    def get_api_bundle(self) -> Dict[str, Any]:
        """
        Get a bundle suitable for DSS API import.

        Returns:
            Dictionary containing all project configuration
        """
        return {
            "projectKey": self.config.project_key,
            "projectName": self.config.project_name,
            "datasets": [self._build_dataset_config(ds) for ds in self.flow.datasets],
            "recipes": [self._build_recipe_config(r) for r in self.flow.recipes],
            "metadata": {
                "generatedBy": "py2dataiku",
                "sourceFlow": self.flow.name,
                "timestamp": datetime.now().isoformat(),
            },
        }


def export_to_dss(
    flow: DataikuFlow,
    output_dir: str,
    project_key: str = None,
    create_zip: bool = False,
    **kwargs
) -> str:
    """
    Convenience function to export a flow to DSS format.

    Args:
        flow: DataikuFlow to export
        output_dir: Directory to create the project in
        project_key: DSS project key
        create_zip: Whether to create a zip file
        **kwargs: Additional configuration options

    Returns:
        Path to the exported project

    Example:
        >>> from py2dataiku import convert
        >>> from py2dataiku.exporters import export_to_dss
        >>> flow = convert(code)
        >>> export_to_dss(flow, "./output", project_key="MY_PROJECT")
    """
    config = DSSProjectConfig(project_key=project_key or "CONVERTED_PROJECT", **kwargs)
    exporter = DSSExporter(flow, config=config)
    return exporter.export(output_dir, create_zip=create_zip)
