# Plugin System

Extension system for custom recipe handlers, processor handlers, and pandas mappings.

---

## PluginRegistry

Central registry for extending py-iku with custom behavior.

```python
from py2dataiku import PluginRegistry
```

The registry is instance-based with a global default instance for convenience.

### Creating an Instance

```python
# Use global default (shared state)
from py2dataiku.plugins import PluginRegistry
registry = PluginRegistry.default()

# Create isolated instance
registry = PluginRegistry()
```

### Registering Mappings

Map pandas method names to Dataiku recipe or processor types:

```python
from py2dataiku import RecipeType, ProcessorType

# Recipe mapping: pandas method -> Dataiku recipe type
registry.add_recipe_mapping("df.my_custom_join", RecipeType.JOIN)

# Processor mapping: pandas method -> Dataiku processor type
registry.add_processor_mapping("df.custom_transform", ProcessorType.STRING_TRANSFORMER)
```

### Registering Handlers

Custom handler functions for recipe/processor generation:

```python
# Recipe handler
def custom_join_handler(recipe, transformation):
    recipe.join_type = JoinType.LEFT
    return recipe

registry.add_recipe_handler(RecipeType.JOIN, custom_join_handler)

# Processor handler
def custom_processor_handler(step, transformation):
    step.params["custom_param"] = True
    return step

registry.add_processor_handler(ProcessorType.STRING_TRANSFORMER, custom_processor_handler)

# Method handler (called during AST analysis)
def custom_method_handler(node, context):
    return Transformation(...)

registry.add_method_handler("my_custom_method", custom_method_handler)
```

### Looking Up Registrations

```python
registry.find_recipe_mapping("df.my_custom_join")       # -> Optional[RecipeType]
registry.find_processor_mapping("df.custom_transform")   # -> Optional[ProcessorType]
registry.find_method_handler("my_custom_method")         # -> Optional[Callable]
registry.find_recipe_handler(RecipeType.JOIN)             # -> Optional[Callable]
registry.find_processor_handler(ProcessorType.STRING_TRANSFORMER)  # -> Optional[Callable]
```

### Removing Registrations

```python
registry.remove_recipe_mapping("df.my_custom_join")      # -> bool
registry.remove_processor_mapping("df.custom_transform")  # -> bool
registry.remove_method_handler("my_custom_method")        # -> bool
registry.clear_all()                                       # Remove everything
```

### Copying

```python
registry_copy = registry.copy()  # Independent copy
```

---

## Convenience Functions

Global convenience functions that operate on the default registry:

```python
from py2dataiku import (
    register_recipe_handler,
    register_processor_handler,
    register_pandas_mapping,
    plugin_hook,
)
```

### register_pandas_mapping()

```python
register_pandas_mapping("df.my_method", RecipeType.PREPARE)
```

### register_recipe_handler()

Decorator for registering recipe handlers:

```python
@register_recipe_handler(RecipeType.PYTHON)
def handle_python_recipe(recipe, transformation):
    recipe.code = "# custom code"
    return recipe
```

### register_processor_handler()

Decorator for registering processor handlers:

```python
@register_processor_handler(ProcessorType.COLUMN_RENAMER)
def handle_rename(step, transformation):
    step.params["prefix"] = "cleaned_"
    return step
```

### plugin_hook()

Decorator for registering generic plugin hooks:

```python
@plugin_hook("pre_convert")
def before_conversion(code, context):
    return code.replace("old_api", "new_api")
```

---

## Class-Level Registration

For backward compatibility, class-level methods are also available:

```python
PluginRegistry.register_recipe_mapping("method", RecipeType.JOIN)
PluginRegistry.register_processor_mapping("method", ProcessorType.BINNER)
PluginRegistry.register_method_handler("method", handler_fn)
PluginRegistry.register_recipe_handler(RecipeType.JOIN, handler_fn)
PluginRegistry.register_processor_handler(ProcessorType.BINNER, handler_fn)
```

These delegate to the global default instance.
