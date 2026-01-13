"""Tests for the plugin system."""

import pytest

from py2dataiku.plugins import (
    PluginRegistry,
    plugin_hook,
    register_recipe_handler,
    register_processor_handler,
    register_pandas_mapping,
)
from py2dataiku.plugins.registry import Plugin, PluginContext
from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.models.prepare_step import ProcessorType
from py2dataiku.models.transformation import Transformation, TransformationType
from py2dataiku.parser.ast_analyzer import CodeAnalyzer


class TestPluginRegistry:
    """Tests for PluginRegistry class."""

    def setup_method(self):
        """Clear registry before each test."""
        PluginRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        PluginRegistry.clear()

    def test_register_recipe_mapping(self):
        """Test registering a recipe mapping."""
        PluginRegistry.register_recipe_mapping("custom_merge", RecipeType.JOIN)

        assert PluginRegistry.get_recipe_mapping("custom_merge") == RecipeType.JOIN

    def test_register_processor_mapping(self):
        """Test registering a processor mapping."""
        PluginRegistry.register_processor_mapping(
            "custom_fill", ProcessorType.FILL_EMPTY_WITH_VALUE
        )

        assert PluginRegistry.get_processor_mapping("custom_fill") == ProcessorType.FILL_EMPTY_WITH_VALUE

    def test_register_duplicate_recipe_raises(self):
        """Test that duplicate registration raises error."""
        PluginRegistry.register_recipe_mapping("my_method", RecipeType.JOIN)

        with pytest.raises(ValueError, match="already exists"):
            PluginRegistry.register_recipe_mapping("my_method", RecipeType.STACK)

    def test_register_duplicate_processor_raises(self):
        """Test that duplicate processor registration raises error."""
        PluginRegistry.register_processor_mapping("my_fill", ProcessorType.FILL_EMPTY_WITH_VALUE)

        with pytest.raises(ValueError, match="already exists"):
            PluginRegistry.register_processor_mapping("my_fill", ProcessorType.COLUMN_DELETER)

    def test_override_recipe_mapping(self):
        """Test overriding a recipe mapping."""
        PluginRegistry.register_recipe_mapping("custom", RecipeType.JOIN)
        PluginRegistry.register_recipe_mapping("custom", RecipeType.STACK, override=True)

        assert PluginRegistry.get_recipe_mapping("custom") == RecipeType.STACK

    def test_override_processor_mapping(self):
        """Test overriding a processor mapping."""
        PluginRegistry.register_processor_mapping("custom", ProcessorType.FILL_EMPTY_WITH_VALUE)
        PluginRegistry.register_processor_mapping(
            "custom", ProcessorType.COLUMN_DELETER, override=True
        )

        assert PluginRegistry.get_processor_mapping("custom") == ProcessorType.COLUMN_DELETER

    def test_register_method_handler(self):
        """Test registering a method handler."""
        def my_handler(node, context):
            return Transformation(
                transformation_type=TransformationType.FILTER,
                source_dataframe="input",
                target_dataframe="output",
                parameters={},
                source_line=1,
            )

        PluginRegistry.register_method_handler("my_method", my_handler)

        handler = PluginRegistry.get_method_handler("my_method")
        assert handler is not None
        result = handler(None, None)
        assert result.transformation_type == TransformationType.FILTER

    def test_register_duplicate_handler_raises(self):
        """Test that duplicate handler raises error."""
        def handler1(n, c): pass
        def handler2(n, c): pass

        PluginRegistry.register_method_handler("method", handler1)

        with pytest.raises(ValueError, match="already exists"):
            PluginRegistry.register_method_handler("method", handler2)

    def test_list_recipe_mappings(self):
        """Test listing all recipe mappings."""
        PluginRegistry.register_recipe_mapping("m1", RecipeType.JOIN)
        PluginRegistry.register_recipe_mapping("m2", RecipeType.STACK)

        mappings = PluginRegistry.list_recipe_mappings()

        assert len(mappings) == 2
        assert mappings["m1"] == RecipeType.JOIN
        assert mappings["m2"] == RecipeType.STACK

    def test_list_processor_mappings(self):
        """Test listing all processor mappings."""
        PluginRegistry.register_processor_mapping("p1", ProcessorType.FILL_EMPTY_WITH_VALUE)
        PluginRegistry.register_processor_mapping("p2", ProcessorType.COLUMN_DELETER)

        mappings = PluginRegistry.list_processor_mappings()

        assert len(mappings) == 2
        assert mappings["p1"] == ProcessorType.FILL_EMPTY_WITH_VALUE

    def test_clear_registry(self):
        """Test clearing the registry."""
        PluginRegistry.register_recipe_mapping("test", RecipeType.JOIN)
        PluginRegistry.register_processor_mapping("test", ProcessorType.FILL_EMPTY_WITH_VALUE)

        PluginRegistry.clear()

        assert len(PluginRegistry.list_recipe_mappings()) == 0
        assert len(PluginRegistry.list_processor_mappings()) == 0

    def test_unregister_recipe_mapping(self):
        """Test unregistering a recipe mapping."""
        PluginRegistry.register_recipe_mapping("test", RecipeType.JOIN)

        result = PluginRegistry.unregister_recipe_mapping("test")

        assert result is True
        assert PluginRegistry.get_recipe_mapping("test") is None

    def test_unregister_nonexistent_recipe_returns_false(self):
        """Test unregistering nonexistent mapping returns False."""
        result = PluginRegistry.unregister_recipe_mapping("nonexistent")
        assert result is False

    def test_unregister_processor_mapping(self):
        """Test unregistering a processor mapping."""
        PluginRegistry.register_processor_mapping("test", ProcessorType.FILL_EMPTY_WITH_VALUE)

        result = PluginRegistry.unregister_processor_mapping("test")

        assert result is True
        assert PluginRegistry.get_processor_mapping("test") is None

    def test_register_plugin_metadata(self):
        """Test registering plugin metadata."""
        PluginRegistry.register_plugin(
            "my_plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author"
        )

        plugins = PluginRegistry.list_plugins()

        assert "my_plugin" in plugins
        assert plugins["my_plugin"]["version"] == "1.0.0"
        assert plugins["my_plugin"]["description"] == "A test plugin"
        assert plugins["my_plugin"]["author"] == "Test Author"


class TestPluginContext:
    """Tests for PluginContext class."""

    def test_context_creation(self):
        """Test creating a context."""
        ctx = PluginContext(
            source_code="df = df.dropna()",
            current_line=5,
            variables={"x": 10},
            dataframes={"df": "input_ds"},
        )

        assert ctx.source_code == "df = df.dropna()"
        assert ctx.current_line == 5
        assert ctx.get_variable("x") == 10
        assert ctx.get_dataframe_source("df") == "input_ds"

    def test_context_defaults(self):
        """Test context default values."""
        ctx = PluginContext()

        assert ctx.source_code == ""
        assert ctx.current_line == 0
        assert ctx.get_variable("x") is None
        assert ctx.get_dataframe_source("df") is None


class TestRegisterPandasMapping:
    """Tests for register_pandas_mapping convenience function."""

    def setup_method(self):
        """Clear registry before each test."""
        PluginRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        PluginRegistry.clear()

    def test_register_recipe_type(self):
        """Test registering a RecipeType mapping."""
        register_pandas_mapping("custom_agg", RecipeType.GROUPING)

        assert PluginRegistry.get_recipe_mapping("custom_agg") == RecipeType.GROUPING

    def test_register_processor_type(self):
        """Test registering a ProcessorType mapping."""
        register_pandas_mapping("custom_fill", ProcessorType.FILL_EMPTY_WITH_VALUE)

        assert PluginRegistry.get_processor_mapping("custom_fill") == ProcessorType.FILL_EMPTY_WITH_VALUE

    def test_register_with_handler(self):
        """Test registering with a custom handler."""
        def my_handler(node, context):
            return None

        register_pandas_mapping("custom", RecipeType.JOIN, handler=my_handler)

        assert PluginRegistry.get_recipe_mapping("custom") == RecipeType.JOIN
        assert PluginRegistry.get_method_handler("custom") is my_handler

    def test_invalid_type_raises(self):
        """Test that invalid type raises error."""
        with pytest.raises(ValueError, match="must be RecipeType or ProcessorType"):
            register_pandas_mapping("custom", "invalid")


class TestPluginDecorators:
    """Tests for plugin decorators."""

    def setup_method(self):
        """Clear registry before each test."""
        PluginRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        PluginRegistry.clear()

    def test_plugin_hook_decorator(self):
        """Test @plugin_hook decorator for pandas methods."""
        @plugin_hook("pandas_method")
        def custom_method_handler(node, context):
            return Transformation(
                transformation_type=TransformationType.FILTER,
                source_dataframe="a",
                target_dataframe="b",
                parameters={},
                source_line=1,
            )

        handler = PluginRegistry.get_method_handler("custom_method_handler")
        assert handler is not None

    def test_register_recipe_handler_decorator(self):
        """Test @register_recipe_handler decorator."""
        @register_recipe_handler(RecipeType.JOIN)
        def custom_join(transformation):
            return {"custom": True}

        handler = PluginRegistry.get_recipe_handler(RecipeType.JOIN)
        assert handler is not None
        assert handler(None) == {"custom": True}

    def test_register_processor_handler_decorator(self):
        """Test @register_processor_handler decorator."""
        @register_processor_handler(ProcessorType.FILL_EMPTY_WITH_VALUE)
        def custom_fill(step):
            return {"filled": True}

        handler = PluginRegistry.get_processor_handler(ProcessorType.FILL_EMPTY_WITH_VALUE)
        assert handler is not None
        assert handler(None) == {"filled": True}


class TestPluginClass:
    """Tests for Plugin base class."""

    def setup_method(self):
        """Clear registry before each test."""
        PluginRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        PluginRegistry.clear()

    def test_plugin_activation(self):
        """Test activating a plugin."""
        class MyPlugin(Plugin):
            name = "my_test_plugin"
            version = "1.0.0"
            description = "A test plugin"

            def register(self):
                self.add_recipe_mapping("my_agg", RecipeType.GROUPING)
                self.add_processor_mapping("my_fill", ProcessorType.FILL_EMPTY_WITH_VALUE)

        plugin = MyPlugin()
        plugin.activate()

        assert PluginRegistry.get_recipe_mapping("my_agg") == RecipeType.GROUPING
        assert PluginRegistry.get_processor_mapping("my_fill") == ProcessorType.FILL_EMPTY_WITH_VALUE

        plugins = PluginRegistry.list_plugins()
        assert "my_test_plugin" in plugins
        assert plugins["my_test_plugin"]["version"] == "1.0.0"

    def test_plugin_deactivation(self):
        """Test deactivating a plugin."""
        class MyPlugin(Plugin):
            name = "deactivate_test"

            def register(self):
                self.add_recipe_mapping("temp_recipe", RecipeType.JOIN)

        plugin = MyPlugin()
        plugin.activate()

        assert PluginRegistry.get_recipe_mapping("temp_recipe") == RecipeType.JOIN

        plugin.deactivate()

        assert PluginRegistry.get_recipe_mapping("temp_recipe") is None

    def test_plugin_with_handler(self):
        """Test plugin with method handler."""
        class HandlerPlugin(Plugin):
            name = "handler_plugin"

            def register(self):
                self.add_method_handler("custom_op", self.handle_custom)

            def handle_custom(self, node, context):
                return Transformation(
                    transformation_type=TransformationType.COLUMN_RENAME,
                    source_dataframe="in",
                    target_dataframe="out",
                    parameters={},
                    source_line=1,
                )

        plugin = HandlerPlugin()
        plugin.activate()

        handler = PluginRegistry.get_method_handler("custom_op")
        assert handler is not None
        result = handler(None, None)
        assert result.transformation_type == TransformationType.COLUMN_RENAME


class TestPluginIntegrationWithAnalyzer:
    """Integration tests for plugins with CodeAnalyzer."""

    def setup_method(self):
        """Clear registry before each test."""
        PluginRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        PluginRegistry.clear()

    def test_custom_handler_called_during_analysis(self):
        """Test that custom handler is called during code analysis."""
        handler_called = {"value": False}

        def custom_handler(node, context):
            handler_called["value"] = True
            return Transformation(
                transformation_type=TransformationType.CUSTOM_FUNCTION,
                source_dataframe="df",
                target_dataframe="df",
                parameters={"custom": True},
                source_line=context.current_line if context else 0,
            )

        PluginRegistry.register_method_handler("custom_method", custom_handler)

        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.custom_method()
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        assert handler_called["value"] is True

        # Find our custom transformation
        custom_transforms = [
            t for t in transformations
            if t.parameters.get("custom") is True
        ]
        assert len(custom_transforms) == 1

    def test_plugin_handler_receives_context(self):
        """Test that plugin handler receives proper context."""
        received_context = {"ctx": None}

        def context_handler(node, context):
            received_context["ctx"] = context
            return None

        PluginRegistry.register_method_handler("context_test", context_handler)

        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.context_test()
"""
        analyzer = CodeAnalyzer()
        analyzer.analyze(code)

        ctx = received_context["ctx"]
        assert ctx is not None
        assert "pd.read_csv" in ctx.source_code
        assert ctx.current_line > 0

    def test_plugin_handler_returns_multiple_transformations(self):
        """Test plugin handler returning multiple transformations."""
        def multi_handler(node, context):
            return [
                Transformation(
                    transformation_type=TransformationType.FILTER,
                    source_dataframe="df",
                    target_dataframe="df",
                    parameters={"step": 1},
                    source_line=1,
                ),
                Transformation(
                    transformation_type=TransformationType.SORT,
                    source_dataframe="df",
                    target_dataframe="df",
                    parameters={"step": 2},
                    source_line=1,
                ),
            ]

        PluginRegistry.register_method_handler("multi_op", multi_handler)

        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.multi_op()
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_transforms = [t for t in transformations if t.transformation_type == TransformationType.FILTER]
        sort_transforms = [t for t in transformations if t.transformation_type == TransformationType.SORT]

        assert len(filter_transforms) >= 1
        assert len(sort_transforms) >= 1
