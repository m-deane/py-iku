"""
Visual themes for Dataiku flow visualization.

Color choices follow the public Dataiku DSS visual style: recipes appear as
colored circles, where each recipe-type family has a fixed hue (blue =
PREPARE, orange = JOIN, green = GROUPING, gold = ML, etc.). Datasets are
rounded rectangles whose left edge carries a connection-type stripe (green =
filesystem, blue = SQL, orange = blob storage, red = inline, etc.).

The legacy ``recipe_colors`` dict (mapping ``"prepare" -> (bg, border, text)``)
is preserved for backward compatibility — every existing token still resolves.
The new ``recipe_palette`` dict is the source of truth for the upgraded
DSS-fidelity rendering and uses solid fills (filled circle, white icon) rather
than the soft-pastel gradient style.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# DSS-derived hex values — taken from public marketing screenshots & the
# product's own CSS variable tokens. Using the same palette across SVG, PNG,
# Mermaid, PlantUML, and HTML keeps cross-format outputs visually consistent.
_RECIPE_PALETTE_LIGHT: dict[str, tuple[str, str, str]] = {
    # (fill, stroke, label/icon color)
    # Visual recipes
    "prepare": ("#2c8fd9", "#1f6fa9", "#ffffff"),
    "sync": ("#5d6d7e", "#3d4d5e", "#ffffff"),
    "grouping": ("#75bb6a", "#5a9151", "#ffffff"),
    "window": ("#9b59b6", "#7d3f97", "#ffffff"),
    "join": ("#f29222", "#c4761a", "#ffffff"),
    "fuzzyjoin": ("#f0a040", "#c47e2a", "#ffffff"),
    "fuzzy_join": ("#f0a040", "#c47e2a", "#ffffff"),
    "geojoin": ("#e67e22", "#b8631a", "#ffffff"),
    "geo_join": ("#e67e22", "#b8631a", "#ffffff"),
    "stack": ("#3498db", "#2778b3", "#ffffff"),
    "split": ("#2c8fd9", "#1f6fa9", "#ffffff"),
    "sort": ("#7f8c8d", "#5d696a", "#ffffff"),
    "distinct": ("#95a5a6", "#6c7c7d", "#ffffff"),
    "top_n": ("#7f8c8d", "#5d696a", "#ffffff"),
    "topn": ("#7f8c8d", "#5d696a", "#ffffff"),
    "pivot": ("#16a085", "#0f7a64", "#ffffff"),
    "sampling": ("#7f8c8d", "#5d696a", "#ffffff"),
    "sample": ("#7f8c8d", "#5d696a", "#ffffff"),
    "filter": ("#2c8fd9", "#1f6fa9", "#ffffff"),
    "download": ("#e67e22", "#b8631a", "#ffffff"),
    "generate_features": ("#27ae60", "#1d8348", "#ffffff"),
    "generate_statistics": ("#1abc9c", "#138a72", "#ffffff"),
    "push_to_editable": ("#5d6d7e", "#3d4d5e", "#ffffff"),
    "list_folder_contents": ("#5d6d7e", "#3d4d5e", "#ffffff"),
    "list_access": ("#5d6d7e", "#3d4d5e", "#ffffff"),
    "dynamic_repeat": ("#5d6d7e", "#3d4d5e", "#ffffff"),
    "extract_failed_rows": ("#c0392b", "#962d22", "#ffffff"),
    "upsert": ("#5d6d7e", "#3d4d5e", "#ffffff"),

    # Code recipes
    "python": ("#34495e", "#22303c", "#ffffff"),
    "r": ("#1f77b4", "#155481", "#ffffff"),
    "sql": ("#2980b9", "#1f628e", "#ffffff"),
    "sql_script": ("#2980b9", "#1f628e", "#ffffff"),
    "hive": ("#7e5109", "#5a3a07", "#ffffff"),
    "impala": ("#a04000", "#6e2c00", "#ffffff"),
    "sparksql": ("#e67e22", "#b8631a", "#ffffff"),
    "spark_sql_query": ("#e67e22", "#b8631a", "#ffffff"),
    "pyspark": ("#e67e22", "#b8631a", "#ffffff"),
    "spark_scala": ("#e67e22", "#b8631a", "#ffffff"),
    "sparkr": ("#e67e22", "#b8631a", "#ffffff"),
    "shell": ("#34495e", "#22303c", "#ffffff"),

    # ML / scoring
    "prediction_scoring": ("#f39c12", "#c47e0a", "#ffffff"),
    "clustering_scoring": ("#f39c12", "#c47e0a", "#ffffff"),
    "evaluation": ("#f39c12", "#c47e0a", "#ffffff"),
    "standalone_evaluation": ("#f39c12", "#c47e0a", "#ffffff"),
    "ai_assistant_generate": ("#8e44ad", "#6c3483", "#ffffff"),

    "default": ("#9e9e9e", "#6e6e6e", "#ffffff"),
}

# Connection-type stripe colors — the colored band on the left edge of each
# dataset rectangle. Family-grouped: green = local fs, blue = SQL warehouses,
# orange = cloud blob, red = inline, purple = NoSQL, yellow = HTTP/API.
_CONNECTION_STRIPES: dict[str, str] = {
    # Filesystem family — green
    "Filesystem": "#75bb6a",
    "filesystem": "#75bb6a",

    # SQL warehouses — blue
    "PostgreSQL": "#2c8fd9",
    "MySQL": "#2c8fd9",
    "BigQuery": "#2c8fd9",
    "Snowflake": "#2c8fd9",
    "Redshift": "#2c8fd9",
    "Oracle": "#2c8fd9",
    "MSSQL": "#2c8fd9",
    "SQL": "#2c8fd9",

    # Cloud blob — orange
    "S3": "#f29222",
    "GCS": "#f29222",
    "Azure": "#f29222",
    "Azure Blob": "#f29222",
    "HDFS": "#f29222",
    "ManagedFolder": "#f29222",

    # NoSQL — purple
    "MongoDB": "#9b59b6",
    "Cassandra": "#9b59b6",
    "DynamoDB": "#9b59b6",
    "Elasticsearch": "#9b59b6",

    # HTTP / API — yellow
    "HTTP": "#f1c40f",
    "API": "#f1c40f",
    "Twitter": "#f1c40f",

    # Inline — red/coral
    "Inline": "#e74c3c",
    "inline": "#e74c3c",

    "default": "#90a4ae",
}


@dataclass
class DataikuTheme:
    """Visual theme matching Dataiku DSS interface.

    Attributes are grouped into:
    - **Dataset chrome**: input/output/intermediate background, border, text.
    - **Recipe chrome**: legacy ``recipe_colors`` (bg, border, text triples)
      kept verbatim for backward compatibility, plus a new ``recipe_palette``
      dict that drives the high-fidelity DSS-style rendering.
    - **Connection stripes**: ``connection_stripes`` maps DSS connection-type
      names (``PostgreSQL``, ``S3``, ``Filesystem``, ...) to a single hex value
      drawn as a 6px-wide band on the left edge of dataset cards.
    - **Layout**: spacing, fonts, dimensions used by the layout engine.
    """

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

    # Recipe colors by type — legacy soft-pastel palette retained for
    # backwards compatibility (`get_recipe_colors`, downstream tests).
    recipe_colors: dict[str, tuple[str, str, str]] = field(default_factory=lambda: {
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

    # Recipe palette — DSS-fidelity (solid fill, white icon). Source of truth
    # for the upgraded SVG / matplotlib / Mermaid / PlantUML rendering.
    recipe_palette: dict[str, tuple[str, str, str]] = field(
        default_factory=lambda: dict(_RECIPE_PALETTE_LIGHT)
    )

    # Connection-type stripe colors. The left edge of each dataset card uses
    # this 6px-wide vertical band, exactly matching DSS's flow view.
    connection_stripes: dict[str, str] = field(
        default_factory=lambda: dict(_CONNECTION_STRIPES)
    )

    # Connection styling
    connection_color: str = "#90A4AE"
    connection_hover: str = "#1976D2"
    connection_width: float = 1.5
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
    # Width of the connection-type stripe drawn on the left edge of datasets
    connection_stripe_width: int = 6

    # Layout spacing — defaults follow the DSS flow view (column-major,
    # 200px between layers, 100px between rows in the same column).
    layer_spacing: int = 200
    node_spacing: int = 100
    padding: int = 40

    # Background — DSS uses #fafbfc; we keep the existing #FAFAFA default
    # for backwards compatibility with downstream tests/snapshots and expose
    # the closer-to-DSS value as ``dss_background_color`` for opt-in use.
    background_color: str = "#FAFAFA"
    dss_background_color: str = "#fafbfc"
    grid_color: str = "#E0E0E0"
    show_grid: bool = False

    # Zone styling
    zone_colors: list[str] = field(default_factory=lambda: [
        "#E3F2FD", "#F3E5F5", "#E8F5E9", "#FFF3E0",
        "#FCE4EC", "#E0F7FA", "#FFF8E1", "#EFEBE9",
    ])
    zone_border_colors: list[str] = field(default_factory=lambda: [
        "#90CAF9", "#CE93D8", "#A5D6A7", "#FFCC80",
        "#F48FB1", "#80DEEA", "#FFD54F", "#BCAAA4",
    ])
    zone_label_size: int = 11
    zone_padding: int = 20

    def get_recipe_colors(self, recipe_type: str) -> tuple[str, str, str]:
        """Get legacy colors for a recipe type (bg, border, text).

        Returns the soft-pastel ``recipe_colors`` mapping kept for backward
        compatibility. For DSS-fidelity solid-circle rendering use
        :meth:`get_recipe_palette` instead.
        """
        key = (recipe_type or "default").lower().replace(" ", "_")
        if key in self.recipe_colors:
            return self.recipe_colors[key]
        return self.recipe_colors.get("default", ("#F5F5F5", "#9E9E9E", "#616161"))

    def get_recipe_palette(self, recipe_type: str) -> tuple[str, str, str]:
        """Get the new DSS-fidelity recipe palette (fill, stroke, icon)."""
        key = (recipe_type or "default").lower().replace(" ", "_")
        return self.recipe_palette.get(key, self.recipe_palette.get("default", ("#9e9e9e", "#6e6e6e", "#ffffff")))

    def get_connection_stripe(self, connection_type: str | None) -> str:
        """Get the left-edge stripe color for a dataset connection type.

        Lookup is case-sensitive against DSS-canonical names
        (``"PostgreSQL"``, ``"S3"``, ...) but falls back to a
        case-insensitive scan, then to the ``"default"`` value.
        """
        if not connection_type:
            return self.connection_stripes.get("default", "#90a4ae")
        if connection_type in self.connection_stripes:
            return self.connection_stripes[connection_type]
        lc = connection_type.lower()
        for k, v in self.connection_stripes.items():
            if k.lower() == lc:
                return v
        return self.connection_stripes.get("default", "#90a4ae")


# Predefined themes
DATAIKU_LIGHT = DataikuTheme(name="dataiku-light")


# Dark-mode palette: same hues, slightly desaturated, dark background. Recipe
# fills are kept saturated so the family color is still recognizable.
_RECIPE_PALETTE_DARK = {
    k: (v[0], v[1], v[2]) for k, v in _RECIPE_PALETTE_LIGHT.items()
}

DATAIKU_DARK = DataikuTheme(
    name="dataiku-dark",
    background_color="#1E1E1E",  # backward-compat default; DSS-dark = #1a2332
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
    recipe_palette=_RECIPE_PALETTE_DARK,
    connection_stripes=dict(_CONNECTION_STRIPES),
    zone_colors=[
        "#1A2744", "#2D1B3D", "#1B3D1B", "#3D2800",
        "#3D0E20", "#003D40", "#3D3000", "#2A1F1A",
    ],
    zone_border_colors=[
        "#3F51B5", "#7B1FA2", "#388E3C", "#E65100",
        "#AD1457", "#00838F", "#F9A825", "#6D4C41",
    ],
)
