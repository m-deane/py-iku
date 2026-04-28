"""LLM-based Python code analyzer for py2dataiku."""

import json
from typing import Optional

from py2dataiku.exceptions import LLMResponseParseError
from py2dataiku.llm.providers import LLMProvider, get_provider
from py2dataiku.llm.schemas import AnalysisResult, DataStep, OperationType
from py2dataiku.mappings.processor_catalog import ProcessorCatalog


def _build_processor_catalog_section() -> str:
    """
    Auto-generate the processor catalog section of the system prompt
    from ``ProcessorCatalog.PROCESSORS``.

    Output is grouped by category and deterministically sorted (categories
    sorted alphabetically; processors within a category sorted by canonical
    ``ProcessorInfo.name``). Only canonical processor names + 1-line
    descriptions are emitted to keep the prompt compact.

    Each registry key maps to a ``ProcessorInfo``. Some keys are aliases
    (e.g. ``ColumnsSelector_delete`` maps to canonical name
    ``ColumnsSelector``) so we de-duplicate by the ``info.name`` field
    within each category.
    """
    by_category: dict[str, dict[str, str]] = {}
    for info in ProcessorCatalog.PROCESSORS.values():
        # De-duplicate aliased entries (different keys, same canonical name).
        # First occurrence wins; if any later entry shares the canonical
        # name, we keep the existing description (they describe the same
        # processor in DSS).
        bucket = by_category.setdefault(info.category, {})
        if info.name not in bucket:
            bucket[info.name] = info.description

    lines: list[str] = ["Dataiku Prepare Recipe Processors (grouped by category):"]
    for category in sorted(by_category):
        lines.append("")
        lines.append(f"{category}:")
        for name in sorted(by_category[category]):
            description = by_category[category][name]
            lines.append(f"- {name}: {description}")
    return "\n".join(lines)


def _build_analysis_system_prompt() -> str:
    """Construct the LLM system prompt with an auto-generated processor catalog."""
    return f"""# Role

You are an expert data engineer specializing in Python data processing and Dataiku DSS. Your job is to read Python code (pandas, numpy, scikit-learn) and produce a structured JSON description of every data manipulation step so a downstream generator can build an equivalent Dataiku DSS flow.

# Objective

For each meaningful operation in the code, emit one JSON ``step`` object that captures:
1. The operation type (one ``OperationType`` enum value).
2. Input and output datasets (DataFrame variable names — preserve them exactly, do NOT rename or invent intermediates).
3. The columns the operation touches.
4. Operation-specific structured details (filter conditions, aggregations, join keys, sort orders, transforms, etc.).
5. The Dataiku recipe type to use (one of the values in the "Dataiku Recipe Types" section below).
6. Optional processor names from the catalog when the recipe is ``prepare``.
7. Whether the step requires a Python recipe (only when no visual recipe fits).

# Non-Goals (do NOT do these)

- Do NOT execute or simulate the code. Treat it as static text.
- Do NOT invent recipe types or processor names that are not listed below.
- Do NOT rename DataFrame variables. ``df = df.dropna()`` is one step whose input AND output are both ``df``.
- Do NOT split a single conceptual operation into multiple steps just because pandas method-chains it (e.g. ``df.dropna().reset_index()`` may be one prepare step with multiple processors).
- Do NOT emit chain-of-thought, prose, headings, comments, or markdown fences in your response — only the JSON object.
- Do NOT echo this prompt or the user code back.

## Dataiku Recipe Types:

Use exactly these strings in ``suggested_recipe``.

- prepare: Data cleaning, column transforms, filtering, type conversion, simple per-row mutations
- join: Combining datasets on matching keys
- grouping: Aggregations with GROUP BY
- window: Window functions (running totals, LAG, LEAD, RANK, rolling, expanding, shift)
- stack: Vertical concatenation (UNION) — pd.concat with default axis
- split: Splitting data into multiple outputs based on conditions
- pivot: Reshaping data from long to wide format
- sort: Ordering data
- distinct: Removing duplicates
- topn: Getting top/bottom N rows
- sampling: Random sampling, head, tail
- sync: Reading data (no transformation)
- generate_statistics: df.describe() / df.info() profiling — does NOT advance the working dataset
- python: Operations that don't fit any visual recipe (sklearn fit/predict calls on custom estimators, arbitrary user-defined functions, etc.)

{_build_processor_catalog_section()}

# Mapping Rules (non-obvious cases)

These pandas patterns map to specific DSS recipes — they are the cases where naive lexical matching gets the wrong answer:

- ``df.melt()`` / ``pd.melt(df, ...)`` -> **prepare** recipe with ``FoldMultipleColumns`` processor (NOT ``pivot`` — pivot is the opposite operation, long-to-wide)
- ``df.pivot()`` / ``df.pivot_table()`` -> **pivot** recipe
- ``df.rolling(N).mean()``, ``df.cumsum()``, ``df.expanding()``, ``df.shift()`` -> **window** recipe
- ``df.nlargest(N, col)`` / ``df.nsmallest(N, col)`` -> **topn** recipe
- ``df.head(N)`` / ``df.tail(N)`` / ``df.sample(...)`` -> **sampling** recipe
- ``df.round()``, ``df.abs()``, ``df.clip()`` -> **prepare** recipe with ``CreateColumnWithGREL`` (abs uses ``abs()`` formula)
- ``df.drop_duplicates()`` -> **distinct** recipe
- ``pd.concat([a, b, c])`` (axis=0, default) -> **stack** recipe
- ``df.merge()`` / ``pd.merge()`` -> **join** recipe
- ``pd.cut()`` / ``pd.qcut()`` -> **prepare** recipe with ``Binner`` processor
- ``pd.get_dummies()`` -> **prepare** recipe with ``CategoricalEncoder``
- ``df.groupby(...).agg({{col: ['sum', 'mean']}})`` (multi-function dict) -> **grouping** with one aggregation per (col, func) pair
- ``df[df.x > N]`` (single boolean mask) -> **prepare** with ``FilterOnNumericRange`` (NOT ``FilterOnValue`` — that field is for string matching)
- ``df[df.x == 'foo']`` -> **prepare** with ``FilterOnValue`` and ``matchingMode: FULL_STRING``
- ``df[(df.x > N) & (df.y < M)]`` (compound predicate) -> **prepare** with ``FilterOnFormula`` and a GREL ``formula``
- ``df[cond]`` and ``df[~cond]`` on the same source -> ONE multi-output **split** recipe (not two)
- ``pd.read_csv``/``pd.read_parquet``/``pd.read_sql``/``pd.read_excel`` -> **read_data** with ``suggested_recipe: "sync"`` and ``source`` set to the file path or table name
- ``df.describe()`` / ``df.info()`` -> **statistics** operation with ``suggested_recipe: "generate_statistics"`` (side-output, does not advance the pipeline)
- ``df.to_csv()`` / ``df.to_parquet()`` / ``df.to_sql()`` -> **write_data** with ``input_datasets`` set to the DataFrame being written

# sklearn / scikit-learn Handling

scikit-learn preprocessing has visual-recipe equivalents — do NOT default to a python recipe just because the import path starts with ``sklearn``. Map common preprocessing classes (do not echo these class names back as ``suggested_processors`` — they are NOT DSS processor names; use the canonical DSS processor on the right):

- min-max scaler (sklearn ``preprocessing.MinMax...``) -> **prepare** with ``MeasureNormalize`` processor (mode ``MIN_MAX``)
- standard / z-score scaler (sklearn ``preprocessing.Standard...``) -> **prepare** with ``MeasureNormalize`` processor (mode ``ZSCORE``)
- one-hot encoder (sklearn ``preprocessing.OneHot...``) -> **prepare** with ``CategoricalEncoder``
- label encoder (sklearn ``preprocessing.Label...``) -> **prepare** with ``CategoricalEncoder``
- discretizer / binner (sklearn ``preprocessing.KBins...``) -> **prepare** with ``Binner``
- simple imputer (sklearn ``impute.Simple...``) -> **prepare** with ``FillEmptyWithValue`` (or ``FillEmptyWithMean`` etc. depending on strategy)
- ``train_test_split(X, y, ...)`` -> **split** recipe (or ``python`` if the split is non-trivially stratified)
- ``Pipeline([...])``, ``ColumnTransformer([...])`` -> walk the inner steps and map each one; only fall back to ``python`` if a step has no equivalent
- ``model.fit(...)`` / ``model.predict(...)`` for arbitrary estimators -> **python** recipe (DSS visual recipes can't represent model training/inference)

# Aggregation Function Naming

Use canonical DSS names in ``aggregations[].function``: ``SUM``, ``AVG`` (not ``MEAN``), ``COUNT``, ``COUNTD`` (not ``NUNIQUE`` or ``COUNTDISTINCT``), ``MIN``, ``MAX``, ``STDDEV`` (not ``STD``), ``VAR``, ``MEDIAN``, ``FIRST``, ``LAST``.

# Edge Cases

- **Empty / whitespace-only code**: Return ``{{"code_summary": "Empty code", "total_operations": 0, "complexity_score": 1, "datasets": [], "steps": [], "recommendations": [], "warnings": ["No executable statements found"]}}``.
- **Imports / pure assignments without DataFrames**: Skip — they are not data steps.
- **Multi-statement scripts**: Emit one step per data operation in source order.
- **Untyped variables / unknown types**: If a variable is mutated by a pandas call, treat it as a DataFrame.
- **Chained method calls** (``df.dropna().reset_index().rename(columns=...)``): Emit one ``prepare`` step per logical processor, all sharing the same ``input_datasets`` and ``output_dataset``, OR one ``prepare`` step with multiple ``suggested_processors`` if they cleanly compose. Either is acceptable; prefer the latter when in doubt.
- **Custom UDFs** (``df.apply(my_func)``): Emit a ``custom_function`` step with ``suggested_recipe: "python"`` and ``requires_python_recipe: true``.
- **Connectors** (``pd.read_sql("...", conn)``, ``read_parquet("s3://...")``): Set ``source`` to the connector identifier (table name, S3 URI, etc.).
- **When uncertain**: prefer a ``prepare`` recipe with NO ``suggested_processors`` (the downstream generator handles fallbacks gracefully) over fabricating a structural recipe like ``join`` or ``pivot`` from a guess.

# Output Discipline

- Respond with EXACTLY ONE valid JSON object. No markdown code fences. No prose before or after. (If your client wraps the response in fences anyway, the parser strips them — but you should not add them yourself.)
- ``operation`` MUST be one of the OperationType enum values listed in the schema (e.g. ``read_data``, ``filter``, ``group_aggregate``, ``window_function``, ``join``, ``pivot``, ``unpivot``, ``sort``, ``top_n``, ``sample``, ``cast_type``, ``parse_date``, ``split_column``, ``encode_categorical``, ``normalize_scale``, ``geo_operation``, ``statistics``, ``custom_function``, ``unknown``).
- ``suggested_recipe`` MUST be one of the strings in the "Dataiku Recipe Types" section. Do NOT invent new ones.
- ``suggested_processors`` MUST contain only canonical names from the processor catalog above. Do NOT invent new names. If a sklearn / pandas operation has no visual equivalent, leave ``suggested_processors`` empty and set ``suggested_recipe: "python"``.
- If you cannot confidently map a step to a visual recipe, set ``requires_python_recipe: true`` and ``suggested_recipe: "python"``. Do NOT guess.
- For self-mutating ops like ``df = df.dropna()``, use the SAME variable name for both ``input_datasets`` and ``output_dataset`` — do not invent intermediate names like ``df_temp`` or ``df_initial``.

# Reasoning Approach

For each Python statement, internally: (1) identify the pandas/numpy/sklearn operation, (2) pick the OperationType, (3) apply the Mapping Rules to pick the recipe, (4) pick processors if recipe is "prepare". Capture a one-sentence reasoning in the step's ``reasoning`` field. Do NOT emit reasoning text outside the JSON object.

# Confidence + Source-line Attribution (per step)

For EVERY step also emit:

- ``confidence`` (number in [0.0, 1.0]) — your self-rated confidence that this step's recipe + processor mapping faithfully represents the user's Python. Calibrate as follows:
  - **>= 0.85 (high)**: textbook pandas operation with an exact DSS visual equivalent (e.g. ``df.merge(..., on=...)`` -> JOIN, ``df.dropna()`` -> RemoveRowsOnEmpty, simple ``df.groupby().agg({{col: "sum"}})``). The mapping is unambiguous.
  - **0.60 - 0.84 (medium)**: the operation has a visual equivalent but you had to make a judgement call — ambiguous filter routing, a transform you mapped to GREL because the closest processor isn't an exact fit, multi-function aggregations, sklearn preprocessing where the strategy enum isn't fully spelled out.
  - **< 0.60 (low)**: the mapping is a best-effort guess, you fell back to a Python recipe, the user code uses a UDF/lambda whose intent you can't fully read, or a non-pandas library you're approximating. Always emit a low confidence rather than skipping the step.
  - Use ``null`` only when you have no opinion at all (rare — prefer a numeric value).
- ``source_lines`` (array ``[start, end]`` of 1-indexed line numbers from the user's code, inclusive) — the source-code span this step came from. The Studio UI uses this to highlight the originating Python lines on hover. If you can't locate it, omit ``source_lines`` (do not invent a span). Numbering is 1-indexed and matches the line numbers shown in a Monaco editor.
- ``reasoning`` (one short sentence) — what you matched and why. Examples:
  - "df.merge(other, on='id', how='left') -> JOIN with left join_type and one EXACT join key on 'id'."
  - "df['x'] = df['x'].astype(int) -> PREPARE+ColumnTypeChanger because the cast is a single per-column dtype change."
  - "Custom apply(my_udf): no visual equivalent — emitted Python recipe with TODO comment."

The downstream UI bands (high >= 0.85, medium 0.60-0.84, low < 0.60) are derived from your numeric value. Be honest — a low score on a hard mapping is more valuable than a falsely-high one.

## Examples

The following worked examples show the EXACT JSON shape expected. Each example demonstrates a different operation class. Use them as a template; do not copy field values verbatim — adapt to the user's code.

### Example 1: Simple groupby + aggregation (the control case)

Input:
```python
sales = pd.read_csv("sales.csv")
totals = sales.groupby("region").agg({{"amount": "sum"}})
```

Expected JSON:
```json
{{
  "code_summary": "Read sales and aggregate total amount per region.",
  "total_operations": 2, "complexity_score": 2,
  "datasets": [
    {{"name": "sales", "source": "sales.csv", "is_input": true, "is_output": false}},
    {{"name": "totals", "source": "derived", "is_input": false, "is_output": true}}
  ],
  "steps": [
    {{"step_number": 1, "operation": "read_data", "description": "Read sales.csv", "output_dataset": "sales", "suggested_recipe": "sync", "source_lines": [1, 1], "confidence": 0.95, "reasoning": "pd.read_csv -> SYNC recipe, source path captured."}},
    {{"step_number": 2, "operation": "group_aggregate", "description": "Sum amount per region", "input_datasets": ["sales"], "output_dataset": "totals", "group_by_columns": ["region"], "aggregations": [{{"column": "amount", "function": "SUM", "output_column": "amount_sum"}}], "suggested_recipe": "grouping", "source_lines": [2, 2], "confidence": 0.92, "reasoning": "groupby+agg -> grouping; canonical SUM"}}
  ],
  "recommendations": [], "warnings": []
}}
```

### Example 2: pandas melt (the confusion case)

Input:
```python
wide = pd.read_csv("quarterly.csv")
long = pd.melt(wide, id_vars=["product"], value_vars=["q1", "q2", "q3", "q4"], var_name="quarter", value_name="revenue")
```

Expected JSON (CRITICAL: melt is UNPIVOT — wide-to-long. It routes to **prepare** + **FoldMultipleColumns**, NOT the pivot recipe):
```json
{{
  "code_summary": "Unpivot quarterly columns into long format.",
  "total_operations": 2, "complexity_score": 2,
  "datasets": [
    {{"name": "wide", "source": "quarterly.csv", "is_input": true, "is_output": false}},
    {{"name": "long", "source": "derived", "is_input": false, "is_output": true}}
  ],
  "steps": [
    {{"step_number": 1, "operation": "read_data", "description": "Read quarterly.csv", "output_dataset": "wide", "suggested_recipe": "sync"}},
    {{"step_number": 2, "operation": "unpivot", "description": "pd.melt: fold q1..q4 into (quarter, revenue)", "input_datasets": ["wide"], "output_dataset": "long", "columns": ["q1", "q2", "q3", "q4"], "suggested_recipe": "prepare", "suggested_processors": ["FoldMultipleColumns"], "reasoning": "pd.melt is wide-to-long; DSS implements as PREPARE+FoldMultipleColumns, NOT the pivot recipe (pivot is the opposite)."}}
  ],
  "recommendations": [], "warnings": []
}}
```

### Example 3: Multi-recipe ETL (read -> clean -> join -> groupby -> sort)

Input:
```python
import pandas as pd
orders = pd.read_csv("orders.csv")
customers = pd.read_csv("customers.csv")
orders = orders.dropna(subset=["customer_id"])
enriched = orders.merge(customers, on="customer_id", how="left")
revenue = enriched.groupby("country").agg({{"amount": "sum"}})
top = revenue.sort_values("amount", ascending=False)
```

Expected JSON (note: ``orders = orders.dropna(...)`` is self-mutating — reuse the SAME variable name for input and output):
```json
{{
  "code_summary": "Read orders+customers, drop null customer_id, join, sum amount per country, sort desc.",
  "total_operations": 6, "complexity_score": 5,
  "datasets": [
    {{"name": "orders", "source": "orders.csv", "is_input": true, "is_output": false}},
    {{"name": "customers", "source": "customers.csv", "is_input": true, "is_output": false}},
    {{"name": "top", "source": "derived", "is_input": false, "is_output": true}}
  ],
  "steps": [
    {{"step_number": 1, "operation": "read_data", "description": "Read orders", "output_dataset": "orders", "suggested_recipe": "sync"}},
    {{"step_number": 2, "operation": "read_data", "description": "Read customers", "output_dataset": "customers", "suggested_recipe": "sync"}},
    {{"step_number": 3, "operation": "drop_missing", "description": "Drop null customer_id", "input_datasets": ["orders"], "output_dataset": "orders", "columns": ["customer_id"], "suggested_recipe": "prepare", "suggested_processors": ["RemoveRowsOnEmpty"], "reasoning": "Self-mutating dropna; reuse same name"}},
    {{"step_number": 4, "operation": "join", "description": "Left-join on customer_id", "input_datasets": ["orders", "customers"], "output_dataset": "enriched", "join_conditions": [{{"left_column": "customer_id", "right_column": "customer_id", "operator": "equals"}}], "join_type": "left", "suggested_recipe": "join"}},
    {{"step_number": 5, "operation": "group_aggregate", "description": "Sum amount per country", "input_datasets": ["enriched"], "output_dataset": "revenue", "group_by_columns": ["country"], "aggregations": [{{"column": "amount", "function": "SUM", "output_column": "amount_sum"}}], "suggested_recipe": "grouping"}},
    {{"step_number": 6, "operation": "sort", "description": "Sort desc by amount", "input_datasets": ["revenue"], "output_dataset": "top", "sort_columns": [{{"column": "amount", "order": "desc"}}], "suggested_recipe": "sort"}}
  ],
  "recommendations": ["Filter orders before join to reduce volume"],
  "warnings": []
}}
```

### Example 4: scikit-learn preprocessing (mapped to PREPARE processors)

Input:
```python
import pandas as pd
from sklearn import preprocessing as skp

df = pd.read_csv("features.csv")
df[["age", "income"]] = skp.MinMaxScaler().fit_transform(df[["age", "income"]])
df = pd.get_dummies(df, columns=["country"])
```

Expected JSON (CRITICAL: a sklearn min-max scaler -> ``MeasureNormalize`` with mode ``MIN_MAX``; ``pd.get_dummies`` (and one-hot encoders generally) -> ``CategoricalEncoder``. Do NOT fall back to a ``python`` recipe — these have visual equivalents):
```json
{{
  "code_summary": "Read features, min-max scale numeric columns, one-hot encode country.",
  "total_operations": 3, "complexity_score": 3,
  "datasets": [
    {{"name": "df", "source": "features.csv", "is_input": true, "is_output": false}}
  ],
  "steps": [
    {{"step_number": 1, "operation": "read_data", "description": "Read features.csv", "output_dataset": "df", "suggested_recipe": "sync"}},
    {{"step_number": 2, "operation": "normalize_scale", "description": "MinMax scale age, income", "input_datasets": ["df"], "output_dataset": "df_scaled", "columns": ["age", "income"], "column_transforms": [{{"column": "age", "operation": "min_max", "parameters": {{"mode": "min_max"}}}}, {{"column": "income", "operation": "min_max", "parameters": {{"mode": "min_max"}}}}], "suggested_recipe": "prepare", "suggested_processors": ["MeasureNormalize"], "reasoning": "MinMaxScaler -> PREPARE+MeasureNormalize(MIN_MAX); fresh output name to avoid self-loop."}},
    {{"step_number": 3, "operation": "encode_categorical", "description": "One-hot encode country", "input_datasets": ["df_scaled"], "output_dataset": "df_encoded", "columns": ["country"], "suggested_recipe": "prepare", "suggested_processors": ["CategoricalEncoder"], "reasoning": "pd.get_dummies and sklearn one-hot encoders both map to PREPARE+CategoricalEncoder."}}
  ],
  "recommendations": [], "warnings": []
}}
```

### Example 5: complementary-condition SPLIT (the consolidation case)

Input:
```python
curves = pd.read_csv("curves.csv")
cond = curves["effective_date"] <= "2024-12-31"
current = curves[cond]
history = curves[~cond]
```

Expected JSON (CRITICAL: ONE step with ``suggested_recipe="split"``, ``output_datasets`` listing BOTH branch names, NOT one output plus orphan datasets):
```json
{{
  "code_summary": "Read curves, split into current and history at the cutoff.",
  "total_operations": 2, "complexity_score": 2,
  "datasets": [
    {{"name": "curves", "source": "curves.csv", "is_input": true, "is_output": false}},
    {{"name": "current", "source": "derived", "is_input": false, "is_output": true}},
    {{"name": "history", "source": "derived", "is_input": false, "is_output": true}}
  ],
  "steps": [
    {{"step_number": 1, "operation": "read_data", "description": "Read curves.csv", "output_dataset": "curves", "suggested_recipe": "sync"}},
    {{"step_number": 2, "operation": "split", "description": "Partition curves into current vs history at the cutoff", "input_datasets": ["curves"], "output_datasets": ["current", "history"], "split_condition": "val(\"effective_date\") <= \"2024-12-31\"", "suggested_recipe": "split", "source_lines": [2, 4], "confidence": 0.95, "reasoning": "Complementary cond/~cond on the same dataframe -> one SPLIT recipe with both branches as outputs."}}
  ],
  "recommendations": [], "warnings": []
}}
```

Note the ``output_datasets`` (plural) field on the SPLIT step — this is the canonical way to express both branches. Do NOT emit a step with ``output_dataset: "filtered_1"`` and then leak ``current`` and ``history`` as orphan datasets — the SPLIT MUST own both names.

## CRITICAL output-dataset naming rules

A recipe's ``input_datasets`` and ``output_dataset`` MUST NOT share a name. The downstream graph layer rejects recipes with input == output as cycles, breaking every consumer.

When the user's pandas code rebinds the same variable (e.g., ``trades = trades[trades["x"] > 0]`` or ``df["a"] = df["a"].fillna(0)``), pick a FRESH output dataset name:
- ``trades`` -> ``trades_filtered`` -> ``trades_clean`` (one rename per step)
- For long mutation chains, use ``<name>_step_2``, ``<name>_step_3``, ...
- Never reuse the input name for the output, even when the user's variable name is reused.

## Pattern catalog (use these mappings exactly)

These idioms are commonly mis-routed. Apply them deterministically:

1. ``df.sort_values(col, ascending=False).head(N)`` -> **TOP_N** with ``ranking_column=col``, ``top_n=N``. NOT ``SAMPLING``.
2. ``df.head(N)`` (no preceding sort) -> **SAMPLING** with ``rows=N``.
3. ``df.nlargest(N, col)`` / ``df.nsmallest(N, col)`` -> **TOP_N**.
4. ``df["new"] = df["src"].str.extract(r"(<regex>)")`` -> **PREPARE + PatternExtract** with ``pattern=<regex>``. NOT ``ColumnsSplitter``.
5. ``df[(df.x > 5) & (df.y < 10)]`` (compound predicate with ``&`` or ``|``) -> **PREPARE + FilterOnFormula** with a single GREL expression like ``val("x") > 5 && val("y") < 10``. NOT multiple ``FilterOnNumericRange`` processors.
6. ``df[df.x > N]`` (single-clause numeric comparison) -> **PREPARE + FilterOnNumericRange** with ``min=N``.
7. ``df[df.x == "v"]`` (single-clause equality) -> **PREPARE + FilterOnValue** with ``matchingMode=FULL_STRING``.
8. ``cond = <expr>; current = df[cond]; history = df[~cond]`` (complementary predicates) -> ONE **SPLIT** recipe with ``inputs=[df]`` and ``outputs=[current, history]`` (BOTH outputs on the SAME recipe). NOT a SPLIT with one output plus a separate orphan dataset. NOT two filter recipes. The split_condition is the GREL of ``<expr>``.

Be precise and thorough. Extract ALL operations, even implicit ones. When in doubt, prefer a ``prepare`` recipe with no processors over guessing a structural recipe."""


# System prompt for code analysis. Built once at import time from the
# ProcessorCatalog so the prompt cannot drift away from the actual code.
ANALYSIS_SYSTEM_PROMPT = _build_analysis_system_prompt()


def get_analysis_prompt(code: str) -> str:
    """Generate the analysis prompt for given code.

    The prompt is intentionally short: the recipe taxonomy, processor catalog,
    mapping rules, and worked examples are all in the system prompt
    (``ANALYSIS_SYSTEM_PROMPT``) so they can be Anthropic-prompt-cached across
    calls. The user prompt only contains the per-call code payload and a
    reminder of the JSON shape's required fields.
    """
    return f"""Analyze the following Python code and extract every data manipulation step.

Required top-level JSON fields:
- ``code_summary`` (string): one-line description of the whole pipeline.
- ``total_operations`` (int): count of steps you emit.
- ``complexity_score`` (int 1-10): your subjective complexity rating.
- ``datasets`` (array): each dataset (input, intermediate, output) with ``name``, ``source``, ``is_input``, ``is_output``, optional ``inferred_columns``.
- ``steps`` (array): one entry per data operation. See the system prompt for the per-step schema and worked examples.
- ``recommendations`` (array of strings): optimization hints (may be empty).
- ``warnings`` (array of strings): caveats or skipped lines (may be empty).

Per-step required fields: ``step_number``, ``operation``, ``description``. Add the operation-specific fields (``filter_conditions``, ``aggregations``, ``group_by_columns``, ``join_conditions``, ``join_type``, ``column_transforms``, ``rename_mapping``, ``sort_columns``, ``columns``, ``fill_value``) only when they apply. Always include ``suggested_recipe`` and (when the recipe is ``prepare``) ``suggested_processors`` with canonical names from the catalog.

Python Code to Analyze:
```python
{code}
```

Respond with ONLY the JSON object — no markdown fences, no commentary."""


class LLMCodeAnalyzer:
    """
    Analyze Python code using an LLM to extract data manipulation steps.

    This is the primary analyzer for py2dataiku, using an LLM to understand
    code semantics rather than relying on pattern matching.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        provider_name: str = "anthropic",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the analyzer.

        Args:
            provider: Pre-configured LLMProvider instance
            provider_name: Provider name if no provider given ("anthropic", "openai")
            api_key: API key for provider
            model: Model name override
        """
        if provider:
            self.provider = provider
        else:
            self.provider = get_provider(provider_name, api_key, model)

    def analyze(self, code: str) -> AnalysisResult:
        """
        Analyze Python code and extract data manipulation steps.

        Args:
            code: Python source code to analyze

        Returns:
            AnalysisResult containing all extracted steps and metadata
        """
        prompt = get_analysis_prompt(code)

        try:
            # Call complete() directly (rather than complete_json) so we can
            # capture LLMResponse.usage and surface it on the AnalysisResult.
            # The MockProvider returns mock JSON that doesn't go through the
            # real-LLM path, so fall back to complete_json there.
            from py2dataiku.llm.providers import (
                AnthropicProvider,
                OpenAIProvider,
                _extract_json,
            )
            if isinstance(self.provider, (AnthropicProvider, OpenAIProvider)):
                # Mirror the JSON-instruction wrapping that complete_json does
                # so behaviour matches existing tests.
                json_system = (ANALYSIS_SYSTEM_PROMPT or "") + (
                    "\n\nYou must respond with valid JSON only. No other text."
                )
                llm_response = self.provider.complete(prompt, json_system)
                json_text = _extract_json(llm_response.content)
                response_data = json.loads(json_text)
                usage = llm_response.usage
            else:
                # MockProvider / custom provider — keep the old contract.
                response_data = self.provider.complete_json(
                    prompt=prompt,
                    system_prompt=ANALYSIS_SYSTEM_PROMPT,
                )
                usage = None

            result = AnalysisResult.from_dict(response_data)
            result.model_used = self.provider.model_name
            result.usage = usage
            result.raw_response = json.dumps(response_data)

            # Post-process to ensure consistency
            result = self._post_process(result)

            return result

        except json.JSONDecodeError as e:
            raise LLMResponseParseError(f"Failed to parse LLM response as JSON: {e}") from e

    def analyze_with_context(
        self,
        code: str,
        context: Optional[str] = None,
        existing_datasets: Optional[list[str]] = None,
    ) -> AnalysisResult:
        """
        Analyze code with additional context.

        Args:
            code: Python source code
            context: Additional context about the codebase or requirements
            existing_datasets: Names of datasets that already exist in Dataiku

        Returns:
            AnalysisResult
        """
        # Build enhanced prompt
        prompt = get_analysis_prompt(code)

        if context:
            prompt = f"Context: {context}\n\n{prompt}"

        if existing_datasets:
            prompt = f"Existing Dataiku datasets: {', '.join(existing_datasets)}\n\n{prompt}"

        try:
            response_data = self.provider.complete_json(
                prompt=prompt,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
            )

            result = AnalysisResult.from_dict(response_data)
            result.model_used = self.provider.model_name
            result = self._post_process(result)

            return result

        except json.JSONDecodeError as e:
            raise LLMResponseParseError(f"Failed to parse LLM response as JSON: {e}") from e

    def _post_process(self, result: AnalysisResult) -> AnalysisResult:
        """Post-process the analysis result for consistency."""
        # Ensure step numbers are sequential
        for i, step in enumerate(result.steps, 1):
            step.step_number = i

        # Validate operation types
        for step in result.steps:
            if isinstance(step.operation, str):
                try:
                    step.operation = OperationType(step.operation)
                except ValueError:
                    step.operation = OperationType.UNKNOWN

        # Add default suggestions if missing
        for step in result.steps:
            if not step.suggested_recipe:
                step.suggested_recipe = self._infer_recipe(step)

        # Validate suggested_processors against ProcessorCatalog. Wave A
        # determinism prober found the LLM occasionally invents processor
        # names that aren't in the catalog (e.g. invented sklearn names).
        # Drop unknown names and surface a warning so the user knows what
        # happened, rather than silently failing downstream when
        # LLMFlowGenerator tries to look the name up.
        canonical_names = {
            info.name for info in ProcessorCatalog.PROCESSORS.values()
        }
        for step in result.steps:
            if not step.suggested_processors:
                continue
            valid = []
            invalid = []
            for proc_name in step.suggested_processors:
                if proc_name in canonical_names:
                    valid.append(proc_name)
                else:
                    invalid.append(proc_name)
            if invalid:
                step.suggested_processors = valid
                result.warnings.append(
                    f"Step {step.step_number}: dropped unknown processor names "
                    f"{invalid} (not in ProcessorCatalog). Valid alternatives "
                    f"can be found in py2dataiku.mappings.processor_catalog.ProcessorCatalog."
                )

        # Update total operations count
        result.total_operations = len(result.steps)

        return result

    def _infer_recipe(self, step: DataStep) -> str:
        """Infer the best Dataiku recipe type for a step."""
        op = step.operation

        recipe_map = {
            OperationType.READ_DATA: "sync",
            OperationType.WRITE_DATA: "sync",
            OperationType.FILTER: "prepare",
            OperationType.SELECT_COLUMNS: "prepare",
            OperationType.DROP_COLUMNS: "prepare",
            OperationType.RENAME_COLUMNS: "prepare",
            OperationType.ADD_COLUMN: "prepare",
            OperationType.TRANSFORM_COLUMN: "prepare",
            OperationType.FILL_MISSING: "prepare",
            OperationType.DROP_MISSING: "prepare",
            OperationType.DROP_DUPLICATES: "distinct",
            OperationType.GROUP_AGGREGATE: "grouping",
            OperationType.WINDOW_FUNCTION: "window",
            OperationType.JOIN: "join",
            OperationType.UNION: "stack",
            OperationType.PIVOT: "pivot",
            OperationType.UNPIVOT: "prepare",  # FOLD_MULTIPLE_COLUMNS in PREPARE
            OperationType.SORT: "sort",
            OperationType.TOP_N: "topn",
            OperationType.SAMPLE: "sampling",
            OperationType.CAST_TYPE: "prepare",
            OperationType.PARSE_DATE: "prepare",
            OperationType.SPLIT_COLUMN: "prepare",
            OperationType.ENCODE_CATEGORICAL: "prepare",
            OperationType.NORMALIZE_SCALE: "prepare",
            OperationType.GEO_OPERATION: "prepare",
            OperationType.STATISTICS: "generate_statistics",
            OperationType.CUSTOM_FUNCTION: "python",
            OperationType.UNKNOWN: "python",
        }

        return recipe_map.get(op, "python")

    def get_optimization_suggestions(self, result: AnalysisResult) -> list[str]:
        """
        Get optimization suggestions for the analyzed code.

        Args:
            result: Analysis result to optimize

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Check for filter after join
        for i, step in enumerate(result.steps):
            if step.operation == OperationType.FILTER and i > 0:
                prev_step = result.steps[i - 1]
                if prev_step.operation == OperationType.JOIN:
                    suggestions.append(
                        f"Step {step.step_number}: Consider moving filter before join "
                        f"to reduce data volume (currently after step {prev_step.step_number})"
                    )

        # Check for multiple consecutive prepare-type operations
        prepare_streak = 0
        for step in result.steps:
            if step.suggested_recipe == "prepare":
                prepare_streak += 1
            else:
                if prepare_streak > 1:
                    suggestions.append(
                        f"Found {prepare_streak} consecutive prepare operations - "
                        "these can be combined into a single Prepare recipe"
                    )
                prepare_streak = 0

        # Check for Python recipe requirements
        python_steps = [s for s in result.steps if s.requires_python_recipe]
        if python_steps:
            suggestions.append(
                f"{len(python_steps)} operation(s) require Python recipes - "
                "review if visual alternatives exist"
            )

        return suggestions
