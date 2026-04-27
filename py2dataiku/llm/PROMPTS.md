# LLM Prompt Design — py2dataiku

How the LLM-based analyzer in `py2dataiku.llm` constructs its prompts, what JSON contract the model must satisfy, and how to extend it.

Audience: contributors editing `analyzer.py`, `providers.py`, `schemas.py`.

## Architecture

`LLMCodeAnalyzer.analyze(code)` builds a static **system prompt** (`ANALYSIS_SYSTEM_PROMPT`) and a per-call **user prompt** (`get_analysis_prompt(code)`), then calls the configured `LLMProvider`. The provider returns text; `_extract_json` strips fences; `json.loads` parses; `AnalysisResult.from_dict` deserializes; `_post_process` normalizes operation enums, fills missing `suggested_recipe`, and drops hallucinated processor names. The result feeds `LLMFlowGenerator`.

## Why two prompts?

- **System prompt** (~12 KB, stable): role, recipe taxonomy, processor catalog, mapping rules, examples. Stable so Anthropic's `cache_control: ephemeral` block can cache it across calls (~10% input-token cost on cache hits).
- **User prompt** (~500 bytes + code): per-call. Only the JSON-contract reminder and the user code.

## System prompt sections (in order)

1. **Role** — sets the model as a Dataiku-DSS data engineer.
2. **Objective** — numbered list of what each step must capture.
3. **Non-Goals** — explicit "do NOT" list. Strongest defense against hallucinations and chain-of-thought leakage.
4. **Dataiku Recipe Types** — canonical strings allowed in `suggested_recipe`.
5. **Processor catalog** (auto-generated from `ProcessorCatalog.PROCESSORS`) — the prompt cannot drift from the code.
6. **Mapping Rules** — non-obvious pandas → DSS routings (melt, filter dispatch, etc.).
7. **sklearn Handling** — scikit-learn estimators → DSS processors. Avoids literal class names that the LLM might echo back as fake processor names.
8. **Aggregation Function Naming** — canonical DSS names (`AVG`, `COUNTD`, `STDDEV`).
9. **Edge Cases** — empty code, imports, multi-statement scripts, untyped variables, chained calls, custom UDFs, connectors, "when uncertain" fallback.
10. **Output Discipline** — single JSON object, no fences, no chain-of-thought outside `step.reasoning`.
11. **Reasoning Approach** — keep reasoning inside `step.reasoning`.
12. **Examples** — four worked few-shot examples.

## The four worked examples

| # | Pattern | What it locks in |
|---|---------|------------------|
| 1 | `groupby + agg` | Canonical aggregation function names |
| 2 | `pd.melt` | melt → PREPARE+FoldMultipleColumns, NOT pivot |
| 3 | Multi-recipe ETL | Self-mutating dropna preserves variable name |
| 4 | sklearn preprocessing | MinMax → MeasureNormalize, get_dummies → CategoricalEncoder |

## JSON contract

Required top-level: `code_summary`, `steps`, `datasets`. Required per-step: `step_number`, `operation`, `description`. `operation` must be an `OperationType` enum value. `complexity_score` is bounded [1,10]. See `ANALYSIS_JSON_SCHEMA` in `schemas.py` for the authoritative definition.

`AnalysisResult.from_dict` is defensive: missing optional fields default sensibly, invalid `operation` values become `OperationType.UNKNOWN`, and join conditions accept both `left_column`/`left` aliases.

## Adding a few-shot example

1. Pick a real pattern from `py2dataiku/examples/` so behaviour matches the rule-based path.
2. Add a `### Example N` block in `_build_analysis_system_prompt`. Include input Python and the exact expected JSON.
3. **Use double-braces** (`{{`, `}}`) inside the f-string.
4. Keep it minimal — only fields needed to demonstrate the pattern.
5. Add a snapshot test in `tests/test_py2dataiku/test_llm_prompts.py` checking a unique substring.

## Adding a mapping rule

1. Add a bullet to **Mapping Rules** or **sklearn Handling**. Use bold/`NOT` callouts for confusion cases.
2. Add a regression test in `test_llm_prompts.py`.
3. If the misrouting is post-hoc detectable, strengthen `_post_process`.

## Testing without API calls

```python
from py2dataiku.llm.providers import MockProvider
from py2dataiku.llm.analyzer import LLMCodeAnalyzer

mock = MockProvider(responses={"sales": '{"code_summary": "...", "steps": [], "datasets": []}'})
analyzer = LLMCodeAnalyzer(provider=mock)
result = analyzer.analyze("sales = pd.read_csv('s.csv')")
```

`MockProvider` matches by substring of the user prompt. For provider-specific behaviour (caching), patch the SDK client with `unittest.mock.MagicMock` — see `TestAnthropicPromptCaching`.

## Token budget

System prompt: ~12 KB / ~3.5k tokens. Processor catalog dominates (~6 KB). Keep new sections tight.
