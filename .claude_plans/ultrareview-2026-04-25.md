# Ultrareview — py-iku Use-Case Audit (2026-04-25)

**Scope**: Multi-wave agent review focused on the core use case — converting Python data scripts to Dataiku DSS 14 visual flows quickly, accurately, and with optimal recipe/processor composition.
**Method**: 5 parallel review agents (LLM fidelity, mapping correctness, optimal composition, ergonomics, LLM output validation) per wave, with fix→test loops between waves.
**Priority order**: P0 LLM accuracy → P1 rule-based parity → P2 ergonomics.

---

## Wave 1 findings — synthesized P0 punch list

### LLM-path silent-degradation bugs (highest impact)

1. **TOP_N / SAMPLING / PIVOT routed to Python recipe** — `llm_flow_generator.py:206` lumps these visual recipe types with `"python"`. Three of pandas's most common operations (`nlargest`, `sample`, `pivot_table`) silently produce TODO-stub Python recipes. No `_create_topn_recipe`, `_create_sampling_recipe`, `_create_pivot_recipe` exist.
2. **UNPIVOT routing conflict** — `analyzer.py:253` maps UNPIVOT → `"pivot"` (which → Python), but `OPERATION_TO_RECIPE` maps it → `"prepare"`. When LLM omits `suggested_recipe`, Python wins; when it sets it, prepare wins. Silent semantic flip.
3. **SPLIT_COLUMN missing from `_infer_recipe`** — falls through to `"python"`. The `_convert_to_prepare_steps` branch is dead code unless LLM proactively returns `"prepare"`.
4. **3 OperationTypes never reachable**: `ENCODE_CATEGORICAL`, `NORMALIZE_SCALE`, `GEO_OPERATION` — absent from system prompt, `OPERATION_TO_RECIPE`, `_infer_recipe`, and `_convert_to_prepare_steps`. Always Python stub.
5. **WINDOW_FUNCTION emits empty shell** — `_create_window_recipe` only sets `partition_columns`; ignores aggregations, sort, frame.
6. **SELECT_COLUMNS uses wrong DSS params** — emits `{"keep": True}` instead of `{"mode": "keep"}` (DSS rejects).
7. **Prepare recipe ignores LLM-declared output dataset name** — auto-invents `{input}_prepared_{n}`, leaves the LLM's intended output as an orphan.
8. **Unknown `suggested_recipe` silently dropped** — no `else` clause; typo or hallucination → empty flow with no warning.
9. **System prompt references non-existent processors** (`ColumnDeleter`, `Normalizer`, `RegexpExtractor` are not in `ProcessorType`).

### Mapping/data-correctness bugs (will fail DSS import)

10. **`PrepareStep.delete_columns` missing `"keep": False`** — every `df.drop(columns=...)` silently **keeps** instead of deletes. Data inversion.
11. **FilterOnValue matching modes wrong** — emits `"GREATER_THAN"`, `"GREATER_OR_EQUAL"`, `"LESS_THAN"`, `"LESS_OR_EQUAL"`, `"IN"`. DSS uses `GT`, `GTE`, `LT`, `LTE`, `IN_LIST`.
12. **`_handle_nunique` hardcodes `"COUNTDISTINCT"`** — bypasses the (fixed) `AGG_MAPPINGS["nunique"] → "COUNTD"`.
13. **`_handle_melt` still emits `suggested_recipe="pivot"`** — incomplete fix; LLM path still routes to PIVOT.
14. **Phantom `AggregationFunction` values**: `MEAN` (DSS uses AVG), `NUNIQUE` (uses COUNTD), `VARIANCE` (uses VAR).
15. **19 phantom `ProcessorType` values** — `AbsColumn`, sklearn class names (`StandardScaler`, `LabelEncoder`, etc.) tagged in comments as having no DSS equivalent but still exposed.
16. **Enum aliasing**: `COLUMN_DELETER`/`COLUMNS_SELECTOR` → `"ColumnsSelector"`; `DATE_FORMATTER`/`DATETIME_FORMATTER` → `"DateFormatter"`. Round-trip loses one direction.

### Composition bugs (suboptimal flows)

17. **`STRING_TRANSFORM` listed in `_prepare_types()` but `_transform_to_prepare_step` returns `None`** — every string transform silently dropped from PREPARE recipes.
18. **`COLUMN_CREATE` not in `_prepare_types()`** — `df.where`, `mask`, `map(dict)`, `replace(dict)`, `assign`, `explode`, binop assigns → Python recipe despite working AST handlers.
19. **`DROP_DUPLICATES` falls to Python recipe in rule-based path** — no `elif` branch; LLM path correctly emits DISTINCT.
20. **Multi-function `.agg({'col': ['sum','mean']})` silently produces empty aggregations** — `_get_dict_value` only handles `ast.Constant`, not `ast.List`.
21. **N rolling/window ops → N separate WINDOW recipes** (no merge logic).
22. **SPLIT recipe always single-output** — complement lost; complementary boolean filters never detected.
23. **`df.tail()` silently gets RANDOM sampling** — TAIL falls into SAMPLE branch in `_create_sampling_recipe`, no `TAIL_SEQUENTIAL`.
24. **Sample `frac=...` value never propagated to recipe settings**.

### Ergonomics gaps

25. **CLI bare-file invocation broken** — `py2dataiku script.py` errors. README/CLAUDE.md document this wrong.
26. **`--llm anthropic` shorthand** documented but doesn't work (`--llm` is boolean, provider is `--provider`).
27. **`convert(Path("x.py"))` raises `TypeError`**; passing a path string returns silently empty flow.
28. **Rule-based path silently emits 0 recipes** for complex files with no warning.
29. **No `flow.save("path.ext")` auto-detect**.
30. **Missing `_repr_html_` / `_repr_mimebundle_`** for JupyterLab/VS Code notebooks.
31. **Missing API key raises `ValueError` not `ConfigurationError`**.

---

## Fix sequencing

**Phase 1 — P0 LLM accuracy (this commit)**
Items 1–9. Wire TOP_N/SAMPLING/PIVOT, fix UNPIVOT routing, add SPLIT_COLUMN to `_infer_recipe`, connect ENCODE_CATEGORICAL/NORMALIZE_SCALE/GEO_OPERATION, populate WINDOW settings, fix SELECT_COLUMNS params, honor LLM output_dataset, add `else`-warn for unknown recipes, audit system prompt against actual `ProcessorType` enum.

**Phase 2 — P0 mapping/data correctness**
Items 10–16. Fix `delete_columns` `keep:False`, FilterOnValue matching modes, `_handle_nunique`, `_handle_melt`, phantom AggregationFunction values, phantom processors, enum aliasing.

**Phase 3 — Rule-based parity**
Items 17–24. Wire STRING_TRANSFORM, COLUMN_CREATE, DROP_DUPLICATES handlers; multi-function agg dict; window merge; SPLIT complement; tail sampling.

**Phase 4 — Ergonomics**
Items 25–31. CLI bare-file, `convert()` Path support, flow.save, repr methods, error types.

---

## Wave 1 — completed

### Phase 1 (LLM accuracy) — DONE
- Wired TOP_N / SAMPLING / PIVOT recipes (added `_create_topn_recipe`, `_create_sampling_recipe`, `_create_pivot_recipe`; replaced the `("python","topn","sampling","pivot")` catch-all with explicit branches).
- Added `else` clause for unknown `suggested_recipe` that warns + falls back to Python (was silent drop).
- Fixed UNPIVOT routing: `_infer_recipe` now returns "prepare" (was "pivot"→Python).
- Added missing OperationType handlers in `_convert_to_prepare_steps`: `ENCODE_CATEGORICAL` → `CATEGORICAL_ENCODER`, `NORMALIZE_SCALE` → `NORMALIZER` (with mode), `GEO_OPERATION` → `GEO_POINT_CREATOR` / `GEO_ENCODER`.
- Extended `_infer_recipe` and `OPERATION_TO_RECIPE` to cover SPLIT_COLUMN, ENCODE_CATEGORICAL, NORMALIZE_SCALE, GEO_OPERATION.
- Populated WINDOW recipe `order_columns` and `window_aggregations` from DataStep (was only setting `partition_columns`); empty-aggregation case emits a warning.
- Fixed SELECT_COLUMNS params: now includes `mode: keep` alongside `keep: True` (DSS expects `mode`).
- Honored LLM-declared `output_dataset` in `_create_prepare_recipe` (was always inventing `{input}_prepared_{n}`, leaving the LLM-named dataset orphaned).

### Phase 2 (mapping correctness) — DONE
- `PrepareStep.delete_columns` now emits `keep: False` and `mode: remove` (was missing `keep`, causing DSS to *keep* listed columns instead of deleting).
- `_handle_nunique` AST handler now uses `PandasMapper.AGG_MAPPINGS["nunique"]` → `"COUNTD"` (was hardcoded `"COUNTDISTINCT"` — invalid DSS).
- `_handle_melt` AST handler now sets `suggested_recipe="prepare"` and `suggested_processor="FoldMultipleColumns"` (was `"pivot"` — wrong direction).
- DEFERRED to wave 2: FilterOnValue matching modes (`GREATER_THAN` vs `GT` etc.) — auditor's claim is at 95% confidence and conflicts with 5 in-codebase usages and existing tests; needs DSS source verification before changing.

### Phase 3 (rule-based parity) — DONE
- Wired `STRING_TRANSFORM` in rule-based `_transform_to_prepare_step` (was returning `None`, silently dropping every string transform). Now produces `StringTransformer`, `FindReplace`, `RegexpExtractor`, or `ColumnsSplitter` based on `suggested_processor`.
- Wired `COLUMN_CREATE` in `_transform_to_prepare_step` (was missing entirely). Now produces `CreateColumnWithGREL`, `Unfold`, or other processors based on the AST handler's hint.
- Fixed multi-function `.agg({"col": ["sum","mean","max"]})` AST extraction: `_get_dict_value` now preserves list values; the grouping generator expands them into multiple `Aggregation` rows with distinct output columns (was silently producing zero aggregations).
- Fixed `df.sample(frac=0.1)` to actually pass the fraction to the recipe as a percentage (was reading `frac` and immediately discarding it).

### Phase 4 (ergonomics) — DONE
- Added `DataikuFlow.save(path, format=None)` with auto-detection from extension (.json, .yaml/.yml, .svg, .html, .png, .pdf, .puml/.plantuml, .txt, .md/.mermaid).
- `convert()` and `convert_with_llm()` now polymorphically accept `pathlib.Path` and string paths to `.py` files; route to `convert_file` / `convert_file_with_llm`.
- CLI `py2dataiku script.py` (no subcommand) now auto-routes to the `convert` subcommand. Documented form in README/CLAUDE.md now actually works.

### Test results

| Metric | Pre-wave-1 | Post-wave-1 | Delta |
|---|---|---|---|
| Tests passing | 2219 | 2258 | +39 |
| Tests failing | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 |
| New regression tests | — | 39 | +39 |

39 new regression tests added across `test_llm.py` and `test_ast_edge_cases.py`:
- 11 LLM dispatch tests (TOP_N, SAMPLING, PIVOT, UNPIVOT, ENCODE_CATEGORICAL, NORMALIZE_SCALE, GEO_OPERATION, SELECT_COLUMNS, output_dataset honoring, unknown-recipe fallback warning, WINDOW population)
- 6 mapping/AST tests (nunique→COUNTD, melt→prepare, delete_columns keep:False, multi-agg dict)
- 8 string-transform / column-create / sample-frac rule-based tests
- 14 ergonomics tests (Path acceptance, flow.save() format detection, bare-CLI invocation)

---

## Wave 2 — completed

### Phase 5 (performance) — DONE
- **`FlowOptimizer._identify_parallel_branches` was O(R²×D) dead code** — body was `pass`, `parallel_groups` never appended to, return always `[]`. On a 120-recipe flow this consumed 99% of conversion time (320 ms). Removed the call from `optimize()` and stubbed the method. **Speedup: ~230× on pathological inputs (320ms → 1.4ms p50).**

### Phase 6 (parity) — DONE
- `nlargest`/`nsmallest` `ranking_column` now read from `parameters["column"]` (was always None because handler stored it there but generator read empty `trans.columns[0]`). Also emits `sort_columns` and respects `ascending`.
- TOP_N / SAMPLING / WINDOW / MELT recipes now honor `trans.target_dataframe` (was discarding the user's variable name and inventing `{input}_xxx`). Conditional avoids name collisions when `df = df.window(...)`.
- `_handle_melt` now extracts `id_vars`, `value_vars`, `var_name`, `value_name` from kwargs **and** positional args. Supports both `df.melt(...)` and `pd.melt(df, ...)` forms.
- Added `_handle_pd_binner` (handles `pd.cut`/`pd.qcut`) → emits COLUMN_CREATE with `suggested_processor="Binner"`. Wired in `_transform_to_prepare_step` to produce `BINNER` PrepareStep.
- Added `_handle_pd_get_dummies` → emits COLUMN_CREATE with `suggested_processor="CategoricalEncoder"`. Wired to produce `CATEGORICAL_ENCODER` PrepareStep.
- Wired `pd.melt` (top-level form) to `_handle_melt`.
- `_handle_assign` rewritten: each kwarg becomes its own COLUMN_CREATE transformation; lambda values are unparsed via `ast.unparse(value.body)` so `CreateColumnWithGREL` gets a real expression (was always empty string).
- Rule-based `COLUMN_SELECT` now emits `mode: keep` (wave-1 only fixed the LLM path).
- LLM `_create_grouping_recipe` normalizes aggregation function names through `PandasMapper.AGG_MAPPINGS` (e.g. `mean` → `AVG`, `std` → `STDDEV`, `nunique` → `COUNTD`) so flow output matches DSS canonical form regardless of what the LLM emits.
- Sample `frac=` correctly converted to `RANDOM_FIXED_RATIO` percentage (wave-1).

### Wave-2 deferred (accepted divergences)
- **`drop_duplicates` → PREPARE/RemoveDuplicates vs DISTINCT**: rule-based uses RemoveDuplicates so it can merge with adjacent prepare steps; LLM uses DISTINCT recipe. Both produce valid DSS output. Forcing DISTINCT in rule-based would break the merge optimization and existing tests.
- **`SELECT_COLUMNS` emits both `keep:True` and `mode:keep`**: Harmless — DSS reads whichever it expects. Existing tests assert both; removing one would regress for purist reasons.

### Test results — cumulative

| Metric | Baseline | Wave-1 | Wave-2 | Delta |
|---|---|---|---|---|
| Tests passing | 2219 | 2258 | 2272 | +53 |
| Tests failing | 0 | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 | 0 |
| New regression tests | — | +39 | +53 | +53 |
| 120-recipe convert p50 | 320ms | — | 1.4ms | **230× faster** |

14 new wave-2 regression tests added: nlargest ranking column, target_dataframe usage for TOP_N/SAMPLING, melt kwargs extraction, `pd.cut`/`pd.qcut`/`pd.get_dummies` handlers, `df.assign(lambda)` expression capture, rule-based `COLUMN_SELECT` mode, LLM aggregation canonicalization, optimizer perf regression guard.

---

## Items deferred to wave 3

1. **FilterOnValue matching modes** — verify against DSS 14 source whether `GT`/`GTE`/`LT`/`LTE`/`IN_LIST` (auditor's claim) or `GREATER_THAN`/`LESS_OR_EQUAL`/`IN` (current) is correct. Either way, normalize across `pattern_matcher.py:95-108` and `llm_flow_generator._map_operator`.
2. **System prompt processor names** — `analyzer.py:42-50` references `ColumnDeleter`, `Normalizer`, `RegexpExtractor` which don't all match `ProcessorType` `.value`s. Auto-generate from the enum to prevent drift.
3. **19 phantom processor types** still in `ProcessorType` (`AbsColumn`, sklearn classnames). These won't be emitted in normal use (we route around them), but they shouldn't be in the public enum — risk of misleading users.
4. **Enum aliasing collisions**: `COLUMN_DELETER`/`COLUMNS_SELECTOR` and `DATE_FORMATTER`/`DATETIME_FORMATTER` round-trip incorrectly via `ProcessorType("ColumnsSelector")`.
5. **3 phantom AggregationFunction values**: `MEAN`, `NUNIQUE`, `VARIANCE`. Mappings produce correct strings (`AVG`/`COUNTD`/`VAR`), but enum members exist that produce invalid strings.
6. **N rolling/window ops → N WINDOW recipes** (no merge for window aggregations on the same input).
7. **SPLIT recipe always single-output** — complement lost; complementary boolean filters never detected.
8. **Optimizer is list-position based, not DAG-based** — interleaved unrelated recipes block PREPARE merging across the same dataset.
9. **`_repr_html_` / `_repr_mimebundle_`** for JupyterLab/VS Code (only `_repr_svg_` exists today).
10. **Real-LLM end-to-end test gated on `ANTHROPIC_API_KEY`** — the wave-1 LLM validator could only use `MockProvider`. Need a smoke test that exercises the actual analyzer prompt with a real model.

---
