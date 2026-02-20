"""Base class for flow generators."""

from abc import ABC, abstractmethod
from typing import Optional

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import RecipeType


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
        """Sanitize a name for use as a dataset/recipe name."""
        return (
            name.replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
            .replace("'", "")
        )

    def _optimize_flow(self) -> None:
        """Optimize the generated flow."""
        self._merge_prepare_recipes()

        # Add recipe type counts as optimization notes
        recipe_counts: dict[str, int] = {}
        for recipe in self.flow.recipes:
            t = recipe.recipe_type.value
            recipe_counts[t] = recipe_counts.get(t, 0) + 1

        for rtype, count in recipe_counts.items():
            self.flow.optimization_notes.append(f"{rtype}: {count} recipe(s)")

    def _merge_prepare_recipes(self) -> None:
        """Merge consecutive Prepare recipes when possible.

        This is a simplified implementation.
        Full implementation would rebuild the flow graph.
        """
        pass
