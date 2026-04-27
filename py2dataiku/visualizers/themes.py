"""
Visual themes for Dataiku flow visualization.

Color choices follow the public Dataiku DSS visual style: recipes appear as
colored circles, where each recipe-type family has a fixed hue (blue =
PREPARE, orange = JOIN, green = GROUPING, gold = ML, etc.). Datasets are
rounded rectangles whose left edge carries a connection-type stripe (green =
filesystem, blue = SQL, orange = blob storage, red = inline, etc.).

Single source of truth (Sprint-7)
---------------------------------
The recipe palette, connection stripes, layout spacing, edge styling, and
node sizes are loaded at import time from ``docs/design/tokens.json``
(the ``flow.*`` block). The same JSON file feeds the React/CSS pipeline via
``apps/web/scripts/sync-tokens.ts`` — both sides cannot drift.

Phantom-name aliases (`fuzzy_join` <-> `fuzzyjoin`, `top_n` <-> `topn`, etc.)
are generated in this module from a fixed alias table so the JSON stays
canonical. The legacy ``recipe_colors`` dict (Sprint-1 soft-pastel) is still
preserved for backward compatibility — every existing token still resolves.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


# ---------------------------------------------------------------------------
# Token JSON loading
# ---------------------------------------------------------------------------

# Path resolved relative to the repository root (visualizers/ -> py2dataiku/ ->
# repo root). Cached so import-time cost is paid once.
_TOKENS_PATH = Path(__file__).resolve().parents[2] / "docs" / "design" / "tokens.json"


@lru_cache(maxsize=1)
def _load_tokens() -> dict:
    """Load and cache the canonical token JSON.

    Raises ``FileNotFoundError`` if the file is missing — this is a hard
    requirement for the package to function. CI catches a missing JSON via
    the drift-check test in ``test_token_drift.py``.
    """
    with _TOKENS_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# Phantom-name alias table — DSS canonical names map to friendly aliases used
# elsewhere in the codebase. Each canonical key in tokens.json is expanded to
# the listed aliases at load time. Keep in sync with ProcessorType phantoms.
_RECIPE_ALIASES: dict[str, tuple[str, ...]] = {
    "fuzzy_join": ("fuzzyjoin",),
    "geo_join": ("geojoin",),
    "top_n": ("topn",),
    "sampling": ("sample",),
    "sql": ("sql_script",),
    "sparksql": ("spark_sql_query",),
    "evaluation": ("standalone_evaluation",),
}


def _build_recipe_palette() -> dict[str, tuple[str, str, str]]:
    """Build the (fill, stroke, icon) recipe palette from tokens.json.

    The JSON layout uses ``{ bg, fg, border }``; the legacy Python tuple is
    ``(fill, stroke, icon_color)`` which corresponds to ``(bg, border, fg)``.
    """
    tokens = _load_tokens()
    flow_recipe = tokens["flow"]["recipe"]
    palette: dict[str, tuple[str, str, str]] = {}
    for canonical, triplet in flow_recipe.items():
        value = (triplet["bg"], triplet["border"], triplet["fg"])
        palette[canonical] = value
        for alias in _RECIPE_ALIASES.get(canonical, ()):
            palette[alias] = value
    return palette


def _build_connection_stripes() -> dict[str, str]:
    """Build the per-connection-type stripe map from the family table.

    The JSON groups stripes by family (filesystem/sql/cloud/...); we expand to
    DSS-canonical connection-type names + lowercased aliases at load time so
    string lookups by ``"PostgreSQL"``, ``"S3"``, ``"Filesystem"`` keep
    working.
    """
    tokens = _load_tokens()
    families = tokens["flow"]["dataset"]["stripe"]
    fs = families["filesystem"]
    sql = families["sql"]
    cloud = families["cloud"]
    nosql = families["nosql"]
    http = families["http"]
    inline = families["inline"]
    default = families["default"]

    return {
        # Filesystem family — green
        "Filesystem": fs,
        "filesystem": fs,
        # SQL warehouses — blue
        "PostgreSQL": sql,
        "MySQL": sql,
        "BigQuery": sql,
        "Snowflake": sql,
        "Redshift": sql,
        "Oracle": sql,
        "MSSQL": sql,
        "SQL": sql,
        # Cloud blob — orange
        "S3": cloud,
        "GCS": cloud,
        "Azure": cloud,
        "Azure Blob": cloud,
        "HDFS": cloud,
        "ManagedFolder": cloud,
        # NoSQL — purple
        "MongoDB": nosql,
        "Cassandra": nosql,
        "DynamoDB": nosql,
        "Elasticsearch": nosql,
        # HTTP / API — yellow
        "HTTP": http,
        "API": http,
        "Twitter": http,
        # Inline — red/coral
        "Inline": inline,
        "inline": inline,
        "default": default,
    }


# Module-level palette dicts — built once at import time from tokens.json.
# These names (`_RECIPE_PALETTE_LIGHT`, `_CONNECTION_STRIPES`) are preserved
# for any internal code that references them directly.
_RECIPE_PALETTE_LIGHT: dict[str, tuple[str, str, str]] = _build_recipe_palette()
_CONNECTION_STRIPES: dict[str, str] = _build_connection_stripes()


def _flow_layout() -> dict:
    return _load_tokens()["flow"]["layout"]


def _flow_edge() -> dict:
    return _load_tokens()["flow"]["edge"]


def _flow_node() -> dict:
    return _load_tokens()["flow"]["node"]


@dataclass
class DataikuTheme:
    """Visual theme matching Dataiku DSS interface.

    Attributes are grouped into:
    - **Dataset chrome**: input/output/intermediate background, border, text.
    - **Recipe chrome**: legacy ``recipe_colors`` (bg, border, text triples)
      kept verbatim for backward compatibility, plus a new ``recipe_palette``
      dict that drives the high-fidelity DSS-style rendering.
    - **Connection stripes**: ``connection_stripes`` maps DSS connection-type
      names (``PostgreSQL``, ``S3``, ``Filesystem``, ...) to a single hex
      value drawn as a 6px-wide band on the left edge of dataset cards.
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
    # for the upgraded SVG / matplotlib / Mermaid / PlantUML rendering. Loaded
    # from docs/design/tokens.json (flow.recipe.*).
    recipe_palette: dict[str, tuple[str, str, str]] = field(
        default_factory=lambda: dict(_RECIPE_PALETTE_LIGHT)
    )

    # Connection-type stripe colors. The left edge of each dataset card uses
    # this 6px-wide vertical band, exactly matching DSS's flow view. Loaded
    # from docs/design/tokens.json (flow.dataset.stripe.*).
    connection_stripes: dict[str, str] = field(
        default_factory=lambda: dict(_CONNECTION_STRIPES)
    )

    # Connection styling — sourced from flow.edge in tokens.json (designer
    # decision Sprint-7: edge stroke is the slate-400 #94a3b8 used by the
    # web canvas, not the legacy #90A4AE).
    connection_color: str = field(default_factory=lambda: _flow_edge()["stroke"])
    connection_hover: str = field(default_factory=lambda: _flow_edge()["stroke_hover"])
    connection_width: float = field(
        default_factory=lambda: float(_flow_edge()["stroke_width"])
    )
    arrow_size: int = 8

    # Typography
    font_family: str = "Arial, Helvetica, sans-serif"
    dataset_font_size: int = 13
    recipe_font_size: int = 11
    icon_font_size: int = 20

    # Dimensions — sourced from flow.node in tokens.json (designer decision
    # Sprint-7: 140x56 dataset, 78 recipe diameter — DSS-fidelity sizes).
    dataset_width: int = field(
        default_factory=lambda: int(_flow_node()["dataset_width"])
    )
    dataset_height: int = field(
        default_factory=lambda: int(_flow_node()["dataset_height"])
    )
    dataset_radius: int = 6
    recipe_size: int = field(
        default_factory=lambda: int(_flow_node()["recipe_diameter"])
    )
    recipe_radius: int = 10
    # Width of the connection-type stripe drawn on the left edge of datasets
    connection_stripe_width: int = 6

    # Layout spacing — sourced from flow.layout in tokens.json (designer
    # decision Sprint-7: 220 / 110 / 60 DSS-fidelity values).
    layer_spacing: int = field(
        default_factory=lambda: int(_flow_layout()["layer_spacing"])
    )
    node_spacing: int = field(
        default_factory=lambda: int(_flow_layout()["node_spacing"])
    )
    padding: int = field(default_factory=lambda: int(_flow_layout()["padding"]))

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
        return self.recipe_palette.get(
            key,
            self.recipe_palette.get("default", ("#9e9e9e", "#6e6e6e", "#ffffff")),
        )

    def get_connection_stripe(self, connection_type: str | None) -> str:
        """Get the left-edge stripe color for a dataset connection type.

        Lookup is case-sensitive against DSS-canonical names
        (``"PostgreSQL"``, ``"S3"``, ...) but falls back to a
        case-insensitive scan, then to the ``"default"`` value.
        """
        if not connection_type:
            return self.connection_stripes.get("default", "#94a3b8")
        if connection_type in self.connection_stripes:
            return self.connection_stripes[connection_type]
        lc = connection_type.lower()
        for k, v in self.connection_stripes.items():
            if k.lower() == lc:
                return v
        return self.connection_stripes.get("default", "#94a3b8")


# Predefined themes
DATAIKU_LIGHT = DataikuTheme(name="dataiku-light")


# Dark-mode palette: same hues, slightly desaturated, dark background. Recipe
# fills are kept saturated so the family color is still recognizable. (The
# Sprint-6 palette uses identical fill/stroke/icon for light + dark; the dark
# treatment differs only in the surrounding chrome.)
_RECIPE_PALETTE_DARK = dict(_RECIPE_PALETTE_LIGHT)

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
