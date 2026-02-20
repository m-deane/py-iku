"""Plugin registry for custom recipe and processor registration.

This module provides a centralized registry for plugins that extend
py2dataiku's conversion capabilities.
"""

import copy
import functools
from typing import Any, Callable, Dict, List, Optional, Type, Union

from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType
from py2dataiku.models.transformation import Transformation, TransformationType


class PluginRegistry:
    """
    Central registry for all plugins.

    This class maintains mappings between pandas operations and Dataiku
    constructs, allowing users to extend the default behavior.

    Can be used as instance-based (for isolated registries) or via the
    default global instance through classmethods for backward compatibility.
    """

    # Default global instance (lazily created)
    _default_instance: Optional["PluginRegistry"] = None

    def __init__(self):
        self._recipe_mappings: Dict[str, RecipeType] = {}
        self._processor_mappings: Dict[str, ProcessorType] = {}
        self._method_handlers: Dict[str, Callable] = {}
        self._recipe_handlers: Dict[RecipeType, Callable] = {}
        self._processor_handlers: Dict[ProcessorType, Callable] = {}
        self._plugins: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _get_default(cls) -> "PluginRegistry":
        """Get or create the default global instance."""
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    def copy(self) -> "PluginRegistry":
        """Create an independent copy of this registry."""
        new = PluginRegistry()
        new._recipe_mappings = self._recipe_mappings.copy()
        new._processor_mappings = self._processor_mappings.copy()
        new._method_handlers = self._method_handlers.copy()
        new._recipe_handlers = self._recipe_handlers.copy()
        new._processor_handlers = self._processor_handlers.copy()
        new._plugins = copy.deepcopy(self._plugins)
        return new

    # --- Instance methods ---

    def add_recipe_mapping(
        self,
        pandas_method: str,
        recipe_type: RecipeType,
        override: bool = False,
    ) -> None:
        """Register a mapping from a pandas method to a Dataiku recipe type."""
        if pandas_method in self._recipe_mappings and not override:
            raise ValueError(
                f"Recipe mapping for '{pandas_method}' already exists. "
                "Use override=True to replace."
            )
        self._recipe_mappings[pandas_method] = recipe_type

    def add_processor_mapping(
        self,
        pandas_method: str,
        processor_type: ProcessorType,
        override: bool = False,
    ) -> None:
        """Register a mapping from a pandas method to a Dataiku processor type."""
        if pandas_method in self._processor_mappings and not override:
            raise ValueError(
                f"Processor mapping for '{pandas_method}' already exists. "
                "Use override=True to replace."
            )
        self._processor_mappings[pandas_method] = processor_type

    def add_method_handler(
        self,
        method_name: str,
        handler: Callable,
        override: bool = False,
    ) -> None:
        """Register a custom handler for a pandas method."""
        if method_name in self._method_handlers and not override:
            raise ValueError(
                f"Handler for '{method_name}' already exists. "
                "Use override=True to replace."
            )
        self._method_handlers[method_name] = handler

    def add_recipe_handler(
        self,
        recipe_type: RecipeType,
        handler: Callable,
        override: bool = False,
    ) -> None:
        """Register a custom handler for generating a recipe type."""
        if recipe_type in self._recipe_handlers and not override:
            raise ValueError(
                f"Handler for recipe type '{recipe_type}' already exists. "
                "Use override=True to replace."
            )
        self._recipe_handlers[recipe_type] = handler

    def add_processor_handler(
        self,
        processor_type: ProcessorType,
        handler: Callable,
        override: bool = False,
    ) -> None:
        """Register a custom handler for generating a processor type."""
        if processor_type in self._processor_handlers and not override:
            raise ValueError(
                f"Handler for processor type '{processor_type}' already exists. "
                "Use override=True to replace."
            )
        self._processor_handlers[processor_type] = handler

    def add_plugin(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        **kwargs,
    ) -> None:
        """Register a plugin with metadata."""
        self._plugins[name] = {
            "version": version,
            "description": description,
            **kwargs,
        }

    def find_recipe_mapping(self, method: str) -> Optional[RecipeType]:
        """Get custom recipe mapping for a method."""
        return self._recipe_mappings.get(method)

    def find_processor_mapping(self, method: str) -> Optional[ProcessorType]:
        """Get custom processor mapping for a method."""
        return self._processor_mappings.get(method)

    def find_method_handler(self, method: str) -> Optional[Callable]:
        """Get custom handler for a method."""
        return self._method_handlers.get(method)

    def find_recipe_handler(self, recipe_type: RecipeType) -> Optional[Callable]:
        """Get custom handler for a recipe type."""
        return self._recipe_handlers.get(recipe_type)

    def find_processor_handler(
        self, processor_type: ProcessorType
    ) -> Optional[Callable]:
        """Get custom handler for a processor type."""
        return self._processor_handlers.get(processor_type)

    def remove_recipe_mapping(self, method: str) -> bool:
        """Remove a recipe mapping. Returns True if removed."""
        if method in self._recipe_mappings:
            del self._recipe_mappings[method]
            return True
        return False

    def remove_processor_mapping(self, method: str) -> bool:
        """Remove a processor mapping. Returns True if removed."""
        if method in self._processor_mappings:
            del self._processor_mappings[method]
            return True
        return False

    def remove_method_handler(self, method: str) -> bool:
        """Remove a method handler. Returns True if removed."""
        if method in self._method_handlers:
            del self._method_handlers[method]
            return True
        return False

    def clear_all(self) -> None:
        """Clear all registered plugins and mappings."""
        self._recipe_mappings.clear()
        self._processor_mappings.clear()
        self._method_handlers.clear()
        self._recipe_handlers.clear()
        self._processor_handlers.clear()
        self._plugins.clear()

    # --- Classmethod backward-compatible API (delegates to default instance) ---

    @classmethod
    def register_recipe_mapping(
        cls,
        pandas_method: str,
        recipe_type: RecipeType,
        override: bool = False,
    ) -> None:
        """Register a mapping from a pandas method to a Dataiku recipe type.

        Example:
            >>> PluginRegistry.register_recipe_mapping("my_merge", RecipeType.JOIN)
        """
        cls._get_default().add_recipe_mapping(pandas_method, recipe_type, override)

    @classmethod
    def register_processor_mapping(
        cls,
        pandas_method: str,
        processor_type: ProcessorType,
        override: bool = False,
    ) -> None:
        """Register a mapping from a pandas method to a Dataiku processor type.

        Example:
            >>> PluginRegistry.register_processor_mapping(
            ...     "my_fillna", ProcessorType.FILL_EMPTY_WITH_VALUE
            ... )
        """
        cls._get_default().add_processor_mapping(pandas_method, processor_type, override)

    @classmethod
    def register_method_handler(
        cls,
        method_name: str,
        handler: Callable,
        override: bool = False,
    ) -> None:
        """Register a custom handler for a pandas method.

        Example:
            >>> def my_handler(node, context):
            ...     return Transformation(...)
            >>> PluginRegistry.register_method_handler("my_method", my_handler)
        """
        cls._get_default().add_method_handler(method_name, handler, override)

    @classmethod
    def register_recipe_handler(
        cls,
        recipe_type: RecipeType,
        handler: Callable,
        override: bool = False,
    ) -> None:
        """Register a custom handler for generating a recipe type."""
        cls._get_default().add_recipe_handler(recipe_type, handler, override)

    @classmethod
    def register_processor_handler(
        cls,
        processor_type: ProcessorType,
        handler: Callable,
        override: bool = False,
    ) -> None:
        """Register a custom handler for generating a processor type."""
        cls._get_default().add_processor_handler(processor_type, handler, override)

    @classmethod
    def register_plugin(
        cls,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        **kwargs,
    ) -> None:
        """Register a plugin with metadata."""
        cls._get_default().add_plugin(name, version, description, **kwargs)

    @classmethod
    def get_recipe_mapping(cls, method: str) -> Optional[RecipeType]:
        """Get custom recipe mapping for a method."""
        return cls._get_default().find_recipe_mapping(method)

    @classmethod
    def get_processor_mapping(cls, method: str) -> Optional[ProcessorType]:
        """Get custom processor mapping for a method."""
        return cls._get_default().find_processor_mapping(method)

    @classmethod
    def get_method_handler(cls, method: str) -> Optional[Callable]:
        """Get custom handler for a method."""
        return cls._get_default().find_method_handler(method)

    @classmethod
    def get_recipe_handler(cls, recipe_type: RecipeType) -> Optional[Callable]:
        """Get custom handler for a recipe type."""
        return cls._get_default().find_recipe_handler(recipe_type)

    @classmethod
    def get_processor_handler(
        cls, processor_type: ProcessorType
    ) -> Optional[Callable]:
        """Get custom handler for a processor type."""
        return cls._get_default().find_processor_handler(processor_type)

    @classmethod
    def list_recipe_mappings(cls) -> Dict[str, RecipeType]:
        """List all registered recipe mappings."""
        return cls._get_default()._recipe_mappings.copy()

    @classmethod
    def list_processor_mappings(cls) -> Dict[str, ProcessorType]:
        """List all registered processor mappings."""
        return cls._get_default()._processor_mappings.copy()

    @classmethod
    def list_plugins(cls) -> Dict[str, Dict[str, Any]]:
        """List all registered plugins."""
        return cls._get_default()._plugins.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered plugins and mappings on the default instance."""
        cls._get_default().clear_all()

    @classmethod
    def unregister_recipe_mapping(cls, method: str) -> bool:
        """Remove a recipe mapping. Returns True if removed."""
        return cls._get_default().remove_recipe_mapping(method)

    @classmethod
    def unregister_processor_mapping(cls, method: str) -> bool:
        """Remove a processor mapping. Returns True if removed."""
        return cls._get_default().remove_processor_mapping(method)

    @classmethod
    def unregister_method_handler(cls, method: str) -> bool:
        """Remove a method handler. Returns True if removed."""
        return cls._get_default().remove_method_handler(method)


def plugin_hook(hook_type: str):
    """
    Decorator to register a function as a plugin hook.

    Args:
        hook_type: Type of hook ("pandas_method", "recipe", "processor")

    Example:
        >>> @plugin_hook("pandas_method")
        ... def handle_custom_method(node, context):
        ...     return Transformation(...)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Register based on hook type
        if hook_type == "pandas_method":
            PluginRegistry.register_method_handler(func.__name__, func)
        elif hook_type == "recipe":
            # Expect func.__recipe_type__ attribute
            recipe_type = getattr(func, "__recipe_type__", None)
            if recipe_type:
                PluginRegistry.register_recipe_handler(recipe_type, func)
        elif hook_type == "processor":
            # Expect func.__processor_type__ attribute
            processor_type = getattr(func, "__processor_type__", None)
            if processor_type:
                PluginRegistry.register_processor_handler(processor_type, func)

        return wrapper
    return decorator


def register_recipe_handler(recipe_type: RecipeType):
    """
    Decorator to register a recipe handler.

    Args:
        recipe_type: The RecipeType this handler processes

    Example:
        >>> @register_recipe_handler(RecipeType.JOIN)
        ... def custom_join_handler(transformation):
        ...     return DataikuRecipe(...)
    """
    def decorator(func: Callable) -> Callable:
        func.__recipe_type__ = recipe_type
        PluginRegistry.register_recipe_handler(recipe_type, func)
        return func
    return decorator


def register_processor_handler(processor_type: ProcessorType):
    """
    Decorator to register a processor handler.

    Args:
        processor_type: The ProcessorType this handler processes

    Example:
        >>> @register_processor_handler(ProcessorType.FILL_EMPTY_WITH_VALUE)
        ... def custom_fill_handler(step):
        ...     return PrepareStep(...)
    """
    def decorator(func: Callable) -> Callable:
        func.__processor_type__ = processor_type
        PluginRegistry.register_processor_handler(processor_type, func)
        return func
    return decorator


def register_pandas_mapping(
    method_name: str,
    target_type: Union[RecipeType, ProcessorType],
    handler: Optional[Callable] = None
):
    """
    Convenience function to register a pandas method mapping.

    Args:
        method_name: The pandas method to map
        target_type: RecipeType or ProcessorType to map to
        handler: Optional custom handler function

    Example:
        >>> register_pandas_mapping("custom_fill", ProcessorType.FILL_EMPTY_WITH_VALUE)
        >>> register_pandas_mapping("custom_agg", RecipeType.GROUPING, my_handler)
    """
    if isinstance(target_type, RecipeType):
        PluginRegistry.register_recipe_mapping(method_name, target_type)
    elif isinstance(target_type, ProcessorType):
        PluginRegistry.register_processor_mapping(method_name, target_type)
    else:
        raise ValueError(f"target_type must be RecipeType or ProcessorType, got {type(target_type)}")

    if handler:
        PluginRegistry.register_method_handler(method_name, handler)


class PluginContext:
    """
    Context object passed to plugin handlers.

    Provides access to analysis state and utilities.
    """

    def __init__(
        self,
        source_code: str = "",
        current_line: int = 0,
        variables: Optional[Dict[str, Any]] = None,
        dataframes: Optional[Dict[str, str]] = None,
    ):
        self.source_code = source_code
        self.current_line = current_line
        self.variables = variables or {}
        self.dataframes = dataframes or {}

    def get_variable(self, name: str) -> Any:
        """Get a tracked variable value."""
        return self.variables.get(name)

    def get_dataframe_source(self, name: str) -> Optional[str]:
        """Get the source dataset for a dataframe variable."""
        return self.dataframes.get(name)


class Plugin:
    """
    Base class for creating py2dataiku plugins.

    Subclass this to create a self-contained plugin with
    multiple handlers and mappings.

    Example:
        >>> class MyPlugin(Plugin):
        ...     name = "my_plugin"
        ...     version = "1.0.0"
        ...
        ...     def register(self):
        ...         self.add_recipe_mapping("custom_agg", RecipeType.GROUPING)
        ...         self.add_method_handler("custom_method", self.handle_custom)
        ...
        ...     def handle_custom(self, node, context):
        ...         return Transformation(...)
    """

    name: str = "unnamed_plugin"
    version: str = "1.0.0"
    description: str = ""

    def __init__(self, registry: Optional[PluginRegistry] = None):
        self._registry = registry or PluginRegistry._get_default()
        self._local_recipe_mappings: Dict[str, RecipeType] = {}
        self._local_processor_mappings: Dict[str, ProcessorType] = {}
        self._local_handlers: Dict[str, Callable] = {}

    def register(self) -> None:
        """
        Override this method to register plugin components.

        Called automatically when the plugin is activated.
        """
        pass

    def activate(self) -> None:
        """Activate this plugin, registering all components."""
        # Register plugin metadata
        self._registry.add_plugin(
            self.name,
            version=self.version,
            description=self.description,
        )

        # Call user's register method
        self.register()

        # Register local mappings
        for method, recipe_type in self._local_recipe_mappings.items():
            self._registry.add_recipe_mapping(method, recipe_type)

        for method, processor_type in self._local_processor_mappings.items():
            self._registry.add_processor_mapping(method, processor_type)

        for method, handler in self._local_handlers.items():
            self._registry.add_method_handler(method, handler)

    def deactivate(self) -> None:
        """Deactivate this plugin, removing all components."""
        for method in self._local_recipe_mappings:
            self._registry.remove_recipe_mapping(method)

        for method in self._local_processor_mappings:
            self._registry.remove_processor_mapping(method)

        for method in self._local_handlers:
            self._registry.remove_method_handler(method)

    def add_recipe_mapping(
        self, pandas_method: str, recipe_type: RecipeType
    ) -> None:
        """Add a recipe mapping to this plugin."""
        self._local_recipe_mappings[pandas_method] = recipe_type

    def add_processor_mapping(
        self, pandas_method: str, processor_type: ProcessorType
    ) -> None:
        """Add a processor mapping to this plugin."""
        self._local_processor_mappings[pandas_method] = processor_type

    def add_method_handler(
        self, method_name: str, handler: Callable
    ) -> None:
        """Add a method handler to this plugin."""
        self._local_handlers[method_name] = handler
