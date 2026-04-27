"""Plugin marketplace service — exposes a static catalog of bundled plugin
metadata plus a live introspection of the global ``PluginRegistry``.

v1 is *information-only*: clicking "Install" in the UI shows a copy-pastable
``pip install`` command; we do not actually invoke pip.  Real install flow
requires a package registry and is tracked as a Wave 5+ extension.

The catalog is hand-curated because the textbook chapter and worked-examples
each ship one plugin and we want the marketplace to reflect that scope without
pulling random packages off PyPI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from py2dataiku.plugins.registry import PluginRegistry


# ---------------------------------------------------------------------------
# Catalog dataclass + bundled entries
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PluginCatalogEntry:
    """Static description of a bundled or third-party plugin."""

    name: str
    version: str
    description: str
    author: str
    supported_recipes: tuple[str, ...]
    supported_processors: tuple[str, ...]
    source_code_url: str
    install_command: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    homepage_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Tuples roundtrip as lists in JSON; normalise here so the FastAPI
        # response shape is identical to what the frontend expects.
        d["supported_recipes"] = list(self.supported_recipes)
        d["supported_processors"] = list(self.supported_processors)
        d["tags"] = list(self.tags)
        return d


# Five bundled catalog entries — keep alphabetised by name for stable UI.
BUNDLED_PLUGINS: tuple[PluginCatalogEntry, ...] = (
    PluginCatalogEntry(
        name="py-iku-aggregations-extra",
        version="0.2.0",
        description=(
            "Extra aggregation handlers for trader analytics: median, "
            "percentile (p5/p25/p75/p95), and mode. Plugs into GROUPING "
            "recipes so .agg('median') and .agg('p95') are first-class."
        ),
        author="py-iku core team",
        supported_recipes=("GROUPING",),
        supported_processors=(),
        source_code_url=(
            "https://github.com/m-deane/py-iku-aggregations-extra"
        ),
        install_command="pip install py-iku-aggregations-extra",
        tags=("aggregation", "GROUPING", "trader-analytics"),
    ),
    PluginCatalogEntry(
        name="py-iku-numpy-extensions",
        version="0.3.1",
        description=(
            "Maps np.where(cond, a, b) and np.select to PREPARE recipes "
            "with conditional CREATE_COLUMN_WITH_GREL processors. Useful "
            "for structured-rule mark validation and exposure flags."
        ),
        author="py-iku core team",
        supported_recipes=("PREPARE",),
        supported_processors=("CREATE_COLUMN_WITH_GREL",),
        source_code_url=(
            "https://github.com/m-deane/py-iku-numpy-extensions"
        ),
        install_command="pip install py-iku-numpy-extensions",
        tags=("numpy", "PREPARE", "GREL"),
    ),
    PluginCatalogEntry(
        name="py-iku-sklearn-bridge",
        version="0.4.2",
        description=(
            "Maps scikit-learn preprocessing transformers — StandardScaler, "
            "MinMaxScaler, OneHotEncoder — to the equivalent PREPARE "
            "processors. Lets quants port feature pipelines without "
            "rewriting them in pandas first."
        ),
        author="py-iku core team",
        supported_recipes=("PREPARE",),
        supported_processors=(
            "NUMERIC_TRANSFORM",
            "CATEGORICAL_ENCODER",
            "BINNER",
        ),
        source_code_url=(
            "https://github.com/m-deane/py-iku-sklearn-bridge"
        ),
        install_command="pip install py-iku-sklearn-bridge",
        tags=("sklearn", "ML", "PREPARE"),
    ),
    PluginCatalogEntry(
        name="py-iku-time-series",
        version="0.5.0",
        description=(
            "First-class handlers for .rolling(), .resample() and .shift() — "
            "the LMP-tick-analytics shape. Maps to WINDOW recipes with the "
            "correct partition / order columns derived from the .groupby() "
            "context."
        ),
        author="py-iku core team",
        supported_recipes=("WINDOW",),
        supported_processors=(),
        source_code_url=(
            "https://github.com/m-deane/py-iku-time-series"
        ),
        install_command="pip install py-iku-time-series",
        tags=("time-series", "WINDOW", "PJM", "LMP"),
    ),
    PluginCatalogEntry(
        name="py-iku-trading-domain",
        version="1.0.0",
        description=(
            "The canonical example from Ch 12 of the textbook — registers "
            "domain-specific helpers like safe_fill (FILL_EMPTY_WITH_VALUE), "
            "inner_match (JOIN inner), and rank_top (TOP_N). Drop-in "
            "vocabulary for front-office trade-blotter pipelines."
        ),
        author="py-iku core team",
        supported_recipes=("JOIN", "TOP_N", "PREPARE"),
        supported_processors=(
            "FILL_EMPTY_WITH_VALUE",
            "COLUMN_RENAMER",
        ),
        source_code_url=(
            "https://github.com/m-deane/py-iku-trading-domain"
        ),
        install_command="pip install py-iku-trading-domain",
        tags=(
            "trading",
            "trade-blotter",
            "JOIN",
            "TOP_N",
            "front-office",
        ),
    ),
)


def list_catalog() -> list[dict[str, Any]]:
    """Return the bundled plugin catalog as plain dicts (FastAPI-friendly)."""
    return [entry.to_dict() for entry in BUNDLED_PLUGINS]


def get_catalog_entry(name: str) -> dict[str, Any] | None:
    """Look up a single catalog entry by exact name."""
    for entry in BUNDLED_PLUGINS:
        if entry.name == name:
            return entry.to_dict()
    return None


# ---------------------------------------------------------------------------
# Live introspection of the global PluginRegistry
# ---------------------------------------------------------------------------


def list_installed() -> dict[str, Any]:
    """Snapshot the global ``PluginRegistry`` and return its active mappings.

    Returned dict has shape::

        {
            "plugins": {name: metadata, ...},
            "recipe_mappings": {pandas_method: RecipeType.value, ...},
            "processor_mappings": {pandas_method: ProcessorType.value, ...},
            "method_handlers": [method_name, ...],
            "recipe_handlers": [RecipeType.value, ...],
            "processor_handlers": [ProcessorType.value, ...],
        }

    Only enum *values* are exposed because the frontend type-checker has no
    way to import the Python enums.
    """
    registry = PluginRegistry._get_default()

    plugins = {
        name: dict(meta) for name, meta in registry._plugins.items()
    }
    recipe_mappings = {
        method: rec.value if hasattr(rec, "value") else str(rec)
        for method, rec in registry._recipe_mappings.items()
    }
    processor_mappings = {
        method: proc.value if hasattr(proc, "value") else str(proc)
        for method, proc in registry._processor_mappings.items()
    }
    method_handlers = sorted(registry._method_handlers.keys())
    recipe_handlers = sorted(
        rec.value if hasattr(rec, "value") else str(rec)
        for rec in registry._recipe_handlers.keys()
    )
    processor_handlers = sorted(
        proc.value if hasattr(proc, "value") else str(proc)
        for proc in registry._processor_handlers.keys()
    )

    return {
        "plugins": plugins,
        "recipe_mappings": recipe_mappings,
        "processor_mappings": processor_mappings,
        "method_handlers": method_handlers,
        "recipe_handlers": recipe_handlers,
        "processor_handlers": processor_handlers,
    }
