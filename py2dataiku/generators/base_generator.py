"""Base class for flow generators."""

from abc import ABC, abstractmethod
from typing import Optional

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.optimizer.flow_optimizer import FlowOptimizer
from py2dataiku.optimizer.recipe_merger import RecipeMerger


class BaseFlowGenerator(ABC):
    """
    Abstract base class for flow generators.

    Provides shared infrastructure and utility methods used by both
    the rule-based FlowGenerator and the LLM-based LLMFlowGenerator.
    """

    def __init__(self):
        self.flow: Optional[DataikuFlow] = None
        self.recipe_counter = 0

    @abstractmethod
    def generate(self, *args, **kwargs) -> DataikuFlow:
        """Generate a DataikuFlow. Subclasses define the input type."""
        ...

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use as a dataset/recipe name.

        Dataiku dataset names must contain only alphanumeric characters and
        underscores, and must not start with a digit.
        """
        import re

        # Strip surrounding quotes
        name = name.strip("'\"")

        # Extract column name from subscript patterns like df['name'] or df["col"]
        subscript_match = re.match(r"^(\w+)\[(['\"]?)(.+?)\2\]$", name)
        if subscript_match:
            name = subscript_match.group(3)

        # Replace common separators and special chars with underscores
        name = (
            name.replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
            .replace("'", "")
            .replace('"', "")
            .replace("[", "_")
            .replace("]", "")
            .replace("(", "")
            .replace(")", "")
            .replace("/", "_")
        )

        # Remove any remaining non-alphanumeric/underscore characters
        name = re.sub(r"[^a-zA-Z0-9_]", "", name)

        # Collapse multiple consecutive underscores
        name = re.sub(r"_+", "_", name)

        # Strip leading/trailing underscores
        name = name.strip("_")

        # Must not start with a digit
        if name and name[0].isdigit():
            name = f"ds_{name}"

        # Fallback for empty names
        if not name:
            name = "dataset"

        return name

    def _optimize_flow(self) -> None:
        """Optimize the generated flow using FlowOptimizer.

        Applies recipe merging, orphan dataset removal, step reordering,
        and redundant step elimination via FlowOptimizer and RecipeMerger.
        """
        optimizer = FlowOptimizer()
        optimizer.optimize(self.flow, apply=True)

        # Optimize individual Prepare recipe steps
        self._optimize_prepare_steps()

        # Add recipe type counts as optimization notes
        recipe_counts: dict[str, int] = {}
        for recipe in self.flow.recipes:
            t = recipe.recipe_type.value
            recipe_counts[t] = recipe_counts.get(t, 0) + 1

        for rtype, count in recipe_counts.items():
            self.flow.optimization_notes.append(f"{rtype}: {count} recipe(s)")

    def _optimize_prepare_steps(self) -> None:
        """Optimize steps within each Prepare recipe.

        Applies RecipeMerger.remove_redundant_steps() to eliminate
        contradictory steps, then RecipeMerger.optimize_prepare_steps()
        to reorder remaining steps for efficiency.
        """
        for recipe in self.flow.recipes:
            if recipe.recipe_type == RecipeType.PREPARE and recipe.steps:
                steps = RecipeMerger.remove_redundant_steps(recipe.steps)
                steps = RecipeMerger.optimize_prepare_steps(steps)
                recipe.steps = steps
