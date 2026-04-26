# Chapter 12 — Extending py-iku

## What you'll learn

How `PluginRegistry` keeps the library's authoring surface small while making the extension surface — pandas-method handlers, recipe handlers, processor handlers — tractable for teams with domain-specific code. The chapter walks through the three registration entry points (`register_pandas_mapping`, `register_recipe_handler`, `register_processor_handler`), then uses scikit-learn's `StandardScaler` as a worked case study because that is the clearest example of code the core library deliberately does not handle.

## The extension contract

The library's public API has roughly five entry-point functions: `convert`, `convert_with_llm`, `convert_file`, `convert_file_with_llm`, and the model classes. Adding domain-specific behaviour means adding to that surface, but adding to the library itself is a contributor concern, not an extension concern. The plugin registry is the line between the two: contributors edit `RecipeType`/`ProcessorType`/`pandas_mappings.py`; extension authors call `register_*` and ship their plugin alongside their pipeline code.

The contract has four properties.

First, plugins are additive. They register a mapping or a handler under a key (a pandas method name, a `RecipeType`, a `ProcessorType`); they do not replace the library's parser or generator. Calling `register_recipe_mapping("merge", RecipeType.JOIN)` while `merge` is already mapped to `JOIN` raises `ValueError` unless `override=True` is passed.

Second, plugins are class-based with global shorthand. `PluginRegistry()` creates an isolated registry that doesn't share state with the default registry; the global `register_recipe_handler(...)` shorthand operates on the class-level default singleton via `PluginRegistry._get_default()`. Tests that need isolation create their own `PluginRegistry()`; production code uses the global form.

Third, plugins compose with the optimizer. A custom recipe handler that emits a PREPARE recipe will participate in the merge passes from Chapter 10, exactly as built-in PREPARE recipes do. A handler that emits a custom recipe type will not — the optimizer has no rule for unknown types, which is the right default.

Fourth, plugins are introspectable at runtime. `PluginRegistry.list_recipe_mappings()`, `list_processor_mappings()`, and `list_plugins()` return copies of the underlying dicts. A CI assertion that "no plugin overrides core mappings" is straightforward to write.

## The three registration entry points

The three relevant decorators and convenience functions are:

- `register_pandas_mapping(method_name, target_type, handler=None)` — the one-liner. Routes a pandas method by name to either a `RecipeType` (the method becomes its own recipe) or a `ProcessorType` (the method becomes a step inside a PREPARE recipe). An optional handler customizes how the method's arguments are translated.
- `@register_recipe_handler(recipe_type)` — decorator. Registers a function that turns an internal `Transformation` object into a `DataikuRecipe`. Useful when an existing `RecipeType` needs a non-default settings shape.
- `@register_processor_handler(processor_type)` — decorator. Registers a function that turns a step into a `PrepareStep` with a custom settings payload.

For most domain extensions, `register_pandas_mapping` is sufficient. The two decorator forms are for cases where the default settings inferred by the library are not what the team wants emitted into the DSS recipe.

## A minimal worked example

The shortest useful extension routes a domain method name to an existing processor type. Suppose a team has wrapped pandas's `fillna` in a helper called `safe_fill` and wants py-iku to recognize it:

```python
from py2dataiku import register_pandas_mapping, ProcessorType

# After this call, df.safe_fill(...) routes to PREPARE+FillEmptyWithValue
# in both the rule-based path and (via the system prompt's catalog) the LLM path.
register_pandas_mapping("safe_fill", ProcessorType.FILL_EMPTY_WITH_VALUE)
```

The mapping persists for the lifetime of the Python process. To use it, call `convert()` with code that calls `df.safe_fill(...)`. To remove it later (in a test teardown), call `PluginRegistry.unregister_processor_mapping("safe_fill")` — the `unregister_*` family operates on the same default registry as the `register_*` family.

A recipe-level mapping uses the same call site:

```python
from py2dataiku import register_pandas_mapping, RecipeType

# Route a domain method to its own JOIN recipe.
register_pandas_mapping("inner_match", RecipeType.JOIN)
```

For mappings that need argument translation, pass a handler function. The handler's signature is `(node, context) -> Transformation`, where `node` is the AST node for the method call and `context` is a `PluginContext` carrying the source code, the current line, and the tracked-variable map. Handlers are the right place to put logic that needs to inspect arguments.

## Discovering registered handlers

The introspection methods return copies, so iterating them is safe:

```python
from py2dataiku import PluginRegistry

mappings = PluginRegistry.list_recipe_mappings()
for method, recipe_type in mappings.items():
    print(f"  {method:30s} -> {recipe_type.value}")

plugins = PluginRegistry.list_plugins()
for name, info in plugins.items():
    print(f"  plugin: {name} (v{info['version']}) — {info['description']}")
```

A CI guard that asserts no plugin has been registered before a clean conversion runs:

```python
def test_no_plugins_registered():
    assert PluginRegistry.list_recipe_mappings() == {}
    assert PluginRegistry.list_processor_mappings() == {}
    assert PluginRegistry.list_plugins() == {}
```

This is useful for tests that want to characterise the library's default behaviour without contamination from a previously-loaded plugin.

## A custom processor handler

The decorator form lets the handler control the emitted `PrepareStep` directly. A toy example: emit a `FORMULA` step with a custom GREL expression whenever the source uses a domain-specific log transform:

```python
from py2dataiku import register_processor_handler, ProcessorType, PrepareStep


@register_processor_handler(ProcessorType.CREATE_COLUMN_WITH_GREL)
def safe_log_handler(step):
    """Emit a GREL expression that handles zero/negative inputs.

    Routes anything tagged as a log-transform step to a FORMULA processor
    that returns 0 instead of NaN/-Infinity for non-positive inputs.
    """
    column = step.params.get("column", "value")
    output = step.params.get("output_column", f"{column}_log")
    grel = f"if(toNumber({column}) > 0, log(toNumber({column})), 0)"
    return PrepareStep(
        processor_type=ProcessorType.CREATE_COLUMN_WITH_GREL,
        params={
            "column": output,
            "expression": grel,
        },
    )
```

The handler returns a `PrepareStep` rather than mutating the input — the registry composes the returned object back into the flow. The same pattern works for recipe handlers, returning a `DataikuRecipe`.

For the decorator to fire automatically during conversion, the registry has to know the source pattern that triggers it. That is the role of `register_pandas_mapping` — the mapping says "when you see method X, route to processor type Y", and the handler says "when you build a step of type Y, use this code path." The two combine:

```python
# Step 1: route the method name to the processor type.
register_pandas_mapping("safe_log", ProcessorType.CREATE_COLUMN_WITH_GREL)

# Step 2: the @register_processor_handler decorator above customizes
# how the step is built when the processor type matches.
```

Without the mapping, the analyzer never builds a `safe_log` step, so the handler never fires.

## The sklearn case study

This is the only point in the textbook where scikit-learn appears. The reason is that `sklearn.preprocessing.StandardScaler` is the canonical example of code that the core library does not handle: it is not a pandas method, it has stateful `fit`/`transform` semantics that a visual recipe cannot fully express, and the right translation depends on whether the team wants a pure-DSS pipeline or a Python-recipe wrapper.

Two valid translations exist.

**Option A: emit a PREPARE chain.** A simplified `StandardScaler` over a single column applies `(x - mean) / std`. If the team is willing to compute mean and std offline (or via a separate GROUPING recipe) and inject them as constants, the transform itself is a `CREATE_COLUMN_WITH_GREL` step:

```python
from py2dataiku import (
    register_pandas_mapping,
    register_processor_handler,
    ProcessorType,
    PrepareStep,
)


def standard_scaler_handler(node, context):
    """Translate StandardScaler.fit_transform(df[[col]]) to a GREL formula step.

    Assumes mean/std are precomputed and stored in context.variables under
    keys f'{col}_mean' and f'{col}_std'. A real handler would inspect the
    source to identify the column.
    """
    # In a real handler, parse node.args to find the column.
    column = "value"
    mean_var = f"{column}_mean"
    std_var = f"{column}_std"

    grel = (
        f"(toNumber({column}) - ${{{mean_var}}}) / ${{{std_var}}}"
    )
    return PrepareStep(
        processor_type=ProcessorType.CREATE_COLUMN_WITH_GREL,
        params={
            "column": f"{column}_scaled",
            "expression": grel,
        },
    )


register_pandas_mapping(
    "fit_transform",
    ProcessorType.CREATE_COLUMN_WITH_GREL,
    handler=standard_scaler_handler,
)
```

The trade-off is that the team owns the offline mean/std computation. The DSS flow shows the scaling as a PREPARE step rather than as a black-box Python recipe, which preserves lineage and lets downstream consumers see the formula.

**Option B: emit a Python recipe.** When the offline computation is not feasible — for example, when scaling is part of a larger sklearn `Pipeline` — the right translation is to emit a Python recipe that wraps the sklearn call. This is what happens by default when the analyzer cannot map a pandas idiom: `requires_python_recipe=True` propagates through to a `RecipeType.PYTHON` recipe carrying the original source as its body. The team gets a working flow, but the visual representation collapses to a single opaque node.

The trade-off is the inverse of option A. The DSS flow is correct but loses the per-column lineage. Downstream tools that introspect the prepare-step list cannot see what the recipe does without reading the embedded Python.

The library's official position, captured in the `py2dataiku/examples/` folder, is that domain teams should pick the option that matches their downstream tooling. Plugins make both choices expressible without modifying the core code.

For documentation on the `StandardScaler` API itself, see [scikit-learn's `StandardScaler` reference](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html). The library's mapping decision — that sklearn is not a built-in dependency and must be registered as a plugin — is intentional: scikit-learn is an optional install, and pulling its API surface into py-iku's core would force every user to carry it.

## Bundling related extensions

For teams that ship more than two or three handlers, the cleanest way to organise a related group is to write a single function that does all the registrations against an explicit `PluginRegistry` instance and to record the bundle's metadata via `add_plugin`:

```python
from py2dataiku import PluginRegistry
from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.models.prepare_step import ProcessorType


def register_retail_domain(registry: PluginRegistry) -> None:
    """Register all retail-domain extensions on the given registry."""
    registry.add_plugin(
        name="retail_domain",
        version="1.0.0",
        description="Retail-specific pandas extensions for py-iku.",
    )
    # Domain method names that route to existing core types.
    registry.add_recipe_mapping("inner_match", RecipeType.JOIN)
    registry.add_recipe_mapping("complementary_split", RecipeType.SPLIT)
    registry.add_processor_mapping("safe_fill", ProcessorType.FILL_EMPTY_WITH_VALUE)
    registry.add_method_handler("compute_revenue", _handle_revenue)


def _handle_revenue(node, context):
    # ... build and return a Transformation
    ...


# Activate against the default registry (touches the global namespace).
register_retail_domain(PluginRegistry._get_default())
```

The function form is what makes per-test-suite isolation tractable. Each test creates its own registry, activates the bundle on it, and lets the registry fall out of scope at tear-down without touching the global namespace:

```python
from py2dataiku import PluginRegistry

isolated = PluginRegistry()
register_retail_domain(isolated)

# Verify the isolated registry — the global registry is unaffected.
assert isolated.find_recipe_mapping("inner_match") == RecipeType.JOIN
assert PluginRegistry._get_default().find_recipe_mapping("inner_match") is None
```

## Plugins and the optimizer

A custom recipe handler that emits a PREPARE recipe participates in the merge passes from Chapter 10 by virtue of having `recipe_type == RecipeType.PREPARE`. The optimizer does not care which handler emitted the recipe — only that the merge predicates hold (matching dataset edges, single fan-out, both recipes being PREPARE).

A handler that emits a custom recipe type — say, the team registered a new `RecipeType` value via a contributor PR and now wants the optimizer to merge two adjacent instances — has to carry its own merge logic. The default optimizer has no rule for unknown types, which means custom recipes are passed through unchanged. This is the right default: a wrong merge is worse than a missing merge, and the team that introduced the type knows the merge predicate.

For the more common case — a plugin that emits PREPARE and processor steps — the optimizer requires no special configuration. The running example V1's three PREPARE recipes still merge into one even if the third was emitted by a custom handler instead of the rule-based path.

## A walk-through of registration order

When `convert()` runs, the analyzer's lookup order for any given pandas method is:

1. The plugin registry's method-handler map (`PluginRegistry.get_method_handler(name)`).
2. The plugin registry's recipe-mapping map.
3. The plugin registry's processor-mapping map.
4. The library's built-in mapping table (`mappings/pandas_mappings.py`).

The plugin entries take precedence over the built-ins. A team that registers `register_pandas_mapping("merge", RecipeType.JOIN)` does not change behaviour because `merge` already maps to JOIN; a team that registers `register_pandas_mapping("merge", RecipeType.STACK, override=True)` does change behaviour, and the `override=True` is mandatory — the registry refuses to silently shadow an existing mapping.

The lookup order means plugins can specialize built-in methods. A team that wants `merge` with `how="cross"` to emit a custom recipe handler can register a handler keyed on `merge` and inspect the call's arguments to decide whether to delegate to the built-in JOIN handling or emit the custom path. The pattern is extension-by-specialization rather than fork-and-modify.

## Further reading

- [Plugins API reference](../api/plugins.md)
- [Models API reference](../api/models.md)
- [Notebook 03: sklearn pipelines](https://github.com/m-deane/py-iku/blob/main/notebooks/03_sklearn_pipelines.ipynb)
- [scikit-learn StandardScaler reference](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)

## What's next

The chapter sequence ends here; the appendices cover terminology (A), troubleshooting (B), and a one-page cheatsheet (C).
