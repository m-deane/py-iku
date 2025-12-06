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
    COLUMN_REORDER = "ColumnReorder"
    COLUMNS_CONCATENATOR = "ColumnsConcatenator"

    # Missing value handling
    FILL_EMPTY_WITH_VALUE = "FillEmptyWithValue"
    REMOVE_ROWS_ON_EMPTY = "RemoveRowsOnEmpty"
    FILL_EMPTY_WITH_PREVIOUS_NEXT = "FillEmptyWithPreviousNext"
    FILL_EMPTY_WITH_COMPUTED_VALUE = "FillEmptyWithComputedValue"
    IMPUTE_WITH_ML = "ImputeWithML"

    # String transformations
    STRING_TRANSFORMER = "StringTransformer"
    TOKENIZER = "Tokenizer"
    REGEXP_EXTRACTOR = "RegexpExtractor"
    FIND_REPLACE = "FindReplace"
    SPLIT_COLUMN = "SplitColumn"
    CONCAT_COLUMNS = "ConcatColumns"
    HTML_STRIPPER = "HtmlStripper"
    MULTI_COLUMN_FIND_REPLACE = "MultiColumnFindReplace"
    NGRAMMER = "Ngrammer"
    TEXT_SIMPLIFIER = "TextSimplifier"
    STEM_TEXT = "StemText"
    LEMMATIZE_TEXT = "LemmatizeText"
    LANGUAGE_DETECTOR = "LanguageDetector"
    SENTIMENT_ANALYZER = "SentimentAnalyzer"
    TEXT_HASHER = "TextHasher"
    UNICODE_NORMALIZER = "UnicodeNormalizer"
    URL_PARSER = "URLParser"
    IP_ADDRESS_PARSER = "IPAddressParser"
    EMAIL_DOMAIN_EXTRACTOR = "EmailDomainExtractor"
    PHONE_FORMATTER = "PhoneFormatter"
    COUNTRY_NORMALIZER = "CountryNormalizer"
    USER_AGENT_PARSER = "UserAgentParser"

    # Numeric transformations
    NUMERICAL_TRANSFORMER = "NumericalTransformer"
    ROUND_COLUMN = "RoundColumn"
    ABS_COLUMN = "AbsColumn"
    CLIP_COLUMN = "ClipColumn"
    BINNER = "Binner"
    NORMALIZER = "Normalizer"
    DISCRETIZER = "Discretizer"
    QUANTILE_TRANSFORMER = "QuantileTransformer"
    ROBUST_SCALER = "RobustScaler"
    MIN_MAX_SCALER = "MinMaxScaler"
    STANDARD_SCALER = "StandardScaler"
    LOG_TRANSFORMER = "LogTransformer"
    POWER_TRANSFORMER = "PowerTransformer"
    BOX_COX_TRANSFORMER = "BoxCoxTransformer"

    # Type conversion
    TYPE_SETTER = "TypeSetter"
    DATE_PARSER = "DateParser"
    DATE_FORMATTER = "DateFormatter"
    BOOLEAN_CONVERTER = "BooleanConverter"
    NUMBER_TO_STRING = "NumberToString"
    STRING_TO_NUMBER = "StringToNumber"

    # Date/Time operations
    DATE_COMPONENTS_EXTRACTOR = "DateComponentsExtractor"
    DATE_DIFF_CALCULATOR = "DateDiffCalculator"
    HOLIDAYS_COMPUTER = "HolidaysComputer"
    TIMEZONE_CONVERTER = "TimezoneConverter"
    DATE_RANGE_CLASSIFIER = "DateRangeClassifier"
    DATETIME_FORMATTER = "DatetimeFormatter"
    TIMESTAMP_EXTRACTOR = "TimestampExtractor"

    # Filtering
    FILTER_ON_VALUE = "FilterOnValue"
    FILTER_ON_BAD_TYPE = "FilterOnBadType"
    FILTER_ON_FORMULA = "FilterOnFormula"
    FILTER_ON_DATE_RANGE = "FilterOnDateRange"
    FILTER_ON_NUMERIC_RANGE = "FilterOnNumericRange"
    FILTER_ON_MULTIPLE_VALUES = "FilterOnMultipleValues"
    FILTER_ON_NULL_NUMERIC = "FilterOnNullNumeric"
    FILTER_ON_GEO_ZONE = "FilterOnGeoZone"
    FILTER_ON_CUSTOM_CONDITION = "FilterOnCustomCondition"

    # Flagging
    FLAG_ON_VALUE = "FlagOnValue"
    FLAG_ON_FORMULA = "FlagOnFormula"
    FLAG_ON_BAD_TYPE = "FlagOnBadType"
    FLAG_ON_DATE_RANGE = "FlagOnDateRange"
    FLAG_ON_NUMERIC_RANGE = "FlagOnNumericRange"

    # Row operations
    REMOVE_DUPLICATES = "RemoveDuplicates"
    SORT_ROWS = "SortRows"
    SAMPLE_ROWS = "SampleRows"
    SHUFFLE_ROWS = "ShuffleRows"

    # Computed columns
    CREATE_COLUMN_WITH_GREL = "CreateColumnWithGREL"
    FORMULA = "Formula"
    MULTI_COLUMN_FORMULA = "MultiColumnFormula"
    COLUMN_PSEUDO_ANONYMIZER = "ColumnPseudoAnonymizer"
    HASH_COMPUTER = "HashComputer"
    UUID_GENERATOR = "UUIDGenerator"

    # Categorical
    MERGE_LONG_TAIL_VALUES = "MergeLongTailValues"
    CATEGORICAL_ENCODER = "CategoricalEncoder"
    ONE_HOT_ENCODER = "OneHotEncoder"
    LABEL_ENCODER = "LabelEncoder"
    ORDINAL_ENCODER = "OrdinalEncoder"
    TARGET_ENCODER = "TargetEncoder"
    LEAVE_ONE_OUT_ENCODER = "LeaveOneOutEncoder"
    WOE_ENCODER = "WOEEncoder"
    FEATURE_HASHER = "FeatureHasher"

    # Geographic
    GEO_POINT_CREATOR = "GeoPointCreator"
    GEO_ENCODER = "GeoEncoder"
    GEO_IP_RESOLVER = "GeoIPResolver"
    GEO_DISTANCE_CALCULATOR = "GeoDistanceCalculator"
    GEO_POLYGON_MATCHER = "GeoPolygonMatcher"
    ADDRESS_PARSER = "AddressParser"
    REVERSE_GEOCODER = "ReverseGeocoder"

    # Array/JSON operations
    ARRAY_SPLITTER = "ArraySplitter"
    ARRAY_JOINER = "ArrayJoiner"
    ARRAY_SORTER = "ArraySorter"
    ARRAY_UNFOLD = "ArrayUnfold"
    ARRAY_FOLD = "ArrayFold"
    ARRAY_ELEMENT_EXTRACTOR = "ArrayElementExtractor"
    JSON_FLATTENER = "JSONFlattener"
    JSON_EXTRACTOR = "JSONExtractor"
    XML_EXTRACTOR = "XMLExtractor"

    # Nested/Group processors
    NESTED_PROCESSOR = "NestedProcessor"
    PROCESSOR_GROUP = "ProcessorGroup"

    # Python UDF (fallback)
    PYTHON_UDF = "PythonUDF"


# String transformer modes
class StringTransformerMode(Enum):
    """Modes for StringTransformer processor."""

    # Case transformations
    UPPERCASE = "TO_UPPER"
    LOWERCASE = "TO_LOWER"
    TITLECASE = "TITLECASE"
    CAPITALIZE = "CAPITALIZE"
    SWAPCASE = "SWAPCASE"

    # Whitespace handling
    TRIM = "TRIM"
    TRIM_LEFT = "TRIM_LEFT"
    TRIM_RIGHT = "TRIM_RIGHT"
    NORMALIZE_WHITESPACE = "NORMALIZE_WHITESPACE"
    REMOVE_WHITESPACE = "REMOVE_WHITESPACE"
    COLLAPSE_WHITESPACE = "COLLAPSE_WHITESPACE"

    # Text cleaning
    REMOVE_ACCENTS = "REMOVE_ACCENTS"
    ASCII_TRANSLITERATE = "ASCII_TRANSLITERATE"
    REMOVE_NON_ALPHANUMERIC = "REMOVE_NON_ALPHANUMERIC"
    REMOVE_NON_PRINTABLE = "REMOVE_NON_PRINTABLE"
    REMOVE_PUNCTUATION = "REMOVE_PUNCTUATION"
    REMOVE_DIGITS = "REMOVE_DIGITS"
    KEEP_ONLY_DIGITS = "KEEP_ONLY_DIGITS"
    KEEP_ONLY_ALPHA = "KEEP_ONLY_ALPHA"

    # Padding
    PAD_LEFT = "PAD_LEFT"
    PAD_RIGHT = "PAD_RIGHT"
    PAD_CENTER = "PAD_CENTER"

    # Other
    REVERSE = "REVERSE"
    QUOTE = "QUOTE"
    UNQUOTE = "UNQUOTE"


# Numerical transformer modes
class NumericalTransformerMode(Enum):
    """Modes for NumericalTransformer processor."""

    # Arithmetic operations
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    POWER = "POWER"
    SQRT = "SQRT"
    LOG = "LOG"
    LOG10 = "LOG10"
    LOG2 = "LOG2"
    EXP = "EXP"
    ABS = "ABS"
    NEGATE = "NEGATE"
    INVERSE = "INVERSE"
    MODULO = "MODULO"

    # Rounding operations
    ROUND = "ROUND"
    FLOOR = "FLOOR"
    CEIL = "CEIL"
    TRUNCATE = "TRUNCATE"
    ROUND_TO_SIGNIFICANT = "ROUND_TO_SIGNIFICANT"

    # Trigonometric
    SIN = "SIN"
    COS = "COS"
    TAN = "TAN"
    ASIN = "ASIN"
    ACOS = "ACOS"
    ATAN = "ATAN"

    # Unit conversions
    DEGREES_TO_RADIANS = "DEGREES_TO_RADIANS"
    RADIANS_TO_DEGREES = "RADIANS_TO_DEGREES"


class FilterMatchMode(Enum):
    """Match modes for filtering processors."""

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    REGEX = "REGEX"
    NOT_REGEX = "NOT_REGEX"
    IS_EMPTY = "IS_EMPTY"
    IS_NOT_EMPTY = "IS_NOT_EMPTY"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"
    IN_LIST = "IN_LIST"
    NOT_IN_LIST = "NOT_IN_LIST"


class DateComponentType(Enum):
    """Date component types for DateComponentsExtractor."""

    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"
    DAY_OF_WEEK = "DAY_OF_WEEK"
    DAY_OF_YEAR = "DAY_OF_YEAR"
    WEEK_OF_YEAR = "WEEK_OF_YEAR"
    QUARTER = "QUARTER"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    SECOND = "SECOND"
    MILLISECOND = "MILLISECOND"
    TIMESTAMP = "TIMESTAMP"
    ISO_WEEK = "ISO_WEEK"
    ISO_YEAR = "ISO_YEAR"


class BinningMode(Enum):
    """Binning modes for Binner processor."""

    EQUAL_WIDTH = "EQUAL_WIDTH"
    EQUAL_FREQUENCY = "EQUAL_FREQUENCY"
    CUSTOM_BOUNDARIES = "CUSTOM_BOUNDARIES"
    QUANTILE = "QUANTILE"
    KMEANS = "KMEANS"


class NormalizationMode(Enum):
    """Normalization modes for Normalizer processor."""

    MIN_MAX = "MIN_MAX"
    Z_SCORE = "Z_SCORE"
    ROBUST = "ROBUST"
    L1 = "L1"
    L2 = "L2"
    MAX_ABS = "MAX_ABS"


class EncodingType(Enum):
    """Encoding types for categorical encoders."""

    ONE_HOT = "ONE_HOT"
    LABEL = "LABEL"
    ORDINAL = "ORDINAL"
    BINARY = "BINARY"
    TARGET = "TARGET"
    FREQUENCY = "FREQUENCY"
    COUNT = "COUNT"
    LEAVE_ONE_OUT = "LEAVE_ONE_OUT"
    WOE = "WOE"
    HASH = "HASH"


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
