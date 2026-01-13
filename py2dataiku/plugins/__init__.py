"""Plugin system for py2dataiku.

This module provides a plugin architecture for registering custom:
- Recipe types and their mappings
- Processor types
- Pandas method handlers
- Custom transformation rules

Example usage:
    from py2dataiku.plugins import PluginRegistry, plugin_hook

    # Register a custom pandas method handler
    @plugin_hook("pandas_method")
    def handle_custom_method(node, context):
        # Custom handling logic
        return transformation

    # Register custom recipe mapping
    PluginRegistry.register_recipe_mapping("custom_agg", RecipeType.GROUPING)

    # Register custom processor
    PluginRegistry.register_processor("custom_clean", ProcessorType.FILL_EMPTY_WITH_VALUE)
"""

from py2dataiku.plugins.registry import (
    PluginRegistry,
    plugin_hook,
    register_recipe_handler,
    register_processor_handler,
    register_pandas_mapping,
)

__all__ = [
    "PluginRegistry",
    "plugin_hook",
    "register_recipe_handler",
    "register_processor_handler",
    "register_pandas_mapping",
]
