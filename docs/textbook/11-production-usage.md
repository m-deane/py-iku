# Chapter 11 — Production Usage

## What you'll learn

This chapter covers how to wire `convert()` into a CI pipeline so that the produced flow is asserted-against on every commit, how to load API credentials from `.env.local` without leaking them into shell history or git, how to monitor LLM-path cost via `AnalysisResult.usage`, and how `DSSFlowDeployer` carries a flow object the rest of the way to a running [DSS](appendix-a-glossary.md#dss) instance. The chapter ends with a worked `pytest` example covering V3 of the running example.

If you have not yet read Chapter 12 (extending), this chapter assumes only the rule-based + LLM paths — plugins are not strictly required for production deployment.

## The production contract

A production pipeline that uses py-iku is making three commitments to its users.

The first commitment is determinism. Chapter 2 established that the rule-based path is deterministic by construction; Chapter 7 established that the LLM path is deterministic at `temperature=0` (measured: 3/3 identical runs at temperature=0 across the smoke-test corpus). Both paths produce the same `DataikuFlow` for the same input, so a CI assertion against the flow shape is meaningful.

The second commitment is asserted output. The library does not promise that every conversion is correct; it promises that the conversion is reproducible and inspectable. A team running py-iku in production picks the assertions they care about — [recipe](appendix-a-glossary.md#recipe) count, recipe types in [topological order](appendix-a-glossary.md#topological-order), specific [processor](appendix-a-glossary.md#processor) types in a specific PREPARE step — and writes them into the test suite.

The third commitment is credentials hygiene. The LLM path needs an API key. A production runbook that exposes that key in shell history, in a CI log, or in the git tree will leak it eventually. The patterns in this chapter exist because the project's own smoke test uses them.

## Bare-file CLI form

`py2dataiku <file.py>` is the shortest invocation. The CLI dispatches into the `convert` subcommand by default. For the running example V1 file, the rule-based shape comes out as:

```bash
# Rule-based, JSON output to stdout
py2dataiku convert running_example_v1.py

# LLM-based, requires ANTHROPIC_API_KEY, output to file
py2dataiku convert running_example_v1.py --llm -o flow.json

# YAML format, optimizer disabled
py2dataiku convert running_example_v1.py --format yaml --no-optimize -o flow.yaml
```

The CLI is fine for local exploration. For CI, prefer the Python entry points — they make assertions tractable and give access to `AnalysisResult.usage` for cost tracking.

## Loading credentials from `.env.local`

The repository ships `.env.example` as a committed template and gitignores `.env.local` for the real values. The smoke test's loader is the canonical pattern; it has no dependencies and reads `KEY=value` lines into a dictionary.

```python
# Adapted from scripts/llm_smoke_test.py.
from pathlib import Path
import os


def load_env_local(path: Path = Path(".env.local")) -> dict[str, str]:
    """Tiny KEY=value parser. No deps, no shell interpolation."""
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (
            v.startswith("'") and v.endswith("'")
        ):
            v = v[1:-1]
        out[k.strip()] = v
    return out


# Load into the current process only — never persisted, never logged.
file_env = load_env_local()
key = file_env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
if key:
    os.environ["ANTHROPIC_API_KEY"] = key
```

The pattern has three properties worth being explicit about:

- The key never enters the shell history (no `export ANTHROPIC_API_KEY=...`).
- The key never enters the git history (`.env.local` is gitignored — see the committed `.env.example` for the template).
- The key never enters the conversation transcript (the loader only logs the variable name, never the value).

Every CI runner this codebase has been used in supports the same pattern: load the secret from the runner's secret manager into `.env.local` at job start, run the test, and discard the file at job end.

For shell-style `export` use, prefer the runner's secret-injection mechanism (GitHub Actions `secrets`, GitLab CI `variables`) over a manual `export`. The point is the same: the key should live in one place — the secret manager — and reach the process only through `os.environ`.

## Progress callbacks

`convert_with_llm()` accepts an `on_progress` callable that is invoked at each phase of the pipeline. The signature is `on_progress(phase: str, info: dict) -> None`, and the six phases in order are `start`, `analyzing`, `analyzed`, `generating`, `optimizing` (only when `optimize=True`), and `done`. Exceptions raised inside the callback are silently swallowed so that a buggy progress handler never aborts the conversion.

```python
# Requires ANTHROPIC_API_KEY. See scripts/llm_smoke_test.py for the runner pattern.
from py2dataiku import convert_with_llm


def log_progress(phase: str, info: dict) -> None:
    print(f"[{phase}] {info}")


flow = convert_with_llm(
    open("running_example_v3.py").read(),
    on_progress=log_progress,
)
# [start] {'code_size': 612}
# [analyzing] {'provider': 'anthropic', 'model': 'claude-sonnet-4-6'}
# [analyzed] {'steps': 7, 'datasets': 4, 'complexity': 5}
# [generating] {'step_count': 7}
# [optimizing] {'recipe_count': 3}
# [done] {'recipes': 3, 'datasets': 4}
```

The `analyzed` phase carries the step and [dataset](appendix-a-glossary.md#dataset) counts the LLM extracted before generation; the `optimizing` phase carries the pre-optimization recipe count. A CI runner can compare those to the post-optimization counts in `done` to track how much consolidation the [optimizer](appendix-a-glossary.md#optimizer) performed on each commit.

## Cost monitoring

`AnalysisResult.usage` is the single field to log. For Anthropic, it carries four keys: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens`. The first call in a session writes the cache; the second within the 5-minute window reads it. A monitoring loop that logs all four to a metrics backend (Prometheus, Datadog, an internal database) gives a per-conversion cost line and a cache-hit-rate trend.

```python
# Requires ANTHROPIC_API_KEY in the environment.
from py2dataiku import LLMCodeAnalyzer

analyzer = LLMCodeAnalyzer(provider_name="anthropic")
result = analyzer.analyze(open("running_example_v3.py").read())

usage = result.usage or {}

# Per-conversion cost line for a metrics backend:
metric_payload = {
    "model": result.model_used,
    "input_tokens": usage.get("input_tokens", 0),
    "output_tokens": usage.get("output_tokens", 0),
    "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
    "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
    "warnings": result.warnings,
}
```

The interpretation rule from Chapter 7 holds: a session that does not see `cache_read_input_tokens` rising over time has either disabled caching, exceeded the cache window, or sent a varying system prompt. All three are debuggable without re-running the conversion.

A budget guard at the call site is one line. If `input_tokens + output_tokens` exceeds a threshold, surface it before the next call:

```python
total = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
if total > 8000:
    raise RuntimeError(f"Conversion exceeded token budget: {total}")
```

The library does not enforce this — the right threshold is workload-dependent — but the data is on `usage` waiting to be checked.

## A real `pytest` example

The asserted-output commitment cashes out as test code. The pattern is: convert a known input, walk the produced flow, and assert against the structural properties the running example contracts. V3 of the running example is the right test case — three recipes (`PREPARE`, [`JOIN`](appendix-a-glossary.md#join), [`WINDOW`](appendix-a-glossary.md#window)) in topological order, with explicit assertions on the WINDOW [partitioning](appendix-a-glossary.md#partition).

```python
# tests/test_running_example_v3.py
import pytest
from py2dataiku import convert
from py2dataiku.models.dataiku_recipe import RecipeType


V3_SOURCE = """
import pandas as pd
orders = pd.read_csv('orders.csv')
orders['discount_pct'] = orders['discount_pct'].fillna(0.0)
orders['revenue'] = orders['quantity'] * orders['unit_price'] * (1 - orders['discount_pct'])
orders = orders.rename(columns={'order_date': 'ordered_at'})
orders_clean = orders

customers = pd.read_csv('customers.csv')
products = pd.read_csv('products.csv')
orders_enriched = orders_clean.merge(customers, on='customer_id', how='left')
orders_enriched = orders_enriched.merge(products, on='product_id', how='left')

orders_enriched = orders_enriched.sort_values(['customer_id', 'ordered_at'])
orders_windowed = orders_enriched.copy()
orders_windowed['rolling_30d_revenue'] = (
    orders_windowed
    .groupby('customer_id')['revenue']
    .rolling('30D', on='ordered_at')
    .sum()
    .reset_index(level=0, drop=True)
)
"""


def test_v3_recipe_count():
    flow = convert(V3_SOURCE)
    # V3 expects [PREPARE, JOIN, WINDOW] post-optimization.
    assert len(flow.recipes) == 3


def test_v3_recipe_types_topological():
    flow = convert(V3_SOURCE)
    # flow.recipes is already in build (topological) order; for an explicit
    # graph-based check, filter topological_sort() to recipe nodes:
    #   ordered = flow.graph.topological_sort()
    #   recipes = [n for n in ordered if flow.graph.get_node(n).is_recipe()]
    types = [r.recipe_type for r in flow.recipes]
    assert types == [RecipeType.PREPARE, RecipeType.JOIN, RecipeType.WINDOW]


def test_v3_window_configuration():
    flow = convert(V3_SOURCE)
    window = next(r for r in flow.recipes if r.recipe_type == RecipeType.WINDOW)
    assert window.partition_columns == ["customer_id"]
    assert "ordered_at" in window.order_columns


def test_v3_round_trip_serialization():
    flow = convert(V3_SOURCE)
    rebuilt = type(flow).from_dict(flow.to_dict())
    assert len(rebuilt.recipes) == len(flow.recipes)
    assert [r.recipe_type for r in rebuilt.recipes] == [
        r.recipe_type for r in flow.recipes
    ]
```

The test suite is what enforces the production contract. If a future version of the library changes how merge behaviour is triggered, the recipe-count assertion will catch it before the change reaches users. If the JOIN-merging optimization changes its mind about whether two `merge` calls collapse into one JOIN, the topological-order assertion will catch it. The cost of the test is one rule-based conversion per commit — microseconds.

For the LLM path, the same test pattern applies, but the test should run only when the API key is present:

```python
import os
import pytest
from py2dataiku import convert_with_llm


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="LLM-path test requires ANTHROPIC_API_KEY",
)
def test_v3_llm_path_matches_rule_based():
    flow_llm = convert_with_llm(V3_SOURCE)
    types = {r.recipe_type.value for r in flow_llm.recipes}
    # Both paths should produce a JOIN and a WINDOW for V3.
    assert "join" in types
    assert "window" in types
```

The test is asserting against a property both paths share, not against a byte-level identity. Chapter 7 already noted two LLM-vs-rule-based divergences (`drop_duplicates` and `SELECT_COLUMNS` settings) that would defeat a strict equality check.

## Wiring it into CI

A GitHub Actions step that runs the test suite uses the runner's secret manager to populate `.env.local` before the test step. The secret-management primitive is the runner's; py-iku reads `os.environ` like any other library:

```yaml
# .github/workflows/test.yml — fragment
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev,llm]"
      - name: Provision .env.local
        run: |
          echo "ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}" > .env.local
      - run: python -m pytest tests/ -v
```

The `python -m pytest tests/ -v` step is the same command developers run locally. The `.env.local` file is provisioned at job start, gitignored from the workspace, and discarded with the runner at job end. The smoke test (`scripts/llm_smoke_test.py`) is the canonical end-to-end form: it loads `.env.local`, runs `convert_with_llm` over seven snippets, and exits 0 on full pass. Treat it as a reference for any new CI integration.

## Configuration file precedence

`Py2DataikuConfig` accepts toml, yaml, and rc-style files via `load_config()`. The precedence order is: explicit kwargs to the function call, then environment variables, then the config file. A typical project drops a `pyproject.toml` section or a `.py2dataikurc` at the repo root and uses environment variables for per-environment overrides:

```toml
# pyproject.toml — optional [tool.py2dataiku] block
[tool.py2dataiku]
default_provider = "anthropic"
default_model = "claude-sonnet-4-6"
optimize = true
```

```python
from py2dataiku import find_config_file, load_config

config_path = find_config_file()  # walks parents until it finds a config file
if config_path is not None:
    config = load_config(config_path)
    # Use config.default_provider, config.default_model, etc.
```

The library does not require a config file. Every option has a sensible default; the file is for teams that want to centralize defaults across multiple repos.

## Deploying the flow to DSS

The textbook's scope ends at the flow object — DSS execution is not in scope, and the flow is only useful in production once it is shipped to a DSS instance. `DSSFlowDeployer` is the bridge.

```python
from py2dataiku import convert, DSSFlowDeployer


flow = convert(open("running_example_v3.py").read())

# Dry-run first — validates the flow without making API calls.
dry = DSSFlowDeployer(
    host="https://dss.example.com",
    api_key="...",
    project_key="RETAIL_REVENUE",
    dry_run=True,
)
result = dry.deploy(flow)
assert result.success, result.errors

# Real deploy: requires the dataikuapi package and a reachable DSS instance.
deployer = DSSFlowDeployer(
    host="https://dss.example.com",
    api_key="...",
    project_key="RETAIL_REVENUE",
)
result = deployer.deploy(flow)
print(f"created {len(result.datasets_created)} datasets, "
      f"{len(result.recipes_created)} recipes")
```

`deploy()` validates the flow, topologically sorts the graph, creates datasets first, then creates recipes in dependency order. The `dataikuapi` package is the official Dataiku Python client (see [Dataiku DSS Python API documentation](https://doc.dataiku.com/dss/latest/python-api/outside-usage.html)); the deployer surfaces a clear `ExportError` if it is not installed. The `DeploymentResult.success` property is the right thing to gate on in CI: it is `True` only when no error was recorded during deploy.

> **Operational callouts.** Deployment runs share two cross-cutting concerns: (1) cost tracking — see the [Cheatsheet's token-usage formula](appendix-c-cheatsheet.md#token-usage) for the rough Anthropic cost estimate; and (2) transient provider failures — see the [retry pattern in Appendix B](appendix-b-troubleshooting.md#providererror-rate-limited-by-the-llm-provider) for the canonical sleep-and-retry loop.

## Versioning and reproducibility

Two version pins make a CI run reproducible. The first is the `py-iku` version itself — pin it in `requirements.txt` or `pyproject.toml` so that a library upgrade does not silently change the produced flow. The second is the LLM model name. The provider defaults to a specific model (`claude-sonnet-4-6` for Anthropic, `gpt-4o` for OpenAI), but a major-version model upgrade can change the produced flow even at temperature=0. Pin the model explicitly:

```python
flow = convert_with_llm(source, model="claude-sonnet-4-6")
```

A test that hits the LLM path without pinning the model is asserting against a moving target. Pin both, and the only remaining drift is the model's own behavior at temperature=0 — which is what the experiment in Chapter 7 was designed to characterize.

## Failure-handling protocol

Three exceptions deserve separate handling because each signals a different fix. The hierarchy from `py2dataiku.exceptions` makes the distinction explicit:

```python
from py2dataiku import (
    convert, convert_with_llm,
    ConfigurationError,
    LLMResponseParseError,
    InvalidPythonCodeError,
    ValidationError,
)


def safe_convert(source: str, prefer_llm: bool = True):
    """Convert with graceful degradation across the LLM and rule-based paths."""
    if prefer_llm:
        try:
            return convert_with_llm(source)
        except ConfigurationError:
            # API key missing — fall back to rule-based without complaint.
            pass
        except LLMResponseParseError as exc:
            # Model returned malformed JSON — log and fall back.
            print(f"LLM parse error ({exc}); falling back to rule-based")
        except ValidationError as exc:
            # Parsed flow failed structural validation — log and fall back.
            print(f"LLM produced invalid flow ({exc}); falling back to rule-based")
    try:
        return convert(source)
    except InvalidPythonCodeError as exc:
        # The source itself is unparseable — re-raise; nothing to fall back to.
        raise
```

The protocol is opinionated: API-key issues fall back silently because they are environmental, not data-related; LLM parse errors fall back with a log line because they may indicate a transient model issue; structural validation errors fall back with a log line because they indicate a model hallucination that the post-process did not catch. `InvalidPythonCodeError` is re-raised because no path can recover from unparseable source.

The same protocol pattern works in CI: a test that wraps `safe_convert` and asserts against the result will pass whether the LLM path is available or not. That property is what makes the test runnable on a developer laptop without API keys and on a CI runner with them.

## Pinning a single conversion in an integration test

A team that wants to track a specific conversion's recipe shape over time pins it as a test fixture. The pattern is to record the expected `flow.to_dict()` once, save it as a JSON fixture, and assert against it on every test run:

```python
import json
from pathlib import Path
from py2dataiku import convert, DataikuFlow


FIXTURE = Path(__file__).parent / "fixtures" / "v3_flow.json"


def test_v3_matches_pinned_fixture():
    flow = convert(open("running_example_v3.py").read())
    actual = flow.to_dict(include_timestamp=False)

    if not FIXTURE.exists():
        # First run: write the fixture. Re-run the test to assert.
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2, sort_keys=True))
        pytest.skip("Fixture freshly written; re-run to assert.")

    expected = json.loads(FIXTURE.read_text())
    assert actual == expected
```

The `include_timestamp=False` argument to `to_dict()` strips the generation timestamp from the output, which is the dominant byte-level instability between identical conversions. Without that flag, the same conversion run twice produces dicts that differ in one field. The flag is what makes the fixture-comparison pattern viable.

This is the strongest assertion the library supports: byte-level identity of the produced flow. It is also the most brittle — a library upgrade that legitimately changes the produced flow (a new optimizer rule, a corrected mapping) will fail this test until the fixture is regenerated. Use it for high-stakes conversions where any change should be reviewed; prefer the property-based assertions (recipe count, recipe types) for everything else.

## Further reading

- [Cheatsheet](appendix-c-cheatsheet.md) — full reference for production patterns
- [Troubleshooting](appendix-b-troubleshooting.md)
- [Installation guide](../getting-started/installation.md) — for CI runner setup
- [Glossary](appendix-a-glossary.md)
- [Configuration API reference](../api/configuration.md)
- [Integration API reference](../api/integration.md)
- [Notebook 04: expert patterns](https://github.com/m-deane/py-iku/blob/main/notebooks/04_expert.ipynb)
- [Dataiku DSS Python API documentation](https://doc.dataiku.com/dss/latest/python-api/outside-usage.html)

## What's next

Chapter 12 covers the plugin system that lets domain teams register custom recipe and processor handlers without modifying the library.
