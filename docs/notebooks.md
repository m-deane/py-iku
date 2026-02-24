# Notebooks & Examples

Interactive Jupyter notebooks demonstrating py-iku from beginner to expert level. Each notebook builds on the previous one and uses real library imports with executable code. The notebooks include use-case demos and feature showcases for recently added capabilities.

All notebooks are in the [`notebooks/`](https://github.com/m-deane/py-iku/tree/main/notebooks) directory.

---

## 01 - Beginner: Getting Started

**File:** [`notebooks/01_beginner.ipynb`](https://github.com/m-deane/py-iku/blob/main/notebooks/01_beginner.ipynb)

Introduces the fundamentals of py-iku:

- Importing the library and using `convert()`
- Understanding `DataikuFlow`, `DataikuRecipe`, and `DataikuDataset`
- Flow iteration with `len(flow)` and `for recipe in flow`
- Flow summaries with `get_summary()`
- ASCII and Mermaid visualization
- Serialization round-trips (`to_dict`/`from_dict`, `to_json`/`from_json`)
- Converting from `.py` files with `convert_file()`
- Practical examples: `read_csv`, `dropna`, `sort_values`, `groupby`, `drop_duplicates`, `rename`
- Use-case demos showing end-to-end conversion of common pandas pipelines

---

## 02 - Intermediate: Recipe Types & Visualizations

**File:** [`notebooks/02_intermediate.ipynb`](https://github.com/m-deane/py-iku/blob/main/notebooks/02_intermediate.ipynb)

Explores recipe types and all visualization formats:

- The `RecipeType` enum (all 37 types)
- Pandas-to-recipe mappings: PREPARE, GROUPING, JOIN, STACK, SORT, DISTINCT, TOP_N, WINDOW, PIVOT, SPLIT, SAMPLING, MELT
- `DataikuRecipe` attributes and factory methods (`create_grouping`, `create_join`, etc.)
- Recipe settings classes (`GroupingSettings`, `JoinSettings`, `WindowSettings`, `PivotSettings`, etc.)
- All 6 visualization formats: SVG, ASCII, HTML, Mermaid, PlantUML, Interactive
- Theme support: `DATAIKU_LIGHT`, `DATAIKU_DARK`, and custom themes
- Jupyter inline display with `_repr_svg_()`
- YAML serialization round-trips
- Feature showcases for WINDOW, PIVOT, TOP_N, and SAMPLING recipe generation

---

## NumPy Operations

**File:** [`notebooks/02_numpy_operations.ipynb`](https://github.com/m-deane/py-iku/blob/main/notebooks/02_numpy_operations.ipynb)

Dedicated deep-dive on NumPy support:

- Mathematical transformations: `np.log`, `np.exp`, `np.sqrt`, `np.power`, `np.abs`
- Rounding and clipping: `np.round`, `np.floor`, `np.ceil`, `np.clip`
- Conditional operations: `np.where`, `np.isnan`, `np.isfinite`, `np.nan_to_num`
- Aggregation functions: `np.sum`, `np.mean`, `np.std`, `np.percentile`
- Array operations: `np.concatenate`, `np.vstack`, `np.sort`, `np.unique`
- Feature engineering pipeline combining NumPy and pandas
- Complete supported NumPy functions reference (30+ functions)

---

## Scikit-learn Pipelines

**File:** [`notebooks/03_sklearn_pipelines.ipynb`](https://github.com/m-deane/py-iku/blob/main/notebooks/03_sklearn_pipelines.ipynb)

Demonstrates scikit-learn ML pipeline conversion:

- Data scaling: `StandardScaler`, `MinMaxScaler`, `RobustScaler`
- Categorical encoding: `LabelEncoder`, `OneHotEncoder`, `OrdinalEncoder`
- Missing value imputation: `SimpleImputer`, `KNNImputer`
- Train-test split: `train_test_split` to Dataiku Split recipe
- Feature selection: `PCA`, `TruncatedSVD`, `SelectKBest`
- Complete ML pipeline combining multiple sklearn components
- sklearn Pipeline object recognition
- sklearn-to-Dataiku mapping reference table

---

## 03 - Advanced: Processors, DAG Analysis & Flow Optimization

**File:** [`notebooks/03_advanced.ipynb`](https://github.com/m-deane/py-iku/blob/main/notebooks/03_advanced.ipynb)

Covers advanced analysis and optimization features:

- `ProcessorCatalog`: browsing 100+ Dataiku processors with metadata
- Building `PrepareStep` instances for 17+ processor types
- `PrepareSettings` for composing multi-step Prepare recipes
- `FlowGraph` DAG analysis: topological sort, cycle detection, path finding, disconnected subgraphs
- `FlowOptimizer`: merging consecutive Prepare recipes, removing orphan datasets, step reordering
- `convert(optimize=True)` demonstration showing before/after recipe counts
- Flow validation with `flow.validate()`
- Column lineage tracing with `flow.get_column_lineage()`
- `to_api_dict()` output format showcasing Dataiku API-compatible payloads

---

## 04 - Expert: LLM Analysis, DSS Export & Configuration

**File:** [`notebooks/04_expert.ipynb`](https://github.com/m-deane/py-iku/blob/main/notebooks/04_expert.ipynb)

Demonstrates LLM-based analysis and project export:

- LLM-based conversion with `MockProvider` (no API key needed)
- LLM provider architecture: `AnthropicProvider`, `OpenAIProvider`, `get_provider()`
- `LLMCodeAnalyzer` and `AnalysisResult` with `DataStep` and `OperationType`
- Rule-based vs LLM-based comparison
- `Py2Dataiku` hybrid class with automatic fallback
- Configuration via `Py2DataikuConfig`, TOML/YAML/RC files, environment variables
- DSS project export with `DSSExporter` and `export_to_dss()`
- `DatasetConnectionType` (13 types) and `ColumnSchema`
- `FlowZone` for organizing large flows

---

## 05 - Master: Extensibility, Scenarios, MLOps & Pipelines

**File:** [`notebooks/05_master.ipynb`](https://github.com/m-deane/py-iku/blob/main/notebooks/05_master.ipynb)

The comprehensive master class covering all advanced features:

- **Plugin Registry**: instance-based and global APIs, `plugin_hook` decorator, `Plugin` base class, `PluginContext`
- **Scenarios**: `DataikuScenario` with triggers (4 types), steps (6 types), reporters (3 types)
- **Metrics & Data Quality**: `DataikuMetric` (10 types), `DataikuCheck` (8 conditions), `DataQualityRule` (5 rule types)
- **MLOps**: `APIEndpoint` (REST/batch), `ModelVersion` (6 frameworks), `DriftConfig` (4 metrics)
- **Exception handling**: the full `Py2DataikuError` hierarchy (7 exception types)
- **Advanced enums**: aggregation functions, window functions, join types, string/numeric modes
- **Real-world pipelines**: ETL, ML feature engineering, data quality monitoring
- **Grand finale**: multi-zone production fraud detection system with scenarios, metrics, MLOps, and visualization
