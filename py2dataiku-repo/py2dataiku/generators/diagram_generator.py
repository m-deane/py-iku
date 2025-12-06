"""Generate visual flow diagrams from Dataiku flows."""

from typing import Dict, List, Optional, Set

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType


class DiagramGenerator:
    """
    Generate visual representations of Dataiku flows.

    Supports multiple output formats:
    - Mermaid (for Markdown/GitHub)
    - GraphViz DOT
    - ASCII art
    - PlantUML
    """

    # Recipe type colors for Mermaid
    RECIPE_COLORS = {
        RecipeType.PREPARE: "#fff3e0",
        RecipeType.JOIN: "#e3f2fd",
        RecipeType.GROUPING: "#e8f5e9",
        RecipeType.SPLIT: "#fce4ec",
        RecipeType.STACK: "#f3e5f5",
        RecipeType.PYTHON: "#ffccbc",
        RecipeType.WINDOW: "#e0f7fa",
        RecipeType.SORT: "#f5f5f5",
        RecipeType.DISTINCT: "#fff8e1",
        RecipeType.TOP_N: "#efebe9",
    }

    # Dataset type colors
    DATASET_COLORS = {
        DatasetType.INPUT: "#e1f5fe",
        DatasetType.OUTPUT: "#c8e6c9",
        DatasetType.INTERMEDIATE: "#f5f5f5",
    }

    def to_mermaid(self, flow: DataikuFlow) -> str:
        """
        Generate Mermaid diagram syntax.

        Example output:
        ```mermaid
        flowchart LR
            A[(raw_data)] --> B{Prepare}
            B --> C[(cleaned_data)]
        ```
        """
        lines = ["flowchart TD"]

        # Create node IDs
        dataset_ids: Dict[str, str] = {}
        recipe_ids: Dict[str, str] = {}

        # Generate dataset node IDs
        for i, ds in enumerate(flow.datasets):
            dataset_ids[ds.name] = f"D{i}"

        # Generate recipe node IDs
        for i, recipe in enumerate(flow.recipes):
            recipe_ids[recipe.name] = f"R{i}"

        # Add subgraphs for organization
        input_datasets = [ds for ds in flow.datasets if ds.dataset_type == DatasetType.INPUT]
        output_datasets = [ds for ds in flow.datasets if ds.dataset_type == DatasetType.OUTPUT]

        if input_datasets:
            lines.append("    subgraph inputs[Input Datasets]")
            for ds in input_datasets:
                node_id = dataset_ids[ds.name]
                lines.append(f"        {node_id}[({ds.name})]")
            lines.append("    end")

        if output_datasets:
            lines.append("    subgraph outputs[Output Datasets]")
            for ds in output_datasets:
                node_id = dataset_ids[ds.name]
                lines.append(f"        {node_id}[({ds.name})]")
            lines.append("    end")

        # Add intermediate datasets
        intermediate = [ds for ds in flow.datasets if ds.dataset_type == DatasetType.INTERMEDIATE]
        for ds in intermediate:
            node_id = dataset_ids[ds.name]
            lines.append(f"    {node_id}[({ds.name})]")

        # Add recipe nodes
        for recipe in flow.recipes:
            node_id = recipe_ids[recipe.name]
            label = self._get_recipe_label(recipe)
            lines.append(f"    {node_id}{{{label}}}")

        # Add edges
        for recipe in flow.recipes:
            recipe_id = recipe_ids[recipe.name]
            # Input edges
            for inp in recipe.inputs:
                if inp in dataset_ids:
                    lines.append(f"    {dataset_ids[inp]} --> {recipe_id}")
            # Output edges
            for out in recipe.outputs:
                if out in dataset_ids:
                    lines.append(f"    {recipe_id} --> {dataset_ids[out]}")

        # Add styling
        lines.append("")
        for ds in input_datasets:
            lines.append(f"    style {dataset_ids[ds.name]} fill:{self.DATASET_COLORS[DatasetType.INPUT]}")
        for ds in output_datasets:
            lines.append(f"    style {dataset_ids[ds.name]} fill:{self.DATASET_COLORS[DatasetType.OUTPUT]}")
        for recipe in flow.recipes:
            color = self.RECIPE_COLORS.get(recipe.recipe_type, "#ffffff")
            lines.append(f"    style {recipe_ids[recipe.name]} fill:{color}")

        return "\n".join(lines)

    def to_graphviz(self, flow: DataikuFlow) -> str:
        """
        Generate GraphViz DOT syntax.

        Can be rendered with: dot -Tpng flow.dot -o flow.png
        """
        lines = [
            "digraph DataikuFlow {",
            "    rankdir=LR;",
            "    node [fontname=\"Arial\"];",
            "",
            "    // Datasets",
        ]

        # Add datasets
        for ds in flow.datasets:
            shape = "cylinder"
            color = {
                DatasetType.INPUT: "lightblue",
                DatasetType.OUTPUT: "lightgreen",
                DatasetType.INTERMEDIATE: "white",
            }.get(ds.dataset_type, "white")
            lines.append(
                f"    \"{ds.name}\" [shape={shape}, style=filled, fillcolor={color}];"
            )

        lines.append("")
        lines.append("    // Recipes")

        # Add recipes
        for recipe in flow.recipes:
            shape = "diamond"
            color = {
                RecipeType.PREPARE: "moccasin",
                RecipeType.JOIN: "lightcyan",
                RecipeType.GROUPING: "honeydew",
                RecipeType.PYTHON: "mistyrose",
            }.get(recipe.recipe_type, "white")
            label = self._get_recipe_label(recipe)
            lines.append(
                f"    \"{recipe.name}\" [shape={shape}, style=filled, fillcolor={color}, label=\"{label}\"];"
            )

        lines.append("")
        lines.append("    // Edges")

        # Add edges
        for recipe in flow.recipes:
            for inp in recipe.inputs:
                lines.append(f"    \"{inp}\" -> \"{recipe.name}\";")
            for out in recipe.outputs:
                lines.append(f"    \"{recipe.name}\" -> \"{out}\";")

        lines.append("}")
        return "\n".join(lines)

    def to_ascii(self, flow: DataikuFlow) -> str:
        """
        Generate ASCII art diagram for terminal display.

        Example:
        ┌─────────────┐     ┌─────────┐     ┌──────────────┐
        │ raw_customers│────▶│ Prepare │────▶│cleaned_data  │
        └─────────────┘     └─────────┘     └──────────────┘
        """
        if not flow.recipes:
            return "Empty flow - no recipes"

        lines = []
        processed: Set[str] = set()

        # Find starting datasets (inputs with no upstream recipes)
        start_datasets = set()
        for ds in flow.datasets:
            if ds.dataset_type == DatasetType.INPUT:
                start_datasets.add(ds.name)

        # Build adjacency
        recipe_outputs: Dict[str, List[str]] = {}
        for recipe in flow.recipes:
            for out in recipe.outputs:
                recipe_outputs[out] = recipe.inputs

        # Process each path
        for start in sorted(start_datasets):
            path_lines = self._build_ascii_path(flow, start, processed)
            lines.extend(path_lines)
            lines.append("")

        return "\n".join(lines)

    def _build_ascii_path(
        self, flow: DataikuFlow, start: str, processed: Set[str]
    ) -> List[str]:
        """Build ASCII representation of a single path."""
        lines = []
        current = start

        while current and current not in processed:
            processed.add(current)

            # Find recipe that uses this as input
            recipe = None
            for r in flow.recipes:
                if current in r.inputs:
                    recipe = r
                    break

            if recipe:
                # Draw: dataset -> recipe -> output
                ds_box = self._ascii_box(current, "dataset")
                recipe_box = self._ascii_box(self._get_recipe_label(recipe), "recipe")

                if recipe.outputs:
                    out_box = self._ascii_box(recipe.outputs[0], "dataset")
                    lines.append(f"{ds_box}────▶{recipe_box}────▶{out_box}")
                    current = recipe.outputs[0]
                else:
                    lines.append(f"{ds_box}────▶{recipe_box}")
                    current = None
            else:
                # Terminal dataset
                ds_box = self._ascii_box(current, "dataset")
                lines.append(ds_box)
                current = None

        return lines

    def _ascii_box(self, text: str, box_type: str = "dataset") -> str:
        """Create an ASCII box around text."""
        width = len(text) + 2
        if box_type == "dataset":
            return f"[{text}]"
        else:
            return f"{{{text}}}"

    def to_plantuml(self, flow: DataikuFlow) -> str:
        """Generate PlantUML activity diagram syntax."""
        lines = [
            "@startuml",
            "!theme plain",
            "skinparam backgroundColor white",
            "",
        ]

        # Add datasets as states
        for ds in flow.datasets:
            if ds.dataset_type == DatasetType.INPUT:
                lines.append(f"state \"{ds.name}\" as {self._sanitize_id(ds.name)} <<input>>")
            elif ds.dataset_type == DatasetType.OUTPUT:
                lines.append(f"state \"{ds.name}\" as {self._sanitize_id(ds.name)} <<output>>")
            else:
                lines.append(f"state \"{ds.name}\" as {self._sanitize_id(ds.name)}")

        lines.append("")

        # Add recipes as choices/activities
        for recipe in flow.recipes:
            label = self._get_recipe_label(recipe)
            lines.append(f"state \"{label}\" as {self._sanitize_id(recipe.name)} <<recipe>>")

        lines.append("")

        # Add transitions
        for recipe in flow.recipes:
            recipe_id = self._sanitize_id(recipe.name)
            for inp in recipe.inputs:
                lines.append(f"{self._sanitize_id(inp)} --> {recipe_id}")
            for out in recipe.outputs:
                lines.append(f"{recipe_id} --> {self._sanitize_id(out)}")

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def _get_recipe_label(self, recipe: DataikuRecipe) -> str:
        """Get display label for a recipe."""
        rtype = recipe.recipe_type.value.title()
        if recipe.recipe_type == RecipeType.PREPARE:
            return f"{rtype}\\n({len(recipe.steps)} steps)"
        elif recipe.recipe_type == RecipeType.GROUPING:
            return f"{rtype}\\n({len(recipe.aggregations)} aggs)"
        elif recipe.recipe_type == RecipeType.JOIN:
            return f"{rtype}\\n({recipe.join_type.value})"
        return rtype

    def _sanitize_id(self, name: str) -> str:
        """Sanitize a name for use as an ID."""
        return name.replace(" ", "_").replace("-", "_").replace(".", "_")

    def save_png(self, flow: DataikuFlow, path: str) -> None:
        """
        Render and save as PNG image.

        Requires graphviz to be installed.
        """
        try:
            import graphviz
        except ImportError:
            raise ImportError("graphviz package required: pip install graphviz")

        dot_source = self.to_graphviz(flow)
        graph = graphviz.Source(dot_source)
        # Remove .png extension if present
        if path.endswith(".png"):
            path = path[:-4]
        graph.render(path, format="png", cleanup=True)

    def save_svg(self, flow: DataikuFlow, path: str) -> None:
        """
        Render and save as SVG.

        Requires graphviz to be installed.
        """
        try:
            import graphviz
        except ImportError:
            raise ImportError("graphviz package required: pip install graphviz")

        dot_source = self.to_graphviz(flow)
        graph = graphviz.Source(dot_source)
        if path.endswith(".svg"):
            path = path[:-4]
        graph.render(path, format="svg", cleanup=True)

    def save_mermaid_md(self, flow: DataikuFlow, path: str) -> None:
        """Save Mermaid diagram as Markdown file."""
        content = f"""# Dataiku Flow: {flow.name}

## Flow Diagram

```mermaid
{self.to_mermaid(flow)}
```

## Summary

{flow.get_summary()}
"""
        with open(path, "w") as f:
            f.write(content)
