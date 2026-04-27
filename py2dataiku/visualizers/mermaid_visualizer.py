"""Mermaid diagram visualizer for Dataiku flows.

Emits a left-to-right ``graph LR`` diagram. Recipe nodes are styled per
recipe-type family using ``classDef`` directives that mirror the SVG / PNG
DSS-fidelity palette: blue for PREPARE, orange for JOIN, green for GROUPING,
gold for ML, etc. Each emitted recipe carries a ``class my_recipe joinRecipe;``
declaration that resolves to a ``classDef joinRecipe fill:#f29222,...``.
"""

from collections import defaultdict
from typing import Optional

from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.themes import DataikuTheme


# Recipe-type -> CSS-safe class name suffix used in classDef declarations.
# We keep this stable across releases so user-authored Mermaid theme
# overrides keep working.
_CLASS_SUFFIX = {
    "prepare": "prepareRecipe",
    "join": "joinRecipe",
    "fuzzyjoin": "fuzzyJoinRecipe",
    "fuzzy_join": "fuzzyJoinRecipe",
    "geojoin": "geoJoinRecipe",
    "geo_join": "geoJoinRecipe",
    "grouping": "groupingRecipe",
    "window": "windowRecipe",
    "split": "splitRecipe",
    "stack": "stackRecipe",
    "sort": "sortRecipe",
    "distinct": "distinctRecipe",
    "top_n": "topNRecipe",
    "topn": "topNRecipe",
    "pivot": "pivotRecipe",
    "sampling": "samplingRecipe",
    "sample": "samplingRecipe",
    "sync": "syncRecipe",
    "filter": "filterRecipe",
    "download": "downloadRecipe",
    "generate_features": "generateFeaturesRecipe",
    "generate_statistics": "generateStatisticsRecipe",
    "python": "pythonRecipe",
    "r": "rRecipe",
    "sql": "sqlRecipe",
    "sql_script": "sqlRecipe",
    "hive": "hiveRecipe",
    "impala": "impalaRecipe",
    "pyspark": "sparkRecipe",
    "sparksql": "sparkRecipe",
    "spark_sql_query": "sparkRecipe",
    "spark_scala": "sparkRecipe",
    "sparkr": "sparkRecipe",
    "shell": "shellRecipe",
    "prediction_scoring": "mlRecipe",
    "clustering_scoring": "mlRecipe",
    "evaluation": "mlRecipe",
    "standalone_evaluation": "mlRecipe",
    "ai_assistant_generate": "aiRecipe",
    "default": "defaultRecipe",
}


class MermaidVisualizer(FlowVisualizer):
    """Generate Mermaid diagram syntax for Dataiku flows."""

    def __init__(self, theme: Optional[DataikuTheme] = None):
        super().__init__(theme=theme)

    def render(self, flow) -> str:
        """Render the flow as a Mermaid diagram with zone subgraphs."""
        lines = ["graph LR"]

        # Build zone membership lookup
        zone_datasets = {}
        zone_recipes = {}
        has_zones = hasattr(flow, 'zones') and flow.zones

        if has_zones:
            for zone in flow.zones:
                for d in zone.datasets:
                    zone_datasets[d] = zone.name
                for r in zone.recipes:
                    zone_recipes[r] = zone.name

        zone_nodes = defaultdict(list)
        recipe_class_assignments: list[tuple[str, str]] = []  # (safe_id, css class)

        for dataset in flow.datasets:
            node_str = self._dataset_node(dataset)
            zone = zone_datasets.get(dataset.name, "__unzoned__")
            zone_nodes[zone].append(node_str)

        for recipe in flow.recipes:
            node_str, css_class = self._recipe_node(recipe)
            zone = zone_recipes.get(recipe.name, "__unzoned__")
            zone_nodes[zone].append(node_str)
            recipe_class_assignments.append((self._safe_id(recipe.name), css_class))

        # Subgraphs for named zones
        if has_zones:
            for zone in flow.zones:
                safe_id = zone.name.replace(" ", "_")
                lines.append(f"  subgraph {safe_id}[{zone.name}]")
                for node in zone_nodes.get(zone.name, []):
                    lines.append(f"    {node}")
                lines.append("  end")

        # Top-level / unzoned nodes
        for node in zone_nodes.get("__unzoned__", []):
            lines.append(f"  {node}")

        # Edges
        for recipe in flow.recipes:
            recipe_id = self._safe_id(recipe.name)
            for inp in recipe.inputs:
                inp_ref = inp.get("ref", inp) if isinstance(inp, dict) else inp
                lines.append(f"  {self._safe_id(inp_ref)} --> {recipe_id}")
            for out in recipe.outputs:
                out_ref = out.get("ref", out) if isinstance(out, dict) else out
                lines.append(f"  {recipe_id} --> {self._safe_id(out_ref)}")

        # ClassDefs — per recipe-type family
        used_classes = {cls for _, cls in recipe_class_assignments}
        for css_class in sorted(used_classes):
            lines.append(self._class_def(css_class))

        # Class assignments per recipe node
        for safe_id, css_class in recipe_class_assignments:
            lines.append(f"  class {safe_id} {css_class};")

        return "\n".join(lines)

    def _safe_id(self, name: str) -> str:
        return name.replace(" ", "_").replace("-", "_")

    def _dataset_node(self, dataset) -> str:
        safe = self._safe_id(dataset.name)
        return f'{safe}["{dataset.name}"]'

    def _recipe_node(self, recipe) -> tuple[str, str]:
        safe = self._safe_id(recipe.name)
        recipe_type = recipe.recipe_type.value if hasattr(recipe.recipe_type, 'value') else str(recipe.recipe_type)
        css_class = _CLASS_SUFFIX.get(recipe_type, _CLASS_SUFFIX["default"])
        return f'{safe}{{"{recipe.name}\\n{recipe_type}"}}', css_class

    def _class_def(self, css_class: str) -> str:
        """Emit a Mermaid classDef matching the recipe-type's palette."""
        # Reverse-lookup the recipe key for this class.
        recipe_key = next(
            (k for k, v in _CLASS_SUFFIX.items() if v == css_class),
            "default",
        )
        fill, stroke, icon_color = self.theme.get_recipe_palette(recipe_key)
        return (
            f"  classDef {css_class} fill:{fill},stroke:{stroke},"
            f"color:{icon_color},stroke-width:2px;"
        )
