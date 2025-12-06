"""Complete catalog of Dataiku Prepare recipe processor types."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ProcessorInfo:
    """Information about a Dataiku processor type."""

    name: str
    category: str
    description: str
    required_params: List[str]
    optional_params: List[str]
    example_params: Dict[str, Any]


class ProcessorCatalog:
    """
    Catalog of all Dataiku Prepare recipe processors.

    This class provides comprehensive information about available
    processors, their parameters, and usage examples.
    """

    PROCESSORS: Dict[str, ProcessorInfo] = {
        # Column manipulation
        "ColumnRenamer": ProcessorInfo(
            name="ColumnRenamer",
            category="Column Manipulation",
            description="Rename one or more columns",
            required_params=["renamings"],
            optional_params=[],
            example_params={
                "renamings": [{"from": "old_name", "to": "new_name"}]
            },
        ),
        "ColumnCopier": ProcessorInfo(
            name="ColumnCopier",
            category="Column Manipulation",
            description="Create a copy of an existing column",
            required_params=["inputColumn", "outputColumn"],
            optional_params=[],
            example_params={
                "inputColumn": "source_col",
                "outputColumn": "target_col",
            },
        ),
        "ColumnDeleter": ProcessorInfo(
            name="ColumnDeleter",
            category="Column Manipulation",
            description="Delete one or more columns",
            required_params=["columns"],
            optional_params=[],
            example_params={"columns": ["col1", "col2"]},
        ),
        "ColumnsSelector": ProcessorInfo(
            name="ColumnsSelector",
            category="Column Manipulation",
            description="Keep only specified columns",
            required_params=["columns"],
            optional_params=["keep"],
            example_params={"columns": ["col1", "col2"], "keep": True},
        ),
        # Missing value handling
        "FillEmptyWithValue": ProcessorInfo(
            name="FillEmptyWithValue",
            category="Missing Values",
            description="Fill empty cells with a constant value",
            required_params=["column", "value"],
            optional_params=[],
            example_params={"column": "my_col", "value": "0"},
        ),
        "RemoveRowsOnEmpty": ProcessorInfo(
            name="RemoveRowsOnEmpty",
            category="Missing Values",
            description="Remove rows where specified columns are empty",
            required_params=["columns"],
            optional_params=["keep"],
            example_params={"columns": ["col1"], "keep": False},
        ),
        "FillEmptyWithPreviousNext": ProcessorInfo(
            name="FillEmptyWithPreviousNext",
            category="Missing Values",
            description="Fill empty cells with previous or next value",
            required_params=["column", "direction"],
            optional_params=[],
            example_params={"column": "my_col", "direction": "PREVIOUS"},
        ),
        # String transformations
        "StringTransformer": ProcessorInfo(
            name="StringTransformer",
            category="String Operations",
            description="Transform string values (uppercase, lowercase, trim, etc.)",
            required_params=["column", "mode"],
            optional_params=[],
            example_params={"column": "name", "mode": "TO_LOWER"},
        ),
        "FindReplace": ProcessorInfo(
            name="FindReplace",
            category="String Operations",
            description="Find and replace text patterns",
            required_params=["column", "find", "replace"],
            optional_params=["matchMode"],
            example_params={
                "column": "text",
                "find": "old",
                "replace": "new",
                "matchMode": "LITERAL",
            },
        ),
        "RegexpExtractor": ProcessorInfo(
            name="RegexpExtractor",
            category="String Operations",
            description="Extract values using regular expression",
            required_params=["column", "pattern"],
            optional_params=["outputColumns"],
            example_params={
                "column": "text",
                "pattern": r"(\d+)",
                "outputColumns": ["extracted"],
            },
        ),
        "SplitColumn": ProcessorInfo(
            name="SplitColumn",
            category="String Operations",
            description="Split column values by separator",
            required_params=["column", "separator"],
            optional_params=["limit", "outputColumns"],
            example_params={"column": "full_name", "separator": " "},
        ),
        "ConcatColumns": ProcessorInfo(
            name="ConcatColumns",
            category="String Operations",
            description="Concatenate multiple columns into one",
            required_params=["columns", "outputColumn"],
            optional_params=["separator"],
            example_params={
                "columns": ["first", "last"],
                "outputColumn": "full_name",
                "separator": " ",
            },
        ),
        "Tokenizer": ProcessorInfo(
            name="Tokenizer",
            category="String Operations",
            description="Tokenize text into words or patterns",
            required_params=["column", "operation"],
            optional_params=["pattern"],
            example_params={"column": "text", "operation": "SPLIT_WHITESPACE"},
        ),
        # Numeric transformations
        "NumericalTransformer": ProcessorInfo(
            name="NumericalTransformer",
            category="Numeric Operations",
            description="Apply mathematical transformations",
            required_params=["column", "mode"],
            optional_params=["value"],
            example_params={"column": "amount", "mode": "MULTIPLY", "value": 100},
        ),
        "RoundColumn": ProcessorInfo(
            name="RoundColumn",
            category="Numeric Operations",
            description="Round numeric values",
            required_params=["column"],
            optional_params=["precision", "mode"],
            example_params={"column": "price", "precision": 2},
        ),
        "Binner": ProcessorInfo(
            name="Binner",
            category="Numeric Operations",
            description="Bin numeric values into categories",
            required_params=["column", "mode"],
            optional_params=["bins", "labels"],
            example_params={
                "column": "age",
                "mode": "FIXED_BINS",
                "bins": [0, 18, 35, 50, 100],
            },
        ),
        "Normalizer": ProcessorInfo(
            name="Normalizer",
            category="Numeric Operations",
            description="Normalize numeric values",
            required_params=["column", "mode"],
            optional_params=[],
            example_params={"column": "value", "mode": "ZSCORE"},
        ),
        # Type conversion
        "TypeSetter": ProcessorInfo(
            name="TypeSetter",
            category="Type Conversion",
            description="Set column data type",
            required_params=["column", "type"],
            optional_params=[],
            example_params={"column": "id", "type": "bigint"},
        ),
        "DateParser": ProcessorInfo(
            name="DateParser",
            category="Type Conversion",
            description="Parse string to date",
            required_params=["column"],
            optional_params=["formats", "timezone"],
            example_params={"column": "date_str", "formats": ["yyyy-MM-dd"]},
        ),
        "DateFormatter": ProcessorInfo(
            name="DateFormatter",
            category="Type Conversion",
            description="Format date to string",
            required_params=["column", "format"],
            optional_params=[],
            example_params={"column": "date", "format": "yyyy-MM-dd"},
        ),
        # Filtering
        "FilterOnValue": ProcessorInfo(
            name="FilterOnValue",
            category="Filtering",
            description="Filter rows based on column values",
            required_params=["column", "matchingMode", "values"],
            optional_params=["keep"],
            example_params={
                "column": "status",
                "matchingMode": "EQUALS",
                "values": ["active"],
                "keep": True,
            },
        ),
        "FilterOnFormula": ProcessorInfo(
            name="FilterOnFormula",
            category="Filtering",
            description="Filter rows using a formula",
            required_params=["formula"],
            optional_params=["keep"],
            example_params={"formula": "age > 18", "keep": True},
        ),
        "FilterOnNumericRange": ProcessorInfo(
            name="FilterOnNumericRange",
            category="Filtering",
            description="Filter rows by numeric range",
            required_params=["column"],
            optional_params=["min", "max", "keep"],
            example_params={"column": "price", "min": 0, "max": 100},
        ),
        # Row operations
        "RemoveDuplicates": ProcessorInfo(
            name="RemoveDuplicates",
            category="Row Operations",
            description="Remove duplicate rows",
            required_params=[],
            optional_params=["columns"],
            example_params={"columns": ["id"]},
        ),
        "SortRows": ProcessorInfo(
            name="SortRows",
            category="Row Operations",
            description="Sort rows by column values",
            required_params=["columns"],
            optional_params=[],
            example_params={
                "columns": [{"column": "date", "order": "DESC"}]
            },
        ),
        # Computed columns
        "CreateColumnWithGREL": ProcessorInfo(
            name="CreateColumnWithGREL",
            category="Computed Columns",
            description="Create column using GREL expression",
            required_params=["column", "expression"],
            optional_params=[],
            example_params={
                "column": "full_name",
                "expression": 'concat(first_name, " ", last_name)',
            },
        ),
        "Formula": ProcessorInfo(
            name="Formula",
            category="Computed Columns",
            description="Create column using formula",
            required_params=["outputColumn", "expression"],
            optional_params=[],
            example_params={
                "outputColumn": "total",
                "expression": "price * quantity",
            },
        ),
        # Flagging
        "FlagOnValue": ProcessorInfo(
            name="FlagOnValue",
            category="Flagging",
            description="Create boolean flag based on value match",
            required_params=["column", "outputColumn"],
            optional_params=["values", "matchMode"],
            example_params={
                "column": "status",
                "outputColumn": "is_active",
                "values": ["active"],
            },
        ),
        # Categorical
        "MergeLongTailValues": ProcessorInfo(
            name="MergeLongTailValues",
            category="Categorical",
            description="Merge infrequent categorical values",
            required_params=["column"],
            optional_params=["threshold", "replacement"],
            example_params={
                "column": "category",
                "threshold": 10,
                "replacement": "OTHER",
            },
        ),
        # Python UDF
        "PythonUDF": ProcessorInfo(
            name="PythonUDF",
            category="Custom",
            description="Apply custom Python function",
            required_params=["code"],
            optional_params=["inputColumns", "outputColumn"],
            example_params={
                "code": "return row['col'].upper()",
                "inputColumns": ["col"],
                "outputColumn": "col_upper",
            },
        ),
    }

    @classmethod
    def get_processor(cls, name: str) -> Optional[ProcessorInfo]:
        """Get processor information by name."""
        return cls.PROCESSORS.get(name)

    @classmethod
    def list_processors(cls, category: Optional[str] = None) -> List[str]:
        """List all processor names, optionally filtered by category."""
        if category:
            return [
                name
                for name, info in cls.PROCESSORS.items()
                if info.category == category
            ]
        return list(cls.PROCESSORS.keys())

    @classmethod
    def list_categories(cls) -> List[str]:
        """List all processor categories."""
        return sorted(set(info.category for info in cls.PROCESSORS.values()))

    @classmethod
    def get_required_params(cls, name: str) -> List[str]:
        """Get required parameters for a processor."""
        info = cls.PROCESSORS.get(name)
        return info.required_params if info else []

    @classmethod
    def get_example(cls, name: str) -> Dict[str, Any]:
        """Get example parameters for a processor."""
        info = cls.PROCESSORS.get(name)
        return info.example_params if info else {}
