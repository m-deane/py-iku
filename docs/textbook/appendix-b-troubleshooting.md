# Appendix B — Troubleshooting

## Scope

The ten errors a user is most likely to hit when running py-iku, ordered roughly by frequency. Each entry has a symptom (what the user sees), a cause (what is actually going wrong), a fix (the specific code or configuration change that resolves it), and a related-chapter pointer for context. Where a symptom can have multiple causes, the most common one is described here and the rarer ones are deferred to the chapter linked at the end of the entry.

## Index

Quick-jump to a symptom by anchor:

- [ConfigurationError: missing API key](#configurationerror-missing-api-key)
- [LLMResponseParseError: provider returned non-conforming JSON](#llmresponseparseerror-provider-returned-non-conforming-json)
- [InvalidPythonCodeError: source did not parse](#invalidpythoncodeerror-source-did-not-parse)
- [ProviderError: rate-limited by the LLM provider](#providererror-rate-limited-by-the-llm-provider)
- [Unknown processor name dropped from suggested_processors](#unknown-processor-name-dropped-from-suggested_processors)
- [Filter mis-routing: predicate became a Python recipe](#filter-mis-routing-predicate-became-a-python-recipe)
- [Zero recipes returned from a non-empty file](#zero-recipes-returned-from-a-non-empty-file)
- [ImportError for matplotlib or cairosvg](#importerror-for-matplotlib-or-cairosvg)
- [Broken DAG after manual flow editing](#broken-dag-after-manual-flow-editing)
- [Slow conversion on large files (token budget)](#slow-conversion-on-large-files-token-budget)

## ConfigurationError: missing API key

### Symptom

`convert_with_llm(code, provider="anthropic")` raises `py2dataiku.exceptions.ConfigurationError: ANTHROPIC_API_KEY not set`. The rule-based `convert(code)` call (no API key required) succeeds against the same source.

### Cause

The LLM analyzer requires a provider API key. The library reads `ANTHROPIC_API_KEY` (for Anthropic) or `OPENAI_API_KEY` (for OpenAI) from the process environment, from a `.env.local` file in the working directory, or from the `api_key=` keyword passed directly to `convert_with_llm`. None of those sources had a value.

### Fix

Set the key in a `.env.local` next to the script:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Or pass it explicitly to `convert_with_llm`:

```python
from py2dataiku import convert_with_llm
flow = convert_with_llm(source, provider="anthropic", api_key="sk-ant-...")
```

Hard-coding the key in source is a known anti-pattern — prefer the env-var or `.env.local` form.

**Related**: Chapter 11 covers configuration precedence in detail.

## LLMResponseParseError: provider returned non-conforming JSON

### Symptom

`convert_with_llm(..., provider="anthropic")` raises `LLMResponseParseError: response did not match expected schema`. The exception's `raw_response` attribute holds the provider's reply.

### Cause

The LLM produced a reply that did not parse against the structured-output schema the library handed it. With temperature=0 this is uncommon but happens when the input code is unusually short, unusually long, or contains characters that interact badly with the system prompt.

### Fix

First, retry. The library does not retry automatically because retries are a policy decision. If the retry also fails, fall back to the rule-based path for the affected file:

```python
try:
    flow = convert_with_llm(source, provider="anthropic")
except LLMResponseParseError:
    flow = convert(source)  # rule-based fallback
```

If a specific file consistently triggers the error, file an issue with the input attached so the prompt can be tuned.

**Related**: Chapter 7.

## InvalidPythonCodeError: source did not parse

### Symptom

`convert(source)` raises `InvalidPythonCodeError: failed to parse Python source`. The exception holds the underlying `SyntaxError`.

### Cause

The input is not valid Python. The most common variant is a Jupyter cell that begins with `%pip install ...` or another magic line; the `%` is not Python syntax and the AST parser rejects the file before any analysis runs.

### Fix

Strip Jupyter magics before passing the source to `convert`. The library does not strip magics automatically because the same syntax is occasionally meaningful in non-Jupyter contexts. A one-line filter is enough:

```python
clean = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("%"))
flow = convert(clean)
```

If the source is genuinely invalid Python (not magics), the underlying `SyntaxError` message points at the offending line.

**Related**: Chapter 2.

## ProviderError: rate-limited by the LLM provider

### Symptom

`convert_with_llm(..., provider="anthropic")` raises `ProviderError: rate limit exceeded (429)`. The exception holds the provider's retry-after hint.

### Cause

The provider's per-minute or per-day token budget for the API key has been exceeded. This is most common when batch-converting an entire codebase in a single run.

### Fix

Throttle the calls. The library does not implement automatic retry-with-backoff because the right retry policy depends on the provider's plan tier. A simple `time.sleep(retry_after)` loop is sufficient for one-off batch jobs:

```python
import time
from py2dataiku.exceptions import ProviderError
for path in paths:
    while True:
        try:
            flow = convert_with_llm(open(path).read(), provider="anthropic")
            break
        except ProviderError as e:
            time.sleep(e.retry_after or 30)
```

For sustained batch conversion, consider running the rule-based path in CI and reserving the LLM path for files that the rule-based path misclassifies.

**Related**: Chapter 11.

## Unknown processor name dropped from suggested_processors

### Symptom

The LLM analyzer returns a flow but a processor named in the input prompt does not appear in the resulting recipe steps. `flow.warnings` contains a line like `dropped unknown processor 'COLUMN_FOO'`.

### Cause

The LLM occasionally hallucinates a processor name that is not in the `ProcessorType` enum. The validator catches the unknown name and drops the step rather than emitting an invalid `PrepareStep`. The flow is still produced, but it is missing a step.

### Fix

Inspect `flow.warnings` after every LLM-mode conversion. If a step was dropped, either rewrite the offending pandas operation in a form the rule-based path handles, or register a custom processor handler for the missing operation:

```python
from py2dataiku.plugins import register_processor_handler
@register_processor_handler("CUSTOM_NAME")
def _handler(step):
    ...
```

**Related**: Chapter 7 (LLM failure modes), Chapter 12 (extension surface).

## Filter mis-routing: predicate became a Python recipe

### Symptom

A pandas line `df = df[df["a"] > 0 & (df["b"].isin(["x", "y"]))]` produced a `PYTHON` recipe wrapping the original code instead of a `PREPARE` recipe with the appropriate filter processors (or a `SPLIT` recipe in the complementary-filter case).

### Cause

The compound predicate did not match any of the AST patterns the rule-based analyzer recognises for predicates. The fallback for an unrecognised filter is a `PYTHON` recipe — correct, but invisible to lineage. The most common cause is operator precedence: `a > 0 & b.isin(...)` parses as `a > (0 & b.isin(...))` because `&` has higher precedence than `>` in Python.

### Fix

Add explicit parentheses: `(df["a"] > 0) & (df["b"].isin(["x", "y"]))`. The corrected predicate matches the multi-clause pattern and the filter becomes a `PREPARE` recipe with `FilterOnValue` and `FilterOnNumericRange` processor steps (or a single `FilterOnFormula` step for compound conditions). Note: there is no `RecipeType.FILTER` — filtering is always either a processor inside `PREPARE` or, for complementary predicates, a `SPLIT` recipe with multiple outputs.

**Related**: Chapter 8.

## Zero recipes returned from a non-empty file

### Symptom

`convert(source)` returns a `DataikuFlow` with `len(flow.recipes) == 0` even though the input has dataframe operations.

### Cause

The input parsed (no `InvalidPythonCodeError`) but the analyzer found no operations it could classify. The most common reason is that the dataframe variable was never assigned from a recognised source — for instance, `df` came from a function argument rather than from `pd.read_csv` or a literal `pd.DataFrame(...)`.

### Fix

Ensure the script begins with a recognisable read: `pd.read_csv`, `pd.read_parquet`, `pd.DataFrame(...)`, or an explicit `# input: dataset_name` comment. The analyzer uses the read call to anchor the input dataset; without an anchor it cannot decide where the flow begins.

**Related**: Chapter 2 (the V1 example uses `pd.read_csv` for exactly this reason), Chapter 4.

## ImportError for matplotlib or cairosvg

### Symptom

`flow.visualize(format="png")` raises `ImportError: matplotlib is required for the matplotlib visualizer` or `ImportError: cairosvg is required for PNG export`.

### Cause

The visualization extras are optional. The base install pulls in only the SVG and ASCII visualizers; PNG and matplotlib-based renders require `pip install py-iku[viz]`.

### Fix

Install the extras:

```
pip install -e ".[viz]"
```

Or use a format that does not require them: `flow.visualize(format="svg")`, `flow.visualize(format="ascii")`, `flow.visualize(format="mermaid")`.

**Related**: Chapter 2 has the visualization walkthrough.

## Broken DAG after manual flow editing

### Symptom

`flow.graph.topological_sort()` raises `CycleError: cycle detected involving recipes [a, b, c]` after the user manually appended recipes to `flow.recipes`.

### Cause

Direct mutation of `flow.recipes` bypasses the dependency tracking that `FlowGraph` maintains. Adding a recipe whose inputs reference an output that does not yet exist, or whose output is consumed by an upstream recipe, produces a cycle.

### Fix

Avoid mutating `flow.recipes` and `flow.datasets` directly. Use `flow.add_recipe(recipe)`, which validates the recipe's inputs against existing datasets and refuses to introduce a cycle. If the manual edit was already made, drop the offending recipe and re-add it through the validated path.

**Related**: Chapter 3 covers `FlowGraph`; Chapter 10 covers the optimizer's reliance on a valid DAG.

## Slow conversion on large files (token budget)

### Symptom

`convert_with_llm(source, provider="anthropic")` takes 60+ seconds for a single file or raises `ProviderError: context length exceeded`.

### Cause

The LLM analyzer sends the full source as input. For files over roughly 1500 lines the token budget approaches the provider's context limit, latency grows, and a few-thousand-line file does not fit at all.

### Fix

Chunk the file by top-level function or class and convert each chunk separately, then merge the resulting flows with `DataikuFlow.merge`:

```python
chunks = split_by_top_level_def(source)
flows = [convert_with_llm(c, provider="anthropic") for c in chunks]
final = flows[0]
for f in flows[1:]:
    final = final.merge(f)
```

For files that are hot in CI, prefer the rule-based path — its cost is O(LOC) parsing, not O(LOC) tokens, and it does not have the context-length ceiling.

**Related**: Chapter 7 (LLM cost shape), Chapter 11 (CI integration).
