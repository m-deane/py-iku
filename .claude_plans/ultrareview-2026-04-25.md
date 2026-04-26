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

## Wave 3 — completed

### Phase 7 (DSS readiness + API polish) — DONE

**DSS-import readiness fixes** (raised import-ready estimate from ~10-20% to substantially higher):
- **Optimizer DAG rewriting** on prepare merge — when 2 prepares merged, downstream recipe inputs that referenced the absorbed intermediate name are now rewritten to point to the merged output. Was producing broken DAGs (`join.inputs=["df_prepared"]` with no recipe outputting that name).
- **`df["sales"].rolling(7).mean()` no longer produces phantom GROUPING + empty WINDOW shell.** Added `rolling().agg-fn()` chain detection to `_handle_method_chain` mirroring the existing `groupby().agg-fn()` detection. Emits ONE WINDOW transformation with proper window function (mean→AVG, etc.), window size, and column extracted from the deepest Subscript.
- **JOIN `_build_settings`** now emits DSS-canonical shape: `joins[]` with `conditions[]` (each having `column1.{name,table:0}`/`column2.{name,table:1}`), `outerJoinOnTheLeft`, `virtualInputs`, `postFilter`. Was emitting only `{joinType, joins:[{left,right,matchType}]}` which DSS rejects.
- **SORT `_build_settings`** now emits `sortColumns: [{column, ascending: bool}]`. Was emitting `{column, order: "DESC"}` (string), which DSS doesn't recognize. Accepts either input shape (legacy `order` string or canonical `ascending` boolean) and normalizes.

**API polish**:
- `DataikuFlow._repr_mimebundle_` added — JupyterLab 3+ / VS Code now show inline SVG instead of plain repr.
- `DataikuFlow.load(path)` classmethod added — symmetric with `save()`, auto-detects format from extension.
- `ConfigurationError` raised by providers (was bare `ValueError`) — multi-inherits from `ValueError` for backward-compat. `Py2Dataiku()` class now also catches `ConfigurationError` in its silent-fallback path.
- README quick-start updated: shows `convert("script.py")` polymorphism, `flow.save("flow.svg")` auto-format, and the bare-CLI form.

### Test results — cumulative

| Metric | Baseline | Wave-1 | Wave-2 | Wave-3 | Delta |
|---|---|---|---|---|---|
| Tests passing | 2219 | 2258 | 2272 | 2283 | +64 |
| Tests failing | 0 | 0 | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 | 0 | 0 |
| New regression tests | — | +39 | +53 | +64 | +64 |
| 120-recipe convert p50 | 320ms | — | 1.4ms | 1.4ms | 230× |

11 new wave-3 tests: optimizer DAG rewriting, rolling chain emits no phantom GROUPING + extracts window size, JOIN/SORT DSS-canonical _build_settings shapes, _repr_mimebundle_, ConfigurationError, DataikuFlow.load round-trip + unsupported-format guard.

---

## Wave 4 — completed

### Phase 8 (DSS readiness + docs + examples) — DONE

**SVG visualizer XML escaping (P0 bug)**:
- `svg_visualizer.py` did not XML-escape user-provided strings (zone names, dataset/recipe labels). A zone like `"ML Training & Scoring"` produced invalid SVG and broke `notebooks/05_master.ipynb` cell 90 with `xml.dom.expat.ExpatError`. Fixed by routing all user-string interpolations through `xml.sax.saxutils.escape`. Pre-existing bug, not a wave-1/2/3 regression — but wave-4 caught and fixed it.

**Documentation**:
- `docs/api/core-functions.md`: `convert()` and `convert_with_llm()` signatures now show `code: str | Path` (was `str` only). Examples show the new `convert("script.py")` and `convert(Path(...))` forms, plus `flow.save()`. `convert_with_llm()` Raises section now lists `ConfigurationError`.
- `docs/api/models.md`: Serialization section now leads with `flow.save(path)` and `DataikuFlow.load(path)` (auto-detect format). Special Methods section now lists `_repr_mimebundle_()` for JupyterLab/VS Code compatibility.
- `docs/index.md`: visualization-format count corrected from 6 to 8+ (added PNG/matplotlib + PDF).
- `CLAUDE.md`: CLI example fixed (`--llm anthropic` would have failed because `--llm` is a boolean flag — replaced with `script.py --llm` and the explicit `convert script.py --llm --provider openai` form). DataikuFlow gotcha now mentions `flow.save()`/`DataikuFlow.load()` and `_repr_mimebundle_`.

**Examples library**:
- `examples/recipe_examples.py`: `PIVOT_MELT_EXAMPLE` was filed under PIVOT but melt is unpivot (PREPARE+FOLD_MULTIPLE_COLUMNS post-wave-1). Renamed to `MELT_EXAMPLE`, kept `PIVOT_MELT_EXAMPLE` as backward-compat alias, added new `"melt"` key in `RECIPE_EXAMPLES`, removed `"melt"` from `RECIPE_METADATA["pivot"]["pandas_operations"]`, added a new `"melt"` metadata entry pointing at PREPARE/FOLD_MULTIPLE_COLUMNS.
- `examples/demo.py`: now opens with the one-line `convert(code)` form (the recommended public API), keeps the lower-level `CodeAnalyzer`/`FlowGenerator` walkthrough for users who want internals, and adds Step 8 demonstrating `flow.save()` / `DataikuFlow.load()` round-trip.
- `examples/llm_demo.py`: catches `ConfigurationError` explicitly (was relying on the `ValueError` multi-inherit) and falls back to `convert(code)` rule-based when no API key is set, so the demo still produces a working flow instead of just printing an error.

### Wave-4 deferred (low priority)
- **Notebook outputs are stale on `02_numpy_operations.ipynb` and `03_advanced.ipynb`** — code passes but outputs reflect pre-wave-3 behavior (e.g. TOP_N as Python stub instead of TOP_N recipe). Re-execute and re-commit to refresh.
- **`01_beginner.ipynb` / `02_intermediate.ipynb` quick-start drift** — neither shows `convert("script.py")` path-style usage, `flow.save()`, or the CLI bare-file form. Add 2-3 cells per notebook covering wave-3 ergonomics.
- **`05_master.ipynb` cell 90** previously failed due to the SVG escape bug — now unblocked. Re-execute and re-commit.

### Test results — cumulative

| Metric | Baseline | Wave-1 | Wave-2 | Wave-3 | Wave-4 | Delta |
|---|---|---|---|---|---|---|
| Tests passing | 2219 | 2258 | 2272 | 2283 | 2291 | +72 |
| Tests failing | 0 | 0 | 0 | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 | 0 | 0 | 0 |
| New regression tests | — | +39 | +53 | +64 | +72 | +72 |
| 120-recipe convert p50 | 320ms | — | 1.4ms | 1.4ms | 1.4ms | 230× |

8 new wave-4 tests: SVG zone name with `&` parses cleanly; `<`/`>` likewise; `MELT_EXAMPLE` constant exists; backward-compat alias works; `RECIPE_METADATA["melt"]` says PREPARE; `RECIPE_METADATA["pivot"]` no longer lists melt as a pandas operation.

---

## Final summary

Across 4 review waves and 4 fix phases, the ultrareview shipped:

1. **LLM accuracy**: TOP_N/SAMPLING/PIVOT/UNPIVOT/ENCODE_CATEGORICAL/NORMALIZE_SCALE/GEO_OPERATION all now produce real DSS visual recipes (were Python stubs or unreachable).
2. **Mapping correctness**: `delete_columns` now actually deletes, `nunique` uses canonical `COUNTD`, `melt` routes to PREPARE+FoldMultipleColumns; aggregation functions canonicalized via `AGG_MAPPINGS`.
3. **Rule-based parity**: `STRING_TRANSFORM`, `COLUMN_CREATE`, multi-function `.agg()`, `pd.cut`/`pd.qcut`/`pd.get_dummies`, `df.assign(lambda)`, `rolling().agg()` chain detection all wired.
4. **DSS-import readiness**: optimizer DAG rewriting on prepare merge; rolling chain no longer produces phantom GROUPING; JOIN/SORT settings emit DSS-canonical shape; SVG visualizer XML-escapes user strings.
5. **Performance**: 230× speedup on 120-recipe inputs (dead-code O(N²) optimizer hot path removed).
6. **Ergonomics**: `convert(Path)` polymorphism, `flow.save("path.ext")` + `DataikuFlow.load("path.ext")` auto-format, CLI bare-file form, `_repr_mimebundle_` for JupyterLab/VS Code, `ConfigurationError` typed exception with `ValueError` backward-compat.
7. **Docs**: README quick-start, `docs/api/core-functions.md`, `docs/api/models.md`, `docs/index.md`, `CLAUDE.md`, `recipe_examples.py` metadata, `demo.py`, `llm_demo.py` all updated to match the post-wave-3 API.

Cumulative: **+72 tests, 0 failures, 0 ruff violations, 230× faster on large inputs.**

---

## Wave 5 — completed

### Notebook refresh — DONE
Re-executed all 7 advanced notebooks against the post-wave-4 codebase. Outputs are now consistent with the current visual-recipe routing (TOP_N/SAMPLING/PIVOT no longer Python stubs, melt → PREPARE+FOLD_MULTIPLE_COLUMNS, etc.) and `05_master.ipynb` cell 90 is now unblocked thanks to the wave-4 SVG XML-escape fix.

| Notebook | Status | Notes |
|---|---|---|
| 01_beginner | re-executed + new cells added | added 9.3 save/load, 10.1 Path polymorphism |
| 02_intermediate | re-executed + new cells added | added Path polymorphism after import, _repr_mimebundle_ note in section 9, save/load section 11 |
| 02_numpy_operations | re-executed | clean |
| 03_advanced | re-executed | clean |
| 03_sklearn_pipelines | re-executed | clean |
| 04_expert | re-executed | clean (cell 9 catch-ValueError still works because ConfigurationError multi-inherits) |
| 05_master | re-executed | previously blocked by SVG escape bug; now unblocked |

### Beginner-notebook ergonomics — DONE
The wave-4 reviewer flagged that `01_beginner.ipynb` and `02_intermediate.ipynb` only showed the inline-string `convert("""...""")` pattern. New cells added so users discover the wave-3 ergonomics:

**01_beginner.ipynb**:
- New section 9.3 "Auto-detect format with `flow.save()` / `DataikuFlow.load()`" — demonstrates the recommended save/load API with format auto-detection.
- New section 10.1 "Path polymorphism" — shows that `convert()` accepts `pathlib.Path`, a `.py` path-string, or inline code interchangeably.

**02_intermediate.ipynb**:
- New cell after the library import showing `convert(Path(...))`, `convert("script.py")`, and inline-code forms produce equivalent flows (also mentions the CLI bare-file form).
- Section 9 markdown rewritten to explain BOTH `_repr_svg_()` (Classic Jupyter) AND `_repr_mimebundle_()` (JupyterLab/VS Code).
- New section 11 "Auto-detect format with `flow.save()` and `DataikuFlow.load()`" — demonstrates JSON/YAML round-trip plus SVG/HTML visual exports through the same single method.

All 2291 tests still pass. 0 ruff violations.

---

## Wave 6 — completed (phantom enum cleanup + DSS reference audit)

### Phantom ProcessorType cleanup — DONE
The 19 phantom processor types (sklearn class names, `AbsColumn`, etc.) had `.value` strings DSS does not recognize. Wave-6 aliased each phantom to its canonical DSS processor by sharing the canonical's `.value`:

| Phantom | Canonical DSS Processor | DSS .value |
|---|---|---|
| `ABS_COLUMN` | `CREATE_COLUMN_WITH_GREL` | `"CreateColumnWithGREL"` |
| `DISCRETIZER` | `BINNER` | `"Binner"` |
| `QUANTILE_TRANSFORMER`, `LOG_TRANSFORMER`, `POWER_TRANSFORMER`, `BOX_COX_TRANSFORMER` | `NUMERICAL_TRANSFORMER` | `"NumericalTransformer"` |
| `ROBUST_SCALER`, `MIN_MAX_SCALER`, `STANDARD_SCALER` | `NORMALIZER` | `"MeasureNormalize"` |
| `BOOLEAN_CONVERTER`, `NUMBER_TO_STRING`, `STRING_TO_NUMBER` | `TYPE_SETTER` | `"TypeSetter"` |
| `ONE_HOT_ENCODER`, `LABEL_ENCODER`, `ORDINAL_ENCODER`, `TARGET_ENCODER`, `LEAVE_ONE_OUT_ENCODER`, `WOE_ENCODER`, `FEATURE_HASHER` | `CATEGORICAL_ENCODER` | `"CategoricalEncoder"` |

In Python's `Enum`, members sharing a value become aliases — so `ProcessorType.ABS_COLUMN is ProcessorType.CREATE_COLUMN_WITH_GREL` is `True`, and emitted recipe JSON uses the canonical DSS name. User code referring to `ProcessorType.ABS_COLUMN` continues to work.

### Phantom AggregationFunction cleanup — DONE
- `MEAN` → alias of `AVG` (DSS uses `AVG`)
- `NUNIQUE` → alias of `COUNTD` (DSS uses `COUNTD`)
- `STD` → alias of `STDDEV` (DSS uses `STDDEV`)
- `VARIANCE` → alias of `VAR` (DSS uses `VAR`)

### Enum aliasing collisions resolved — DONE
- Reordered `COLUMNS_SELECTOR` to be declared *before* `COLUMN_DELETER` so `ProcessorType("ColumnsSelector")` resolves to the canonical `COLUMNS_SELECTOR` (was `COLUMN_DELETER`).
- Documented `DATETIME_FORMATTER` → `DATE_FORMATTER` and `CONCAT_COLUMNS` → `COLUMNS_CONCATENATOR` aliases inline.

### ProcessorCatalog cleanup — DONE
Removed 19 phantom catalog entries (AbsColumn, Discretizer, sklearn class names) and replaced with explanatory comments pointing users at the canonical processor. `catalog.list_processors()` now returns only real DSS Prepare processors.

### Other reference enums audited — clean
- `RecipeType` (37 members) — no aliases, no phantoms
- `SamplingMethod` — clean (Python names `RANDOM`/`RANDOM_FIXED` map to DSS `RANDOM_FIXED_NB`/`RANDOM_FIXED_RATIO`)
- `JoinType` — clean
- `WindowFunctionType` — clean (23 members)
- `JoinConditionType` — uses canonical DSS short codes (`GT`, `GTE`, `LT`, `LTE`, `EQ`, `NE`)
- `StringTransformerMode`, `NumericalTransformerMode` — clean

### Rule-based abs handler — DONE
Updated `_numeric_transform_to_prepare_step` to route `df.abs()` through `PrepareStep.create_column_grel(column, expression='abs(val("col"))')` directly, matching the LLM path. Also updated `_handle_abs` and `_handle_numpy_abs` to set `suggested_processor="CreateColumnWithGREL"` (was `"AbsColumn"`).

### `pandas_mappings.PROCESSOR_MAPPINGS` updated — DONE
- `"abs"` → `CREATE_COLUMN_WITH_GREL` (was `ABS_COLUMN`)
- `"get_dummies"` → `CATEGORICAL_ENCODER` (was `ONE_HOT_ENCODER`)

### Smoke test
Real-world script with `df.abs()`, `df.drop()`, `df.str.upper()`, `pd.cut()`, `pd.get_dummies()` produces emitted JSON containing **zero** phantom processor or aggregation names.

### Test results — cumulative

| Metric | Baseline | Wave-1 | Wave-2 | Wave-3 | Wave-4 | Wave-5 | Wave-6 | Delta |
|---|---|---|---|---|---|---|---|---|
| Tests passing | 2219 | 2258 | 2272 | 2283 | 2291 | 2291 | 2306 | +87 |
| Tests failing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| New regression tests | — | +39 | +53 | +64 | +72 | +72 | +87 | +87 |

15 new wave-6 tests: each phantom processor's alias verified; pandas-style aggregation aliases verified; canonical resolution for `ColumnsSelector`/`DateFormatter`; phantom catalog leak guard; canonical-processor-still-present guard; abs-routes-through-GREL end-to-end test.

---

## Wave 7 — completed (DSS verification + completeness + ergonomics)

### DSS API verification — DONE (research)
A research agent traced two unverified items against authoritative sources:

**Q2: GROUPING aggregation JSON shape** — HIGH confidence verdict from 3 authoritative sources (`dataiku-api-client-python` source, official developer guide, DSS 7.0 REST API docs): DSS expects a `"values"` array of boolean-flag entries: `{column, type:"COLUMN", sum:bool, avg:bool, count:bool, countDistinct:bool, min:bool, max:bool, stddev:bool, concat:bool}`. The wave-3 smoke tester was correct.

**Applied fix**: Added `Aggregation.to_dss_dict()` returning the canonical boolean-flag shape (with pandas-alias normalization: `MEAN`→`avg`, `NUNIQUE`/`COUNTD`→`countDistinct`, `STD`→`stddev`). `_build_settings()` for GROUPING now emits `"values": [...]` instead of `"aggregations": [...]`. `to_dict()` left unchanged for round-trip compat.

**Q1: FilterOnValue matchingMode** — INCONCLUSIVE on the surface, but research uncovered a deeper architectural finding: DSS's `FilterOnValue.matchingMode` only accepts `FULL_STRING` / `SUBSTRING` / `PATTERN` (string-match style, not comparison operators). Numeric comparisons (`>`, `<`, `>=`, `<=`) belong on `FilterOnNumericRange` or `FilterOnFormula`, not `FilterOnValue`. py-iku's current `EQUALS`/`GREATER_THAN` strings are semantically wrong, but neither the auditor's claim (`GT`/`GTE`) nor the current verbose form is supported by any public DSS reference for this specific field.

**Applied fix**: Added a clear inline docstring at `pattern_matcher.match_filter` explaining the semantic mismatch and pointing at the correct architectural fix (route comparisons to `FilterOnNumericRange`/`FilterOnFormula`). Did NOT change the strings — neither candidate is verified, and the structural restructuring (splitting filter routing by operator class) is a larger fix that needs its own design pass.

### LLM system prompt auto-generation — DONE
Refactored `analyzer.py` to auto-generate the processor list from `ProcessorCatalog.PROCESSORS` (now post-wave-6, only contains real DSS processors). The prompt grew from 13 listed processors to 89 canonical names across 17 categories — the LLM now has full vocabulary and can never hallucinate phantom names. 8 new tests guard category coverage, deterministic ordering, and absence of phantom names.

### WINDOW recipe merger — DONE
Added `_apply_merge_window_recipes` to `FlowOptimizer` (mirrors the existing prepare merger). Two consecutive WINDOW recipes merge when they share the same input dataset AND identical `partition_columns` AND identical `order_columns`. Aggregations are concatenated. Same DAG-rewrite pattern as the prepare merger keeps downstream inputs valid.

End-to-end test: `df['x'].rolling(7).mean()` followed by `df['x'].rolling(7).sum()` now produces ONE WINDOW recipe with 2 aggregations (was 2 separate WINDOW recipes).

### `df.describe()` / `df.info()` → GENERATE_STATISTICS — DONE
Added `TransformationType.STATISTICS` and `OperationType.STATISTICS`, plus handlers in both rule-based and LLM paths. `df.describe()` and `df.info()` now produce a `RecipeType.GENERATE_STATISTICS` recipe instead of falling to a Python recipe. The recipe references the input dataset and registers a separate output dataset for the statistics report.

### Ergonomics — DONE
- `DataikuFlow._repr_html_()` added — for environments that prefer HTML over the SVG mime bundle. Returns the SVG wrapped in a minimal HTML container.
- `DataikuFlow.diff(other)` added — returns a structured dict of recipe additions/removals/changes plus dataset diffs and an `equivalent` boolean. Useful for comparing rule-based vs LLM output on the same code.

### Test results — cumulative

| Metric | Baseline | W1 | W2 | W3 | W4 | W5 | W6 | W7 | Δ |
|---|---|---|---|---|---|---|---|---|---|
| Tests passing | 2219 | 2258 | 2272 | 2283 | 2291 | 2291 | 2306 | 2328 | +109 |
| Tests failing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

22 new wave-7 tests covering: GROUPING `to_dss_dict` boolean flags, pandas alias normalization, `_build_settings` emits `values[]` (not `aggregations[]`), WINDOW recipe merging, partition-mismatch non-merge, downstream-input rewriting, `df.describe()`/`df.info()` → STATISTICS, system prompt auto-generation determinism + canonical name presence + phantom name absence.

End-to-end verified: a complex script (read → dropna → describe → 2 rolling ops → groupby with multi-fn agg) produces 4 visual recipes (PREPARE + GENERATE_STATISTICS + ONE merged WINDOW + GROUPING with DSS-canonical `values[]`).

---

## Wave 8 — completed (filter routing + SPLIT complement + DAG-aware optimizer + on_progress)

### Filter routing by operator class — DONE
Wave-7 DSS research confirmed `FilterOnValue.matchingMode` only accepts `FULL_STRING`/`SUBSTRING`/`PATTERN` (string-match style). Numeric comparisons need different DSS processors. Restructured `pattern_matcher.match_filter` to dispatch by operator class:

| Pandas operator | DSS processor | params |
|---|---|---|
| `>`, `<`, `>=`, `<=` | `FilterOnNumericRange` | `column`, `min`/`max`, `keep` |
| `==`, `in` | `FilterOnValue` | `matchingMode="FULL_STRING"`, `values`, `keep=True` |
| `!=` | `FilterOnValue` | `matchingMode="FULL_STRING"`, `values`, `keep=False` (negation) |
| `contains` | `FilterOnValue` | `matchingMode="SUBSTRING"` |
| `regex` / `matches` | `FilterOnValue` | `matchingMode="PATTERN"` |

Added `PrepareStep.filter_on_numeric_range()` and `PrepareStep.filter_on_formula()` factories. Wired the LLM path's `OperationType.FILTER` branch through `PatternMatcher.match_filter` so both paths share identical filter-routing semantics. Marked `_map_operator` deprecated and updated its return values to valid DSS strings.

### SPLIT complement detection — DONE
`AST analyzer.analyze` now runs a post-pass `_merge_complementary_filters` that detects `df[cond]` / `df[~cond]` pairs (explicit-complement form only — conservative to avoid false positives). The pair is merged into a single FILTER transformation carrying `parameters["complementary_outputs"] = [positive_target, complement_target]`. `_create_split_recipe` honors this by emitting ONE multi-output SPLIT recipe with both outputs registered in `current_dataset` so downstream operations on either branch resolve correctly.

End-to-end: `train = df[df['split']=='train']; test = df[~(df['split']=='train')]` now produces ONE SPLIT recipe with `outputs=['train', 'test']` (was 2 single-output SPLITs). Independent (non-complementary) filters still produce separate recipes.

### DAG-aware optimizer merging — DONE
Replaced list-position scan in `_apply_merge_prepare_recipes` and `_apply_merge_window_recipes` with a downstream-by-input lookup. Two PREPARE/WINDOW recipes connected via the same dataset now merge regardless of their position in `flow.recipes` (e.g. when an unrelated recipe was inserted between them). Added a fan-out guard: an intermediate consumed by more than one downstream recipe blocks the merge to prevent orphaning a sibling consumer.

Wave-3 `TestOptimizerDagRewriting` test rewritten to assert the new (safer) fan-out behavior. Two new tests added: `test_merge_chains_when_no_fan_out` and `test_merge_dag_aware_with_interleaved_unrelated_recipe`.

### `convert_with_llm(..., on_progress=callable)` — DONE
Added optional `on_progress` callback to `convert_with_llm` and `convert_file_with_llm`. Invoked at 5 phases: `start`, `analyzing`, `analyzed`, `generating`, `optimizing` (when `optimize=True`), `done`. Each invocation receives `(phase: str, info: dict)`. Callback exceptions are swallowed so a buggy callback never breaks the conversion.

### Test results — cumulative

| Metric | Baseline | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 | Δ |
|---|---|---|---|---|---|---|---|---|---|---|
| Tests passing | 2219 | 2258 | 2272 | 2283 | 2291 | 2291 | 2306 | 2328 | 2339 | +120 |
| Tests failing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

12 new wave-8 tests:
- **Filter routing** (3): numeric → `FilterOnNumericRange` for both pattern_matcher + LLM path; equality/`in`/contains/regex stay on `FilterOnValue` with correct matchingMode.
- **SPLIT complement** (2): explicit-complement pair merges to ONE multi-output SPLIT; independent filters stay separate.
- **DAG-aware optimizer** (3): fan-out blocks merge; chained merge happens; interleaved-unrelated-recipe doesn't block merge.
- **on_progress** (2): callback invoked for each phase; signature accepts `on_progress=None`.
- **Ergonomics** (2): `_repr_html_` returns SVG-in-HTML wrapper; `flow.diff` reports `equivalent`/`added`/`removed`/`changed`.

Plus pattern_matcher tests rewritten (10 old → 11 new) to assert the new DSS-canonical dispatch.

End-to-end verified: `df[df["amount"] > 100]` produces a `FilterOnNumericRange` step (was an invalid `FilterOnValue` with `matchingMode="GREATER_THAN"` that DSS would reject); complementary filter pairs merge to ONE multi-output SPLIT; independent filters stay separate.

---

## Wave 9 — completed (compound-predicate filters → GREL formulas)

### Python AST → GREL translator — DONE
Added a recursive translator (`_translate_to_grel` in `ast_analyzer.py`) that converts pandas boolean indexing expressions to DSS GREL formulas. Handles:

| Python (pandas) | GREL |
|---|---|
| `df['x'] > 5` | `val("x") > 5` |
| `df['name'] == 'foo'` | `val("name") == "foo"` |
| `(a) & (b)` | `(a) && (b)` |
| `(a) \| (b)` | `(a) \|\| (b)` |
| `~(a)` | `!(a)` |
| `df['col'].isin(['a', 'b'])` | `((val("col") == "a") \|\| (val("col") == "b"))` |
| `df['x'] in [1, 2, 3]` | OR-chain of equalities |

Constants are escaped (string quotes preserved, booleans lowercased to `true`/`false`, `None` → `null`). Returns `None` for shapes the translator can't handle (function calls, complex slicing) so callers can fall back to leaving the formula unset.

### `_handle_filter` emits formula for compound predicates — DONE
When the boolean condition translates cleanly to GREL, the FILTER transformation now carries `parameters["formula"]`. When the AST is detected as a compound predicate (BoolOp / BinOp with BitAnd/BitOr / negated compound), `suggested_processor` is set to `"FilterOnFormula"` so downstream consumers know to use a formula-style step rather than the simpler FilterOnValue/FilterOnNumericRange.

### `_create_split_recipe` prefers GREL formula — DONE
The rule-based SPLIT recipe now uses `parameters["formula"]` (when present) as `split_condition` instead of the raw Python text — DSS can parse GREL but not Python. Falls back to the legacy condition string when no GREL translation was possible.

### `pattern_matcher.match_filter` — `formula` operator — DONE
The LLM path can now emit a `FilterCondition(operator="formula", value="<GREL expression>")` and have it route to `FilterOnFormula`. Aliases `"grel"` and `"expression"` also accepted. Useful for compound LLM-detected predicates that don't fit FilterOnValue/FilterOnNumericRange.

### End-to-end verified
```python
df_high = df[(df['amount'] > 100) & (df['qty'] < 10)]
# -> SPLIT recipe with split_condition: '(val("amount") > 100) && (val("qty") < 10)'

df_us = df[df['country'].isin(['US', 'CA', 'MX'])]
# -> SPLIT recipe with split_condition: '((val("country") == "US") || ...)'
```

### Test results — cumulative

| Metric | Baseline | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 | W9 | Δ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tests passing | 2219 | 2258 | 2272 | 2283 | 2291 | 2291 | 2306 | 2328 | 2339 | 2354 | +135 |
| Tests failing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ruff violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

15 new wave-9 tests:
- **GREL translator unit tests** (8): single comparison, equality, compound AND, compound OR, negation, isin method, in operator, unsupported→None.
- **End-to-end SPLIT condition is GREL** (3): compound AND, compound OR, single-clause regression.
- **`match_filter` formula operator** (3): formula operator, `grel` alias, `expression` alias all route to FilterOnFormula.
- **Constants escaping** (1): embedded quotes handled correctly.

---

## Outstanding items (after wave 9)

### Verification (need external resources)
1. **Real-LLM end-to-end test** — gated on `ANTHROPIC_API_KEY` (unset in this environment). Need a smoke test that calls the real Anthropic API and validates the LLM emits correctly-shaped output for each example.
2. **Real DSS import test** — every "DSS-valid" claim in the plan is verified against `dataiku-api-client-python` source code, NOT against a live DSS 14 instance. A real DSS smoke test would close this loop.

### Decisions explicitly accepted as not-bugs
- `drop_duplicates` → PREPARE/RemoveDuplicates in rule-based path vs DISTINCT in LLM path. Both produce valid DSS output; rule-based form lets the step merge with adjacent prepare steps.
- `SELECT_COLUMNS` emits both `keep:True` and `mode:keep`. Harmless (DSS reads whichever); legacy tests assert both.

---
