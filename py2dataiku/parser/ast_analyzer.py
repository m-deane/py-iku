"""Python AST analysis for extracting data transformations."""

import ast
from typing import Any, Dict, List, Optional, Set, Tuple

from py2dataiku.models.transformation import Transformation, TransformationType


class CodeAnalyzer:
    """
    Analyze Python code and extract data transformation operations.

    Uses Python's AST module to parse code and identify patterns
    like pandas DataFrame operations, merges, groupby, etc.
    """

    def __init__(self):
        self.transformations: List[Transformation] = []
        self.dataframes: Dict[str, str] = {}  # variable -> source
        self.current_line: int = 0

    def analyze(self, code: str) -> List[Transformation]:
        """
        Extract all transformations from Python code.

        Args:
            code: Python source code string

        Returns:
            List of Transformation objects
        """
        self.transformations = []
        self.dataframes = {}

        try:
            tree = ast.parse(code)
            self._visit_module(tree)
        except SyntaxError as e:
            # Re-raise syntax errors so callers know about invalid input
            raise SyntaxError(
                f"Invalid Python syntax at line {e.lineno}: {e.msg}"
            ) from e

        return self.transformations

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
            else:
                # DataFrame method calls
                self._handle_dataframe_method(obj, method_name, node, target)

        elif isinstance(func, ast.Name):
            # Direct function call
            func_name = func.id
            if func_name == "pd":
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

    def _unwind_method_chain(self, node: ast.Call) -> List[Tuple[str, ast.Call]]:
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

        method_handlers = {
            "fillna": self._handle_fillna,
            "dropna": self._handle_dropna,
            "drop_duplicates": self._handle_drop_duplicates,
            "drop": self._handle_drop,
            "rename": self._handle_rename,
            "merge": self._handle_merge,
            "join": self._handle_join,
            "groupby": self._handle_groupby,
            "sort_values": self._handle_sort,
            "head": self._handle_head,
            "tail": self._handle_tail,
            "sample": self._handle_sample,
            "astype": self._handle_astype,
            "to_datetime": self._handle_to_datetime,
            "pivot": self._handle_pivot,
            "pivot_table": self._handle_pivot,
            "melt": self._handle_melt,
            "rolling": self._handle_rolling,
            "str": self._handle_str_accessor,
            "nlargest": self._handle_nlargest,
            "nsmallest": self._handle_nsmallest,
            "query": self._handle_query,
            "assign": self._handle_assign,
            "clip": self._handle_clip,
            "round": self._handle_round,
            "abs": self._handle_abs,
        }

        handler = method_handlers.get(method_name)
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
                transformation_type=TransformationType.HEAD,
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
                transformation_type=TransformationType.HEAD,
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
        """Handle assign() calls for creating new columns."""
        new_columns = []
        for kw in node.keywords:
            new_columns.append(kw.arg)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.COLUMN_CREATE,
                source_dataframe=df,
                target_dataframe=target,
                columns=new_columns,
                parameters={"columns": new_columns},
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
                suggested_processor="AbsColumn",
            )
        )

    def _handle_string_method(self, df: str, method: str, node: ast.Call, target: str) -> None:
        """Handle string methods like upper(), lower(), strip()."""
        mode_map = {
            "upper": "TO_UPPER",
            "lower": "TO_LOWER",
            "strip": "TRIM",
            "title": "TO_TITLE",
            "capitalize": "CAPITALIZE",
        }

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.STRING_TRANSFORM,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"mode": mode_map.get(method, method)},
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

    def _handle_dataframe_method(
        self, obj: ast.expr, method: str, node: ast.Call, target: str
    ) -> None:
        """Handle DataFrame method calls."""
        obj_name = self._get_name(obj)

        # Check for method chains
        if isinstance(obj, ast.Attribute):
            # This is part of a chain, recurse
            self._handle_dataframe_method(obj.value, obj.attr, node, target)

        method_handlers = {
            "fillna": self._handle_fillna,
            "dropna": self._handle_dropna,
            "drop_duplicates": self._handle_drop_duplicates,
            "drop": self._handle_drop,
            "rename": self._handle_rename,
            "merge": self._handle_merge,
            "join": self._handle_join,
            "groupby": self._handle_groupby,
            "sort_values": self._handle_sort,
            "head": self._handle_head,
            "tail": self._handle_tail,
            "sample": self._handle_sample,
            "astype": self._handle_astype,
            "to_datetime": self._handle_to_datetime,
            "pivot": self._handle_pivot,
            "melt": self._handle_melt,
            "rolling": self._handle_rolling,
            "str": self._handle_str_accessor,
        }

        handler = method_handlers.get(method)
        if handler:
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

    def _handle_fillna(self, df: str, node: ast.Call, target: str) -> None:
        """Handle fillna() calls."""
        value = None
        if node.args:
            val_node = node.args[0]
            if isinstance(val_node, ast.Constant):
                value = val_node.value

        # Check for column-specific fillna in subscript context
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"value": value},
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

    def _handle_astype(self, df: str, node: ast.Call, target: str) -> None:
        """Handle astype() calls."""
        dtype = None
        if node.args and isinstance(node.args[0], ast.Name):
            dtype = node.args[0].id
        elif node.args and isinstance(node.args[0], ast.Constant):
            dtype = str(node.args[0].value)

        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.TYPE_CAST,
                source_dataframe=df,
                target_dataframe=target,
                parameters={"dtype": dtype},
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
        """Handle melt() calls."""
        self.transformations.append(
            Transformation(
                transformation_type=TransformationType.MELT,
                source_dataframe=df,
                target_dataframe=target,
                parameters={},
                source_line=self.current_line,
                suggested_recipe="pivot",
                notes=["Melt is unpivot operation"],
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

    def _handle_filter(self, node: ast.Subscript, target: str) -> None:
        """Handle filtering operations like df[df['col'] > 0]."""
        df_name = self._get_name(node.value)
        condition = ast.unparse(node.slice) if hasattr(ast, "unparse") else "condition"

        self.transformations.append(
            Transformation.filter_rows(df_name, target, condition, self.current_line)
        )

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

    def _get_list_value(self, node: ast.expr) -> List[str]:
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

    def _get_dict_value(self, node: ast.expr) -> Dict[str, str]:
        """Extract a dict value from an AST node."""
        if isinstance(node, ast.Dict):
            result = {}
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                    result[str(k.value)] = str(v.value)
            return result
        return {}
