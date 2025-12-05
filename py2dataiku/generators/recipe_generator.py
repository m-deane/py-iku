"""Generate individual Dataiku recipe configurations."""

from typing import Any, Dict, List

from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.prepare_step import PrepareStep


class RecipeGenerator:
    """
    Generate Dataiku recipe configurations.

    This class provides utilities for creating properly formatted
    Dataiku recipe JSON configurations.
    """

    @staticmethod
    def generate_prepare(
        name: str,
        input_dataset: str,
        output_dataset: str,
        steps: List[PrepareStep],
    ) -> Dict[str, Any]:
        """Generate a Prepare recipe configuration."""
        return {
            "type": "prepare",
            "name": name,
            "inputs": [{"ref": input_dataset}],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "mode": "NORMAL",
                "steps": [step.to_json() for step in steps],
            },
        }

    @staticmethod
    def generate_join(
        name: str,
        left_dataset: str,
        right_dataset: str,
        output_dataset: str,
        join_type: str,
        join_conditions: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Generate a Join recipe configuration."""
        return {
            "type": "join",
            "name": name,
            "inputs": [
                {"ref": left_dataset, "role": "left"},
                {"ref": right_dataset, "role": "right"},
            ],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "joinType": join_type,
                "joins": [
                    {
                        "left": {"column": cond["left"]},
                        "right": {"column": cond["right"]},
                        "matchType": cond.get("matchType", "EXACT"),
                    }
                    for cond in join_conditions
                ],
            },
        }

    @staticmethod
    def generate_grouping(
        name: str,
        input_dataset: str,
        output_dataset: str,
        keys: List[str],
        aggregations: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Generate a Grouping recipe configuration."""
        return {
            "type": "grouping",
            "name": name,
            "inputs": [{"ref": input_dataset}],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "keys": [{"column": k} for k in keys],
                "aggregations": [
                    {
                        "column": agg["column"],
                        "type": agg["function"],
                        "outputColumn": agg.get("outputColumn"),
                    }
                    for agg in aggregations
                ],
                "globalCount": False,
            },
        }

    @staticmethod
    def generate_stack(
        name: str,
        input_datasets: List[str],
        output_dataset: str,
    ) -> Dict[str, Any]:
        """Generate a Stack recipe configuration."""
        return {
            "type": "stack",
            "name": name,
            "inputs": [{"ref": ds} for ds in input_datasets],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "mode": "UNION",
            },
        }

    @staticmethod
    def generate_split(
        name: str,
        input_dataset: str,
        output_datasets: List[str],
        condition: str,
    ) -> Dict[str, Any]:
        """Generate a Split recipe configuration."""
        return {
            "type": "split",
            "name": name,
            "inputs": [{"ref": input_dataset}],
            "outputs": [{"ref": ds} for ds in output_datasets],
            "settings": {
                "splitMode": "FILTER",
                "condition": condition,
            },
        }

    @staticmethod
    def generate_python(
        name: str,
        input_datasets: List[str],
        output_datasets: List[str],
        code: str,
    ) -> Dict[str, Any]:
        """Generate a Python recipe configuration."""
        return {
            "type": "python",
            "name": name,
            "inputs": [{"ref": ds} for ds in input_datasets],
            "outputs": [{"ref": ds} for ds in output_datasets],
            "settings": {
                "code": code,
            },
        }

    @staticmethod
    def generate_window(
        name: str,
        input_dataset: str,
        output_dataset: str,
        partition_columns: List[str],
        order_columns: List[str],
        aggregations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a Window recipe configuration."""
        return {
            "type": "window",
            "name": name,
            "inputs": [{"ref": input_dataset}],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "partitionColumns": [{"column": c} for c in partition_columns],
                "orderColumns": [{"column": c} for c in order_columns],
                "aggregations": aggregations,
            },
        }

    @staticmethod
    def generate_sort(
        name: str,
        input_dataset: str,
        output_dataset: str,
        sort_columns: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Generate a Sort recipe configuration."""
        return {
            "type": "sort",
            "name": name,
            "inputs": [{"ref": input_dataset}],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "sortColumns": sort_columns,
            },
        }

    @staticmethod
    def generate_distinct(
        name: str,
        input_dataset: str,
        output_dataset: str,
    ) -> Dict[str, Any]:
        """Generate a Distinct recipe configuration."""
        return {
            "type": "distinct",
            "name": name,
            "inputs": [{"ref": input_dataset}],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "computeCount": False,
            },
        }

    @staticmethod
    def generate_sampling(
        name: str,
        input_dataset: str,
        output_dataset: str,
        sampling_method: str = "RANDOM_FIXED_RATIO",
        ratio: float = 0.1,
    ) -> Dict[str, Any]:
        """Generate a Sampling recipe configuration."""
        return {
            "type": "sampling",
            "name": name,
            "inputs": [{"ref": input_dataset}],
            "outputs": [{"ref": output_dataset}],
            "settings": {
                "samplingMethod": sampling_method,
                "ratio": ratio,
            },
        }
