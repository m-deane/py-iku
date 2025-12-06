"""Prepare recipe step/processor model for Dataiku DSS."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProcessorType(Enum):
    """
    Dataiku Prepare recipe processor types.

    These correspond to the transformation steps available in
    Dataiku's Prepare recipe visual interface.
    """

    # Column manipulation
    COLUMN_RENAMER = "ColumnRenamer"
    COLUMN_COPIER = "ColumnCopier"
    COLUMN_DELETER = "ColumnDeleter"
    COLUMNS_SELECTOR = "ColumnsSelector"

    # Missing value handling
    FILL_EMPTY_WITH_VALUE = "FillEmptyWithValue"
    REMOVE_ROWS_ON_EMPTY = "RemoveRowsOnEmpty"
    FILL_EMPTY_WITH_PREVIOUS_NEXT = "FillEmptyWithPreviousNext"

    # String transformations
    STRING_TRANSFORMER = "StringTransformer"
    TOKENIZER = "Tokenizer"
    REGEXP_EXTRACTOR = "RegexpExtractor"
    FIND_REPLACE = "FindReplace"
    SPLIT_COLUMN = "SplitColumn"
    CONCAT_COLUMNS = "ConcatColumns"
    HTML_STRIPPER = "HtmlStripper"

    # Numeric transformations
    NUMERICAL_TRANSFORMER = "NumericalTransformer"
    ROUND_COLUMN = "RoundColumn"
    ABS_COLUMN = "AbsColumn"
    CLIP_COLUMN = "ClipColumn"
    BINNER = "Binner"
    NORMALIZER = "Normalizer"

    # Type conversion
    TYPE_SETTER = "TypeSetter"
    DATE_PARSER = "DateParser"
    DATE_FORMATTER = "DateFormatter"

    # Filtering
    FILTER_ON_VALUE = "FilterOnValue"
    FILTER_ON_BAD_TYPE = "FilterOnBadType"
    FILTER_ON_FORMULA = "FilterOnFormula"
    FILTER_ON_DATE_RANGE = "FilterOnDateRange"
    FILTER_ON_NUMERIC_RANGE = "FilterOnNumericRange"

    # Flagging
    FLAG_ON_VALUE = "FlagOnValue"
    FLAG_ON_FORMULA = "FlagOnFormula"
    FLAG_ON_BAD_TYPE = "FlagOnBadType"

    # Row operations
    REMOVE_DUPLICATES = "RemoveDuplicates"
    SORT_ROWS = "SortRows"
    SAMPLE_ROWS = "SampleRows"

    # Computed columns
    CREATE_COLUMN_WITH_GREL = "CreateColumnWithGREL"
    FORMULA = "Formula"

    # Categorical
    MERGE_LONG_TAIL_VALUES = "MergeLongTailValues"
    CATEGORICAL_ENCODER = "CategoricalEncoder"

    # Geographic
    GEO_POINT_CREATOR = "GeoPointCreator"
    GEO_ENCODER = "GeoEncoder"

    # Python UDF (fallback)
    PYTHON_UDF = "PythonUDF"


# String transformer modes
class StringTransformerMode(Enum):
    """Modes for StringTransformer processor."""

    UPPERCASE = "TO_UPPER"
    LOWERCASE = "TO_LOWER"
    TITLECASE = "TITLECASE"
    TRIM = "TRIM"
    TRIM_LEFT = "TRIM_LEFT"
    TRIM_RIGHT = "TRIM_RIGHT"
    NORMALIZE_WHITESPACE = "NORMALIZE_WHITESPACE"
    REMOVE_WHITESPACE = "REMOVE_WHITESPACE"


# Numerical transformer modes
class NumericalTransformerMode(Enum):
    """Modes for NumericalTransformer processor."""

    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    POWER = "POWER"
    ROUND = "ROUND"
    FLOOR = "FLOOR"
    CEIL = "CEIL"


@dataclass
class PrepareStep:
    """
    Represents a single step/processor in a Dataiku Prepare recipe.

    Each step performs a specific transformation on the data.
    Steps are executed in order within a Prepare recipe.
    """

    processor_type: ProcessorType
    params: Dict[str, Any] = field(default_factory=dict)
    disabled: bool = False
    name: Optional[str] = None  # Optional step label
    meta_type: str = "PROCESSOR"  # PROCESSOR or GROUP
    source_line: Optional[int] = None  # Line in original Python code
    source_code: Optional[str] = None  # Original Python expression

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "metaType": self.meta_type,
            "type": self.processor_type.value,
            "disabled": self.disabled,
            "params": self.params,
        }
        if self.name:
            result["name"] = self.name
        return result

    def to_json(self) -> Dict[str, Any]:
        """Convert to Dataiku API-compatible JSON."""
        return self.to_dict()

    @classmethod
    def fill_empty(
        cls,
        column: str,
        value: Any,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a FillEmptyWithValue step."""
        return cls(
            processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
            params={"column": column, "value": str(value)},
            source_line=source_line,
        )

    @classmethod
    def rename_columns(
        cls,
        renamings: Dict[str, str],
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a ColumnRenamer step."""
        return cls(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={
                "renamings": [
                    {"from": old, "to": new} for old, new in renamings.items()
                ]
            },
            source_line=source_line,
        )

    @classmethod
    def delete_columns(
        cls,
        columns: List[str],
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a ColumnDeleter step."""
        return cls(
            processor_type=ProcessorType.COLUMN_DELETER,
            params={"columns": columns},
            source_line=source_line,
        )

    @classmethod
    def string_transform(
        cls,
        column: str,
        mode: StringTransformerMode,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a StringTransformer step."""
        return cls(
            processor_type=ProcessorType.STRING_TRANSFORMER,
            params={"column": column, "mode": mode.value},
            source_line=source_line,
        )

    @classmethod
    def set_type(
        cls,
        column: str,
        target_type: str,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a TypeSetter step."""
        return cls(
            processor_type=ProcessorType.TYPE_SETTER,
            params={"column": column, "type": target_type},
            source_line=source_line,
        )

    @classmethod
    def parse_date(
        cls,
        column: str,
        formats: Optional[List[str]] = None,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a DateParser step."""
        params = {"column": column}
        if formats:
            params["formats"] = formats
        return cls(
            processor_type=ProcessorType.DATE_PARSER,
            params=params,
            source_line=source_line,
        )

    @classmethod
    def filter_on_value(
        cls,
        column: str,
        values: List[Any],
        matching_mode: str = "EQUALS",
        keep: bool = True,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a FilterOnValue step."""
        return cls(
            processor_type=ProcessorType.FILTER_ON_VALUE,
            params={
                "column": column,
                "values": [str(v) for v in values],
                "matchingMode": matching_mode,
                "keep": keep,
            },
            source_line=source_line,
        )

    @classmethod
    def remove_rows_on_empty(
        cls,
        columns: List[str],
        keep_empty: bool = False,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a RemoveRowsOnEmpty step."""
        return cls(
            processor_type=ProcessorType.REMOVE_ROWS_ON_EMPTY,
            params={"columns": columns, "keep": keep_empty},
            source_line=source_line,
        )

    @classmethod
    def remove_duplicates(
        cls,
        columns: Optional[List[str]] = None,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a RemoveDuplicates step."""
        params = {}
        if columns:
            params["columns"] = columns
        return cls(
            processor_type=ProcessorType.REMOVE_DUPLICATES,
            params=params,
            source_line=source_line,
        )

    @classmethod
    def create_column_grel(
        cls,
        column: str,
        expression: str,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a CreateColumnWithGREL step."""
        return cls(
            processor_type=ProcessorType.CREATE_COLUMN_WITH_GREL,
            params={"column": column, "expression": expression},
            source_line=source_line,
        )

    @classmethod
    def regexp_extract(
        cls,
        column: str,
        pattern: str,
        output_columns: Optional[List[str]] = None,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a RegexpExtractor step."""
        params = {"column": column, "pattern": pattern}
        if output_columns:
            params["outputColumns"] = output_columns
        return cls(
            processor_type=ProcessorType.REGEXP_EXTRACTOR,
            params=params,
            source_line=source_line,
        )

    @classmethod
    def python_udf(
        cls,
        code: str,
        input_columns: List[str],
        output_column: str,
        source_line: Optional[int] = None,
    ) -> "PrepareStep":
        """Create a PythonUDF step (fallback for complex operations)."""
        return cls(
            processor_type=ProcessorType.PYTHON_UDF,
            params={
                "code": code,
                "inputColumns": input_columns,
                "outputColumn": output_column,
            },
            source_line=source_line,
        )

    def get_description(self) -> str:
        """Get a human-readable description of this step."""
        ptype = self.processor_type.value
        params = self.params

        if self.processor_type == ProcessorType.FILL_EMPTY_WITH_VALUE:
            return f"Fill empty values in '{params.get('column')}' with '{params.get('value')}'"
        elif self.processor_type == ProcessorType.COLUMN_RENAMER:
            renamings = params.get("renamings", [])
            renames = ", ".join([f"{r['from']} -> {r['to']}" for r in renamings])
            return f"Rename columns: {renames}"
        elif self.processor_type == ProcessorType.COLUMN_DELETER:
            cols = ", ".join(params.get("columns", []))
            return f"Delete columns: {cols}"
        elif self.processor_type == ProcessorType.STRING_TRANSFORMER:
            return f"Transform string '{params.get('column')}' with mode {params.get('mode')}"
        elif self.processor_type == ProcessorType.TYPE_SETTER:
            return f"Set type of '{params.get('column')}' to {params.get('type')}"
        elif self.processor_type == ProcessorType.REMOVE_DUPLICATES:
            cols = params.get("columns")
            if cols:
                return f"Remove duplicates on columns: {', '.join(cols)}"
            return "Remove duplicate rows"
        elif self.processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY:
            cols = ", ".join(params.get("columns", []))
            return f"Remove rows with empty values in: {cols}"
        else:
            return f"{ptype}: {params}"

    def __repr__(self) -> str:
        return f"PrepareStep(type={self.processor_type.value}, params={self.params})"
