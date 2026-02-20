"""Tests for py2dataiku visualizers."""

import pytest
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.visualizers import (
    SVGVisualizer,
    ASCIIVisualizer,
    PlantUMLVisualizer,
    HTMLVisualizer,
    InteractiveVisualizer,
    MermaidVisualizer,
    FlowVisualizer,
    visualize_flow,
    DataikuTheme,
    DATAIKU_LIGHT,
    DATAIKU_DARK,
)
from py2dataiku.visualizers.layout_engine import LayoutEngine, NodePosition, Edge
from py2dataiku.visualizers.icons import RecipeIcons
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType


# Fixtures

@pytest.fixture
def simple_flow():
    """Create a simple flow for testing."""
    flow = DataikuFlow(name="test_flow")

    # Add datasets
    flow.add_dataset(DataikuDataset(name="input_data", dataset_type=DatasetType.INPUT))
    flow.add_dataset(DataikuDataset(name="cleaned_data", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="output_data", dataset_type=DatasetType.OUTPUT))

    # Add recipes
    prepare_recipe = DataikuRecipe(
        name="prepare_1",
        recipe_type=RecipeType.PREPARE,
        inputs=["input_data"],
        outputs=["cleaned_data"],
    )
    flow.recipes.append(prepare_recipe)

    grouping_recipe = DataikuRecipe(
        name="grouping_1",
        recipe_type=RecipeType.GROUPING,
        inputs=["cleaned_data"],
        outputs=["output_data"],
    )
    flow.recipes.append(grouping_recipe)

    return flow


@pytest.fixture
def complex_flow():
    """Create a more complex flow with joins."""
    flow = DataikuFlow(name="complex_flow")

    # Input datasets
    flow.add_dataset(DataikuDataset(name="customers", dataset_type=DatasetType.INPUT))
    flow.add_dataset(DataikuDataset(name="orders", dataset_type=DatasetType.INPUT))

    # Intermediate
    flow.add_dataset(DataikuDataset(name="customers_clean", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="merged", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="summary", dataset_type=DatasetType.INTERMEDIATE))

    # Output
    flow.add_dataset(DataikuDataset(name="high_value", dataset_type=DatasetType.OUTPUT))

    # Recipes
    flow.recipes.append(DataikuRecipe(
        name="prepare_customers",
        recipe_type=RecipeType.PREPARE,
        inputs=["customers"],
        outputs=["customers_clean"],
    ))

    flow.recipes.append(DataikuRecipe(
        name="join_1",
        recipe_type=RecipeType.JOIN,
        inputs=["customers_clean", "orders"],
        outputs=["merged"],
    ))

    flow.recipes.append(DataikuRecipe(
        name="grouping_1",
        recipe_type=RecipeType.GROUPING,
        inputs=["merged"],
        outputs=["summary"],
    ))

    flow.recipes.append(DataikuRecipe(
        name="split_1",
        recipe_type=RecipeType.SPLIT,
        inputs=["summary"],
        outputs=["high_value"],
    ))

    return flow


# Theme Tests

class TestThemes:
    """Test theme configuration."""

    def test_default_theme(self):
        """Test default theme values."""
        theme = DATAIKU_LIGHT
        assert theme.name == "dataiku-light"
        assert theme.background_color == "#FAFAFA"
        assert theme.input_bg == "#E3F2FD"
        assert theme.output_bg == "#E8F5E9"

    def test_dark_theme(self):
        """Test dark theme values."""
        theme = DATAIKU_DARK
        assert theme.name == "dataiku-dark"
        assert theme.background_color == "#1E1E1E"

    def test_recipe_colors(self):
        """Test recipe color retrieval."""
        theme = DATAIKU_LIGHT
        colors = theme.get_recipe_colors("prepare")
        assert len(colors) == 3  # bg, border, text
        assert colors[0] == "#FFF3E0"  # orange background

    def test_unknown_recipe_type(self):
        """Test fallback for unknown recipe type."""
        theme = DATAIKU_LIGHT
        colors = theme.get_recipe_colors("unknown_type")
        assert colors == theme.recipe_colors["default"]


# Icons Tests

class TestIcons:
    """Test recipe icons."""

    def test_unicode_icons(self):
        """Test Unicode icon retrieval."""
        assert RecipeIcons.get_unicode("prepare") == "\u2699"  # ⚙
        assert RecipeIcons.get_unicode("join") == "\u22c8"  # ⋈
        assert RecipeIcons.get_unicode("grouping") == "\u03a3"  # Σ

    def test_labels(self):
        """Test label retrieval."""
        assert RecipeIcons.get_label("prepare") == "Prepare"
        assert RecipeIcons.get_label("join") == "Join"
        assert RecipeIcons.get_label("grouping") == "Grouping"

    def test_ascii_icons(self):
        """Test ASCII icon retrieval."""
        assert RecipeIcons.get_ascii("prepare") == "[*]"
        assert RecipeIcons.get_ascii("join") == "[><]"

    def test_unknown_icon(self):
        """Test fallback for unknown recipe type."""
        assert RecipeIcons.get_unicode("unknown") == RecipeIcons.UNICODE["default"]


# Layout Engine Tests

class TestLayoutEngine:
    """Test layout engine."""

    def test_simple_layout(self, simple_flow):
        """Test layout calculation for simple flow."""
        engine = LayoutEngine()
        positions = engine.calculate_layout(simple_flow)

        assert len(positions) > 0
        # Should have positions for datasets and recipes
        assert any(p.node_type == "dataset" for p in positions.values())
        assert any(p.node_type == "recipe" for p in positions.values())

    def test_layer_assignment(self, simple_flow):
        """Test that nodes are assigned to layers."""
        engine = LayoutEngine()
        positions = engine.calculate_layout(simple_flow)

        layers = set(p.layer for p in positions.values())
        assert len(layers) > 1  # Should have multiple layers

    def test_position_bounds(self, simple_flow):
        """Test canvas bounds calculation."""
        engine = LayoutEngine()
        engine.calculate_layout(simple_flow)

        min_x, min_y, max_x, max_y = engine.get_bounds()
        assert max_x > min_x
        assert max_y > min_y

    def test_canvas_size(self, simple_flow):
        """Test canvas size calculation."""
        engine = LayoutEngine()
        engine.calculate_layout(simple_flow)

        width, height = engine.get_canvas_size()
        assert width >= 400
        assert height >= 200

    def test_edges(self, simple_flow):
        """Test edge extraction."""
        engine = LayoutEngine()
        engine.calculate_layout(simple_flow)

        edges = engine.get_edges()
        assert len(edges) > 0


# SVG Visualizer Tests

class TestSVGVisualizer:
    """Test SVG visualization."""

    def test_render_simple_flow(self, simple_flow):
        """Test SVG rendering of simple flow."""
        visualizer = SVGVisualizer()
        svg = visualizer.render(simple_flow)

        assert svg.startswith("<svg")
        assert "</svg>" in svg
        assert "xmlns" in svg

    def test_svg_contains_nodes(self, simple_flow):
        """Test that SVG contains node elements."""
        visualizer = SVGVisualizer()
        svg = visualizer.render(simple_flow)

        assert "input_data" in svg
        assert "cleaned_data" in svg
        assert "output_data" in svg

    def test_svg_contains_recipes(self, simple_flow):
        """Test that SVG contains recipe elements."""
        visualizer = SVGVisualizer()
        svg = visualizer.render(simple_flow)

        assert "Prepare" in svg or "prepare" in svg
        assert "Grouping" in svg or "grouping" in svg

    def test_svg_with_custom_theme(self, simple_flow):
        """Test SVG with dark theme."""
        visualizer = SVGVisualizer(theme=DATAIKU_DARK)
        svg = visualizer.render(simple_flow)

        assert "#1E1E1E" in svg  # Dark background

    def test_svg_defs(self, simple_flow):
        """Test SVG contains definitions."""
        visualizer = SVGVisualizer()
        svg = visualizer.render(simple_flow)

        assert "<defs>" in svg
        assert "filter" in svg
        assert "marker" in svg


# ASCII Visualizer Tests

class TestASCIIVisualizer:
    """Test ASCII visualization."""

    def test_render_simple_flow(self, simple_flow):
        """Test ASCII rendering of simple flow."""
        visualizer = ASCIIVisualizer()
        ascii_art = visualizer.render(simple_flow)

        assert len(ascii_art) > 0
        assert "DATAIKU FLOW" in ascii_art

    def test_ascii_contains_nodes(self, simple_flow):
        """Test that ASCII contains node names."""
        visualizer = ASCIIVisualizer()
        ascii_art = visualizer.render(simple_flow)

        assert "input_data" in ascii_art
        assert "output_data" in ascii_art

    def test_ascii_contains_legend(self, simple_flow):
        """Test that ASCII contains legend."""
        visualizer = ASCIIVisualizer()
        ascii_art = visualizer.render(simple_flow)

        assert "Legend" in ascii_art

    def test_compact_render(self, simple_flow):
        """Test compact ASCII rendering."""
        visualizer = ASCIIVisualizer()
        compact = visualizer.render_compact(simple_flow)

        assert "-->" in compact


# PlantUML Visualizer Tests

class TestPlantUMLVisualizer:
    """Test PlantUML visualization."""

    def test_render_simple_flow(self, simple_flow):
        """Test PlantUML rendering."""
        visualizer = PlantUMLVisualizer()
        plantuml = visualizer.render(simple_flow)

        assert "@startuml" in plantuml
        assert "@enduml" in plantuml

    def test_plantuml_contains_nodes(self, simple_flow):
        """Test that PlantUML contains node declarations."""
        visualizer = PlantUMLVisualizer()
        plantuml = visualizer.render(simple_flow)

        assert "rectangle" in plantuml
        assert "card" in plantuml

    def test_plantuml_contains_arrows(self, simple_flow):
        """Test that PlantUML contains connections."""
        visualizer = PlantUMLVisualizer()
        plantuml = visualizer.render(simple_flow)

        assert "-->" in plantuml

    def test_plantuml_styling(self, simple_flow):
        """Test that PlantUML contains styling."""
        visualizer = PlantUMLVisualizer()
        plantuml = visualizer.render(simple_flow)

        assert "skinparam" in plantuml


# HTML Visualizer Tests

class TestHTMLVisualizer:
    """Test HTML visualization."""

    def test_render_simple_flow(self, simple_flow):
        """Test HTML rendering."""
        visualizer = HTMLVisualizer()
        html = visualizer.render(simple_flow)

        assert "<!DOCTYPE html>" in html
        assert "<canvas" in html
        assert "</html>" in html

    def test_html_contains_javascript(self, simple_flow):
        """Test that HTML contains JavaScript."""
        visualizer = HTMLVisualizer()
        html = visualizer.render(simple_flow)

        assert "<script>" in html
        assert "const nodes" in html
        assert "const edges" in html

    def test_html_contains_theme(self, simple_flow):
        """Test that HTML contains theme configuration."""
        visualizer = HTMLVisualizer()
        html = visualizer.render(simple_flow)

        assert "const theme" in html

    def test_html_interactive_features(self, simple_flow):
        """Test that HTML has interactive features."""
        visualizer = HTMLVisualizer()
        html = visualizer.render(simple_flow)

        assert "tooltip" in html
        assert "mousemove" in html
        assert "legend" in html


# Integration Tests

class TestVisualizationIntegration:
    """Integration tests for visualization."""

    def test_visualize_flow_function(self, simple_flow):
        """Test visualize_flow convenience function."""
        svg = visualize_flow(simple_flow, format="svg")
        assert "<svg" in svg

        ascii_art = visualize_flow(simple_flow, format="ascii")
        assert "DATAIKU FLOW" in ascii_art

        html = visualize_flow(simple_flow, format="html")
        assert "<canvas" in html

    def test_flow_visualization_methods(self, simple_flow):
        """Test DataikuFlow visualization methods."""
        svg = simple_flow.to_svg()
        assert "<svg" in svg

        ascii_art = simple_flow.to_ascii()
        assert "DATAIKU FLOW" in ascii_art

        html = simple_flow.to_html()
        assert "<canvas" in html

        plantuml = simple_flow.to_plantuml()
        assert "@startuml" in plantuml

    def test_flow_visualize_method(self, simple_flow):
        """Test DataikuFlow.visualize() method."""
        svg = simple_flow.visualize(format="svg")
        assert "<svg" in svg

        # Mermaid should still work
        mermaid = simple_flow.visualize(format="mermaid")
        assert "flowchart" in mermaid

    def test_complex_flow_visualization(self, complex_flow):
        """Test visualization of complex flow with multiple inputs."""
        svg = complex_flow.to_svg()
        assert "<svg" in svg
        assert "customers" in svg
        assert "orders" in svg
        assert "Join" in svg or "join" in svg

    def test_unknown_format_raises_error(self, simple_flow):
        """Test that unknown format raises ValueError."""
        with pytest.raises(ValueError):
            visualize_flow(simple_flow, format="unknown")


# Edge Cases

class TestEdgeCases:
    """Test edge cases."""

    def test_empty_flow(self):
        """Test visualization of empty flow."""
        flow = DataikuFlow(name="empty_flow")

        # Should not raise
        svg = flow.to_svg()
        assert "<svg" in svg

    def test_single_dataset_flow(self):
        """Test flow with single dataset."""
        flow = DataikuFlow(name="single")
        flow.add_dataset(DataikuDataset(name="only_dataset", dataset_type=DatasetType.INPUT))

        svg = flow.to_svg()
        assert "only_dataset" in svg

    def test_long_names(self):
        """Test handling of long dataset/recipe names."""
        flow = DataikuFlow(name="long_names")
        flow.add_dataset(DataikuDataset(
            name="this_is_a_very_long_dataset_name_that_should_be_truncated",
            dataset_type=DatasetType.INPUT
        ))

        svg = flow.to_svg()
        assert "<svg" in svg  # Should render without error

    def test_special_characters_in_names(self):
        """Test handling of special characters."""
        flow = DataikuFlow(name="special-chars_flow")
        flow.add_dataset(DataikuDataset(
            name="data-with-dashes",
            dataset_type=DatasetType.INPUT
        ))

        plantuml = flow.to_plantuml()
        assert "@startuml" in plantuml  # Should render without error


# Interactive Visualizer Tests

class TestInteractiveVisualizer:
    """Test interactive HTML visualization."""

    def test_render_simple_flow(self, simple_flow):
        """Test interactive HTML rendering."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "<!DOCTYPE html>" in html
        assert "<canvas" in html
        assert "</html>" in html

    def test_interactive_contains_search(self, simple_flow):
        """Test that interactive HTML contains search functionality."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "searchInput" in html
        assert "handleSearch" in html

    def test_interactive_contains_zoom(self, simple_flow):
        """Test that interactive HTML contains zoom controls."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "zoomIn" in html
        assert "zoomOut" in html
        assert "fitToScreen" in html
        assert "zoomLevel" in html

    def test_interactive_contains_details_panel(self, simple_flow):
        """Test that interactive HTML contains details panel."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "detailsPanel" in html
        assert "showDetailsPanel" in html
        assert "closePanel" in html

    def test_interactive_contains_node_data(self, simple_flow):
        """Test that interactive HTML embeds node data as JSON."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "const nodes" in html
        assert "const edges" in html
        assert "const theme" in html
        assert "const stats" in html

    def test_interactive_contains_export_functions(self, simple_flow):
        """Test that interactive HTML contains export functions."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "exportSVG" in html
        assert "exportPNG" in html

    def test_interactive_contains_keyboard_shortcuts(self, simple_flow):
        """Test that interactive HTML has keyboard shortcut handling."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "handleKeyboard" in html
        assert "Escape" in html

    def test_interactive_with_dark_theme(self, simple_flow):
        """Test interactive rendering with dark theme."""
        visualizer = InteractiveVisualizer(theme=DATAIKU_DARK)
        html = visualizer.render(simple_flow)

        assert "<!DOCTYPE html>" in html
        assert "<canvas" in html

    def test_interactive_with_complex_flow(self, complex_flow):
        """Test interactive rendering with complex flow."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(complex_flow)

        assert "customers" in html
        assert "orders" in html

    def test_interactive_stats_json(self, simple_flow):
        """Test that stats JSON is correctly embedded."""
        visualizer = InteractiveVisualizer()
        html = visualizer.render(simple_flow)

        assert "totalDatasets" in html
        assert "totalRecipes" in html
        assert "inputDatasets" in html

    def test_interactive_flow_with_steps(self):
        """Test interactive rendering with a recipe that has steps."""
        flow = DataikuFlow(name="steps_flow")
        flow.add_dataset(DataikuDataset(name="in", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="out", dataset_type=DatasetType.OUTPUT))
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            steps=[
                PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={"column": "a", "new_name": "b"}),
                PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE, params={"column": "x", "value": 0}),
            ],
        )
        flow.recipes.append(recipe)

        visualizer = InteractiveVisualizer()
        html = visualizer.render(flow)
        assert "<!DOCTYPE html>" in html
        assert "stepCount" in html


# Mermaid Visualizer Tests

class TestMermaidVisualizer:
    """Test Mermaid diagram visualization."""

    def test_render_simple_flow(self, simple_flow):
        """Test Mermaid rendering of simple flow."""
        visualizer = MermaidVisualizer()
        mermaid = visualizer.render(simple_flow)

        assert "flowchart" in mermaid

    def test_mermaid_contains_nodes(self, simple_flow):
        """Test that Mermaid contains node declarations."""
        visualizer = MermaidVisualizer()
        mermaid = visualizer.render(simple_flow)

        assert "input_data" in mermaid
        assert "output_data" in mermaid

    def test_mermaid_contains_connections(self, simple_flow):
        """Test that Mermaid contains connection arrows."""
        visualizer = MermaidVisualizer()
        mermaid = visualizer.render(simple_flow)

        assert "-->" in mermaid

    def test_mermaid_with_complex_flow(self, complex_flow):
        """Test Mermaid rendering with complex flow."""
        visualizer = MermaidVisualizer()
        mermaid = visualizer.render(complex_flow)

        assert "customers" in mermaid
        assert "orders" in mermaid

    def test_mermaid_via_visualize_flow(self, simple_flow):
        """Test Mermaid via visualize_flow convenience function."""
        mermaid = visualize_flow(simple_flow, format="mermaid")
        assert "flowchart" in mermaid


# visualize_flow Additional Format Tests

class TestVisualizeFlowFormats:
    """Test visualize_flow with all supported formats."""

    def test_interactive_format(self, simple_flow):
        """Test interactive format via visualize_flow."""
        html = visualize_flow(simple_flow, format="interactive")
        assert "<!DOCTYPE html>" in html
        assert "searchInput" in html

    def test_mermaid_format(self, simple_flow):
        """Test mermaid format via visualize_flow."""
        mermaid = visualize_flow(simple_flow, format="mermaid")
        assert "flowchart" in mermaid

    def test_all_formats_produce_output(self, simple_flow):
        """Test that all formats produce non-empty output."""
        for fmt in ["svg", "ascii", "plantuml", "html", "interactive", "mermaid"]:
            result = visualize_flow(simple_flow, format=fmt)
            assert len(result) > 0, f"Format {fmt} produced empty output"

    def test_theme_kwarg_passed_through(self, simple_flow):
        """Test that theme kwarg is passed through to visualizers."""
        svg = visualize_flow(simple_flow, format="svg", theme=DATAIKU_DARK)
        assert "#1E1E1E" in svg


# Layout Engine Additional Tests

class TestLayoutEngineDetailed:
    """Additional layout engine tests."""

    def test_node_position_properties(self):
        """Test NodePosition computed properties."""
        pos = NodePosition(
            x=10, y=20, width=100, height=50,
            layer=0, node_type="dataset",
            node_id="test", label="Test",
        )
        assert pos.center_x == 60.0
        assert pos.center_y == 45.0
        assert pos.right == 110.0
        assert pos.bottom == 70.0

    def test_edge_dataclass(self):
        """Test Edge dataclass."""
        edge = Edge(source="a", target="b", label="connects")
        assert edge.source == "a"
        assert edge.target == "b"
        assert edge.label == "connects"

    def test_edge_no_label(self):
        """Test Edge with no label."""
        edge = Edge(source="a", target="b")
        assert edge.label is None

    def test_empty_flow_bounds(self):
        """Test bounds for empty layout."""
        engine = LayoutEngine()
        bounds = engine.get_bounds()
        assert bounds == (0, 0, 100, 100)

    def test_custom_spacing(self, simple_flow):
        """Test layout with custom spacing parameters."""
        engine = LayoutEngine(
            layer_spacing=300,
            node_spacing=200,
            dataset_width=200,
            dataset_height=80,
        )
        positions = engine.calculate_layout(simple_flow)
        assert len(positions) > 0

        # Larger spacing should produce larger canvas
        width, height = engine.get_canvas_size()
        assert width > 400

    def test_complex_flow_multiple_layers(self, complex_flow):
        """Test that complex flow produces multiple layers."""
        engine = LayoutEngine()
        positions = engine.calculate_layout(complex_flow)

        layers = set(p.layer for p in positions.values())
        assert len(layers) >= 3  # At minimum: input, recipe, output

    def test_disconnected_nodes_handled(self):
        """Test that disconnected nodes don't crash layout."""
        flow = DataikuFlow(name="disconnected")
        flow.add_dataset(DataikuDataset(name="island1", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="island2", dataset_type=DatasetType.INPUT))
        # No recipes connecting them

        engine = LayoutEngine()
        positions = engine.calculate_layout(flow)
        assert len(positions) == 2


# FlowVisualizer Base Class Tests

class TestFlowVisualizerBase:
    """Test FlowVisualizer abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that FlowVisualizer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FlowVisualizer()

    def test_default_theme(self):
        """Test that default theme is DATAIKU_LIGHT."""
        visualizer = SVGVisualizer()
        assert visualizer.theme == DATAIKU_LIGHT

    def test_custom_theme(self):
        """Test that custom theme is applied."""
        visualizer = SVGVisualizer(theme=DATAIKU_DARK)
        assert visualizer.theme == DATAIKU_DARK

    def test_save_method(self, simple_flow, tmp_path):
        """Test that save method writes to file."""
        visualizer = SVGVisualizer()
        output_path = str(tmp_path / "test_output.svg")
        visualizer.save(simple_flow, output_path)

        with open(output_path, 'r') as f:
            content = f.read()
        assert "<svg" in content

    def test_save_ascii(self, simple_flow, tmp_path):
        """Test saving ASCII visualization."""
        visualizer = ASCIIVisualizer()
        output_path = str(tmp_path / "test_output.txt")
        visualizer.save(simple_flow, output_path)

        with open(output_path, 'r') as f:
            content = f.read()
        assert "DATAIKU FLOW" in content


# Recipe Icons Additional Tests

class TestRecipeIconsDetailed:
    """Additional tests for recipe icons."""

    def test_all_recipe_types_have_unicode(self):
        """Test that all standard recipe types have Unicode icons."""
        recipe_types = ["prepare", "join", "grouping", "split", "sort",
                       "distinct", "stack", "python", "window"]
        for rt in recipe_types:
            icon = RecipeIcons.get_unicode(rt)
            assert icon is not None
            assert len(icon) > 0

    def test_all_recipe_types_have_ascii(self):
        """Test that all standard recipe types have ASCII icons."""
        recipe_types = ["prepare", "join", "grouping", "split", "sort",
                       "distinct", "stack", "python", "window"]
        for rt in recipe_types:
            icon = RecipeIcons.get_ascii(rt)
            assert icon is not None
            assert len(icon) > 0

    def test_all_recipe_types_have_labels(self):
        """Test that all standard recipe types have labels."""
        recipe_types = ["prepare", "join", "grouping", "split", "sort",
                       "distinct", "stack", "python", "window"]
        for rt in recipe_types:
            label = RecipeIcons.get_label(rt)
            assert label is not None
            assert len(label) > 0

    def test_default_fallback(self):
        """Test fallback for completely unknown type."""
        icon = RecipeIcons.get_unicode("nonexistent_type_xyz")
        assert icon == RecipeIcons.UNICODE["default"]


# Theme Additional Tests

class TestThemeDetailed:
    """Additional theme tests."""

    def test_all_recipe_colors_have_three_values(self):
        """Test that all recipe colors have bg, border, text."""
        for recipe_type, colors in DATAIKU_LIGHT.recipe_colors.items():
            assert len(colors) == 3, f"Recipe type {recipe_type} missing color values"

    def test_dark_theme_recipe_colors(self):
        """Test dark theme also has recipe colors."""
        assert len(DATAIKU_DARK.recipe_colors) > 0
        for recipe_type, colors in DATAIKU_DARK.recipe_colors.items():
            assert len(colors) == 3

    def test_theme_spacing_attributes(self):
        """Test that theme has spacing attributes for layout."""
        theme = DATAIKU_LIGHT
        assert hasattr(theme, 'layer_spacing')
        assert hasattr(theme, 'node_spacing')
        assert hasattr(theme, 'dataset_width')
        assert hasattr(theme, 'dataset_height')
        assert hasattr(theme, 'recipe_size')
        assert hasattr(theme, 'padding')

    def test_theme_font_attributes(self):
        """Test that theme has font attributes."""
        theme = DATAIKU_LIGHT
        assert hasattr(theme, 'font_family')
        assert hasattr(theme, 'dataset_font_size')
        assert hasattr(theme, 'recipe_font_size')
        assert hasattr(theme, 'icon_font_size')
