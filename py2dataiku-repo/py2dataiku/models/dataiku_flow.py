"""Flow model for Dataiku DSS."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import yaml

from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType


@dataclass
class FlowRecommendation:
    """A recommendation for improving the flow."""

    type: str  # PERFORMANCE, RECIPE_CHOICE, CONSOLIDATION, etc.
    priority: str  # HIGH, MEDIUM, LOW
    message: str
    impact: Optional[str] = None
    action: Optional[str] = None
    source_lines: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "priority": self.priority,
            "message": self.message,
            "impact": self.impact,
            "action": self.action,
            "source_lines": self.source_lines,
        }


@dataclass
class ColumnLineage:
    """Lineage information for a column."""

    column: str
    final_dataset: str
    origin_dataset: str
    origin_column: str
    transformations: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "column": self.column,
            "final_dataset": self.final_dataset,
            "origin": {
                "dataset": self.origin_dataset,
                "column": self.origin_column,
            },
            "transformations": self.transformations,
        }


@dataclass
class DataikuFlow:
    """
    Represents a complete Dataiku flow (pipeline).

    A flow is a directed acyclic graph (DAG) of datasets connected by recipes.
    This is the main output of the py2dataiku conversion process.
    """

    name: str = "converted_flow"
    source_file: Optional[str] = None
    generation_timestamp: Optional[str] = None

    datasets: List[DataikuDataset] = field(default_factory=list)
    recipes: List[DataikuRecipe] = field(default_factory=list)

    recommendations: List[FlowRecommendation] = field(default_factory=list)
    optimization_notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.generation_timestamp:
            self.generation_timestamp = datetime.now().isoformat()

    # Dataset operations

    def add_dataset(self, dataset: DataikuDataset) -> None:
        """Add a dataset to the flow."""
        if not self._dataset_exists(dataset.name):
            self.datasets.append(dataset)

    def get_dataset(self, name: str) -> Optional[DataikuDataset]:
        """Get a dataset by name."""
        for ds in self.datasets:
            if ds.name == name:
                return ds
        return None

    def _dataset_exists(self, name: str) -> bool:
        """Check if a dataset exists."""
        return any(ds.name == name for ds in self.datasets)

    @property
    def input_datasets(self) -> List[DataikuDataset]:
        """Get all input datasets."""
        return [ds for ds in self.datasets if ds.dataset_type == DatasetType.INPUT]

    @property
    def output_datasets(self) -> List[DataikuDataset]:
        """Get all output datasets."""
        return [ds for ds in self.datasets if ds.dataset_type == DatasetType.OUTPUT]

    @property
    def intermediate_datasets(self) -> List[DataikuDataset]:
        """Get all intermediate datasets."""
        return [ds for ds in self.datasets if ds.dataset_type == DatasetType.INTERMEDIATE]

    # Recipe operations

    def add_recipe(self, recipe: DataikuRecipe) -> None:
        """Add a recipe to the flow."""
        self.recipes.append(recipe)
        # Ensure all input/output datasets exist
        for inp in recipe.inputs:
            if not self._dataset_exists(inp):
                self.add_dataset(DataikuDataset(name=inp, dataset_type=DatasetType.INPUT))
        for out in recipe.outputs:
            if not self._dataset_exists(out):
                self.add_dataset(DataikuDataset(name=out, dataset_type=DatasetType.INTERMEDIATE))

    def get_recipe(self, name: str) -> Optional[DataikuRecipe]:
        """Get a recipe by name."""
        for recipe in self.recipes:
            if recipe.name == name:
                return recipe
        return None

    def get_recipes_by_type(self, recipe_type: RecipeType) -> List[DataikuRecipe]:
        """Get all recipes of a specific type."""
        return [r for r in self.recipes if r.recipe_type == recipe_type]

    # Analysis methods

    def get_recommendations(self) -> List[FlowRecommendation]:
        """Get optimization recommendations for the flow."""
        return self.recommendations

    def add_recommendation(
        self,
        type: str,
        priority: str,
        message: str,
        impact: Optional[str] = None,
        action: Optional[str] = None,
    ) -> None:
        """Add a recommendation."""
        self.recommendations.append(
            FlowRecommendation(
                type=type,
                priority=priority,
                message=message,
                impact=impact,
                action=action,
            )
        )

    def get_column_lineage(self, column: str) -> Optional[ColumnLineage]:
        """Get lineage information for a column."""
        # This would require tracking column transformations through the flow
        # Placeholder implementation
        return None

    def validate(self) -> Dict[str, Any]:
        """Validate the flow structure."""
        errors = []
        warnings = []
        info = []

        # Check for orphan datasets
        referenced_datasets: Set[str] = set()
        for recipe in self.recipes:
            referenced_datasets.update(recipe.inputs)
            referenced_datasets.update(recipe.outputs)

        for ds in self.datasets:
            if ds.name not in referenced_datasets:
                warnings.append({
                    "type": "ORPHAN_DATASET",
                    "message": f"Dataset '{ds.name}' is not connected to any recipe",
                })

        # Check for missing datasets
        for recipe in self.recipes:
            for inp in recipe.inputs:
                if not self._dataset_exists(inp):
                    errors.append({
                        "type": "MISSING_DATASET",
                        "message": f"Recipe '{recipe.name}' references missing input '{inp}'",
                    })

        # Check for Python recipes
        python_recipes = self.get_recipes_by_type(RecipeType.PYTHON)
        for pr in python_recipes:
            info.append({
                "type": "PYTHON_FALLBACK",
                "message": f"Recipe '{pr.name}' requires Python recipe",
                "lines": pr.source_lines,
            })

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings + self.warnings,
            "info": info,
        }

    # Export methods

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "flow_name": self.name,
            "generated_from": self.source_file,
            "generation_timestamp": self.generation_timestamp,
            "total_recipes": len(self.recipes),
            "total_datasets": len(self.datasets),
            "datasets": [ds.to_dict() for ds in self.datasets],
            "recipes": [r.to_dict() for r in self.recipes],
            "optimization_notes": self.optimization_notes,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }

    def to_yaml(self) -> str:
        """Convert to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_recipe_configs(self) -> List[Dict[str, Any]]:
        """Get Dataiku API-compatible recipe configurations."""
        return [r.to_json() for r in self.recipes]

    def get_summary(self) -> str:
        """Get a text summary of the flow."""
        lines = [
            f"Flow: {self.name}",
            f"Source: {self.source_file or 'unknown'}",
            f"Generated: {self.generation_timestamp}",
            "",
            f"Datasets: {len(self.datasets)}",
            f"  - Input: {len(self.input_datasets)}",
            f"  - Intermediate: {len(self.intermediate_datasets)}",
            f"  - Output: {len(self.output_datasets)}",
            "",
            f"Recipes: {len(self.recipes)}",
        ]

        # Count by type
        type_counts: Dict[str, int] = {}
        for recipe in self.recipes:
            t = recipe.recipe_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        for t, count in sorted(type_counts.items()):
            lines.append(f"  - {t}: {count}")

        if self.optimization_notes:
            lines.append("")
            lines.append("Optimization Notes:")
            for note in self.optimization_notes:
                lines.append(f"  - {note}")

        if self.recommendations:
            lines.append("")
            lines.append(f"Recommendations: {len(self.recommendations)}")

        return "\n".join(lines)

    def export_all(self, directory: str) -> None:
        """Export all flow artifacts to a directory."""
        import os

        os.makedirs(directory, exist_ok=True)

        # Export flow summary
        with open(os.path.join(directory, "flow_summary.yaml"), "w") as f:
            f.write(self.to_yaml())

        # Export recipe configurations
        recipes_dir = os.path.join(directory, "recipes")
        os.makedirs(recipes_dir, exist_ok=True)
        for recipe in self.recipes:
            filepath = os.path.join(recipes_dir, f"{recipe.name}.json")
            with open(filepath, "w") as f:
                json.dump(recipe.to_json(), f, indent=2)

    # Visualization methods

    def visualize(self, format: str = "svg", **kwargs) -> str:
        """
        Generate a visual representation of the flow.

        Args:
            format: Output format - "svg", "ascii", "plantuml", "html", "mermaid"
            **kwargs: Additional arguments passed to the visualizer

        Returns:
            String containing the visualization in the requested format
        """
        if format == "mermaid":
            # Use existing diagram generator for backwards compatibility
            from py2dataiku.generators.diagram_generator import DiagramGenerator
            return DiagramGenerator().to_mermaid(self)

        from py2dataiku.visualizers import visualize_flow
        return visualize_flow(self, format=format, **kwargs)

    def to_svg(self, output_path: str = None) -> str:
        """
        Generate SVG visualization.

        Args:
            output_path: Optional file path to save the SVG

        Returns:
            SVG content as string
        """
        content = self.visualize(format="svg")
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return content

    def to_ascii(self) -> str:
        """Generate ASCII art visualization."""
        return self.visualize(format="ascii")

    def to_html(self, output_path: str = None) -> str:
        """
        Generate interactive HTML visualization.

        Args:
            output_path: Optional file path to save the HTML

        Returns:
            HTML content as string
        """
        content = self.visualize(format="html")
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return content

    def to_plantuml(self, output_path: str = None) -> str:
        """
        Generate PlantUML visualization.

        Args:
            output_path: Optional file path to save the PlantUML code

        Returns:
            PlantUML content as string
        """
        content = self.visualize(format="plantuml")
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return content

    def to_png(self, output_path: str, scale: float = 2.0) -> None:
        """
        Export flow as PNG image.

        Requires cairosvg package: pip install cairosvg

        Args:
            output_path: File path to save the PNG
            scale: Scale factor for resolution (default 2.0)
        """
        from py2dataiku.visualizers import SVGVisualizer
        visualizer = SVGVisualizer()
        visualizer.export_png(self, output_path, scale=scale)

    def to_pdf(self, output_path: str) -> None:
        """
        Export flow as PDF.

        Requires cairosvg package: pip install cairosvg

        Args:
            output_path: File path to save the PDF
        """
        from py2dataiku.visualizers import SVGVisualizer
        visualizer = SVGVisualizer()
        visualizer.export_pdf(self, output_path)

    def __repr__(self) -> str:
        return (
            f"DataikuFlow(name='{self.name}', "
            f"datasets={len(self.datasets)}, recipes={len(self.recipes)})"
        )
