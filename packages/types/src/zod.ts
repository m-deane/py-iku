// AUTO-GENERATED — do not edit. Run `pnpm codegen`
// Zod runtime schemas generated from /openapi.json components.schemas

import { z } from "zod";

export const ConvertModeSchema = z.enum(["rule", "llm"]);
export type ConvertMode = z.infer<typeof ConvertModeSchema>;

export const DatasetConnectionTypeEnumSchema = z.enum(["Filesystem", "PostgreSQL", "MySQL", "BigQuery", "Snowflake", "Redshift", "S3", "GCS", "Azure", "HDFS", "ManagedFolder", "MongoDB", "Elasticsearch"]);
export type DatasetConnectionTypeEnum = z.infer<typeof DatasetConnectionTypeEnumSchema>;

export const DatasetTypeEnumSchema = z.enum(["input", "intermediate", "output"]);
export type DatasetTypeEnum = z.infer<typeof DatasetTypeEnumSchema>;

export const ProcessorTypeEnumSchema = z.enum(["ColumnRenamer", "ColumnCopier", "ColumnsSelector", "ColumnReorder", "ColumnsConcat", "FillEmptyWithValue", "RemoveRowsOnEmpty", "UpDownFill", "FillEmptyWithComputedValue", "ImputeWithML", "StringTransformer", "Tokenizer", "PatternExtract", "FindReplace", "ColumnsSplitter", "HtmlStripper", "MultiColumnFindReplace", "Ngrammer", "SimplifyText", "StemText", "LemmatizeText", "LanguageDetector", "SentimentAnalyzer", "TextHasher", "UnicodeNormalizer", "URLParser", "IPAddressParser", "EmailDomainExtractor", "PhoneFormatter", "CountryNormalizer", "UserAgentParser", "NumericalTransformer", "Round", "NumberClipping", "Binner", "MeasureNormalize", "TypeSetter", "DateParser", "DateFormatter", "DateComponentExtractor", "DateDifference", "HolidaysComputer", "TimezoneConverter", "DateRangeClassifier", "TimestampExtractor", "FilterOnValue", "FilterOnBadType", "FilterOnFormula", "FilterOnDateRange", "FilterOnNumericRange", "FilterOnMultipleValues", "FilterOnNullNumeric", "FilterOnGeoZone", "FilterOnCustomCondition", "FlagOnValue", "FlagOnFormula", "FlagOnBadType", "FlagOnDateRange", "FlagOnNumericRange", "RemoveDuplicates", "SortRows", "SampleRows", "ShuffleRows", "CreateColumnWithGREL", "Formula", "MultiColumnFormula", "ColumnPseudoAnonymizer", "HashComputer", "UUIDGenerator", "LongTailGrouper", "CategoricalEncoder", "GeoPointCreator", "GeoEncoder", "GeoIPResolver", "GeoDistanceCalculator", "GeoPolygonMatcher", "AddressParser", "ReverseGeocoder", "IfThenElse", "SwitchCase", "TranslateValues", "ExtractWithJSONPath", "SplitURL", "FoldMultipleColumns", "TransposeRowsToColumns", "Unfold", "Coalesce", "FillColumn", "ArraySplitter", "ArrayJoiner", "ArraySorter", "ArrayUnfold", "ArrayFold", "ArrayElementExtractor", "JSONFlattener", "JSONExtractor", "XMLExtractor", "NestedProcessor", "ProcessorGroup", "PythonUDF"]);
export type ProcessorTypeEnum = z.infer<typeof ProcessorTypeEnumSchema>;

export const RecipeTypeEnumSchema = z.enum(["prepare", "sync", "grouping", "window", "join", "fuzzyjoin", "geojoin", "stack", "split", "sort", "distinct", "topn", "pivot", "sampling", "download", "generate_features", "generate_statistics", "push_to_editable", "list_folder_contents", "dynamic_repeat", "extract_failed_rows", "upsert", "list_access", "python", "r", "sql_script", "hive", "impala", "spark_sql_query", "pyspark", "spark_scala", "sparkr", "shell", "prediction_scoring", "clustering_scoring", "standalone_evaluation", "ai_assistant_generate"]);
export type RecipeTypeEnum = z.infer<typeof RecipeTypeEnumSchema>;

export const PrepareStepModelSchema = z.object({
  "metaType": z.string(),
  "type": z.string(),
  "disabled": z.boolean(),
  "params": z.record(z.string(), z.unknown()).optional(),
  "name": z.string().nullable().optional()
}).passthrough();
export type PrepareStepModel = z.infer<typeof PrepareStepModelSchema>;

export const PrepareSettingsModelSchema = z.object({
  "kind": z.enum(["prepare"]),
  "steps": z.array(PrepareStepModelSchema).optional(),
  "step_count": z.number()
}).passthrough();
export type PrepareSettingsModel = z.infer<typeof PrepareSettingsModelSchema>;

export const GroupingSettingsModelSchema = z.object({
  "kind": z.enum(["grouping"]),
  "keys": z.array(z.string()).optional(),
  "aggregations": z.array(z.record(z.string(), z.unknown())).optional()
}).passthrough();
export type GroupingSettingsModel = z.infer<typeof GroupingSettingsModelSchema>;

export const JoinSettingsModelSchema = z.object({
  "kind": z.enum(["join"]),
  "join_type": z.string(),
  "join_keys": z.array(z.record(z.string(), z.unknown())).optional(),
  "selected_columns": z.record(z.string(), z.unknown()).nullable().optional()
}).passthrough();
export type JoinSettingsModel = z.infer<typeof JoinSettingsModelSchema>;

export const WindowSettingsModelSchema = z.object({
  "kind": z.enum(["window"]),
  "partitionColumns": z.array(z.record(z.string(), z.unknown())).optional(),
  "orderColumns": z.array(z.record(z.string(), z.unknown())).optional(),
  "aggregations": z.array(z.record(z.string(), z.unknown())).optional()
}).passthrough();
export type WindowSettingsModel = z.infer<typeof WindowSettingsModelSchema>;

export const SamplingSettingsModelSchema = z.object({
  "kind": z.enum(["sampling"]),
  "samplingMethod": z.string(),
  "sampleSize": z.number().nullable().optional()
}).passthrough();
export type SamplingSettingsModel = z.infer<typeof SamplingSettingsModelSchema>;

export const SplitSettingsModelSchema = z.object({
  "kind": z.enum(["split"]),
  "splitMode": z.string(),
  "condition": z.string()
}).passthrough();
export type SplitSettingsModel = z.infer<typeof SplitSettingsModelSchema>;

export const SortSettingsModelSchema = z.object({
  "kind": z.enum(["sort"]),
  "sortColumns": z.array(z.record(z.string(), z.unknown())).optional()
}).passthrough();
export type SortSettingsModel = z.infer<typeof SortSettingsModelSchema>;

export const TopNSettingsModelSchema = z.object({
  "kind": z.enum(["topn"]),
  "topN": z.number(),
  "rankingColumn": z.string().nullable().optional()
}).passthrough();
export type TopNSettingsModel = z.infer<typeof TopNSettingsModelSchema>;

export const DistinctSettingsModelSchema = z.object({
  "kind": z.enum(["distinct"]),
  "computeCount": z.boolean()
}).passthrough();
export type DistinctSettingsModel = z.infer<typeof DistinctSettingsModelSchema>;

export const StackSettingsModelSchema = z.object({
  "kind": z.enum(["stack"]),
  "mode": z.string()
}).passthrough();
export type StackSettingsModel = z.infer<typeof StackSettingsModelSchema>;

export const PythonSettingsModelSchema = z.object({
  "kind": z.enum(["python"]),
  "code": z.string()
}).passthrough();
export type PythonSettingsModel = z.infer<typeof PythonSettingsModelSchema>;

export const PivotSettingsModelSchema = z.object({
  "kind": z.enum(["pivot"]),
  "rowColumns": z.array(z.string()).optional(),
  "columnColumn": z.string(),
  "valueColumn": z.string(),
  "aggregation": z.string()
}).passthrough();
export type PivotSettingsModel = z.infer<typeof PivotSettingsModelSchema>;

export const RecipeSettingsModelSchema = z.discriminatedUnion("kind", [
  PrepareSettingsModelSchema,
  GroupingSettingsModelSchema,
  JoinSettingsModelSchema,
  WindowSettingsModelSchema,
  SamplingSettingsModelSchema,
  SplitSettingsModelSchema,
  SortSettingsModelSchema,
  TopNSettingsModelSchema,
  DistinctSettingsModelSchema,
  StackSettingsModelSchema,
  PythonSettingsModelSchema,
  PivotSettingsModelSchema
]);
export type RecipeSettingsModel = z.infer<typeof RecipeSettingsModelSchema>;

export const ColumnSchemaModelSchema = z.object({
  "name": z.string(),
  "type": z.string(),
  "nullable": z.boolean(),
  "default": z.unknown().optional(),
  "format": z.string().nullable().optional()
}).passthrough();
export type ColumnSchemaModel = z.infer<typeof ColumnSchemaModelSchema>;

export const ComplexityScoreSchema = z.object({
  "recipe_count": z.number(),
  "processor_count": z.number(),
  "dataset_count": z.number(),
  "max_depth": z.number(),
  "fan_out_max": z.number(),
  "complexity": z.number(),
  "cost_estimate": z.number().nullable().optional()
}).passthrough();
export type ComplexityScore = z.infer<typeof ComplexityScoreSchema>;

export const ConvertOptionsSchema = z.object({
  "provider": z.enum(["anthropic", "openai"]).nullable().optional(),
  "model": z.string().nullable().optional(),
  "temperature": z.number().nullable().optional(),
  "optimize": z.boolean(),
  "max_code_size_bytes": z.number()
}).passthrough();
export type ConvertOptions = z.infer<typeof ConvertOptionsSchema>;

export const ConvertRequestSchema = z.object({
  "code": z.string(),
  "mode": ConvertModeSchema,
  "options": ConvertOptionsSchema.nullable().optional()
}).passthrough();
export type ConvertRequest = z.infer<typeof ConvertRequestSchema>;

export const DataikuDatasetModelSchema = z.object({
  "name": z.string(),
  "type": DatasetTypeEnumSchema,
  "connection_type": DatasetConnectionTypeEnumSchema,
  "schema": z.array(ColumnSchemaModelSchema).optional(),
  "source_variable": z.string().nullable().optional(),
  "source_line": z.number().nullable().optional(),
  "notes": z.array(z.string()).optional()
}).passthrough();
export type DataikuDatasetModel = z.infer<typeof DataikuDatasetModelSchema>;

export const DataikuRecipeModelOutputSchema = z.object({
  "name": z.string(),
  "type": RecipeTypeEnumSchema,
  "inputs": z.array(z.string()).optional(),
  "outputs": z.array(z.string()).optional(),
  "source_lines": z.array(z.number()).optional(),
  "notes": z.array(z.string()).optional(),
  "confidence": z.number().nullable().optional(),
  "reasoning": z.string().nullable().optional(),
  "settings": z.discriminatedUnion("kind", [
      PrepareSettingsModelSchema,
      GroupingSettingsModelSchema,
      JoinSettingsModelSchema,
      WindowSettingsModelSchema,
      SamplingSettingsModelSchema,
      SplitSettingsModelSchema,
      SortSettingsModelSchema,
      TopNSettingsModelSchema,
      DistinctSettingsModelSchema,
      StackSettingsModelSchema,
      PythonSettingsModelSchema,
      PivotSettingsModelSchema
    ]).nullable().optional()
}).passthrough();
export type DataikuRecipeModelOutput = z.infer<typeof DataikuRecipeModelOutputSchema>;

export const FlowRecommendationModelSchema = z.object({
  "type": z.string(),
  "priority": z.string(),
  "message": z.string(),
  "impact": z.string().nullable().optional(),
  "action": z.string().nullable().optional(),
  "source_lines": z.array(z.number()).optional()
}).passthrough();
export type FlowRecommendationModel = z.infer<typeof FlowRecommendationModelSchema>;

export const FlowZoneModelSchema = z.object({
  "name": z.string(),
  "color": z.string(),
  "datasets": z.array(z.string()).optional(),
  "recipes": z.array(z.string()).optional()
}).passthrough();
export type FlowZoneModel = z.infer<typeof FlowZoneModelSchema>;

export const DataikuFlowModelOutputSchema = z.object({
  "flow_name": z.string(),
  "generated_from": z.string().nullable().optional(),
  "generation_timestamp": z.string().nullable().optional(),
  "total_recipes": z.number(),
  "total_datasets": z.number(),
  "datasets": z.array(DataikuDatasetModelSchema).optional(),
  "recipes": z.array(DataikuRecipeModelOutputSchema).optional(),
  "optimization_notes": z.array(z.string()).optional(),
  "recommendations": z.array(FlowRecommendationModelSchema).optional(),
  "zones": z.array(FlowZoneModelSchema).optional()
}).passthrough();
export type DataikuFlowModelOutput = z.infer<typeof DataikuFlowModelOutputSchema>;

export const ConvertResponseSchema = z.object({
  "flow": DataikuFlowModelOutputSchema,
  "score": ComplexityScoreSchema,
  "warnings": z.array(z.string()).optional()
}).passthrough();
export type ConvertResponse = z.infer<typeof ConvertResponseSchema>;

export const CreatedFlowResponseSchema = z.object({
  "id": z.string(),
  "created_at": z.string()
}).passthrough();
export type CreatedFlowResponse = z.infer<typeof CreatedFlowResponseSchema>;

export const DataikuRecipeModelInputSchema = z.object({
  "name": z.string(),
  "type": RecipeTypeEnumSchema,
  "inputs": z.array(z.string()).optional(),
  "outputs": z.array(z.string()).optional(),
  "source_lines": z.array(z.number()).optional(),
  "notes": z.array(z.string()).optional(),
  "confidence": z.number().nullable().optional(),
  "reasoning": z.string().nullable().optional(),
  "settings": z.discriminatedUnion("kind", [
      PrepareSettingsModelSchema,
      GroupingSettingsModelSchema,
      JoinSettingsModelSchema,
      WindowSettingsModelSchema,
      SamplingSettingsModelSchema,
      SplitSettingsModelSchema,
      SortSettingsModelSchema,
      TopNSettingsModelSchema,
      DistinctSettingsModelSchema,
      StackSettingsModelSchema,
      PythonSettingsModelSchema,
      PivotSettingsModelSchema
    ]).nullable().optional()
}).passthrough();
export type DataikuRecipeModelInput = z.infer<typeof DataikuRecipeModelInputSchema>;

export const DataikuFlowModelInputSchema = z.object({
  "flow_name": z.string(),
  "generated_from": z.string().nullable().optional(),
  "generation_timestamp": z.string().nullable().optional(),
  "total_recipes": z.number(),
  "total_datasets": z.number(),
  "datasets": z.array(DataikuDatasetModelSchema).optional(),
  "recipes": z.array(DataikuRecipeModelInputSchema).optional(),
  "optimization_notes": z.array(z.string()).optional(),
  "recommendations": z.array(FlowRecommendationModelSchema).optional(),
  "zones": z.array(FlowZoneModelSchema).optional()
}).passthrough();
export type DataikuFlowModelInput = z.infer<typeof DataikuFlowModelInputSchema>;

export const ValidationErrorSchema = z.object({
  "loc": z.array(z.union([
      z.string(),
      z.number()
    ])),
  "msg": z.string(),
  "type": z.string(),
  "input": z.unknown().optional(),
  "ctx": z.record(z.string(), z.unknown()).optional()
}).passthrough();
export type ValidationError = z.infer<typeof ValidationErrorSchema>;

export const HTTPValidationErrorSchema = z.object({
  "detail": z.array(ValidationErrorSchema).optional()
}).passthrough();
export type HTTPValidationError = z.infer<typeof HTTPValidationErrorSchema>;

export const HealthResponseSchema = z.object({
  "status": z.string(),
  "version": z.string(),
  "py_iku_version": z.string()
}).passthrough();
export type HealthResponse = z.infer<typeof HealthResponseSchema>;

export const ProcessorCatalogEntrySchema = z.object({
  "type": z.union([
      ProcessorTypeEnumSchema,
      z.string()
    ]),
  "name": z.string(),
  "category": z.string(),
  "description": z.string(),
  "required_params": z.array(z.string()).optional(),
  "optional_params": z.array(z.string()).optional(),
  "examples": z.record(z.string(), z.unknown()).optional()
}).passthrough();
export type ProcessorCatalogEntry = z.infer<typeof ProcessorCatalogEntrySchema>;

export const RecipeCatalogEntrySchema = z.object({
  "type": RecipeTypeEnumSchema,
  "name": z.string(),
  "category": z.string(),
  "icon": z.string(),
  "description": z.string(),
  "pandas_examples": z.array(z.string()).optional()
}).passthrough();
export type RecipeCatalogEntry = z.infer<typeof RecipeCatalogEntrySchema>;

export const SaveFlowRequestSchema = z.object({
  "flow": DataikuFlowModelInputSchema,
  "name": z.string(),
  "tags": z.array(z.string()).optional()
}).passthrough();
export type SaveFlowRequest = z.infer<typeof SaveFlowRequestSchema>;

export const SavedFlowResponseSchema = z.object({
  "id": z.string(),
  "name": z.string(),
  "flow": DataikuFlowModelOutputSchema,
  "created_at": z.string(),
  "updated_at": z.string(),
  "tags": z.array(z.string()).optional()
}).passthrough();
export type SavedFlowResponse = z.infer<typeof SavedFlowResponseSchema>;

export const UpdateFlowRequestSchema = z.object({
  "flow": DataikuFlowModelInputSchema.nullable().optional(),
  "name": z.string().nullable().optional(),
  "tags": z.array(z.string()).nullable().optional()
}).passthrough();
export type UpdateFlowRequest = z.infer<typeof UpdateFlowRequestSchema>;

export const VersionResponseSchema = z.object({
  "api_version": z.string(),
  "py_iku_version": z.string(),
  "commit": z.string().nullable(),
  "commit_message": z.string(),
  "source": z.string()
}).passthrough();
export type VersionResponse = z.infer<typeof VersionResponseSchema>;

export const DataikuFlowModelSchema = DataikuFlowModelOutputSchema;
export type DataikuFlowModel = z.infer<typeof DataikuFlowModelSchema>;

export const DataikuRecipeModelSchema = DataikuRecipeModelOutputSchema;
export type DataikuRecipeModel = z.infer<typeof DataikuRecipeModelSchema>;
