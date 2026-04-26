# Appendix C: Cheatsheet

A one-page reference. Print it. Pin it.

---

## Core API

```python
from py2dataiku import convert, convert_with_llm, DataikuFlow
from pathlib import Path
```

| Call | When |
|---|---|
| `convert(code)` | Rule-based, fast, offline, deterministic. |
| `convert(Path("script.py"))` | Same, but reads from a file. |
| `convert_with_llm(code)` | LLM-aware semantic translation; needs an API key. |
| `convert_with_llm(code, on_progress=cb)` | Long calls — emits 6 phase events. |
| `convert_with_llm(code, temperature=0.0)` | Deterministic by default. Raise it for variety. |
| `flow.save("out.json")` | Format auto-detects from extension. Round-trip with `load`. |
| `flow.save("out.svg")` | Visualization save (also `.html`, `.png`, `.pdf`, `.puml`, `.txt`, `.md`). |
| `DataikuFlow.load("out.json")` | Symmetric load. JSON/YAML only. |
| `flow.diff(other_flow)` | Structural comparison; returns `added` / `removed` / `changed` / `equivalent`. |
| `flow.visualize(format=...)` | Returns string or bytes; doesn't write to disk. |

---

## Common pandas → DSS mappings

| Pandas | DSS Recipe / Processor |
|---|---|
| `df.groupby(...).agg(...)` | GROUPING |
| `pd.merge(a, b, ...)` | JOIN |
| `pd.concat([a, b, c])` | STACK |
| `df.drop_duplicates()` | DISTINCT (or PREPARE+RemoveDuplicates) |
| `df.sort_values(...)` | SORT |
| `df.pivot_table(...)` | PIVOT |
| `df.melt(...)` / `pd.melt(df, ...)` | PREPARE + FoldMultipleColumns |
| `df['x'].rolling(N).mean()` | WINDOW |
| `df['x'].cumsum()` | WINDOW |
| `df.nlargest(N, 'col')` | TOP_N |
| `df.head(N)` / `df.tail(N)` | SAMPLING |
| `pd.cut(df['x'], bins=N)` | PREPARE + Binner |
| `pd.get_dummies(df, columns=[...])` | PREPARE + CategoricalEncoder |
| `df['c'].str.upper()` | PREPARE + StringTransformer |
| `df.fillna(value)` | PREPARE + FillEmptyWithValue |
| `df.dropna()` | PREPARE + RemoveRowsOnEmpty |
| `df.rename(columns={...})` | PREPARE + ColumnRenamer |
| `df.drop(columns=[...])` | PREPARE + ColumnsSelector (with `keep=False`) |
| `df.describe()` / `df.info()` | GENERATE_STATISTICS |

### Filter routing (the non-obvious one)

| Pandas | Processor |
|---|---|
| `df[df.x == 'foo']` | FilterOnValue (`matchingMode=FULL_STRING`) |
| `df[df.x.isin([...])]` | FilterOnValue (multi-value) |
| `df[df.x.str.contains(...)]` | FilterOnValue (`matchingMode=SUBSTRING`) |
| `df[df.x > 100]` | FilterOnNumericRange (`min=100`) |
| `df[df.x <= 50]` | FilterOnNumericRange (`max=50`) |
| `df[(df.x > 5) & (df.y < 10)]` | FilterOnFormula (GREL) |
| `df[cond]` and `df[~cond]` (paired) | ONE multi-output SPLIT |

---

## Recipe types at a glance

- `PREPARE` — sequence of in-row processors (filter, derive, type-cast, etc.)
- `GROUPING` — reduces row dimensionality via aggregation
- `JOIN` — composes columns from two datasets on a key
- `STACK` — appends rows from N datasets with a common schema
- `WINDOW` — preserves rows; adds derived columns from partition + order
- `SORT` — permutes rows
- `DISTINCT` — drops duplicate rows
- `TOP_N` — projects to a ranked subset
- `SAMPLING` — projects to a row-count or fractional subset
- `PIVOT` — reshapes long → wide
- `SPLIT` — partitions one input into N outputs by predicate
- `SYNC` — copy a dataset between connections
- `GENERATE_STATISTICS` — row/column profiling
- `PYTHON` / `SQL` / `R` / `PYSPARK` / etc. — code recipes (escape hatch)

---

## Common processor names

The 13 you'll see most often inside a PREPARE recipe:

- `ColumnRenamer`, `ColumnsSelector`, `ColumnReorder`
- `FillEmptyWithValue`, `RemoveRowsOnEmpty`
- `StringTransformer`, `FindReplace`, `RegexpExtractor`
- `TypeSetter`, `DateParser`, `DateFormatter`
- `FilterOnValue`, `FilterOnNumericRange`, `FilterOnFormula`
- `CreateColumnWithGREL`, `Binner`, `CategoricalEncoder`
- `RemoveDuplicates`, `FoldMultipleColumns`, `Unfold`

The full catalog (~89 unique canonical names) is at `py2dataiku/mappings/processor_catalog.py`.

---

## Determinism knobs

| Knob | Default | Effect |
|---|---|---|
| `convert_with_llm(temperature=0.0)` | `0.0` | Deterministic. Raise for variety. |
| `AnthropicProvider(disable_cache=False)` | `False` | Prompt caching on; ~80% input-cost savings on repeat calls. |
| `flow.to_dict(include_timestamp=False)` | `True` | Strip wallclock for byte-stable comparisons. |

---

## Credentials

Put `ANTHROPIC_API_KEY=...` in `.env.local` (gitignored). Load via:

```python
from pathlib import Path
import os

for line in Path(".env.local").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()
```

The runnable reference: `scripts/llm_smoke_test.py`.

---

## Token usage

Every LLM call surfaces token counts on `AnalysisResult.usage`:

```python
{
    "input_tokens": 571,
    "output_tokens": 316,
    "cache_read_input_tokens": 4450,
    "cache_creation_input_tokens": 0,
}
```

Multiply `input_tokens + cache_read_input_tokens * 0.1 + output_tokens * 5` (roughly) for an Anthropic cost estimate.

---

## Further reading

- Foreword: [textbook/index.md](index.md)
- Glossary: [appendix-a-glossary.md](appendix-a-glossary.md)
- Troubleshooting: [appendix-b-troubleshooting.md](appendix-b-troubleshooting.md)
- API reference: [../api/core-functions.md](../api/core-functions.md), [../api/models.md](../api/models.md)
