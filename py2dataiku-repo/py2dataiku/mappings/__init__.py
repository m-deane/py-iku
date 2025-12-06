"""Mappings from Python operations to Dataiku recipes and processors."""

from py2dataiku.mappings.pandas_mappings import PandasMapper
from py2dataiku.mappings.processor_catalog import ProcessorCatalog

__all__ = [
    "PandasMapper",
    "ProcessorCatalog",
]
