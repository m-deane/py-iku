"""Pydantic v2 schemas mirroring PrepareStep and ProcessorType from py-iku."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# ProcessorTypeEnum — generated from py2dataiku.models.prepare_step.ProcessorType
# ---------------------------------------------------------------------------
# We define unique members only (aliases share .value with the canonical member).
# The enum values match ProcessorType.value so JSON round-trips cleanly.


class ProcessorTypeEnum(StrEnum):
    """All 122 unique ProcessorType values from py2dataiku."""

    # Column manipulation
    COLUMN_RENAMER = "ColumnRenamer"
    COLUMN_COPIER = "ColumnCopier"
    COLUMNS_SELECTOR = "ColumnsSelector"
    COLUMN_REORDER = "ColumnReorder"
    COLUMNS_CONCATENATOR = "ColumnsConcat"

    # Missing value handling
    FILL_EMPTY_WITH_VALUE = "FillEmptyWithValue"
    REMOVE_ROWS_ON_EMPTY = "RemoveRowsOnEmpty"
    FILL_EMPTY_WITH_PREVIOUS_NEXT = "UpDownFill"
    FILL_EMPTY_WITH_COMPUTED_VALUE = "FillEmptyWithComputedValue"
    IMPUTE_WITH_ML = "ImputeWithML"

    # String transformations
    STRING_TRANSFORMER = "StringTransformer"
    TOKENIZER = "Tokenizer"
    REGEXP_EXTRACTOR = "PatternExtract"
    FIND_REPLACE = "FindReplace"
    SPLIT_COLUMN = "ColumnsSplitter"
    HTML_STRIPPER = "HtmlStripper"
    MULTI_COLUMN_FIND_REPLACE = "MultiColumnFindReplace"
    NGRAMMER = "Ngrammer"
    TEXT_SIMPLIFIER = "SimplifyText"
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
    ROUND_COLUMN = "Round"
    CLIP_COLUMN = "NumberClipping"
    BINNER = "Binner"
    NORMALIZER = "MeasureNormalize"

    # Type conversion
    TYPE_SETTER = "TypeSetter"
    DATE_PARSER = "DateParser"
    DATE_FORMATTER = "DateFormatter"

    # Date/Time operations
    DATE_COMPONENTS_EXTRACTOR = "DateComponentExtractor"
    DATE_DIFF_CALCULATOR = "DateDifference"
    HOLIDAYS_COMPUTER = "HolidaysComputer"
    TIMEZONE_CONVERTER = "TimezoneConverter"
    DATE_RANGE_CLASSIFIER = "DateRangeClassifier"
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
    MERGE_LONG_TAIL_VALUES = "LongTailGrouper"
    CATEGORICAL_ENCODER = "CategoricalEncoder"

    # Geographic
    GEO_POINT_CREATOR = "GeoPointCreator"
    GEO_ENCODER = "GeoEncoder"
    GEO_IP_RESOLVER = "GeoIPResolver"
    GEO_DISTANCE_CALCULATOR = "GeoDistanceCalculator"
    GEO_POLYGON_MATCHER = "GeoPolygonMatcher"
    ADDRESS_PARSER = "AddressParser"
    REVERSE_GEOCODER = "ReverseGeocoder"

    # Conditional logic
    IF_THEN_ELSE = "IfThenElse"
    SWITCH_CASE = "SwitchCase"

    # Value translation
    TRANSLATE_VALUES = "TranslateValues"

    # Data extraction
    EXTRACT_WITH_JSONPATH = "ExtractWithJSONPath"
    SPLIT_URL = "SplitURL"

    # Reshaping
    FOLD_MULTIPLE_COLUMNS = "FoldMultipleColumns"
    TRANSPOSE_ROWS_TO_COLUMNS = "TransposeRowsToColumns"
    UNFOLD = "Unfold"

    # Value manipulation
    COALESCE = "Coalesce"
    FILL_COLUMN = "FillColumn"

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


# ---------------------------------------------------------------------------
# PrepareStepModel — mirrors PrepareStep.to_dict()
# ---------------------------------------------------------------------------


class PrepareStepModel(BaseModel):
    """Mirrors PrepareStep.to_dict() output.

    Fields: metaType, type (processor DSS string), disabled, params, name.
    """

    metaType: str = Field(default="PROCESSOR", description="PROCESSOR or GROUP")
    type: str = Field(..., description="DSS processor type string (e.g. 'ColumnRenamer')")
    disabled: bool = Field(default=False)
    params: dict[str, Any] = Field(default_factory=dict)
    name: str | None = Field(default=None, description="Optional step label")

    model_config = {"populate_by_name": True}
