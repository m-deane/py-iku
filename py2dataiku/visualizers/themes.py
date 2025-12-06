"""
Visual themes for Dataiku flow visualization.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class DataikuTheme:
    """Visual theme matching Dataiku DSS interface."""

    name: str = "dataiku-light"

    # Dataset colors by type
    input_bg: str = "#E3F2FD"
    input_border: str = "#4A90D9"
    input_text: str = "#1565C0"

    output_bg: str = "#E8F5E9"
    output_border: str = "#43A047"
    output_text: str = "#2E7D32"

    intermediate_bg: str = "#ECEFF1"
    intermediate_border: str = "#78909C"
    intermediate_text: str = "#455A64"

    error_bg: str = "#FFEBEE"
    error_border: str = "#E53935"
    error_text: str = "#C62828"

    # Recipe colors by type (background, border)
    recipe_colors: Dict[str, Tuple[str, str, str]] = field(default_factory=lambda: {
        "prepare": ("#FFF3E0", "#FF9800", "#E65100"),
        "join": ("#E3F2FD", "#2196F3", "#1565C0"),
        "stack": ("#F3E5F5", "#9C27B0", "#6A1B9A"),
        "grouping": ("#E8F5E9", "#4CAF50", "#2E7D32"),
        "window": ("#E0F7FA", "#00BCD4", "#00838F"),
        "split": ("#FCE4EC", "#E91E63", "#AD1457"),
        "sort": ("#FFFDE7", "#FFC107", "#FF8F00"),
        "distinct": ("#EFEBE9", "#795548", "#4E342E"),
        "filter": ("#FBE9E7", "#FF5722", "#D84315"),
        "python": ("#E8EAF6", "#3F51B5", "#283593"),
        "sync": ("#ECEFF1", "#607D8B", "#37474F"),
        "sample": ("#F1F8E9", "#8BC34A", "#558B2F"),
        "pivot": ("#E1F5FE", "#03A9F4", "#0277BD"),
        "top_n": ("#FFF8E1", "#FFB300", "#FF6F00"),
        "default": ("#F5F5F5", "#9E9E9E", "#616161"),
    })

    # Connection styling
    connection_color: str = "#90A4AE"
    connection_hover: str = "#1976D2"
    connection_width: int = 2
    arrow_size: int = 8

    # Typography
    font_family: str = "Arial, Helvetica, sans-serif"
    dataset_font_size: int = 13
    recipe_font_size: int = 11
    icon_font_size: int = 20

    # Dimensions
    dataset_width: int = 160
    dataset_height: int = 50
    dataset_radius: int = 6
    recipe_size: int = 70
    recipe_radius: int = 10

    # Layout spacing
    layer_spacing: int = 180
    node_spacing: int = 100
    padding: int = 40

    # Background
    background_color: str = "#FAFAFA"
    grid_color: str = "#E0E0E0"
    show_grid: bool = False

    def get_recipe_colors(self, recipe_type: str) -> Tuple[str, str, str]:
        """Get colors for a recipe type (bg, border, text)."""
        recipe_type = recipe_type.lower().replace(" ", "_")
        return self.recipe_colors.get(recipe_type, self.recipe_colors["default"])


# Predefined themes
DATAIKU_LIGHT = DataikuTheme(name="dataiku-light")

DATAIKU_DARK = DataikuTheme(
    name="dataiku-dark",
    background_color="#1E1E1E",
    grid_color="#333333",
    input_bg="#1E3A5F",
    input_border="#4A90D9",
    input_text="#90CAF9",
    output_bg="#1B3D1B",
    output_border="#43A047",
    output_text="#A5D6A7",
    intermediate_bg="#2D2D2D",
    intermediate_border="#78909C",
    intermediate_text="#B0BEC5",
    connection_color="#546E7A",
    recipe_colors={
        "prepare": ("#3E2723", "#FF9800", "#FFB74D"),
        "join": ("#1A237E", "#2196F3", "#64B5F6"),
        "stack": ("#4A148C", "#9C27B0", "#CE93D8"),
        "grouping": ("#1B5E20", "#4CAF50", "#81C784"),
        "window": ("#006064", "#00BCD4", "#4DD0E1"),
        "split": ("#880E4F", "#E91E63", "#F48FB1"),
        "sort": ("#F57F17", "#FFC107", "#FFD54F"),
        "distinct": ("#3E2723", "#795548", "#A1887F"),
        "filter": ("#BF360C", "#FF5722", "#FF8A65"),
        "python": ("#1A237E", "#3F51B5", "#7986CB"),
        "sync": ("#263238", "#607D8B", "#90A4AE"),
        "sample": ("#33691E", "#8BC34A", "#AED581"),
        "pivot": ("#01579B", "#03A9F4", "#4FC3F7"),
        "top_n": ("#E65100", "#FFB300", "#FFD54F"),
        "default": ("#424242", "#9E9E9E", "#BDBDBD"),
    },
)
