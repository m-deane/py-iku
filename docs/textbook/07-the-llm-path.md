# Chapter 7 — The LLM Path

## What you'll learn

This chapter explains how `convert_with_llm()` translates Python source into a `DataikuFlow`, why temperature=0 and prompt caching are the two settings that decide whether the LLM path is fit for CI, and how to read `AnalysisResult.usage` to keep per-conversion cost predictable. The chapter ends with the failure modes worth catching by name and a calibration of where the LLM path beats the rule-based path and where it does not.

## Why two paths exist

The library ships two analyzers. The rule-based path (`convert()`) walks the AST and applies a fixed mapping table; the LLM path (`convert_with_llm()`) sends the source to an LLM and parses a structured JSON response back into the same flow model. Both terminate in the same `DataikuFlow` object — only the front half of the pipeline differs.

Rule-based wins on three axes: it is offline, it is microseconds-fast, and it has no per-call cost. LLM-based wins on one axis: it recognizes patterns the AST mapping has not been written for. This is not a hypothetical advantage.

The `scripts/llm_smoke_test.py` corpus contains snippets — `df['rolling_avg'] = df['value'].rolling(7).mean()`, `top10 = df.nlargest(10, 'spend')`, `df[(df['amount'] > 1000) & (df['country'] != 'US')]` — that the rule-based path can mis-shelf into a generic PREPARE recipe. The LLM path routes them to WINDOW, TOP_N, and either SPLIT or PREPARE+`FilterOnFormula` respectively, because those rules are stated explicitly in the system prompt.

A short decision rule:

- The script is short, idiomatic pandas, and runs in CI on every commit: rule-based.
- The script is long, contains conditional branches, or uses pandas idioms outside the canonical mapping table: LLM-based.
- The script will be re-converted thousands of times across a corpus: rule-based, with the LLM path used as a fallback for the few snippets that flag warnings.

The rule-based path is the right default for the running example V1 through V4 — those versions are exactly the patterns the AST analyzer was written to catch. V5 introduces the complementary-filter pattern that benefits from the LLM path's explicit mapping rule for `df[cond]` and `df[~cond]` (see `py2dataiku/llm/analyzer.py`).

## The interface

The entry point is `convert_with_llm(code, provider="anthropic", ...)`. It dispatches through `LLMCodeAnalyzer.analyze()` (which calls the provider) and `LLMFlowGenerator.generate()` (which folds the parsed `AnalysisResult` into a `DataikuFlow`). Both halves are public; a tested workflow is to call `analyze()` directly when you only want the structured JSON.

```python
# Requires ANTHROPIC_API_KEY in the environment. See scripts/llm_smoke_test.py
# for the credentials-safe runner pattern using .env.local.
from py2dataiku import convert_with_llm

# A fragment of the running-example V3 — rolling 30-day revenue per customer.
source = """
import pandas as pd
orders = pd.read_csv('orders.csv')
orders = orders.rename(columns={'order_date': 'ordered_at'})
orders = orders.sort_values(['customer_id', 'ordered_at'])
orders['rolling_30d_revenue'] = (
    orders.groupby('customer_id')['revenue']
          .rolling('30D', on='ordered_at').sum()
          .reset_index(level=0, drop=True)
)
"""

flow = convert_with_llm(source, provider="anthropic")
assert any(r.recipe_type.value == "window" for r in flow.recipes)
```

For local development without API keys, `MockProvider` lets the same call site exercise the parser without spending a token:

```python
from py2dataiku import LLMCodeAnalyzer
from py2dataiku.llm.providers import MockProvider

mock_response = """{
  "code_summary": "Rolling 30-day revenue per customer.",
  "total_operations": 2,
  "complexity_score": 2,
  "datasets": [
    {"name": "orders", "source": "orders.csv", "is_input": true, "is_output": false}
  ],
  "steps": [
    {"step_number": 1, "operation": "read_data", "description": "Read orders.csv",
     "output_dataset": "orders", "suggested_recipe": "sync"},
    {"step_number": 2, "operation": "window_function",
     "description": "30-day rolling revenue per customer_id",
     "input_datasets": ["orders"], "output_dataset": "orders",
     "suggested_recipe": "window"}
  ],
  "recommendations": [], "warnings": []
}"""

provider = MockProvider(responses={"rolling": mock_response})
analyzer = LLMCodeAnalyzer(provider=provider)
result = analyzer.analyze(
    "orders['rolling_30d_revenue'] = "
    "orders.groupby('customer_id')['revenue'].rolling('30D').sum()  # rolling"
)
assert result.steps[1].suggested_recipe == "window"
```

The mock provider records calls in `provider.calls`, which is useful in unit tests that want to assert on the constructed prompt rather than the parsed response.

## Determinism: temperature, seed, and caching

Code-to-flow conversion is a structured extraction task, not a creative one. Two runs over the same input must produce the same flow, otherwise the output cannot be asserted-against in CI. Three settings make this possible.

**Temperature.** Both `AnthropicProvider` and `OpenAIProvider` default `temperature` to 0.0. The rationale comes from a controlled experiment captured in this project's review log: re-running a `df.groupby(...).agg(...)` snippet three times at the post-fix default produced 1/3 unique outputs (perfect determinism), where the same snippet at the pre-fix default of 1.0 produced 5/5 distinct outputs across five attempts. The measured baseline is **3/3 identical runs at temperature=0** across the smoke-test corpus. Any caller that wants run-to-run drift — for example, to sample alternate flow shapes during development — can pass `temperature=0.7` to `convert_with_llm`.

**Seed.** `OpenAIProvider` additionally forwards `seed=42` to the OpenAI API for additional determinism. Anthropic's Messages API does not currently expose a seed parameter, so for the Anthropic provider determinism rests on temperature alone plus the model's own behavior at temperature 0.

**Prompt caching.** The system prompt is large — auto-generated from the full `ProcessorCatalog` plus the mapping rules and three worked examples — and it is identical across calls within a session. `AnthropicProvider.complete()` sends the system prompt as a structured block with `cache_control: {"type": "ephemeral"}` rather than as a plain string, which lets the API return a cache hit on subsequent calls within the ~5-minute cache window (see [Anthropic's prompt caching documentation](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)). Cached input tokens are billed at roughly 10% of the regular input rate, so a session that converts ten files in five minutes pays full freight on the first call and ~10% on each of the remaining nine.

Caching is on by default. The `disable_cache=True` constructor flag falls back to the legacy string `system=...` form for tests or environments where the 5-minute server-side cache state is undesirable.

## Reading `AnalysisResult.usage`

Cost monitoring is a single field. After `analyzer.analyze(code)` returns, `result.usage` contains the dictionary the provider built from the response's `usage` block. For the Anthropic provider:

```python
from py2dataiku import LLMCodeAnalyzer

# Requires ANTHROPIC_API_KEY. See scripts/llm_smoke_test.py for the runner pattern.
analyzer = LLMCodeAnalyzer(provider_name="anthropic")
result = analyzer.analyze(open("running_example_v5.py").read())

usage = result.usage or {}
print("input_tokens:           ", usage.get("input_tokens"))
print("output_tokens:          ", usage.get("output_tokens"))
print("cache_read_input_tokens:", usage.get("cache_read_input_tokens"))
print("cache_creation_tokens:  ", usage.get("cache_creation_input_tokens"))
```

The first call in a session shows a non-zero `cache_creation_input_tokens` and zero `cache_read_input_tokens`. The second call within the cache window inverts that: `cache_creation_input_tokens` drops to zero and `cache_read_input_tokens` rises to the size of the cached system prompt. A session that does not see `cache_read_input_tokens` rising over time has either disabled caching, exceeded the cache window, or sent a varying system prompt — all three are debuggable by reading this field.

`OpenAIProvider` populates only `input_tokens` and `output_tokens` because the OpenAI Chat Completions API does not currently expose cache-hit counters.

## The system prompt is generated, not authored

`ANALYSIS_SYSTEM_PROMPT` is built once at import time by `_build_analysis_system_prompt()`. The processor catalog section comes from `ProcessorCatalog.PROCESSORS` and is regenerated whenever the catalog changes; the prompt cannot drift away from the actual code. The prompt carries:

- A short list of Dataiku recipe types with one-line descriptions.
- A `## Mapping Rules` section enumerating the non-obvious cases — `df.melt()` routes to PREPARE+`FoldMultipleColumns` (not the PIVOT recipe), `df[df.x > N]` routes to PREPARE+`FilterOnNumericRange` (not `FilterOnValue`, which is for string matching), `df[cond]` and `df[~cond]` collapse to a single multi-output SPLIT, and so on.
- A canonical-name table for aggregation functions: `AVG` not `MEAN`, `COUNTD` not `NUNIQUE`. These names match the DSS recipe API.
- An `## Output Discipline` section requiring exactly one JSON object, valid `OperationType` enum values, canonical processor names, and same-variable reuse for self-mutating ops like `df = df.dropna()`.
- Three worked examples covering a control case (groupby+sum), the confusion case (`pd.melt` is unpivot, not pivot), and a multi-recipe ETL.

These are stated as flat rules — the model does not need to infer them from training data, and the few-shot examples set the exact JSON shape that `AnalysisResult.from_dict` expects.

## Post-parse validation

The model can still hallucinate. The most common failure mode observed in the determinism prober was the LLM inventing processor names that do not exist in `ProcessorCatalog` — for example, sklearn-flavoured names invented when the source happened to mention scaling. `LLMCodeAnalyzer._post_process()` defends against this:

```python
canonical_names = {info.name for info in ProcessorCatalog.PROCESSORS.values()}
for step in result.steps:
    valid, invalid = [], []
    for proc_name in step.suggested_processors:
        (valid if proc_name in canonical_names else invalid).append(proc_name)
    if invalid:
        step.suggested_processors = valid
        result.warnings.append(
            f"Step {step.step_number}: dropped unknown processor names {invalid}"
        )
```

Invalid names are dropped, valid names are kept, and the conversion proceeds with a warning on `result.warnings`. The downstream `LLMFlowGenerator` never tries to look up a name that the catalog does not recognize. A caller that wants to fail loudly on warnings can do so:

```python
result = analyzer.analyze(code)
if result.warnings:
    raise RuntimeError(f"LLM produced warnings: {result.warnings}")
```

The same post-process pass also coerces `step.operation` values back into the `OperationType` enum (mapping unknown strings to `UNKNOWN`), renumbers steps to be sequential, and infers a `suggested_recipe` for any step the model left blank.

## Failure modes worth catching

Three exceptions are worth distinguishing in production code:

- `ConfigurationError` — typically "no API key found". Caller fix: set `ANTHROPIC_API_KEY` (or pass `api_key=`) or fall back to rule-based.
- `LLMResponseParseError` — the response was not valid JSON, or the JSON did not match the `AnalysisResult` schema. Caller fix: retry, or fall back to rule-based.
- `ValidationError` — the parsed flow failed structural validation (e.g. a recipe's input dataset was not declared). Caller fix: read the message; usually a model hallucination that the post-process did not catch.

```python
from py2dataiku import (
    convert_with_llm, convert,
    ConfigurationError, LLMResponseParseError, ValidationError,
)

try:
    flow = convert_with_llm(source)
except ConfigurationError:
    flow = convert(source)  # offline fallback
except (LLMResponseParseError, ValidationError) as exc:
    print(f"LLM path failed ({exc}); using rule-based")
    flow = convert(source)
```

The structure mirrors the design rule from `py2dataiku/exceptions.py`: every LLM-specific failure is a subclass of `ProviderError`, which is itself a `Py2DataikuError`. A blanket `except Py2DataikuError` catches everything the library throws.

## Honest tradeoffs

The LLM path is not always the better path. The review log records two specific divergences worth knowing about:

- `df.drop_duplicates()` resolves to PREPARE + `RemoveDuplicates` in the rule-based path but to a DISTINCT recipe in the LLM path. Both are valid DSS configurations; the rule-based shape lets the resulting prepare step merge with adjacent prepare recipes during optimization (Chapter 10), while the DISTINCT shape keeps the operation as a separate recipe. The downstream flow shape differs.
- `SELECT_COLUMNS` operations emit both `keep:True` and `mode:keep` in the generated processor settings — DSS reads either, but the redundancy will surface in any byte-level flow comparison.

Both are documented in the project's outstanding-items log as "decisions accepted as not-bugs" rather than defects. They are the kind of artifact a reader should expect to find when comparing the two paths against each other.

The other tradeoff is cost. A typical V5-sized script costs roughly the input-token count of the source plus the system prompt, billed at the provider's input rate, plus a few hundred output tokens. Prompt caching makes the system prompt nearly free after the first call; without caching, the system prompt dominates per-call cost.

## Comparing the two paths against the running example

A practical sanity check is to convert the same source through both paths and compare. The expected answer for V2 of the running example (V1 plus the two `merge` calls) is `[PREPARE, JOIN]` — the optimizer collapses the two `merge` calls into a single multi-input JOIN. Both paths should produce that shape:

```python
# Rule-based path: deterministic by construction.
from py2dataiku import convert

flow_rule = convert(open("running_example_v2.py").read())
rule_types = {r.recipe_type.value for r in flow_rule.recipes}
assert rule_types == {"prepare", "join"}

# LLM path: requires ANTHROPIC_API_KEY. See scripts/llm_smoke_test.py for
# the credentials-safe runner pattern.
from py2dataiku import convert_with_llm

flow_llm = convert_with_llm(open("running_example_v2.py").read())
llm_types = {r.recipe_type.value for r in flow_llm.recipes}
assert llm_types == {"prepare", "join"}
```

The recipe-type set is the safe property to assert across the two paths. Asserting against `len(flow.recipes)` is also reasonable; asserting against per-recipe processor lists is brittle because the divergences listed above bite at that granularity.

A snippet that the rule-based path mis-classifies but the LLM path handles correctly is the compound-predicate filter. The rule-based AST analyzer can route `df[(df.x > N) & (df.y < M)]` through a generic PREPARE-with-FILTER, missing the fact that DSS has a dedicated `FilterOnFormula` processor for compound predicates that takes a GREL expression. The LLM path's mapping rules — `df[(df.x > N) & (df.y < M)]` → PREPARE + `FilterOnFormula` — pin the routing explicitly. For exactly this kind of pattern, the LLM path is the better translator; for everything in V1 through V4, the rule-based path is fine.

## When to disable optimization

`convert_with_llm` accepts `optimize=False`, the same flag as the rule-based `convert`. Disabling optimization is useful when debugging — the un-merged flow shows exactly which recipes the analyzer emitted before the merge passes ran. For production conversions, leave it on; the optimizer is the cheap part of the pipeline (one O(V+E) pass per call, see Chapter 10), and the merged shape is the one that matches the running example's documented post-optimization recipe counts.

## Further reading

- [LLM providers API reference](../api/llm-providers.md)
- [Core functions API reference](../api/core-functions.md)
- [Notebook 03: advanced patterns](https://github.com/m-deane/py-iku/blob/main/notebooks/03_advanced.ipynb)
- [Anthropic prompt caching documentation](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

## What's next

Chapter 8 takes the `## Mapping Rules` discussion of filter predicates and walks through the predicate-detection logic in detail.
