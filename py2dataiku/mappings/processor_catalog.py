"""Complete catalog of Dataiku Prepare recipe processor types."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ProcessorInfo:
    """Information about a Dataiku processor type.

    ``params`` is the canonical, full list of parameter names that a DSS
    processor accepts on the wire. When omitted, it is auto-derived from
    ``required_params + optional_params`` after construction. Override
    ``params`` explicitly when the doc-canonical wire name set differs
    from the lib's historical ``required_params``/``optional_params``
    split (e.g. when the doc enumerates ``matchingMode`` while the lib
    historically tracked ``matchMode``).
    """

    name: str
    category: str
    description: str
    required_params: list[str]
    optional_params: list[str]
    example_params: dict[str, Any]
    # Full list of canonical wire param names. Defaults to required+optional
    # when not supplied. The DSS round-trip harness validates that every
    # documented param key appears in this list.
    params: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # If params wasn't supplied at construction, derive it from the
        # required/optional union so existing entries don't have to be
        # rewritten. Preserves order: required first, then optional.
        if not self.params:
            seen: set[str] = set()
            merged: list[str] = []
            for p in list(self.required_params) + list(self.optional_params):
                if p not in seen:
                    seen.add(p)
                    merged.append(p)
            self.params = merged


class ProcessorCatalog:
    """
    Catalog of all Dataiku Prepare recipe processors.

    This class provides comprehensive information about available
    processors, their parameters, and usage examples.
    """

    PROCESSORS: dict[str, ProcessorInfo] = {
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
        "ColumnsSelector_delete": ProcessorInfo(
            name="ColumnsSelector",
            category="Column Manipulation",
            description="Delete one or more columns (uses ColumnsSelector processor)",
            required_params=["columns"],
            optional_params=[],
            example_params={"columns": ["col1", "col2"]},
        ),
        "ColumnsSelector": ProcessorInfo(
            name="ColumnsSelector",
            category="Column Manipulation",
            description="Keep only specified columns",
            required_params=["columns"],
            optional_params=["keep", "appliesTo"],
            example_params={
                "columns": ["col1", "col2"],
                "keep": True,
                "appliesTo": "COLUMNS",
            },
        ),
        "ColumnReorder": ProcessorInfo(
            name="ColumnReorder",
            category="Column Manipulation",
            description="Reorder columns in a dataset",
            required_params=["columns"],
            optional_params=[],
            example_params={"columns": ["id", "name", "date", "value"]},
        ),
        "ColumnsConcat": ProcessorInfo(
            name="ColumnsConcat",
            category="Column Manipulation",
            description="Concatenate multiple columns into one",
            required_params=["columns", "outputColumn"],
            optional_params=["separator"],
            example_params={
                "columns": ["first_name", "last_name"],
                "outputColumn": "full_name",
                "separator": " ",
            },
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
        "UpDownFill": ProcessorInfo(
            name="UpDownFill",
            category="Missing Values",
            description="Fill empty cells with previous or next value",
            required_params=["column", "direction"],
            optional_params=[],
            example_params={"column": "my_col", "direction": "PREVIOUS"},
        ),
        "FillEmptyWithComputedValue": ProcessorInfo(
            name="FillEmptyWithComputedValue",
            category="Missing Values",
            description="Fill empty cells with a computed value (mean, median, mode)",
            required_params=["column", "mode"],
            optional_params=[],
            example_params={"column": "score", "mode": "MEAN"},
        ),
        "ImputeWithML": ProcessorInfo(
            name="ImputeWithML",
            category="Missing Values",
            description="Impute missing values using machine learning",
            required_params=["column"],
            optional_params=["method"],
            example_params={"column": "income", "method": "KNN"},
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
        "PatternExtract": ProcessorInfo(
            name="PatternExtract",
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
        "ColumnsSplitter": ProcessorInfo(
            name="ColumnsSplitter",
            category="String Operations",
            description="Split column values by separator",
            required_params=["column", "separator"],
            optional_params=["limit", "outputColumns"],
            example_params={"column": "full_name", "separator": " "},
        ),
        "Tokenizer": ProcessorInfo(
            name="Tokenizer",
            category="String Operations",
            description="Tokenize text into words or patterns",
            required_params=["column", "operation"],
            optional_params=["pattern"],
            example_params={"column": "text", "operation": "SPLIT_WHITESPACE"},
        ),
        "HtmlStripper": ProcessorInfo(
            name="HtmlStripper",
            category="String Operations",
            description="Remove HTML tags from text",
            required_params=["column"],
            optional_params=[],
            example_params={"column": "html_content"},
        ),
        "MultiColumnFindReplace": ProcessorInfo(
            name="MultiColumnFindReplace",
            category="String Operations",
            description="Find and replace text across multiple columns",
            required_params=["columns", "find", "replace"],
            optional_params=["matchMode"],
            example_params={
                "columns": ["col1", "col2"],
                "find": "old",
                "replace": "new",
            },
        ),
        "Ngrammer": ProcessorInfo(
            name="Ngrammer",
            category="String Operations",
            description="Generate n-grams from text",
            required_params=["column", "n"],
            optional_params=["outputColumn"],
            example_params={"column": "text", "n": 2},
        ),
        "SimplifyText": ProcessorInfo(
            name="SimplifyText",
            category="String Operations",
            description="Simplify text by removing special characters and normalizing",
            required_params=["column"],
            optional_params=[],
            example_params={"column": "text"},
        ),
        "StemText": ProcessorInfo(
            name="StemText",
            category="String Operations",
            description="Apply word stemming to text",
            required_params=["column"],
            optional_params=["language"],
            example_params={"column": "text", "language": "english"},
        ),
        "LemmatizeText": ProcessorInfo(
            name="LemmatizeText",
            category="String Operations",
            description="Apply lemmatization to text",
            required_params=["column"],
            optional_params=["language"],
            example_params={"column": "text", "language": "english"},
        ),
        "LanguageDetector": ProcessorInfo(
            name="LanguageDetector",
            category="String Operations",
            description="Detect the language of text",
            required_params=["column"],
            optional_params=["outputColumn"],
            example_params={"column": "text", "outputColumn": "language"},
        ),
        "SentimentAnalyzer": ProcessorInfo(
            name="SentimentAnalyzer",
            category="String Operations",
            description="Analyze sentiment of text",
            required_params=["column"],
            optional_params=["outputColumn"],
            example_params={"column": "review", "outputColumn": "sentiment"},
        ),
        "TextHasher": ProcessorInfo(
            name="TextHasher",
            category="String Operations",
            description="Hash text values",
            required_params=["column"],
            optional_params=["algorithm", "outputColumn"],
            example_params={"column": "text", "algorithm": "MD5"},
        ),
        "UnicodeNormalizer": ProcessorInfo(
            name="UnicodeNormalizer",
            category="String Operations",
            description="Normalize Unicode characters",
            required_params=["column"],
            optional_params=["form"],
            example_params={"column": "text", "form": "NFC"},
        ),
        "URLParser": ProcessorInfo(
            name="URLParser",
            category="String Operations",
            description="Parse URL components",
            required_params=["column"],
            optional_params=["extractComponents"],
            example_params={"column": "url", "extractComponents": ["host", "path"]},
        ),
        "IPAddressParser": ProcessorInfo(
            name="IPAddressParser",
            category="String Operations",
            description="Parse and validate IP addresses",
            required_params=["column"],
            optional_params=["outputColumn"],
            example_params={"column": "ip_address"},
        ),
        "EmailDomainExtractor": ProcessorInfo(
            name="EmailDomainExtractor",
            category="String Operations",
            description="Extract domain from email addresses",
            required_params=["column"],
            optional_params=["outputColumn"],
            example_params={"column": "email", "outputColumn": "domain"},
        ),
        "PhoneFormatter": ProcessorInfo(
            name="PhoneFormatter",
            category="String Operations",
            description="Format phone numbers to a standard format",
            required_params=["column"],
            optional_params=["country"],
            example_params={"column": "phone", "country": "US"},
        ),
        "CountryNormalizer": ProcessorInfo(
            name="CountryNormalizer",
            category="String Operations",
            description="Normalize country names to standard format",
            required_params=["column"],
            optional_params=["outputFormat"],
            example_params={"column": "country", "outputFormat": "ISO_3166_1"},
        ),
        "UserAgentParser": ProcessorInfo(
            name="UserAgentParser",
            category="String Operations",
            description="Parse user agent strings into components",
            required_params=["column"],
            optional_params=[],
            example_params={"column": "user_agent"},
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
        "Round": ProcessorInfo(
            name="Round",
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
        "MeasureNormalize": ProcessorInfo(
            name="MeasureNormalize",
            category="Numeric Operations",
            description="Normalize numeric values",
            required_params=["column", "mode"],
            optional_params=[],
            example_params={"column": "value", "mode": "ZSCORE"},
        ),
        "NumberClipping": ProcessorInfo(
            name="NumberClipping",
            category="Numeric Operations",
            description="Clip numeric values to a range",
            required_params=["column"],
            optional_params=["min", "max"],
            example_params={"column": "score", "min": 0, "max": 100},
        ),
        # Note: AbsColumn, Discretizer, QuantileTransformer, RobustScaler,
        # MinMaxScaler, StandardScaler, LogTransformer, PowerTransformer,
        # BoxCoxTransformer are NOT real DSS Prepare processors — they are
        # sklearn / pandas helper names. ProcessorType aliases each to a
        # canonical DSS processor (CreateColumnWithGREL / Binner /
        # MeasureNormalize / NumericalTransformer) so emitted JSON is valid.
        # The catalog intentionally lists ONLY real DSS processors.
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
            optional_params=["formats", "timezone", "outputColumn"],
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
        # Note: BooleanConverter, NumberToString, StringToNumber are NOT real
        # DSS Prepare processors — they are aliases of TypeSetter in
        # ProcessorType. Emit a TypeSetter step with the desired target type.
        # Date/Time operations
        "DateComponentExtractor": ProcessorInfo(
            name="DateComponentExtractor",
            category="Date/Time",
            description="Extract date components (year, month, day, etc.)",
            required_params=["column", "components"],
            optional_params=[],
            example_params={
                "column": "date",
                "components": ["YEAR", "MONTH", "DAY"],
            },
        ),
        "DateDifference": ProcessorInfo(
            name="DateDifference",
            category="Date/Time",
            description="Calculate difference between two dates",
            required_params=["column1", "column2"],
            optional_params=["unit", "outputColumn"],
            example_params={
                "column1": "start_date",
                "column2": "end_date",
                "unit": "DAYS",
                "outputColumn": "duration_days",
            },
        ),
        "HolidaysComputer": ProcessorInfo(
            name="HolidaysComputer",
            category="Date/Time",
            description="Compute holiday flags for dates",
            required_params=["column"],
            optional_params=["country", "outputColumn"],
            example_params={"column": "date", "country": "US"},
        ),
        "TimezoneConverter": ProcessorInfo(
            name="TimezoneConverter",
            category="Date/Time",
            description="Convert dates between timezones",
            required_params=["column", "fromTimezone", "toTimezone"],
            optional_params=[],
            example_params={
                "column": "event_time",
                "fromTimezone": "UTC",
                "toTimezone": "America/New_York",
            },
        ),
        "DateRangeClassifier": ProcessorInfo(
            name="DateRangeClassifier",
            category="Date/Time",
            description="Classify dates into ranges/buckets",
            required_params=["column"],
            optional_params=["ranges", "outputColumn"],
            example_params={"column": "date", "outputColumn": "date_bucket"},
        ),
        "TimestampExtractor": ProcessorInfo(
            name="TimestampExtractor",
            category="Date/Time",
            description="Extract Unix timestamp from date column",
            required_params=["column"],
            optional_params=["outputColumn", "unit"],
            example_params={"column": "date", "outputColumn": "timestamp_ms"},
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
            # Lib historically used 'formula'/'keep'; doc-canonical wire names
            # are 'expression'/'action' (KEEP_ROW / REMOVE_ROW). Both spellings
            # are accepted because the params dict round-trips opaquely.
            required_params=["formula"],
            optional_params=["keep", "expression", "action"],
            example_params={
                "expression": "age > 18",
                "action": "KEEP_ROW",
            },
        ),
        "FilterOnNumericRange": ProcessorInfo(
            name="FilterOnNumericRange",
            category="Filtering",
            description="Filter rows by numeric range",
            required_params=["column"],
            optional_params=["min", "max", "keep", "action"],
            example_params={
                "column": "price",
                "min": 0,
                "max": 100,
                "action": "KEEP_ROW",
            },
        ),
        "FilterOnDateRange": ProcessorInfo(
            name="FilterOnDateRange",
            category="Filtering",
            description="Filter rows by date range",
            required_params=["column"],
            optional_params=["startDate", "endDate", "keep"],
            example_params={
                "column": "date",
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
            },
        ),
        "FilterOnBadType": ProcessorInfo(
            name="FilterOnBadType",
            category="Filtering",
            description="Filter rows with invalid type values",
            required_params=["column", "expectedType"],
            optional_params=["keep"],
            example_params={"column": "age", "expectedType": "integer"},
        ),
        "FilterOnMultipleValues": ProcessorInfo(
            name="FilterOnMultipleValues",
            category="Filtering",
            description="Filter rows matching multiple values",
            required_params=["column", "values"],
            optional_params=["keep"],
            example_params={"column": "status", "values": ["active", "pending"]},
        ),
        "FilterOnNullNumeric": ProcessorInfo(
            name="FilterOnNullNumeric",
            category="Filtering",
            description="Filter rows with null or non-numeric values",
            required_params=["column"],
            optional_params=["keep"],
            example_params={"column": "score"},
        ),
        "FilterOnGeoZone": ProcessorInfo(
            name="FilterOnGeoZone",
            category="Filtering",
            description="Filter rows by geographic zone",
            required_params=["geoColumn", "zone"],
            optional_params=["keep"],
            example_params={"geoColumn": "location", "zone": "US"},
        ),
        "FilterOnCustomCondition": ProcessorInfo(
            name="FilterOnCustomCondition",
            category="Filtering",
            description="Filter rows using a custom condition expression",
            required_params=["expression"],
            optional_params=["keep"],
            example_params={"expression": "val(age) > 18 && val(status) == 'active'"},
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
        "SampleRows": ProcessorInfo(
            name="SampleRows",
            category="Row Operations",
            description="Sample a subset of rows",
            required_params=["sampleSize"],
            optional_params=["method"],
            example_params={"sampleSize": 1000, "method": "RANDOM"},
        ),
        "ShuffleRows": ProcessorInfo(
            name="ShuffleRows",
            category="Row Operations",
            description="Randomly shuffle rows",
            required_params=[],
            optional_params=["seed"],
            example_params={"seed": 42},
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
        "MultiColumnFormula": ProcessorInfo(
            name="MultiColumnFormula",
            category="Computed Columns",
            description="Apply formula across multiple columns",
            required_params=["columns", "expression"],
            optional_params=["outputPrefix"],
            example_params={
                "columns": ["col1", "col2"],
                "expression": "val * 100",
            },
        ),
        "ColumnPseudoAnonymizer": ProcessorInfo(
            name="ColumnPseudoAnonymizer",
            category="Computed Columns",
            description="Pseudo-anonymize column values",
            required_params=["column"],
            optional_params=["method"],
            example_params={"column": "email", "method": "HASH"},
        ),
        "HashComputer": ProcessorInfo(
            name="HashComputer",
            category="Computed Columns",
            description="Compute hash of column values",
            required_params=["column"],
            optional_params=["algorithm", "outputColumn"],
            example_params={"column": "id", "algorithm": "SHA256"},
        ),
        "UUIDGenerator": ProcessorInfo(
            name="UUIDGenerator",
            category="Computed Columns",
            description="Generate UUID for each row",
            required_params=["outputColumn"],
            optional_params=["version"],
            example_params={"outputColumn": "row_id", "version": 4},
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
        "FlagOnFormula": ProcessorInfo(
            name="FlagOnFormula",
            category="Flagging",
            description="Create boolean flag based on a formula",
            required_params=["formula", "outputColumn"],
            optional_params=[],
            example_params={
                "formula": "age >= 18",
                "outputColumn": "is_adult",
            },
        ),
        "FlagOnBadType": ProcessorInfo(
            name="FlagOnBadType",
            category="Flagging",
            description="Flag rows with invalid type values",
            required_params=["column", "expectedType", "outputColumn"],
            optional_params=[],
            example_params={
                "column": "age",
                "expectedType": "integer",
                "outputColumn": "bad_age",
            },
        ),
        "FlagOnDateRange": ProcessorInfo(
            name="FlagOnDateRange",
            category="Flagging",
            description="Flag rows based on date range",
            required_params=["column", "outputColumn"],
            optional_params=["startDate", "endDate"],
            example_params={
                "column": "date",
                "outputColumn": "in_range",
                "startDate": "2024-01-01",
            },
        ),
        "FlagOnNumericRange": ProcessorInfo(
            name="FlagOnNumericRange",
            category="Flagging",
            description="Flag rows based on numeric range",
            required_params=["column", "outputColumn"],
            optional_params=["min", "max"],
            example_params={
                "column": "score",
                "outputColumn": "in_range",
                "min": 0,
                "max": 100,
            },
        ),
        # Categorical
        "LongTailGrouper": ProcessorInfo(
            name="LongTailGrouper",
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
        "CategoricalEncoder": ProcessorInfo(
            name="CategoricalEncoder",
            category="Categorical",
            description="Encode categorical values",
            required_params=["column", "encoding"],
            optional_params=["outputColumn"],
            example_params={"column": "color", "encoding": "ONE_HOT"},
        ),
        # Note: OneHotEncoder, LabelEncoder, OrdinalEncoder, TargetEncoder,
        # LeaveOneOutEncoder, WOEEncoder, FeatureHasher are NOT real DSS
        # Prepare processors — they are sklearn names. ProcessorType aliases
        # them all to CategoricalEncoder. Specify the encoding mode via the
        # processor's "encoding" param (ONE_HOT, ORDINAL, etc.).
        # Geographic
        "GeoPointCreator": ProcessorInfo(
            name="GeoPointCreator",
            category="Geographic",
            description="Create geographic point from lat/lon columns",
            required_params=["latColumn", "lonColumn"],
            optional_params=["outputColumn"],
            example_params={
                "latColumn": "latitude",
                "lonColumn": "longitude",
                "outputColumn": "geo_point",
            },
        ),
        "GeoEncoder": ProcessorInfo(
            name="GeoEncoder",
            category="Geographic",
            description="Geocode addresses to coordinates",
            required_params=["addressColumn"],
            optional_params=["outputColumn", "provider"],
            example_params={"addressColumn": "address"},
        ),
        "GeoIPResolver": ProcessorInfo(
            name="GeoIPResolver",
            category="Geographic",
            description="Resolve IP addresses to geographic locations",
            required_params=["column"],
            optional_params=["extractComponents"],
            example_params={"column": "ip_address"},
        ),
        "GeoDistanceCalculator": ProcessorInfo(
            name="GeoDistanceCalculator",
            category="Geographic",
            description="Calculate distance between two geographic points",
            required_params=["point1Column", "point2Column"],
            optional_params=["outputColumn", "unit"],
            example_params={
                "point1Column": "origin",
                "point2Column": "destination",
                "unit": "KILOMETER",
            },
        ),
        "GeoPolygonMatcher": ProcessorInfo(
            name="GeoPolygonMatcher",
            category="Geographic",
            description="Match points to polygons/zones",
            required_params=["pointColumn", "polygonColumn"],
            optional_params=["outputColumn"],
            example_params={
                "pointColumn": "location",
                "polygonColumn": "zone",
            },
        ),
        "AddressParser": ProcessorInfo(
            name="AddressParser",
            category="Geographic",
            description="Parse address strings into components",
            required_params=["column"],
            optional_params=["extractComponents"],
            example_params={"column": "address"},
        ),
        "ReverseGeocoder": ProcessorInfo(
            name="ReverseGeocoder",
            category="Geographic",
            description="Convert coordinates to addresses",
            required_params=["latColumn", "lonColumn"],
            optional_params=["outputColumn"],
            example_params={
                "latColumn": "latitude",
                "lonColumn": "longitude",
            },
        ),
        # Conditional logic
        "IfThenElse": ProcessorInfo(
            name="IfThenElse",
            category="Conditional Logic",
            description="Apply if-then-else conditional value assignment",
            # Lib historically modelled the single-branch flat shape
            # (column / condition / thenValue / elseValue). DSS docs describe
            # a richer multi-branch shape (outputColumn + rules:[{condition,
            # value}, ...]). We accept 'rules' here so the catalog metadata
            # covers both shapes; the round-trip preserves whichever shape
            # comes in via the free-form params dict.
            required_params=["column", "condition", "thenValue", "elseValue"],
            optional_params=["outputColumn", "rules"],
            example_params={
                "column": "age",
                "condition": "val >= 18",
                "thenValue": "adult",
                "elseValue": "minor",
                "outputColumn": "age_group",
            },
        ),
        "SwitchCase": ProcessorInfo(
            name="SwitchCase",
            category="Conditional Logic",
            description="Multi-branch conditional logic (switch/case)",
            required_params=["column", "cases"],
            optional_params=["defaultValue", "outputColumn"],
            example_params={
                "column": "status",
                "cases": [
                    {"value": "A", "output": "Active"},
                    {"value": "I", "output": "Inactive"},
                ],
                "defaultValue": "Unknown",
            },
        ),
        # Value translation
        "TranslateValues": ProcessorInfo(
            name="TranslateValues",
            category="Value Manipulation",
            description="Map/translate values using a lookup table",
            # Doc-canonical wire field is 'mappings'; lib historically used
            # 'translations'. Both spellings are accepted; the inner shape
            # ({from, to}) is identical.
            required_params=["column", "translations"],
            optional_params=["outputColumn", "mappings"],
            example_params={
                "column": "code",
                "translations": [
                    {"from": "US", "to": "United States"},
                    {"from": "UK", "to": "United Kingdom"},
                ],
            },
        ),
        # Data extraction
        "ExtractWithJSONPath": ProcessorInfo(
            name="ExtractWithJSONPath",
            category="Data Extraction",
            description="Extract values from JSON using JSONPath expressions",
            required_params=["column", "jsonPath"],
            optional_params=["outputColumn"],
            example_params={
                "column": "json_data",
                "jsonPath": "$.user.name",
                "outputColumn": "user_name",
            },
        ),
        "SplitURL": ProcessorInfo(
            name="SplitURL",
            category="Data Extraction",
            description="Split URL into components",
            required_params=["column"],
            optional_params=["extractComponents"],
            example_params={
                "column": "url",
                "extractComponents": ["scheme", "host", "path", "query"],
            },
        ),
        # Reshaping
        "FoldMultipleColumns": ProcessorInfo(
            name="FoldMultipleColumns",
            category="Reshaping",
            description="Fold (melt/unpivot) multiple columns into rows",
            # Doc-canonical wire names are 'varColumnOutput' / 'valColumnOutput'.
            # Lib historically tracked them as 'varName' / 'valueName'. Both
            # spellings are accepted via the free-form params dict.
            required_params=["columns"],
            optional_params=[
                "varName", "valueName", "varColumnOutput", "valColumnOutput",
            ],
            example_params={
                "columns": ["q1", "q2", "q3", "q4"],
                "varColumnOutput": "quarter",
                "valColumnOutput": "revenue",
            },
        ),
        "TransposeRowsToColumns": ProcessorInfo(
            name="TransposeRowsToColumns",
            category="Reshaping",
            description="Transpose rows to columns",
            required_params=[],
            optional_params=[],
            example_params={},
        ),
        "Unfold": ProcessorInfo(
            name="Unfold",
            category="Reshaping",
            description="Unfold (explode) list-like column into multiple rows",
            required_params=["column"],
            optional_params=[],
            example_params={"column": "tags"},
        ),
        # Value manipulation
        "Coalesce": ProcessorInfo(
            name="Coalesce",
            category="Value Manipulation",
            description="Return the first non-null value from multiple columns",
            required_params=["columns"],
            optional_params=["outputColumn"],
            example_params={
                "columns": ["phone_home", "phone_work", "phone_mobile"],
                "outputColumn": "phone",
            },
        ),
        "FillColumn": ProcessorInfo(
            name="FillColumn",
            category="Value Manipulation",
            description="Fill an entire column with a constant value",
            required_params=["column", "value"],
            optional_params=[],
            example_params={"column": "source", "value": "batch_import"},
        ),
        # Array/JSON operations
        "ArraySplitter": ProcessorInfo(
            name="ArraySplitter",
            category="Array/JSON",
            description="Split array into separate columns",
            required_params=["column"],
            optional_params=["separator"],
            example_params={"column": "tags"},
        ),
        "ArrayJoiner": ProcessorInfo(
            name="ArrayJoiner",
            category="Array/JSON",
            description="Join array elements into a string",
            required_params=["column"],
            optional_params=["separator", "outputColumn"],
            example_params={"column": "tags", "separator": ","},
        ),
        "ArraySorter": ProcessorInfo(
            name="ArraySorter",
            category="Array/JSON",
            description="Sort array elements",
            required_params=["column"],
            optional_params=["order"],
            example_params={"column": "scores", "order": "ASC"},
        ),
        "ArrayUnfold": ProcessorInfo(
            name="ArrayUnfold",
            category="Array/JSON",
            description="Unfold array into separate rows",
            required_params=["column"],
            optional_params=[],
            example_params={"column": "items"},
        ),
        "ArrayFold": ProcessorInfo(
            name="ArrayFold",
            category="Array/JSON",
            description="Fold values into an array",
            required_params=["columns"],
            optional_params=["outputColumn"],
            example_params={"columns": ["tag1", "tag2", "tag3"]},
        ),
        "ArrayElementExtractor": ProcessorInfo(
            name="ArrayElementExtractor",
            category="Array/JSON",
            description="Extract specific element from array",
            required_params=["column", "index"],
            optional_params=["outputColumn"],
            example_params={"column": "items", "index": 0},
        ),
        "JSONFlattener": ProcessorInfo(
            name="JSONFlattener",
            category="Array/JSON",
            description="Flatten JSON objects into columns",
            required_params=["column"],
            optional_params=["depth", "separator"],
            example_params={"column": "json_data", "separator": "_"},
        ),
        "JSONExtractor": ProcessorInfo(
            name="JSONExtractor",
            category="Array/JSON",
            description="Extract specific keys from JSON",
            required_params=["column", "keys"],
            optional_params=[],
            example_params={"column": "json_data", "keys": ["name", "email"]},
        ),
        "XMLExtractor": ProcessorInfo(
            name="XMLExtractor",
            category="Array/JSON",
            description="Extract values from XML using XPath",
            required_params=["column", "xpath"],
            optional_params=["outputColumn"],
            example_params={"column": "xml_data", "xpath": "//name/text()"},
        ),
        # Nested/Group processors
        "NestedProcessor": ProcessorInfo(
            name="NestedProcessor",
            category="Advanced",
            description="Apply a processor within nested/grouped context",
            required_params=["processor"],
            optional_params=["groupColumn"],
            example_params={"processor": "StringTransformer", "groupColumn": "category"},
        ),
        "ProcessorGroup": ProcessorInfo(
            name="ProcessorGroup",
            category="Advanced",
            description="Group multiple processors into a single logical step",
            required_params=["steps"],
            optional_params=["name"],
            example_params={"steps": [], "name": "Cleaning group"},
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
    def list_processors(cls, category: Optional[str] = None) -> list[str]:
        """List all processor names, optionally filtered by category."""
        if category:
            return [
                name
                for name, info in cls.PROCESSORS.items()
                if info.category == category
            ]
        return list(cls.PROCESSORS.keys())

    @classmethod
    def list_categories(cls) -> list[str]:
        """List all processor categories."""
        return sorted({info.category for info in cls.PROCESSORS.values()})

    @classmethod
    def get_required_params(cls, name: str) -> list[str]:
        """Get required parameters for a processor."""
        info = cls.PROCESSORS.get(name)
        return info.required_params if info else []

    @classmethod
    def get_example(cls, name: str) -> dict[str, Any]:
        """Get example parameters for a processor."""
        info = cls.PROCESSORS.get(name)
        return info.example_params if info else {}
