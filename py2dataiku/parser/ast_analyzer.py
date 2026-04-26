"""Python AST analysis for extracting data transformations."""

import ast
from typing import Any, Optional

from py2dataiku.exceptions import InvalidPythonCodeError
from py2dataiku.mappings.pandas_mappings import PandasMapper
from py2dataiku.models.transformation import Transformation, TransformationType
from py2dataiku.plugins.registry import PluginContext, PluginRegistry


class CodeAnalyzer:
    """
    Analyze Python code and extract data transformation operations.

    Uses Python's AST module to parse code and identify patterns
    like pandas DataFrame operations, merges, groupby, etc.
    """

    # Shared dispatch table for DataFrame method handlers.
    # Maps method names to handler method names (resolved to bound methods in __init__).
    _METHOD_HANDLER_NAMES = {
        "fillna": "_handle_fillna",
        "dropna": "_handle_dropna",
        "drop_duplicates": "_handle_drop_duplicates",
        "drop": "_handle_drop",
        "rename": "_handle_rename",
        "merge": "_handle_merge",
        "join": "_handle_join",
        "groupby": "_handle_groupby",
        "sort_values": "_handle_sort",
        "head": "_handle_head",
        "tail": "_handle_tail",
        "sample": "_handle_sample",
        "astype": "_handle_astype",
        "to_datetime": "_handle_to_datetime",
        "pivot": "_handle_pivot",
        "pivot_table": "_handle_pivot",
        "melt": "_handle_melt",
        "rolling": "_handle_rolling",
        "str": "_handle_str_accessor",
        "nlargest": "_handle_nlargest",
        "nsmallest": "_handle_nsmallest",
        "query": "_handle_query",
        "assign": "_handle_assign",
        "clip": "_handle_clip",
        "round": "_handle_round",
        "abs": "_handle_abs",
        "map": "_handle_map",
        "where": "_handle_where",
        "mask": "_handle_mask",
        "replace": "_handle_replace",
        "explode": "_handle_explode",
        "combine_first": "_handle_combine_first",
        "cumsum": "_handle_cumsum",
        "cummin": "_handle_cummin",
        "cummax": "_handle_cummax",
        "cumprod": "_handle_cumprod",
        "diff": "_handle_diff",
        "shift": "_handle_shift",
        "rank": "_handle_rank",
        "nunique": "_handle_nunique",
        "interpolate": "_handle_interpolate",
        "describe": "_handle_describe",
        "info": "_handle_info",
    }

    def __init__(self):
        self.transformations: list[Transformation] = []
        self.dataframes: dict[str, str] = {}  # variable -> source
        self.current_line: int = 0
        self._source_code: str = ""
        # Build bound-method dispatch table from class-level name mapping,
        # skipping any entries whose handler method doesn't exist yet
        self._method_handlers = {
            name: getattr(self, handler_name)
            for name, handler_name in self._METHOD_HANDLER_NAMES.items()
            if hasattr(self, handler_name)
        }

    def analyze(self, code: str) -> list[Transformation]:
        """
        Extract all transformations from Python code.

        Args:
            code: Python source code string

        Returns:
            List of Transformation objects
        """
        self.transformations = []
        self.dataframes = {}
        self._source_code = code

        try:
            tree = ast.parse(code)
            self._visit_module(tree)
        except SyntaxError as e:
            # Raise InvalidPythonCodeError so callers can catch it
            raise InvalidPythonCodeError(
                f"Invalid Python syntax at line {e.lineno}: {e.msg}"
            ) from e

        # Post-pass: detect complementary boolean filters and merge into a
        # single FILTER transformation that the generator turns into a
        # multi-output SPLIT recipe.
        self._merge_complementary_filters()

        return self.transformations

    def _merge_complementary_filters(self) -> None:
        """Detect ``df[cond]`` / ``df[~cond]`` pairs and merge them.

        Walks ``self.transformations`` looking for two consecutive FILTER
        transformations on the same source DataFrame whose conditions are
        explicit complements of each other (one wraps the other in a
        unary ``not``). Replaces the pair with a single FILTER carrying
        ``parameters["complementary_outputs"] = [target_a, target_b]`` so
        the flow generator can emit ONE SPLIT recipe with two output
        datasets — the canonical DSS shape for partitioned filtering.

        Conservative: only matches the explicit ``~condition`` pattern.
        Does NOT try to infer complementarity from value comparisons
        (e.g. ``df[df.x > 5]`` and ``df[df.x <= 5]``) because that risks
        false positives when the semantic complement isn't exact.
        """
        def _condition_text(trans: Transformation) -> str:
            return (trans.parameters or {}).get("condition", "") or ""

        def _is_complement(a_cond: str, b_cond: str) -> bool:
            # Treat "~(X)" or "~X" as complement of "X" (and vice versa).
            for x, y in ((a_cond, b_cond), (b_cond, a_cond)):
                x_stripped = x.strip()
                if x_stripped.startswith("~"):
                    inner = x_stripped[1:].strip()
                    if inner.startswith("(") and inner.endswith(")"):
                        inner = inner[1:-1].strip()
                    if inner == y.strip():
                        return True
            return False

        merged_indices: set[int] = set()
        new_transformations: list[Transformation] = []
        for i, trans in enumerate(self.transformations):
            if i in merged_indices:
                continue
            if trans.transformation_type != TransformationType.FILTER:
                new_transformations.append(trans)
                continue
            # Look for a complementary FILTER later in the list with the
            # same source dataframe and a complementary condition.
            partner_idx = None
            for j in range(i + 1, len(self.transformations)):
                if j in merged_indices:
                    continue
                other = self.transformations[j]
                if other.transformation_type != TransformationType.FILTER:
                    continue
                if other.source_dataframe != trans.source_dataframe:
                    continue
                if _is_complement(
                    _condition_text(trans), _condition_text(other)
                ):
                    partner_idx = j
                    break
            if partner_idx is None:
                new_transformations.append(trans)
                continue
            # Found a complementary pair. Build a merged FILTER that
            # carries both target dataframe names. Use the non-negated
            # condition as the SPLIT condition (so the first output is
            # the "match" and the second is the "complement").
            partner = self.transformations[partner_idx]
            cond_a = _condition_text(trans)
            cond_b = _condition_text(partner)
            if cond_a.strip().startswith("~"):
                positive_cond = cond_b
                positive_target = partner.target_dataframe
                complement_target = trans.target_dataframe
            else:
                positive_cond = cond_a
                positive_target = trans.target_dataframe
                complement_target = partner.target_dataframe

            merged_params = dict(trans.parameters or {})
            merged_params["condition"] = positive_cond
            merged_params["complementary_outputs"] = [
                positive_target,
                complement_target,
            ]
            new_transformations.append(
                Transformation(
                    transformation_type=TransformationType.FILTER,
                    source_dataframe=trans.source_dataframe,
                    target_dataframe=positive_target,
                    parameters=merged_params,
                    source_line=trans.source_line,
                    suggested_recipe="split",
                    notes=(trans.notes or [])
                    + [
                        f"Complementary filter detected: {complement_target} "
                        f"is the negation of {positive_target}"
                    ],
                )
            )
            merged_indices.add(partner_idx)

        self.transformations = new_transformations

    def _visit_module(self, node: ast.Module) -> None:
        """Visit all statements in a module."""
        for stmt in node.body:
            self._visit_statement(stmt)

    def _visit_statement(self, node: ast.stmt) -> None:
        """Visit a single statement."""
        self.current_line = getattr(node, "lineno", 0)

        if isinstance(node, ast.Assign):
            self._handle_assignment(node)
        elif isinstance(node, ast.Expr):
            self._handle_expression(node)
        elif isinstance(node, ast.FunctionDef):
            # Skip function definitions for now
            pass
        elif isinstance(node, ast.If):
            # Handle if statements (could create Split recipes)
            self._handle_if(node)
        elif isinstance(node, ast.For):
            # Handle for loops
            for stmt in node.body:
                self._visit_statement(stmt)

    def _handle_assignment(self, node: ast.Assign) -> None:
        """Handle assignment statements."""
        if len(node.targets) != 1:
            return

        target = node.targets[0]
        if isinstance(target, ast.Name):
            target_name = target.id
        elif isinstance(target, ast.Subscript):
            # df['col'] = ...
            target_name = self._get_subscript_info(target)
        else:
            return

        value = node.value
        self._analyze_value(value, target_name)

    def _analyze_value(self, value: ast.expr, target_name: str) -> None:
        """Analyze the right-hand side of an assignment."""
        if isinstance(value, ast.Call):
            self._handle_call(value, target_name)
        elif isinstance(value, ast.Attribute):
            # Could be a method chain result
            pass
        elif isinstance(value, ast.Subscript):
            # df[condition] - filtering
            self._handle_filter(value, target_name)
        elif isinstance(value, ast.BinOp):
            # df['a'] + df['b']
            self._handle_binop(value, target_name)

    def _handle_call(self, node: ast.Call, target: str) -> None:
        """Handle function/method calls."""
        func = node.func

        if isinstance(func, ast.Attribute):
            # Method call: obj.method()
            method_name = func.attr
            obj = func.value

            # Check if this is a method chain
            if self._is_method_chain(node):
                self._handle_method_chain(node, target)
                return

            # Get the object being called on
            obj_name = self._get_name(obj)

            # Handle pandas read functions
            if method_name == "read_csv" and obj_name == "pd":
                self._handle_read_csv(node, target)
            elif method_name == "read_excel" and obj_name == "pd":
                self._handle_read_data(node, target, "excel")
            elif method_name == "merge" and obj_name == "pd":
                self._handle_pd_merge(node, target)
            elif method_name == "concat" and obj_name == "pd":
                self._handle_concat(node, target)
            elif method_name in ("cut", "qcut") and obj_name == "pd":
                self._handle_pd_binner(method_name, node, target)
            elif method_name == "get_dummies" and obj_name == "pd":
                self._handle_pd_get_dummies(node, target)
            elif method_name == "melt" and obj_name == "pd":
                # df = pd.melt(frame, ...) — extract source from first positional arg
                source_df = (
                    self._get_name(node.args[0]) if node.args else "df"
                )
                self._handle_melt(source_df, node, target)
            # Handle sklearn method calls (fit, transform, fit_transform, predict)
            elif method_name in ("fit", "transform", "fit_transform", "predict", "predict_proba"):
                self._handle_sklearn_method(obj_name, method_name, node, target)
            # Handle NumPy function calls like np.log(), np.clip(), etc.
            elif obj_name in ("np", "numpy"):
                self._handle_numpy_function(method_name, node, target)
            else:
                # DataFrame method calls
                self._handle_dataframe_method(obj, method_name, node, target)

        elif isinstance(func, ast.Name):
            # Direct function call
            func_name = func.id
            # Handle sklearn functions
            if func_name == "train_test_split":
                self._handle_train_test_split(node, target)
            elif func_name in ("StandardScaler", "MinMaxScaler", "RobustScaler",
                              "MaxAbsScaler", "Normalizer"):
                self._handle_sklearn_scaler(func_name, node, target)
            elif func_name in ("LabelEncoder", "OneHotEncoder", "OrdinalEncoder",
                              "LabelBinarizer"):
                self._handle_sklearn_encoder(func_name, node, target)
            elif func_name in ("SimpleImputer", "KNNImputer", "IterativeImputer"):
                self._handle_sklearn_imputer(func_name, node, target)
            elif func_name == "Pipeline":
                self._handle_sklearn_pipeline(node, target)
            elif func_name in ("PCA", "TruncatedSVD", "SelectKBest", "SelectFromModel"):
                self._handle_sklearn_feature_selector(func_name, node, target)
            elif func_name in ("RandomForestClassifier", "RandomForestRegressor",
                              "GradientBoostingClassifier", "GradientBoostingRegressor",
                              "LogisticRegression", "LinearRegression", "SVC", "SVR",
                              "DecisionTreeClassifier", "DecisionTreeRegressor"):
                self._handle_sklearn_model(func_name, node, target)
            elif func_name in ("KMeans", "DBSCAN", "AgglomerativeClustering",
                              "MiniBatchKMeans"):
                self._handle_sklearn_clustering(func_name, node, target)
            elif func_name == "cross_val_score":
                self._handle_cross_val_score(node, target)
            elif func_name == "GridSearchCV":
                self._handle_grid_search(node, target)
            elif func_name == "ColumnTransformer":
                self._handle_column_transformer(node, target)
            # Handle NumPy functions
            elif func_name in ("np", "numpy"):
                pass  # Handled via attribute access below
            elif func_name == "pd":
                # pd.something
                pass

    def _is_method_chain(self, node: ast.Call) -> bool:
        """Check if a Call node is part of a method chain (multiple chained calls)."""
        if not isinstance(node.func, ast.Attribute):
            return False

        # Check if the object being called on is also a Call (chain)
        obj = node.func.value
        if isinstance(obj, ast.Call) and isinstance(obj.func, ast.Attribute):
            # This is a chain like obj.method1().method2()
            return True
        return False

    def _unwind_method_chain(self, node: ast.Call) -> list[tuple[str, ast.Call]]:
        """
        Unwind a method chain into a list of (method_name, call_node) tuples.

        For df.dropna().fillna(0).sort_values('col'), returns:
        [('dropna', call1), ('fillna', call2), ('sort_values', call3)]
        """
        chain = []
        current = node

        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            method_name = current.func.attr
            chain.append((method_name, current))
            current = current.func.value

        # Reverse to get operations in order
        chain.reverse()
        return chain

    def _get_chain_base(self, node: ast.Call) -> str:
        """Get the base DataFrame name from a method chain."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            current = current.func.value

        return self._get_name(current)

    def _handle_method_chain(self, node: ast.Call, target: str) -> None:
        """
        Handle a chain of method calls like df.dropna().fillna(0).sort_values('col').

        Unwinds the chain and processes each method in order.
        """
        chain = self._unwind_method_chain(node)
        base_df = self._get_chain_base(node)

        if not chain:
            return

        # C2: Detect groupby().agg() and groupby().<shorthand>() chains
        _SHORTHAND_AGG_METHODS = {"sum", "mean", "count", "min", "max", "std", "var"}
        if len(chain) >= 2:
            for i in range(len(chain) - 1):
                if chain[i][0] == "groupby" and chain[i + 1][0] in _SHORTHAND_AGG_METHODS | {"agg"}:
                    groupby_call = chain[i][1]
                    agg_call = chain[i + 1][1]
                    agg_method = chain[i + 1][0]

                    # Extract groupby keys
                    keys = []
                    if groupby_call.args:
                        keys = self._get_list_value(groupby_call.args[0])

                    # Extract aggregations: dict form for .agg(), method name for shorthand
                    aggregations: dict = {}
                    if agg_method == "agg":
                        if agg_call.args and isinstance(agg_call.args[0], ast.Dict):
                            aggregations = self._get_dict_value(agg_call.args[0])
                    else:
                        # Shorthand: groupby().sum() -> aggregation is the method name
                        aggregations = {"*": agg_method}

                    self.transformations.append(
                        Transformation(
                            transformation_type=TransformationType.GROUPBY,
                            source_dataframe=base_df,
                            target_dataframe=target,
                            columns=keys,
                            parameters={
                                "keys": keys,
                                "aggregations": aggregations,
                                "aggregation": agg_method,
                            },
                            source_line=self.current_line,
                            suggested_recipe="grouping",
                        )
                    )
                    return

        # Detect rolling().agg-fn() chains and emit ONE WINDOW transformation
        # (was: emitting empty WINDOW shell + phantom GROUPING from the .mean()).
        # Same handling for expanding(), ewm() — all are window operations.
        _WINDOW_OPS = {"rolling", "expanding", "ewm"}
        if len(chain) >= 2:
            for i in range(len(chain) - 1):
                if (
                    chain[i][0] in _WINDOW_OPS
                    and chain[i + 1][0] in _SHORTHAND_AGG_METHODS
                ):
                    window_call = chain[i][1]
                    agg_method = chain[i + 1][0]

                    # Extract window size from rolling(window=N) or rolling(N)
                    window_size = None
                    if window_call.args and isinstance(window_call.args[0], ast.Constant):
                        window_size = window_call.args[0].value
                    for kw in window_call.keywords:
                        if kw.arg == "window" and isinstance(kw.value, ast.Constant):
                            window_size = kw.value.value

                    # Map pandas agg method to DSS window function name
                    window_func_map = {
                        "sum": "SUM",
                        "mean": "AVG",
                        "count": "COUNT",
                        "min": "MIN",
                        "max": "MAX",
                        "std": "STDDEV",
                        "var": "VAR",
                    }
                    window_func = window_func_map.get(agg_method, agg_method.upper())

                    # Walk to the chain's deepest node to detect a Subscript
                    # like df["sales"] and extract the column name.
                    column = ""
                    deepest = node
                    while isinstance(deepest, ast.Call) and isinstance(deepest.func, ast.Attribute):
                        deepest = deepest.func.value
                    if isinstance(deepest, ast.Subscript) and isinstance(deepest.slice, ast.Constant):
                        column = str(deepest.slice.value)

                    self.transformations.append(
                        Transformation(
                            transformation_type=TransformationType.ROLLING,
                            source_dataframe=base_df,
                            target_dataframe=target,
                            columns=[column] if column else [],
                            parameters={
                                "method": agg_method,
                                "window_function": window_func,
                                "window": window_size,
                                "column": column,
                            },
                            source_line=self.current_line,
                            suggested_recipe="window",
                            notes=[
                                f"df.{chain[i][0]}({window_size or ''}).{agg_method}() "
                                f"-> WINDOW recipe with {window_func}"
                            ],
                        )
                    )
                    return

        # Process each method in the chain
        current_df = base_df
        for i, (method_name, call_node) in enumerate(chain):
            # For intermediate steps, use temporary names
            if i < len(chain) - 1:
                step_target = f"_chain_step_{i}"
            else:
                step_target = target

            # Dispatch to appropriate handler
            self._dispatch_method_handler(current_df, method_name, call_node, step_target)
            current_df = step_target

    def _dispatch_method_handler(
        self, df: str, method_name: str, node: ast.Call, target: str
    ) -> None:
        """Dispatch a method call to the appropriate handler."""
        # Skip passthrough methods
        if method_name in ("copy", "reset_index", "to_frame"):
            return

        # Check for plugin handler first
        plugin_handler = PluginRegistry.get_method_handler(method_name)
        if plugin_handler:
            context = PluginContext(
                source_code=self._source_code,
                current_line=self.current_line,
                variables={},
                dataframes=self.dataframes.copy(),
            )
            result = plugin_handler(node, context)
            if result:
                if isinstance(result, list):
                    self.transformations.extend(result)
                else:
                    self.transformations.append(result)
            return

        handler = self._method_handlers.get(method_name)
        if handler:
            handler(df, node, target)
        else:
            # Handle .str, .dt accessors and other patterns
            if method_name in ("upper", "lower", "strip", "title", "capitalize"):
                self._handle_string_method(df, method_name, node, target)
            elif method_name in ("sum", "mean", "count", "min", "max", "std", "var"):
                self._handle_agg_method(df, method_name, node, target)
            else:
                # Unknown method - record it
                self.transformations.append(
                    Transformation(
                        transformation_type=TransformationType.UNKNOWN,
                        source_dataframe=df,
                        target_dataframe=target,
                        parameters={"method": method_name},
                        source_line=self.current_line,
                        notes=[f"Chained method: {method_name}"],
                    )
                )

    def _handle_nlargest(self, df: str, node: ast.Call, target: str) -> None:
        """Handle nlargest() calls."""
        n = 5
        column = None
        if node.args:
            if isinstance(node.args[0], ast.Constant):
                n = node.args[0].value
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                column = node.args[1].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"n": n, "column": column, "ascending": False},
                source_line=self.current_line,
                suggested_recipe="topn",
            )
        )

    def _handle_nsmallest(self, df: str, node: ast.Call, target: str) -> None:
        """Handle nsmallest() calls."""
        n = 5
        column = None
        if node.args:
            if isinstance(node.args[0], ast.Constant):
                n = node.args[0].value
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                column = node.args[1].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"n": n, "column": column, "ascending": True},
                source_line=self.current_line,
                suggested_recipe="topn",
            )
        )

    def _handle_query(self, df: str, node: ast.Call, target: str) -> None:
        """Handle query() calls."""
        condition = ""
        if node.args and isinstance(node.args[0], ast.Constant):
            condition = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FILTER,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"condition": condition},
                source_line=self.current_line,
                suggested_processor="FilterOnFormula",
            )
        )

    def _handle_assign(self, df: str, node: ast.Call, target: str) -> None:
        """Handle assign() calls for creating new columns.

        Each keyword argument becomes a separate COLUMN_CREATE transformation
        so the resulting flow has one PREPARE step per assigned column. For
        lambda values, the lambda body is unparsed back to source so that
        ``CreateColumnWithGREL`` has a real expression to put on the recipe.
        """
        for kw in node.keywords:
            col_name = kw.arg or "new_column"
            value = kw.value
            expression = ""

            if isinstance(value, ast.Lambda):
                # df.assign(c=lambda x: x.a + x.b) -> "x.a + x.b"
                try:
                    expression = ast.unparse(value.body)
                except (AttributeError, ValueError):
                    expression = ""
            elif isinstance(value, ast.Constant):
                expression = repr(value.value)
            else:
                # Arbitrary expression — unparse if possible
                try:
                    expression = ast.unparse(value)
                except (AttributeError, ValueError):
                    expression = ""

            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.COLUMN_CREATE,
                    source_dataframe=df,
                    target_dataframe=target,
                    columns=[col_name],
                    parameters={
                        "output_column": col_name,
                        "expression": expression,
                    },
                    source_line=self.current_line,
                    suggested_processor="CreateColumnWithGREL",
                )
            )

    def _handle_clip(self, df: str, node: ast.Call, target: str) -> None:
        """Handle clip() calls."""
        lower = None
        upper = None
        for kw in node.keywords:
            if kw.arg == "lower" and isinstance(kw.value, ast.Constant):
                lower = kw.value.value
            elif kw.arg == "upper" and isinstance(kw.value, ast.Constant):
                upper = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"operation": "clip", "lower": lower, "upper": upper},
                source_line=self.current_line,
                suggested_processor="ClipColumn",
            )
        )

    def _handle_round(self, df: str, node: ast.Call, target: str) -> None:
        """Handle round() calls."""
        decimals = 0
        if node.args and isinstance(node.args[0], ast.Constant):
            decimals = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"operation": "round", "decimals": decimals},
                source_line=self.current_line,
                suggested_processor="RoundColumn",
            )
        )

    def _handle_abs(self, df: str, node: ast.Call, target: str) -> None:
        """Handle abs() calls."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"operation": "abs"},
                source_line=self.current_line,
                # df.abs() has no native DSS Prepare processor — route through
                # CreateColumnWithGREL with an abs() expression downstream.
                suggested_processor="CreateColumnWithGREL",
            )
        )

    def _handle_string_method(self, df: str, method: str, node: ast.Call, target: str) -> None:
        """Handle string methods like upper(), lower(), strip()."""
        mode_enum = PandasMapper.STRING_MAPPINGS.get(method)
        mode = mode_enum.value if mode_enum else method

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.STRING_TRANSFORM,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"mode": mode},
                source_line=self.current_line,
                suggested_processor="StringTransformer",
            )
        )

    def _handle_agg_method(self, df: str, method: str, node: ast.Call, target: str) -> None:
        """Handle aggregation methods called directly (e.g., df['col'].sum())."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.GROUPBY,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"aggregation": method},
                source_line=self.current_line,
                suggested_recipe="grouping",
            )
        )

    def _handle_read_csv(self, node: ast.Call, target: str) -> None:
        """Handle pd.read_csv() calls."""
        filepath = "unknown"
        if node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant):
                filepath = str(arg.value)

        self.dataframes[target] = filepath
        self.transformations.append(
            Transformation.read_csv(target, filepath, self.current_line)
        )

    def _handle_read_data(self, node: ast.Call, target: str, format: str) -> None:
        """Handle data reading functions."""
        filepath = "unknown"
        if node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant):
                filepath = str(arg.value)

        self.dataframes[target] = filepath
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.READ_DATA,
                target_dataframe=target,
                parameters={"filepath": filepath, "format": format},
                source_line=self.current_line,
            )
        )

    def _extract_column_from_subscript(self, node: ast.expr) -> Optional[str]:
        """Extract column name from a subscript like df['col'] or df['col'].str."""
        current = node
        # Walk through Attribute nodes (e.g., df['col'].str -> Attribute(.str, Subscript))
        while isinstance(current, ast.Attribute):
            current = current.value
        if isinstance(current, ast.Subscript):
            if isinstance(current.slice, ast.Constant) and isinstance(current.slice.value, str):
                return current.slice.value
        return None

    def _handle_dataframe_method(
        self, obj: ast.expr, method: str, node: ast.Call, target: str
    ) -> None:
        """Handle DataFrame method calls."""
        obj_name = self._get_name(obj)

        # H1: Detect .str.method() accessor pattern
        # AST for df['col'].str.upper(): Call(.upper) on Attribute(.str) on Subscript(df['col'])
        if isinstance(obj, ast.Attribute) and obj.attr == "str":
            column = self._extract_column_from_subscript(obj)
            df_name = self._get_name(obj.value)
            self._handle_str_method_call(df_name, column, method, node, target)
            return

        # H2: Extract column from subscript for column-specific methods
        # AST for df['col'].fillna(0): Call(.fillna) on Subscript(df['col'])
        column_from_subscript = self._extract_column_from_subscript(obj)

        # Check for method chains
        if isinstance(obj, ast.Attribute):
            # This is part of a chain, recurse
            self._handle_dataframe_method(obj.value, obj.attr, node, target)

        # Check for plugin handler first
        plugin_handler = PluginRegistry.get_method_handler(method)
        if plugin_handler:
            context = PluginContext(
                source_code=self._source_code,
                current_line=self.current_line,
                variables={},
                dataframes=self.dataframes.copy(),
            )
            result = plugin_handler(node, context)
            if result:
                if isinstance(result, list):
                    self.transformations.extend(result)
                else:
                    self.transformations.append(result)
            return

        handler = self._method_handlers.get(method)
        if handler:
            # H2: Pass column context for fillna/astype when called on subscript
            if column_from_subscript and method in ("fillna", "astype"):
                handler(obj_name, node, target, column=column_from_subscript)
            else:
                handler(obj_name, node, target)
        elif method in ("copy", "reset_index"):
            # Passthrough operations
            pass
        else:
            # Unknown method - might need Python recipe
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.UNKNOWN,
                    source_dataframe=obj_name,
                    target_dataframe=target,
                    parameters={"method": method},
                    source_line=self.current_line,
                    notes=[f"Unknown method: {method}"],
                )
            )

    def _handle_fillna(self, df: str, node: ast.Call, target: str, column: Optional[str] = None) -> None:
        """Handle fillna() calls."""
        value = None
        if node.args:
            val_node = node.args[0]
            if isinstance(val_node, ast.Constant):
                value = val_node.value

        columns = [column] if column else []
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe=df,
                target_dataframe=target,
                columns=columns,
                parameters={"value": value, "column": column or "unknown"},
                source_line=self.current_line,
                suggested_processor="FillEmptyWithValue",
            )
        )

    def _handle_dropna(self, df: str, node: ast.Call, target: str) -> None:
        """Handle dropna() calls."""
        subset = None
        for kw in node.keywords:
            if kw.arg == "subset":
                subset = self._get_list_value(kw.value)

        self.transformations.append(
            Transformation.dropna(df, subset, self.current_line)
        )

    def _handle_drop_duplicates(self, df: str, node: ast.Call, target: str) -> None:
        """Handle drop_duplicates() calls."""
        subset = None
        for kw in node.keywords:
            if kw.arg == "subset":
                subset = self._get_list_value(kw.value)

        self.transformations.append(
            Transformation.drop_duplicates(df, subset, self.current_line)
        )

    def _handle_drop(self, df: str, node: ast.Call, target: str) -> None:
        """Handle drop() calls."""
        columns = []
        for kw in node.keywords:
            if kw.arg == "columns":
                columns = self._get_list_value(kw.value)

        if columns:
            self.transformations.append(
                Transformation.drop_columns(df, columns, self.current_line)
            )

    def _handle_rename(self, df: str, node: ast.Call, target: str) -> None:
        """Handle rename() calls."""
        mapping = {}
        for kw in node.keywords:
            if kw.arg == "columns":
                mapping = self._get_dict_value(kw.value)

        if mapping:
            self.transformations.append(
                Transformation.rename_columns(df, mapping, self.current_line)
            )

    def _handle_merge(self, df: str, node: ast.Call, target: str) -> None:
        """Handle merge() calls on DataFrame."""
        right = None
        on = None
        left_on = None
        right_on = None
        how = "inner"

        if node.args:
            right = self._get_name(node.args[0])

        for kw in node.keywords:
            if kw.arg == "on":
                on = self._get_list_value(kw.value)
            elif kw.arg == "left_on":
                left_on = self._get_list_value(kw.value)
            elif kw.arg == "right_on":
                right_on = self._get_list_value(kw.value)
            elif kw.arg == "how" and isinstance(kw.value, ast.Constant):
                how = kw.value.value

        self.transformations.append(
            Transformation.merge(
                df, right or "", target, on, left_on, right_on, how, self.current_line
            )
        )

    def _handle_pd_merge(self, node: ast.Call, target: str) -> None:
        """Handle pd.merge() calls."""
        left = None
        right = None
        on = None
        left_on = None
        right_on = None
        how = "inner"

        if len(node.args) >= 2:
            left = self._get_name(node.args[0])
            right = self._get_name(node.args[1])

        for kw in node.keywords:
            if kw.arg == "on":
                on = self._get_list_value(kw.value)
            elif kw.arg == "left_on":
                left_on = self._get_list_value(kw.value)
            elif kw.arg == "right_on":
                right_on = self._get_list_value(kw.value)
            elif kw.arg == "how" and isinstance(kw.value, ast.Constant):
                how = kw.value.value

        self.transformations.append(
            Transformation.merge(
                left or "", right or "", target, on, left_on, right_on, how, self.current_line
            )
        )

    def _handle_join(self, df: str, node: ast.Call, target: str) -> None:
        """Handle join() calls."""
        right = None
        if node.args:
            right = self._get_name(node.args[0])

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.JOIN,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"right": right, "type": "index"},
                source_line=self.current_line,
                suggested_recipe="join",
            )
        )

    def _handle_groupby(self, df: str, node: ast.Call, target: str) -> None:
        """Handle groupby() calls - needs to detect .agg() chain."""
        keys = []
        if node.args:
            keys = self._get_list_value(node.args[0])

        # Note: The actual aggregation will be in a chained method
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.GROUPBY,
                source_dataframe=df,
                target_dataframe=target,
                columns=keys,
                parameters={"keys": keys, "aggregations": {}},
                source_line=self.current_line,
                suggested_recipe="grouping",
                notes=["Aggregations parsed from .agg() chain"],
            )
        )

    def _handle_sort(self, df: str, node: ast.Call, target: str) -> None:
        """Handle sort_values() calls."""
        columns = []
        ascending = True

        if node.args:
            columns = self._get_list_value(node.args[0])

        for kw in node.keywords:
            if kw.arg == "by":
                columns = self._get_list_value(kw.value)
            elif kw.arg == "ascending" and isinstance(kw.value, ast.Constant):
                ascending = kw.value.value

        self.transformations.append(
            Transformation.sort_values(df, columns, ascending, self.current_line)
        )

    def _handle_head(self, df: str, node: ast.Call, target: str) -> None:
        """Handle head() calls."""
        n = 5  # Default
        if node.args and isinstance(node.args[0], ast.Constant):
            n = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.HEAD,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"n": n},
                source_line=self.current_line,
                suggested_recipe="topn",
            )
        )

    def _handle_tail(self, df: str, node: ast.Call, target: str) -> None:
        """Handle tail() calls."""
        n = 5
        if node.args and isinstance(node.args[0], ast.Constant):
            n = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.TAIL,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"n": n},
                source_line=self.current_line,
                notes=["Tail requires Python recipe or Sort + TopN"],
            )
        )

    def _handle_sample(self, df: str, node: ast.Call, target: str) -> None:
        """Handle sample() calls."""
        n = None
        frac = None

        for kw in node.keywords:
            if kw.arg == "n" and isinstance(kw.value, ast.Constant):
                n = kw.value.value
            elif kw.arg == "frac" and isinstance(kw.value, ast.Constant):
                frac = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.SAMPLE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"n": n, "frac": frac},
                source_line=self.current_line,
                suggested_recipe="sampling",
            )
        )

    def _handle_astype(self, df: str, node: ast.Call, target: str, column: Optional[str] = None) -> None:
        """Handle astype() calls."""
        dtype = None
        if node.args and isinstance(node.args[0], ast.Name):
            dtype = node.args[0].id
        elif node.args and isinstance(node.args[0], ast.Constant):
            dtype = str(node.args[0].value)

        columns = [column] if column else []
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.TYPE_CAST,
                source_dataframe=df,
                target_dataframe=target,
                columns=columns,
                parameters={"dtype": dtype, "column": column or "unknown"},
                source_line=self.current_line,
                suggested_processor="TypeSetter",
            )
        )

    def _handle_to_datetime(self, df: str, node: ast.Call, target: str) -> None:
        """Handle pd.to_datetime() calls."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.DATE_PARSE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={},
                source_line=self.current_line,
                suggested_processor="DateParser",
            )
        )

    def _handle_pivot(self, df: str, node: ast.Call, target: str) -> None:
        """Handle pivot() calls."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.PIVOT,
                source_dataframe=df,
                target_dataframe=target,
                parameters={},
                source_line=self.current_line,
                suggested_recipe="pivot",
            )
        )

    def _handle_melt(self, df: str, node: ast.Call, target: str) -> None:
        """Handle melt() calls.

        Melt is unpivot (wide-to-long); it maps to a PREPARE recipe with the
        FOLD_MULTIPLE_COLUMNS processor, not PIVOT (which is long-to-wide).

        Extracts ``id_vars``, ``value_vars``, ``var_name``, ``value_name`` from
        kwargs (and corresponding positional args). The columns to fold come
        from ``value_vars``; if absent, all columns except ``id_vars`` should
        be folded, but we cannot know the schema at parse time — store
        ``id_vars`` so the runtime can compute the complement.
        """
        params: dict[str, Any] = {}
        # Positional args of pd.melt: (frame, id_vars, value_vars, var_name, value_name)
        # For df.melt(): (id_vars, value_vars, var_name, value_name)
        positional_offset = 1 if node.args and not isinstance(node.args[0], ast.Constant) else 0
        positional_names = ["id_vars", "value_vars", "var_name", "value_name"]
        for i, name in enumerate(positional_names):
            if positional_offset + i < len(node.args):
                arg = node.args[positional_offset + i]
                if isinstance(arg, (ast.List, ast.Tuple)):
                    params[name] = self._get_list_value(arg)
                elif isinstance(arg, ast.Constant):
                    params[name] = arg.value

        for kw in node.keywords:
            if kw.arg in ("id_vars", "value_vars"):
                params[kw.arg] = self._get_list_value(kw.value)
            elif kw.arg in ("var_name", "value_name") and isinstance(kw.value, ast.Constant):
                params[kw.arg] = kw.value.value

        # Columns to fold = value_vars (the "wide" columns being unpivoted)
        columns_to_fold = params.get("value_vars") or []

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.MELT,
                source_dataframe=df,
                target_dataframe=target,
                columns=columns_to_fold,
                parameters=params,
                source_line=self.current_line,
                suggested_recipe="prepare",
                suggested_processor="FoldMultipleColumns",
                notes=["df.melt() -> PREPARE recipe with FOLD_MULTIPLE_COLUMNS"],
            )
        )

    def _handle_rolling(self, df: str, node: ast.Call, target: str) -> None:
        """Handle rolling() calls."""
        window = None
        if node.args and isinstance(node.args[0], ast.Constant):
            window = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"window": window},
                source_line=self.current_line,
                suggested_recipe="window",
            )
        )

    def _handle_str_accessor(self, df: str, node: ast.Call, target: str) -> None:
        """Handle .str accessor methods."""
        # This handles df['col'].str.method()
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.STRING_TRANSFORM,
                source_dataframe=df,
                target_dataframe=target,
                parameters={},
                source_line=self.current_line,
                suggested_processor="StringTransformer",
            )
        )

    def _handle_str_method_call(
        self, df: str, column: Optional[str], method: str, node: ast.Call, target: str
    ) -> None:
        """Handle .str.method() calls with proper column and method detection (H1)."""
        col = column or "unknown"

        # Extract positional args as constants
        args = []
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                args.append(arg.value)

        # Map string methods to processor types and parameters
        mode_enum = PandasMapper.STRING_MAPPINGS.get(method)
        if mode_enum:
            # Simple string transformations: upper, lower, strip, etc.
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.STRING_TRANSFORM,
                    source_dataframe=df,
                    target_dataframe=target,
                    columns=[col],
                    parameters={"mode": mode_enum.value, "column": col},
                    source_line=self.current_line,
                    suggested_processor="StringTransformer",
                )
            )
        elif method == "replace" and len(args) >= 2:
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.STRING_TRANSFORM,
                    source_dataframe=df,
                    target_dataframe=target,
                    columns=[col],
                    parameters={"column": col, "find": str(args[0]), "replace": str(args[1])},
                    source_line=self.current_line,
                    suggested_processor="FindReplace",
                )
            )
        elif method == "extract" and args:
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.STRING_TRANSFORM,
                    source_dataframe=df,
                    target_dataframe=target,
                    columns=[col],
                    parameters={"column": col, "pattern": str(args[0])},
                    source_line=self.current_line,
                    suggested_processor="RegexpExtractor",
                )
            )
        elif method == "split":
            separator = str(args[0]) if args else ","
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.STRING_TRANSFORM,
                    source_dataframe=df,
                    target_dataframe=target,
                    columns=[col],
                    parameters={"column": col, "separator": separator},
                    source_line=self.current_line,
                    suggested_processor="SplitColumn",
                )
            )
        elif method == "contains" and args:
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.FILTER,
                    source_dataframe=df,
                    target_dataframe=target,
                    columns=[col],
                    parameters={"column": col, "pattern": str(args[0]), "matchMode": "REGEX"},
                    source_line=self.current_line,
                    suggested_processor="FlagOnValue",
                )
            )
        else:
            # Fallback for unrecognized string methods
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.STRING_TRANSFORM,
                    source_dataframe=df,
                    target_dataframe=target,
                    columns=[col],
                    parameters={"method": method, "column": col},
                    source_line=self.current_line,
                    suggested_processor="StringTransformer",
                )
            )

    def _handle_map(self, df: str, node: ast.Call, target: str) -> None:
        """Handle map() calls for value translation."""
        mapping = {}
        if node.args and isinstance(node.args[0], ast.Dict):
            mapping = self._get_dict_value(node.args[0])

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"operation": "translate_values", "mapping": mapping},
                source_line=self.current_line,
                suggested_processor="TranslateValues",
                notes=["df.map(dict) -> TranslateValues processor"],
            )
        )

    def _handle_where(self, df: str, node: ast.Call, target: str) -> None:
        """Handle where() calls for conditional value assignment."""
        condition = None
        other_val = None
        if node.args:
            condition = self._get_name(node.args[0])
        if len(node.args) > 1:
            other_val = self._get_arg_name(node, 1)
        for kw in node.keywords:
            if kw.arg == "other" and isinstance(kw.value, ast.Constant):
                other_val = str(kw.value.value)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={
                    "operation": "if_then_else",
                    "condition": condition,
                    "other": other_val,
                },
                source_line=self.current_line,
                suggested_processor="IfThenElse",
                notes=["df.where() -> IfThenElse processor"],
            )
        )

    def _handle_mask(self, df: str, node: ast.Call, target: str) -> None:
        """Handle mask() calls (inverse of where)."""
        condition = None
        other_val = None
        if node.args:
            condition = self._get_name(node.args[0])
        if len(node.args) > 1:
            other_val = self._get_arg_name(node, 1)
        for kw in node.keywords:
            if kw.arg == "other" and isinstance(kw.value, ast.Constant):
                other_val = str(kw.value.value)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={
                    "operation": "if_then_else",
                    "condition": condition,
                    "other": other_val,
                    "invert": True,
                },
                source_line=self.current_line,
                suggested_processor="IfThenElse",
                notes=["df.mask() -> IfThenElse processor (inverted condition)"],
            )
        )

    def _handle_replace(self, df: str, node: ast.Call, target: str) -> None:
        """Handle replace() calls for value translation."""
        mapping = {}
        if node.args and isinstance(node.args[0], ast.Dict):
            mapping = self._get_dict_value(node.args[0])

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"operation": "translate_values", "mapping": mapping},
                source_line=self.current_line,
                suggested_processor="TranslateValues",
                notes=["df.replace(dict) -> TranslateValues processor"],
            )
        )

    def _handle_explode(self, df: str, node: ast.Call, target: str) -> None:
        """Handle explode() calls for expanding list-like columns."""
        column = None
        if node.args and isinstance(node.args[0], ast.Constant):
            column = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"operation": "unfold", "column": column},
                source_line=self.current_line,
                suggested_processor="Unfold",
                notes=["df.explode() -> Unfold processor"],
            )
        )

    def _handle_combine_first(self, df: str, node: ast.Call, target: str) -> None:
        """Handle combine_first() calls for coalescing values."""
        other = None
        if node.args:
            other = self._get_name(node.args[0])

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"operation": "coalesce", "other": other},
                source_line=self.current_line,
                suggested_processor="Coalesce",
                notes=["df.combine_first() -> Coalesce processor"],
            )
        )

    def _handle_cumsum(self, df: str, node: ast.Call, target: str) -> None:
        """Handle cumsum() calls -> Window recipe with RUNNING_SUM."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"window_function": "RUNNING_SUM"},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["df.cumsum() -> Window recipe with RUNNING_SUM"],
            )
        )

    def _handle_cummin(self, df: str, node: ast.Call, target: str) -> None:
        """Handle cummin() calls -> Window recipe with RUNNING_MIN."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"window_function": "RUNNING_MIN"},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["df.cummin() -> Window recipe with RUNNING_MIN"],
            )
        )

    def _handle_cummax(self, df: str, node: ast.Call, target: str) -> None:
        """Handle cummax() calls -> Window recipe with RUNNING_MAX."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"window_function": "RUNNING_MAX"},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["df.cummax() -> Window recipe with RUNNING_MAX"],
            )
        )

    def _handle_cumprod(self, df: str, node: ast.Call, target: str) -> None:
        """Handle cumprod() calls -> Window recipe with RUNNING_PRODUCT."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"window_function": "RUNNING_PRODUCT"},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["df.cumprod() -> Window recipe with RUNNING_PRODUCT"],
            )
        )

    def _handle_diff(self, df: str, node: ast.Call, target: str) -> None:
        """Handle diff() calls -> Window recipe with LAG_DIFF."""
        periods = 1
        if node.args and isinstance(node.args[0], ast.Constant):
            periods = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"window_function": "LAG_DIFF", "periods": periods},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["df.diff() -> Window recipe with LAG_DIFF"],
            )
        )

    def _handle_shift(self, df: str, node: ast.Call, target: str) -> None:
        """Handle shift() calls -> Window recipe with LAG function."""
        periods = 1
        if node.args and isinstance(node.args[0], ast.Constant):
            periods = node.args[0].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"window_function": "LAG", "periods": periods},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["df.shift() -> Window recipe with LAG function"],
            )
        )

    def _handle_rank(self, df: str, node: ast.Call, target: str) -> None:
        """Handle rank() calls -> Window recipe with RANK function."""
        method = "average"
        ascending = True
        for kw in node.keywords:
            if kw.arg == "method" and isinstance(kw.value, ast.Constant):
                method = kw.value.value
            elif kw.arg == "ascending" and isinstance(kw.value, ast.Constant):
                ascending = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=df,
                target_dataframe=target,
                parameters={
                    "window_function": "RANK",
                    "method": method,
                    "ascending": ascending,
                },
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["df.rank() -> Window recipe with RANK function"],
            )
        )

    def _handle_nunique(self, df: str, node: ast.Call, target: str) -> None:
        """Handle nunique() calls -> Grouping recipe with COUNTD (DSS canonical name)."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.GROUPBY,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"aggregation": PandasMapper.AGG_MAPPINGS.get("nunique", "COUNTD")},
                source_line=self.current_line,
                suggested_recipe="grouping",
                notes=["df.nunique() -> Grouping recipe with COUNTD"],
            )
        )

    def _handle_interpolate(self, df: str, node: ast.Call, target: str) -> None:
        """Handle interpolate() calls -> FillEmptyWithPreviousNext (LINEAR mode)."""
        method = "linear"
        for kw in node.keywords:
            if kw.arg == "method" and isinstance(kw.value, ast.Constant):
                method = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"method": method, "direction": "LINEAR"},
                source_line=self.current_line,
                suggested_processor="FillEmptyWithPreviousNext",
                notes=[f"df.interpolate(method={method}) -> FillEmptyWithPreviousNext"],
            )
        )

    def _handle_describe(self, df: str, node: ast.Call, target: str) -> None:
        """Handle describe() calls -> GENERATE_STATISTICS recipe."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.STATISTICS,
                source_dataframe=df,
                # describe()/info() are profiling reports — do NOT carry over
                # `target` because callers often write `df.describe()` for
                # logging without rebinding `df`. Treating it as an
                # in-place mutation of `df` would break downstream chains.
                target_dataframe=target if target and target != df else None,
                parameters={"method": "describe"},
                source_line=self.current_line,
                suggested_recipe="generate_statistics",
                notes=["df.describe() -> GENERATE_STATISTICS recipe"],
            )
        )

    def _handle_info(self, df: str, node: ast.Call, target: str) -> None:
        """Handle info() calls -> GENERATE_STATISTICS recipe."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.STATISTICS,
                source_dataframe=df,
                target_dataframe=target if target and target != df else None,
                parameters={"method": "info"},
                source_line=self.current_line,
                suggested_recipe="generate_statistics",
                notes=["df.info() -> GENERATE_STATISTICS recipe"],
            )
        )

    def _handle_filter(self, node: ast.Subscript, target: str) -> None:
        """Handle filtering/selection operations like df[condition] or df[['col1','col2']]."""
        df_name = self._get_name(node.value)
        slice_node = node.slice

        # H3: Detect column selection df[['col1', 'col2']] vs row filtering df[condition]
        if isinstance(slice_node, ast.List):
            # Check if all elements are string constants -> column selection
            all_string_constants = all(
                isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                for elt in slice_node.elts
            )
            if all_string_constants:
                columns = [elt.value for elt in slice_node.elts]
                self.transformations.append(
                    Transformation(
                        transformation_type=TransformationType.COLUMN_SELECT,
                        source_dataframe=df_name,
                        target_dataframe=target,
                        columns=columns,
                        parameters={"columns": columns},
                        source_line=self.current_line,
                        suggested_processor="ColumnsSelector",
                    )
                )
                return

        # Row filtering (boolean condition).
        # Try to translate the condition to a GREL formula. Compound predicates
        # (`(df['x'] > 5) & (df['y'] < 10)`) and pandas-Series boolean ops can't
        # be expressed by a single FilterOnValue / FilterOnNumericRange step —
        # they need FilterOnFormula. The translator returns None when the
        # expression isn't statically translatable, and we fall back to the
        # legacy Python-text condition (still useful as documentation in the
        # generated recipe even if DSS itself ignores it).
        condition = ast.unparse(node.slice) if hasattr(ast, "unparse") else "condition"
        grel = _translate_to_grel(slice_node, df_name)
        is_compound = _is_compound_predicate(slice_node)

        params: dict[str, Any] = {"condition": condition}
        if grel is not None:
            params["formula"] = grel
        suggested_processor = (
            "FilterOnFormula" if is_compound and grel is not None else None
        )
        trans = Transformation.filter_rows(df_name, target, condition, self.current_line)
        # Augment the filter_rows-built Transformation with our compound-aware
        # metadata. The original `condition` parameter stays for any caller
        # that reads it.
        trans.parameters.update(params)
        if suggested_processor is not None:
            trans.suggested_processor = suggested_processor
            if grel is not None:
                trans.notes = list(trans.notes or []) + [
                    f"Compound predicate -> FilterOnFormula with GREL: {grel}"
                ]
        self.transformations.append(trans)

    def _handle_concat(self, node: ast.Call, target: str) -> None:
        """Handle pd.concat() calls."""
        dataframes = []
        if node.args and isinstance(node.args[0], ast.List):
            for elt in node.args[0].elts:
                dataframes.append(self._get_name(elt))

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.CONCAT,
                target_dataframe=target,
                parameters={"dataframes": dataframes},
                source_line=self.current_line,
                suggested_recipe="stack",
            )
        )

    def _handle_pd_binner(self, method_name: str, node: ast.Call, target: str) -> None:
        """Handle pd.cut() and pd.qcut() -> Binner processor."""
        # First positional arg is the column/series being binned
        source_col = ""
        source_df = "df"
        if node.args:
            arg0 = node.args[0]
            # Could be df['col'] (Subscript) or just a name
            if isinstance(arg0, ast.Subscript):
                source_df = self._get_name(arg0.value)
                if isinstance(arg0.slice, ast.Constant):
                    source_col = arg0.slice.value
            else:
                source_df = self._get_name(arg0)

        # bins/q is positional[1] or kwarg
        bins: Any = None
        if len(node.args) > 1:
            arg1 = node.args[1]
            if isinstance(arg1, ast.Constant):
                bins = arg1.value
            elif isinstance(arg1, (ast.List, ast.Tuple)):
                bins = self._get_list_value(arg1)
        for kw in node.keywords:
            if kw.arg in ("bins", "q") and isinstance(kw.value, ast.Constant):
                bins = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=source_df,
                target_dataframe=target,
                columns=[source_col] if source_col else [],
                parameters={
                    "column": source_col,
                    "output_column": target,
                    "bins": bins,
                    "method": method_name,
                },
                source_line=self.current_line,
                suggested_processor="Binner",
                notes=[f"pd.{method_name}() -> Binner processor"],
            )
        )

    def _handle_pd_get_dummies(self, node: ast.Call, target: str) -> None:
        """Handle pd.get_dummies() -> CATEGORICAL_ENCODER (one-hot) processor."""
        source_df = "df"
        source_cols: list[str] = []
        if node.args:
            arg0 = node.args[0]
            if isinstance(arg0, ast.Subscript):
                source_df = self._get_name(arg0.value)
                if isinstance(arg0.slice, ast.Constant):
                    source_cols = [arg0.slice.value]
            else:
                source_df = self._get_name(arg0)

        # `columns=` kwarg overrides
        for kw in node.keywords:
            if kw.arg == "columns":
                source_cols = self._get_list_value(kw.value)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=source_df,
                target_dataframe=target,
                columns=source_cols,
                parameters={
                    "columns": source_cols,
                    "encoding": "one_hot",
                },
                source_line=self.current_line,
                suggested_processor="CategoricalEncoder",
                notes=["pd.get_dummies() -> CATEGORICAL_ENCODER (one-hot)"],
            )
        )

    def _handle_binop(self, node: ast.BinOp, target: str) -> None:
        """Handle binary operations like df['a'] + df['b']."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                target_dataframe=target,
                parameters={"operation": "binop"},
                source_line=self.current_line,
                suggested_processor="CreateColumnWithGREL",
            )
        )

    def _handle_expression(self, node: ast.Expr) -> None:
        """Handle expression statements."""
        if isinstance(node.value, ast.Call):
            # Could be df.to_csv() or similar
            func = node.value.func
            if isinstance(func, ast.Attribute):
                method = func.attr
                if method in ("to_csv", "to_excel", "to_parquet"):
                    df_name = self._get_name(func.value)
                    filepath = "output"
                    if node.value.args:
                        arg = node.value.args[0]
                        if isinstance(arg, ast.Constant):
                            filepath = str(arg.value)

                    self.transformations.append(
                        Transformation(
                            transformation_type=TransformationType.WRITE_DATA,
                            source_dataframe=df_name,
                            parameters={"filepath": filepath},
                            source_line=self.current_line,
                        )
                    )
                # Profiling/statistics expressions like `df.describe()` /
                # `df.info()` are commonly written as bare statements (not
                # assigned to a variable). Route them through the standard
                # method-handler dispatch so they emit a STATISTICS
                # transformation -> GENERATE_STATISTICS recipe.
                elif method in ("describe", "info"):
                    df_name = self._get_name(func.value)
                    handler = self._method_handlers.get(method)
                    if handler:
                        handler(df_name, node.value, df_name)

    def _handle_if(self, node: ast.If) -> None:
        """Handle if statements."""
        # If statements that assign different DataFrames could become Split recipes
        for stmt in node.body:
            self._visit_statement(stmt)
        for stmt in node.orelse:
            self._visit_statement(stmt)

    # Helper methods

    def _get_name(self, node: ast.expr) -> str:
        """Extract the name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        return ""

    def _get_subscript_info(self, node: ast.Subscript) -> str:
        """Get info from a subscript like df['col']."""
        base = self._get_name(node.value)
        if isinstance(node.slice, ast.Constant):
            return f"{base}[{node.slice.value!r}]"
        return base

    def _get_list_value(self, node: ast.expr) -> list[str]:
        """Extract a list value from an AST node."""
        if isinstance(node, ast.List):
            result = []
            for elt in node.elts:
                if isinstance(elt, ast.Constant):
                    result.append(str(elt.value))
                elif isinstance(elt, ast.Name):
                    result.append(elt.id)
            return result
        elif isinstance(node, ast.Constant):
            return [str(node.value)]
        elif isinstance(node, ast.Name):
            return [node.id]
        return []

    def _get_dict_value(self, node: ast.expr) -> dict[str, Any]:
        """Extract a dict value from an AST node.

        Handles three value shapes commonly produced by pandas .agg():
        - scalar: ``{"col": "sum"}`` -> ``{"col": "sum"}``
        - list of functions: ``{"col": ["sum", "mean"]}`` -> ``{"col": ["sum","mean"]}``
        - tuple of functions: ``{"col": ("sum", "mean")}`` -> same

        Lists/tuples are preserved so downstream consumers can expand them
        into multiple aggregations on the same column.
        """
        if isinstance(node, ast.Dict):
            result: dict[str, Any] = {}
            for k, v in zip(node.keys, node.values):
                if not isinstance(k, ast.Constant):
                    continue
                key = str(k.value)
                if isinstance(v, ast.Constant):
                    result[key] = str(v.value)
                elif isinstance(v, (ast.List, ast.Tuple)):
                    funcs = []
                    for elt in v.elts:
                        if isinstance(elt, ast.Constant):
                            funcs.append(str(elt.value))
                    if funcs:
                        result[key] = funcs
            return result
        return {}

    # ========== scikit-learn handlers ==========

    def _handle_train_test_split(self, node: ast.Call, target: str) -> None:
        """Handle train_test_split() calls."""
        test_size = 0.25
        random_state = None

        for kw in node.keywords:
            if kw.arg == "test_size" and isinstance(kw.value, ast.Constant):
                test_size = kw.value.value
            elif kw.arg == "random_state" and isinstance(kw.value, ast.Constant):
                random_state = kw.value.value

        # Get input data
        input_data = []
        for arg in node.args:
            input_data.append(self._get_name(arg))

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FILTER,
                target_dataframe=target,
                parameters={
                    "operation": "train_test_split",
                    "test_size": test_size,
                    "random_state": random_state,
                    "inputs": input_data,
                },
                source_line=self.current_line,
                suggested_recipe="split",
                notes=["sklearn train_test_split -> Dataiku Split recipe"],
            )
        )

    def _handle_sklearn_scaler(self, scaler_type: str, node: ast.Call, target: str) -> None:
        """Handle sklearn scaler instantiation (StandardScaler, MinMaxScaler, etc.)."""
        # Map sklearn scalers to Dataiku processors
        scaler_map = {
            "StandardScaler": "STANDARD_SCALER",
            "MinMaxScaler": "MIN_MAX_SCALER",
            "RobustScaler": "ROBUST_SCALER",
            "MaxAbsScaler": "NORMALIZER",
            "Normalizer": "NORMALIZER",
        }

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT_TRANSFORM,
                target_dataframe=target,
                parameters={
                    "scaler_type": scaler_type,
                    "processor": scaler_map.get(scaler_type, "NORMALIZER"),
                },
                source_line=self.current_line,
                suggested_processor=scaler_map.get(scaler_type, "Normalizer"),
                notes=[f"sklearn {scaler_type} -> Dataiku {scaler_map.get(scaler_type)} processor"],
            )
        )

    def _handle_sklearn_encoder(self, encoder_type: str, node: ast.Call, target: str) -> None:
        """Handle sklearn encoder instantiation (LabelEncoder, OneHotEncoder, etc.)."""
        encoder_map = {
            "LabelEncoder": "LABEL_ENCODER",
            "OneHotEncoder": "ONE_HOT_ENCODER",
            "OrdinalEncoder": "ORDINAL_ENCODER",
            "LabelBinarizer": "CATEGORICAL_ENCODER",
        }

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT_TRANSFORM,
                target_dataframe=target,
                parameters={
                    "encoder_type": encoder_type,
                    "processor": encoder_map.get(encoder_type, "CATEGORICAL_ENCODER"),
                },
                source_line=self.current_line,
                suggested_processor=encoder_map.get(encoder_type, "CategoricalEncoder"),
                notes=[f"sklearn {encoder_type} -> Dataiku {encoder_map.get(encoder_type)} processor"],
            )
        )

    def _handle_sklearn_imputer(self, imputer_type: str, node: ast.Call, target: str) -> None:
        """Handle sklearn imputer instantiation (SimpleImputer, KNNImputer, etc.)."""
        strategy = "mean"
        for kw in node.keywords:
            if kw.arg == "strategy" and isinstance(kw.value, ast.Constant):
                strategy = kw.value.value

        imputer_map = {
            "SimpleImputer": "FILL_EMPTY_WITH_COMPUTED_VALUE",
            "KNNImputer": "IMPUTE_WITH_ML",
            "IterativeImputer": "IMPUTE_WITH_ML",
        }

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT_TRANSFORM,
                target_dataframe=target,
                parameters={
                    "imputer_type": imputer_type,
                    "strategy": strategy,
                    "processor": imputer_map.get(imputer_type, "FILL_EMPTY_WITH_COMPUTED_VALUE"),
                },
                source_line=self.current_line,
                suggested_processor=imputer_map.get(imputer_type, "FillEmptyWithComputedValue"),
                notes=[f"sklearn {imputer_type}(strategy={strategy}) -> Dataiku imputation"],
            )
        )

    def _handle_sklearn_pipeline(self, node: ast.Call, target: str) -> None:
        """Handle sklearn Pipeline instantiation."""
        steps = []
        for kw in node.keywords:
            if kw.arg == "steps" and isinstance(kw.value, ast.List):
                for step in kw.value.elts:
                    if isinstance(step, ast.Tuple) and len(step.elts) >= 2:
                        step_name = step.elts[0]
                        if isinstance(step_name, ast.Constant):
                            steps.append(step_name.value)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT_TRANSFORM,
                target_dataframe=target,
                parameters={
                    "pipeline_steps": steps,
                },
                source_line=self.current_line,
                suggested_recipe="prepare",
                notes=["sklearn Pipeline -> Dataiku Prepare recipe with multiple steps"],
            )
        )

    def _handle_sklearn_feature_selector(self, selector_type: str, node: ast.Call, target: str) -> None:
        """Handle sklearn feature selection (PCA, SelectKBest, etc.)."""
        n_components = None
        k = None

        for kw in node.keywords:
            if kw.arg == "n_components" and isinstance(kw.value, ast.Constant):
                n_components = kw.value.value
            elif kw.arg == "k" and isinstance(kw.value, ast.Constant):
                k = kw.value.value

        selector_map = {
            "PCA": "dimensionality_reduction",
            "TruncatedSVD": "dimensionality_reduction",
            "SelectKBest": "feature_selection",
            "SelectFromModel": "feature_selection",
        }

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT_TRANSFORM,
                target_dataframe=target,
                parameters={
                    "selector_type": selector_type,
                    "n_components": n_components,
                    "k": k,
                    "operation": selector_map.get(selector_type, "feature_selection"),
                },
                source_line=self.current_line,
                suggested_recipe="python",
                notes=[f"sklearn {selector_type} -> Dataiku Python recipe (ML feature engineering)"],
            )
        )

    def _handle_sklearn_model(self, model_type: str, node: ast.Call, target: str) -> None:
        """Handle sklearn classifier/regressor instantiation."""
        is_classifier = "Classifier" in model_type or model_type in (
            "LogisticRegression", "SVC",
        )
        recipe_type = "prediction_scoring" if is_classifier else "prediction_scoring"

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT,
                target_dataframe=target,
                parameters={
                    "model_type": model_type,
                    "is_classifier": is_classifier,
                    "operation": "model_instantiation",
                },
                source_line=self.current_line,
                suggested_recipe=recipe_type,
                notes=[f"sklearn {model_type} -> Dataiku Prediction Scoring recipe"],
            )
        )

    def _handle_sklearn_clustering(self, model_type: str, node: ast.Call, target: str) -> None:
        """Handle sklearn clustering model instantiation."""
        n_clusters = None
        for kw in node.keywords:
            if kw.arg == "n_clusters" and isinstance(kw.value, ast.Constant):
                n_clusters = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT,
                target_dataframe=target,
                parameters={
                    "model_type": model_type,
                    "n_clusters": n_clusters,
                    "operation": "clustering",
                },
                source_line=self.current_line,
                suggested_recipe="clustering_scoring",
                notes=[f"sklearn {model_type} -> Dataiku Clustering Scoring recipe"],
            )
        )

    def _handle_cross_val_score(self, node: ast.Call, target: str) -> None:
        """Handle cross_val_score() calls."""
        cv = None
        scoring = None
        for kw in node.keywords:
            if kw.arg == "cv" and isinstance(kw.value, ast.Constant):
                cv = kw.value.value
            elif kw.arg == "scoring" and isinstance(kw.value, ast.Constant):
                scoring = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.TRANSFORM,
                target_dataframe=target,
                parameters={
                    "operation": "cross_validation",
                    "cv": cv,
                    "scoring": scoring,
                },
                source_line=self.current_line,
                suggested_recipe="evaluation",
                notes=["sklearn cross_val_score -> Dataiku Evaluation recipe"],
            )
        )

    def _handle_grid_search(self, node: ast.Call, target: str) -> None:
        """Handle GridSearchCV instantiation."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT,
                target_dataframe=target,
                parameters={
                    "operation": "hyperparameter_tuning",
                },
                source_line=self.current_line,
                suggested_recipe="python",
                notes=["sklearn GridSearchCV -> Dataiku Python recipe (hyperparameter tuning)"],
            )
        )

    def _handle_column_transformer(self, node: ast.Call, target: str) -> None:
        """Handle ColumnTransformer instantiation."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FIT_TRANSFORM,
                target_dataframe=target,
                parameters={
                    "operation": "column_transformer",
                },
                source_line=self.current_line,
                suggested_recipe="prepare",
                notes=["sklearn ColumnTransformer -> Dataiku Prepare recipe"],
            )
        )

    # NumPy handlers

    def _handle_numpy_function(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle NumPy function calls like np.where(), np.clip(), etc."""
        # Numeric transformations
        if func_name in ("log", "log10", "log2", "log1p"):
            self._handle_numpy_log(func_name, node, target)
        elif func_name in ("exp", "expm1"):
            self._handle_numpy_exp(func_name, node, target)
        elif func_name in ("sqrt", "cbrt", "square", "power"):
            self._handle_numpy_power(func_name, node, target)
        elif func_name == "abs":
            self._handle_numpy_abs(node, target)
        elif func_name in ("round", "around", "rint", "floor", "ceil", "trunc"):
            self._handle_numpy_round(func_name, node, target)
        elif func_name == "clip":
            self._handle_numpy_clip(node, target)
        # Conditional operations
        elif func_name == "where":
            self._handle_numpy_where(node, target)
        elif func_name == "select":
            self._handle_numpy_select(node, target)
        elif func_name in ("isnan", "isinf", "isfinite"):
            self._handle_numpy_check(func_name, node, target)
        elif func_name in ("nan_to_num", "nanmean", "nansum", "nanstd"):
            self._handle_numpy_nan_func(func_name, node, target)
        # Binning
        elif func_name == "digitize":
            self._handle_numpy_digitize(node, target)
        # Window/cumulative operations
        elif func_name in ("cumsum", "cumprod"):
            self._handle_numpy_cumulative(func_name, node, target)
        elif func_name == "diff":
            self._handle_numpy_diff(node, target)
        # Array operations
        elif func_name in ("concatenate", "vstack", "hstack", "stack"):
            self._handle_numpy_concat(func_name, node, target)
        elif func_name in ("sort", "argsort"):
            self._handle_numpy_sort(func_name, node, target)
        elif func_name == "unique":
            self._handle_numpy_unique(node, target)
        # Aggregations
        elif func_name in ("sum", "mean", "std", "var", "min", "max", "median"):
            self._handle_numpy_agg(func_name, node, target)
        elif func_name in ("percentile", "quantile"):
            self._handle_numpy_percentile(func_name, node, target)
        # Reshaping
        elif func_name in ("reshape", "flatten", "ravel", "transpose"):
            self._handle_numpy_reshape(func_name, node, target)
        # Creation/initialization
        elif func_name in ("zeros", "ones", "full", "empty", "arange", "linspace"):
            self._handle_numpy_create(func_name, node, target)
        else:
            # Unknown numpy function
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.CUSTOM_FUNCTION,
                    target_dataframe=target,
                    parameters={"numpy_function": func_name},
                    source_line=self.current_line,
                    requires_python_recipe=True,
                    notes=[f"NumPy function np.{func_name}() requires Python recipe"],
                )
            )

    def _handle_numpy_log(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.log, np.log10, np.log2, np.log1p."""
        input_arr = self._get_arg_name(node, 0)
        log_type_map = {
            "log": "NATURAL_LOG",
            "log10": "LOG10",
            "log2": "LOG2",
            "log1p": "LOG1P",
        }
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": log_type_map.get(func_name, "NATURAL_LOG")},
                source_line=self.current_line,
                suggested_processor="NumericalTransformer",
                notes=[f"np.{func_name}() -> Prepare recipe with formula"],
            )
        )

    def _handle_numpy_exp(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.exp, np.expm1."""
        input_arr = self._get_arg_name(node, 0)
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": "EXP" if func_name == "exp" else "EXPM1"},
                source_line=self.current_line,
                suggested_processor="NumericalTransformer",
                notes=[f"np.{func_name}() -> Prepare recipe with formula"],
            )
        )

    def _handle_numpy_power(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.sqrt, np.cbrt, np.square, np.power."""
        input_arr = self._get_arg_name(node, 0)
        power_val = None
        if func_name == "power" and len(node.args) > 1:
            if isinstance(node.args[1], ast.Constant):
                power_val = node.args[1].value

        op_map = {
            "sqrt": "SQRT",
            "cbrt": "CBRT",
            "square": "SQUARE",
            "power": "POWER",
        }
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": op_map.get(func_name, "POWER"), "exponent": power_val},
                source_line=self.current_line,
                suggested_processor="NumericalTransformer",
                notes=[f"np.{func_name}() -> Prepare recipe with formula"],
            )
        )

    def _handle_numpy_abs(self, node: ast.Call, target: str) -> None:
        """Handle np.abs."""
        input_arr = self._get_arg_name(node, 0)
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": "ABS"},
                source_line=self.current_line,
                # np.abs has no native DSS Prepare processor; CreateColumnWithGREL
                # with an abs() expression is the canonical DSS workaround.
                suggested_processor="CreateColumnWithGREL",
                notes=["np.abs() -> Prepare recipe CreateColumnWithGREL with abs() expression"],
            )
        )

    def _handle_numpy_round(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.round, np.around, np.floor, np.ceil, np.trunc."""
        input_arr = self._get_arg_name(node, 0)
        decimals = 0
        for kw in node.keywords:
            if kw.arg == "decimals" and isinstance(kw.value, ast.Constant):
                decimals = kw.value.value
        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
            decimals = node.args[1].value

        round_map = {
            "round": "ROUND",
            "around": "ROUND",
            "rint": "ROUND",
            "floor": "FLOOR",
            "ceil": "CEIL",
            "trunc": "TRUNC",
        }
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": round_map.get(func_name, "ROUND"), "decimals": decimals},
                source_line=self.current_line,
                suggested_processor="RoundColumn",
                notes=[f"np.{func_name}() -> Prepare recipe RoundColumn processor"],
            )
        )

    def _handle_numpy_clip(self, node: ast.Call, target: str) -> None:
        """Handle np.clip(a, min, max)."""
        input_arr = self._get_arg_name(node, 0)
        min_val = None
        max_val = None

        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
            min_val = node.args[1].value
        if len(node.args) > 2 and isinstance(node.args[2], ast.Constant):
            max_val = node.args[2].value

        for kw in node.keywords:
            if kw.arg in ("a_min", "min") and isinstance(kw.value, ast.Constant):
                min_val = kw.value.value
            elif kw.arg in ("a_max", "max") and isinstance(kw.value, ast.Constant):
                max_val = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": "CLIP", "min": min_val, "max": max_val},
                source_line=self.current_line,
                suggested_processor="ClipColumn",
                notes=["np.clip() -> Prepare recipe ClipColumn processor"],
            )
        )

    def _handle_numpy_where(self, node: ast.Call, target: str) -> None:
        """Handle np.where(condition, x, y)."""
        condition = None
        if len(node.args) > 0:
            condition = self._get_name(node.args[0])

        x_val = self._get_arg_name(node, 1) if len(node.args) > 1 else None
        y_val = self._get_arg_name(node, 2) if len(node.args) > 2 else None

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                target_dataframe=target,
                parameters={"condition": condition, "if_true": x_val, "if_false": y_val},
                source_line=self.current_line,
                suggested_processor="CreateColumnWithGREL",
                notes=["np.where() -> Prepare recipe with if/else formula"],
            )
        )

    def _handle_numpy_select(self, node: ast.Call, target: str) -> None:
        """Handle np.select(conditions, choices, default)."""
        default_val = None
        for kw in node.keywords:
            if kw.arg == "default" and isinstance(kw.value, ast.Constant):
                default_val = str(kw.value.value)
        if len(node.args) > 2 and isinstance(node.args[2], ast.Constant):
            default_val = str(node.args[2].value)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                target_dataframe=target,
                parameters={"operation": "switch_case", "default": default_val},
                source_line=self.current_line,
                suggested_processor="SwitchCase",
                notes=["np.select() -> SwitchCase processor"],
            )
        )

    def _handle_numpy_digitize(self, node: ast.Call, target: str) -> None:
        """Handle np.digitize(x, bins)."""
        input_arr = self._get_arg_name(node, 0)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": "BINNER"},
                source_line=self.current_line,
                suggested_processor="Binner",
                notes=["np.digitize() -> Binner processor"],
            )
        )

    def _handle_numpy_cumulative(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.cumsum, np.cumprod."""
        input_arr = self._get_arg_name(node, 0)
        window_map = {
            "cumsum": "RUNNING_SUM",
            "cumprod": "RUNNING_PRODUCT",
        }
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"window_function": window_map.get(func_name, "RUNNING_SUM")},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=[f"np.{func_name}() -> Window recipe with {window_map.get(func_name)}"],
            )
        )

    def _handle_numpy_diff(self, node: ast.Call, target: str) -> None:
        """Handle np.diff."""
        input_arr = self._get_arg_name(node, 0)
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"window_function": "LAG_DIFF"},
                source_line=self.current_line,
                suggested_recipe="window",
                notes=["np.diff() -> Window recipe with LAG_DIFF"],
            )
        )

    def _handle_numpy_check(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.isnan, np.isinf, np.isfinite."""
        input_arr = self._get_arg_name(node, 0)
        check_map = {
            "isnan": "IS_NAN",
            "isinf": "IS_INF",
            "isfinite": "IS_FINITE",
        }
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"check_type": check_map.get(func_name, "IS_NAN")},
                source_line=self.current_line,
                suggested_processor="FlagOnValue",
                notes=[f"np.{func_name}() -> Prepare recipe FlagOnValue processor"],
            )
        )

    def _handle_numpy_nan_func(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.nan_to_num, np.nanmean, np.nansum, np.nanstd."""
        input_arr = self._get_arg_name(node, 0)

        if func_name == "nan_to_num":
            nan_val = 0.0
            for kw in node.keywords:
                if kw.arg == "nan" and isinstance(kw.value, ast.Constant):
                    nan_val = kw.value.value
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.FILL_NA,
                    source_dataframe=input_arr,
                    target_dataframe=target,
                    parameters={"value": nan_val},
                    source_line=self.current_line,
                    suggested_processor="FillEmptyWithValue",
                    notes=["np.nan_to_num() -> Prepare recipe FillEmptyWithValue"],
                )
            )
        else:
            # nanmean, nansum, nanstd
            agg_func = func_name.replace("nan", "").upper()
            self.transformations.append(
                Transformation(
                    transformation_type=TransformationType.GROUPBY,
                    source_dataframe=input_arr,
                    target_dataframe=target,
                    parameters={"aggregation": agg_func, "ignore_nan": True},
                    source_line=self.current_line,
                    suggested_recipe="grouping",
                    notes=[f"np.{func_name}() -> Grouping recipe with {agg_func}"],
                )
            )

    def _handle_numpy_concat(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.concatenate, np.vstack, np.hstack, np.stack."""
        arrays = []
        if node.args:
            if isinstance(node.args[0], (ast.List, ast.Tuple)):
                for elt in node.args[0].elts:
                    arrays.append(self._get_name(elt))
            else:
                arrays.append(self._get_name(node.args[0]))

        axis = 0
        for kw in node.keywords:
            if kw.arg == "axis" and isinstance(kw.value, ast.Constant):
                axis = kw.value.value

        concat_type = "VSTACK" if func_name in ("vstack", "stack") or axis == 0 else "HSTACK"

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.CONCAT,
                source_dataframe=arrays[0] if arrays else None,
                target_dataframe=target,
                parameters={"arrays": arrays, "axis": axis, "mode": concat_type},
                source_line=self.current_line,
                suggested_recipe="stack",
                notes=[f"np.{func_name}() -> Stack recipe"],
            )
        )

    def _handle_numpy_sort(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.sort, np.argsort."""
        input_arr = self._get_arg_name(node, 0)
        axis = -1
        for kw in node.keywords:
            if kw.arg == "axis" and isinstance(kw.value, ast.Constant):
                axis = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.SORT,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"axis": axis, "return_indices": func_name == "argsort"},
                source_line=self.current_line,
                suggested_recipe="sort",
                notes=[f"np.{func_name}() -> Sort recipe"],
            )
        )

    def _handle_numpy_unique(self, node: ast.Call, target: str) -> None:
        """Handle np.unique."""
        input_arr = self._get_arg_name(node, 0)
        return_counts = False
        for kw in node.keywords:
            if kw.arg == "return_counts" and isinstance(kw.value, ast.Constant):
                return_counts = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.DROP_DUPLICATES,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"return_counts": return_counts},
                source_line=self.current_line,
                suggested_recipe="distinct",
                notes=["np.unique() -> Distinct recipe"],
            )
        )

    def _handle_numpy_agg(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.sum, np.mean, np.std, np.var, np.min, np.max, np.median."""
        input_arr = self._get_arg_name(node, 0)
        axis = None
        for kw in node.keywords:
            if kw.arg == "axis" and isinstance(kw.value, ast.Constant):
                axis = kw.value.value

        agg_map = {
            "sum": "SUM",
            "mean": "AVG",
            "std": "STDDEV",
            "var": "VAR",
            "min": "MIN",
            "max": "MAX",
            "median": "MEDIAN",
        }
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.GROUPBY,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"aggregation": agg_map.get(func_name, func_name.upper()), "axis": axis},
                source_line=self.current_line,
                suggested_recipe="grouping",
                notes=[f"np.{func_name}() -> Grouping recipe with {agg_map.get(func_name, func_name.upper())}"],
            )
        )

    def _handle_numpy_percentile(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.percentile, np.quantile."""
        input_arr = self._get_arg_name(node, 0)
        q = None
        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
            q = node.args[1].value

        for kw in node.keywords:
            if kw.arg == "q" and isinstance(kw.value, ast.Constant):
                q = kw.value.value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.GROUPBY,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"aggregation": "PERCENTILE", "percentile": q},
                source_line=self.current_line,
                suggested_recipe="grouping",
                notes=[f"np.{func_name}() -> Grouping recipe with percentile"],
            )
        )

    def _handle_numpy_reshape(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.reshape, np.flatten, np.ravel, np.transpose."""
        input_arr = self._get_arg_name(node, 0)
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.CUSTOM_FUNCTION,
                source_dataframe=input_arr,
                target_dataframe=target,
                parameters={"operation": func_name.upper()},
                source_line=self.current_line,
                requires_python_recipe=True,
                notes=[f"np.{func_name}() requires Python recipe for array reshaping"],
            )
        )

    def _handle_numpy_create(self, func_name: str, node: ast.Call, target: str) -> None:
        """Handle np.zeros, np.ones, np.full, np.empty, np.arange, np.linspace."""
        shape = None
        if node.args and isinstance(node.args[0], (ast.Tuple, ast.List, ast.Constant)):
            if isinstance(node.args[0], ast.Constant):
                shape = node.args[0].value
            else:
                shape = [self._get_name(e) for e in node.args[0].elts]

        fill_value = None
        if func_name == "full" and len(node.args) > 1:
            if isinstance(node.args[1], ast.Constant):
                fill_value = node.args[1].value

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.CUSTOM_FUNCTION,
                target_dataframe=target,
                parameters={
                    "operation": f"CREATE_{func_name.upper()}",
                    "shape": shape,
                    "fill_value": fill_value,
                },
                source_line=self.current_line,
                requires_python_recipe=True,
                notes=[f"np.{func_name}() -> Python recipe for array creation"],
            )
        )

    def _get_arg_name(self, node: ast.Call, index: int) -> Optional[str]:
        """Get the name of a positional argument by index."""
        if len(node.args) > index:
            return self._get_name(node.args[index])
        return None

    def _handle_sklearn_method(
        self, obj_name: str, method_name: str, node: ast.Call, target: str
    ) -> None:
        """Handle sklearn fit/transform/predict method calls."""
        # Get input data
        input_data = []
        for arg in node.args:
            input_data.append(self._get_name(arg))

        method_map = {
            "fit": TransformationType.FIT,
            "transform": TransformationType.TRANSFORM,
            "fit_transform": TransformationType.FIT_TRANSFORM,
            "predict": TransformationType.PREDICT,
            "predict_proba": TransformationType.PREDICT,
        }

        recipe_map = {
            "fit": "python",
            "transform": "prepare",
            "fit_transform": "prepare",
            "predict": "prediction_scoring",
            "predict_proba": "prediction_scoring",
        }

        self.transformations.append(
            Transformation(
                transformation_type=method_map.get(method_name, TransformationType.TRANSFORM),
                source_dataframe=obj_name,
                target_dataframe=target,
                parameters={
                    "method": method_name,
                    "inputs": input_data,
                },
                source_line=self.current_line,
                suggested_recipe=recipe_map.get(method_name, "python"),
                notes=[f"sklearn {obj_name}.{method_name}()"],
            )
        )


# ---------------------------------------------------------------------------
# GREL translator for compound boolean predicates
# ---------------------------------------------------------------------------
#
# pandas boolean indexing uses bitwise operators (`&` / `|` / `~`) on Series.
# In Python AST these appear as ``ast.BinOp`` with ``ast.BitAnd`` / ``ast.BitOr``
# operators (or ``ast.UnaryOp`` with ``ast.Invert``) — NOT as ``ast.BoolOp``
# with ``ast.And`` / ``ast.Or``.
#
# DSS's GREL formula language uses ``&&`` for AND, ``||`` for OR, ``!`` for NOT,
# and ``val("col")`` for column references. Comparison operators (`>`, `<`, etc.)
# are the same.
#
# This translator handles the common predicate shapes — single comparison,
# compound bitwise AND/OR, negation, ``isin`` membership — and returns
# ``None`` for anything it can't translate so the caller can fall back to
# leaving the formula unset.

_COMPARE_OP_MAP = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
}


def _is_compound_predicate(node: ast.expr) -> bool:
    """True when the predicate combines clauses with ``&`` / ``|`` / ``~``.

    Used to decide whether to suggest ``FilterOnFormula`` over the
    simpler ``FilterOnValue`` / ``FilterOnNumericRange`` processors.
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.BitAnd, ast.BitOr)):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
        # ``~(...)`` may wrap a single comparison (handled by complementary
        # filter detection) or a compound — only call it compound when the
        # operand is itself compound or non-trivial.
        return _is_compound_predicate(node.operand)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        return True
    return False


def _column_ref(node: ast.expr, df_name: str) -> Optional[str]:
    """Translate ``df['col']`` or ``df.col`` into a GREL ``val("col")`` ref.

    Returns the column reference string, or None if the node isn't a
    recognized column accessor. The leading DataFrame name is dropped —
    GREL formulas operate on the current row, so column references are
    bare ``val("col")`` regardless of which Python variable the column
    came from.
    """
    # df['col']
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        if isinstance(node.slice.value, str):
            return f'val("{node.slice.value}")'
    # df.col attribute access (rare in idiomatic pandas, but supported)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        # Skip method-y attributes; only treat lowercase identifiers as columns.
        if node.attr.isidentifier():
            return f'val("{node.attr}")'
    return None


def _grel_constant(node: ast.Constant) -> str:
    """Render a Python constant as a GREL literal."""
    v = node.value
    if isinstance(v, str):
        # Escape embedded quotes
        escaped = v.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _translate_compare(node: ast.Compare, df_name: str) -> Optional[str]:
    """Translate ``ast.Compare`` (e.g. ``df['x'] > 5``) into GREL.

    Only handles single-operator comparisons (``a > b``, not chained
    ``a < b < c``) — chained comparisons are uncommon in pandas
    boolean indexing.
    """
    if len(node.ops) != 1 or len(node.comparators) != 1:
        return None
    op = node.ops[0]
    grel_op = _COMPARE_OP_MAP.get(type(op))
    if grel_op is None:
        # ``in`` / ``not in`` etc. — handle ``in [...]`` as a chained ``||``
        # for small lists, otherwise punt.
        if isinstance(op, ast.In) and isinstance(node.comparators[0], ast.List):
            left = _translate_grel_node(node.left, df_name)
            if left is None:
                return None
            elts = node.comparators[0].elts
            literals = []
            for e in elts:
                if isinstance(e, ast.Constant):
                    literals.append(_grel_constant(e))
                else:
                    return None
            if not literals:
                return None
            clauses = [f"({left} == {lit})" for lit in literals]
            return "(" + " || ".join(clauses) + ")"
        return None

    left = _translate_grel_node(node.left, df_name)
    right = _translate_grel_node(node.comparators[0], df_name)
    if left is None or right is None:
        return None
    return f"{left} {grel_op} {right}"


def _translate_grel_node(node: ast.expr, df_name: str) -> Optional[str]:
    """Recursive AST → GREL translator. Returns None on unsupported nodes."""
    # Column reference: df['col'] or df.col
    col = _column_ref(node, df_name)
    if col is not None:
        return col

    # Constant literal
    if isinstance(node, ast.Constant):
        return _grel_constant(node)

    # Comparison: df['x'] > 5
    if isinstance(node, ast.Compare):
        return _translate_compare(node, df_name)

    # Bitwise AND/OR (pandas ``&`` / ``|``)
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.BitAnd):
            left = _translate_grel_node(node.left, df_name)
            right = _translate_grel_node(node.right, df_name)
            if left is None or right is None:
                return None
            return f"({left}) && ({right})"
        if isinstance(node.op, ast.BitOr):
            left = _translate_grel_node(node.left, df_name)
            right = _translate_grel_node(node.right, df_name)
            if left is None or right is None:
                return None
            return f"({left}) || ({right})"

    # Logical AND/OR (rare in pandas — usually short-circuits at row-eval)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, (ast.And, ast.Or)):
            translated = [_translate_grel_node(v, df_name) for v in node.values]
            if any(t is None for t in translated):
                return None
            sep = " && " if isinstance(node.op, ast.And) else " || "
            return "(" + sep.join(translated) + ")"

    # Unary not / invert
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, (ast.Invert, ast.Not)):
            inner = _translate_grel_node(node.operand, df_name)
            if inner is None:
                return None
            return f"!({inner})"

    # Method calls: df['col'].isin([...]), df['col'].str.contains(...)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        method = node.func.attr
        # df['col'].isin([a, b, c]) -> (col == "a" || col == "b" || col == "c")
        if method == "isin" and node.args and isinstance(node.args[0], ast.List):
            target_ref = _translate_grel_node(node.func.value, df_name)
            if target_ref is None:
                return None
            elts = node.args[0].elts
            literals = []
            for e in elts:
                if isinstance(e, ast.Constant):
                    literals.append(_grel_constant(e))
                else:
                    return None
            if not literals:
                return None
            clauses = [f"({target_ref} == {lit})" for lit in literals]
            return "(" + " || ".join(clauses) + ")"

    return None


def _translate_to_grel(node: ast.expr, df_name: str) -> Optional[str]:
    """Public entrypoint: translate a pandas boolean indexing expression to GREL.

    Returns ``None`` for unsupported expression shapes so callers can
    fall back to leaving the formula unset.
    """
    return _translate_grel_node(node, df_name)
