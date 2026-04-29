# Cross-check findings: py-iku ↔ Dataiku public docs (2026-04-29)

Snapshot: `docs/dataiku-reference/` (14 recipes, 95 processors, 7 settings) vs
inventory: `docs/dataiku-reference/_inventory.json` (37 RecipeTypes, 100 canonical
ProcessorTypes / 122 with aliases / 101 catalog entries, 12 RecipeSettings,
21 canonical AggregationFunctions, 16 PROCESSOR_MAPPINGS, 21 RECIPE_MAPPINGS).

## Headline counts

- Recipes covered (doc ↔ lib enum match): **14 / 14** (all 14 doc snapshots map cleanly to a `RecipeType`)
- Recipes lacking a dedicated `RecipeSettings` subclass (despite a doc page that
  enumerates real per-recipe knobs): **4** — `SYNC`, `FUZZY_JOIN`, `GEO_JOIN`,
  `GENERATE_STATISTICS`. (Confirms Agent B's flag.)
- Processors covered (doc ↔ lib catalog, by concept): **56 / 95**. 39 doc
  processors have **no** library catalog entry (~41 % gap).
- Library catalog entries with **no** matching doc snapshot: **44 / 100** —
  many of these are real DSS processors with non-public-doc names, but several
  appear to be invented (notably `FilterOnCustomCondition`,
  `FilterOnGeoZone`, `DateRangeClassifier`, `TimezoneConverter`,
  `TimestampExtractor` reverse direction, `ImputeWithML`, several Geo*
  variants, `LemmatizeText` / `StemText`, `SentimentAnalyzer`, `LanguageDetector`).
- Settings drift instances (settings doc page enumerates a knob the matching
  `RecipeSettings` does not carry): **3** — see by-category section.
- Pandas-mapping inconsistencies / suspect dispatches: **2** (low — mappings
  are largely sane).
- Aggregation-function drift: **0** (the 21 canonical + 4 phantom alias
  members in the inventory exactly match the doc-implied pandas → DSS shape,
  which is documented obliquely in the GROUPING recipe page).

## Top 10 prioritized findings

1. **[blocker] `unixtimestamp-parser` direction mismatch.** The DSS doc
   (`docs/dataiku-reference/processors/unixtimestamp-parser.md:7-15`) describes
   a UNIX-timestamp → ISO-8601 string converter. The library exposes
   `TIMESTAMP_EXTRACTOR` (`py2dataiku/models/prepare_step.py:96`,
   catalog `TimestampExtractor` at
   `py2dataiku/mappings/processor_catalog.py:442-449`) which goes the OTHER
   direction (date → unix ms). The actual DSS `UnixTimestampParser` processor
   is missing from the lib. Fix: add a new `UNIX_TIMESTAMP_PARSER` enum +
   catalog entry; keep `TimestampExtractor` (it is also a real DSS processor,
   but addresses the inverse problem).

2. **[blocker] `column-pseudonymization` parameter set incomplete.** Doc
   (`docs/dataiku-reference/processors/column-pseudonymization.md:23-31`)
   enumerates 4 inputs: column(s), hashing algorithm (`SHA-256`/`SHA-512`/`MD5`),
   pepper (static), salt column. Lib catalog
   (`py2dataiku/mappings/processor_catalog.py` `ColumnPseudoAnonymizer`
   block, ~line 600, inventory line 1581-1588) only declares
   `column` (req) + `method` (opt). Both `pepper` and `salt`/`saltColumn`
   are missing, and the param is named `method` rather than something
   matching the DSS UI (`algorithm`). Fix: add `algorithm`, `pepper`,
   `saltColumn` params; verify camelCase against an exported DSS recipe JSON.

3. **[blocker] `email-split` modeled as domain-only extractor.** Doc
   (`docs/dataiku-reference/processors/email-split.md:9-17`) splits the input
   into BOTH local part and domain (two output columns). Lib has
   `EMAIL_DOMAIN_EXTRACTOR` (`prepare_step.py:55`, catalog at
   inventory line 843-857) which only emits the domain. The actual DSS
   processor is `EmailSplitter`. Fix: rename canonical to `EmailSplitter`
   with `outputLocalPartColumn` and `outputDomainColumn` params (the existing
   `EMAIL_DOMAIN_EXTRACTOR` enum can stay as a phantom alias for back-compat).

4. **[important] `move-columns` is not the same as `ColumnReorder`.** Doc
   (`docs/dataiku-reference/processors/move-columns.md:9`) describes
   relative move (before/after a column, or to begin/end). Lib's
   `COLUMN_REORDER` (`prepare_step.py`, catalog inventory line 417-428)
   takes only a `columns` list — i.e. it implements full reorder, not
   relative move. This is a real DSS processor missing from the lib. Fix:
   add `MoveColumns` to the catalog with params
   `columns` (req), `target` (column ref or `BEGIN`/`END`), `position`
   (`BEFORE` / `AFTER`).

5. **[important] `RemoveDuplicates` row-level processor exists in lib but
   the doc page documents only the `DISTINCT` recipe.** Inventory line
   1457-1469 lists `RemoveDuplicates` as a Prepare processor (catalog
   includes it), `prepare_step.py:117`. There is no matching doc snapshot
   under `processors/`, only the recipe doc
   (`docs/dataiku-reference/recipes/distinct.md`). DSS does not actually
   ship a row-level "remove duplicates" Prepare processor — duplicate
   removal is a recipe. This catalog entry is likely spurious (and
   misleading for the LLM path). Either delete from catalog or document it
   as DSS-internal and unlikely to round-trip.

6. **[important] Doc-only processors (39 missing from lib).** Group A
   (popular, high-impact, should be added first):
   `currency-converter`, `currency-splitter`, `extract-numbers`,
   `count-matches`, `negate`, `mean` (line-by-line arithmetic mean),
   `move-columns` (also #4), `pivot` (processor-level), `numerical-format-convert`,
   `numerical-combinations`, `querystring-split`, `grok`,
   `unixtimestamp-parser` (also #1), `visitor-id`, `zip-arrays`,
   `triggered-unfold`, `split-fold`, `split-unfold`, `split-into-chunks`,
   `fold-columns-by-pattern`, `fold-object`, `object-nest`, `change-crs`,
   `geopoint-buffer`, `geopoint-extract`, `geo-info-extractor`,
   `filter-on-meaning`, `flag-on-meaning`, `meaning-translate`,
   `invalid-split`, `long-tail` (vs the existing `merge-long-tail-values`),
   `enrich-french-departement`, `enrich-french-postcode`,
   `enrich-with-build-context`, `enrich-with-record-context`,
   `generate-big-data`, `fuzzy-join` (processor; deprecated),
   `geo-join` (processor; deprecated), `join` (processor; deprecated).
   Of these, the deprecated and `enrich-french-*` family can be skipped; the
   ML/RAG/timestamp/currency/numerical group is the meaningful gap.

7. **[important] Lib-only catalog entries with no DSS doc page.** 44 entries
   (see "By category > Processors" below). Specifically suspicious
   (could be invented / misnamed): `FilterOnGeoZone`, `FilterOnCustomCondition`,
   `FilterOnNullNumeric`, `DateRangeClassifier`, `TimezoneConverter` (DSS
   formula territory), `LemmatizeText`/`StemText`/`SentimentAnalyzer`/
   `LanguageDetector` (these are typically in the NLP plugin, not core),
   `PhoneFormatter`, `CountryNormalizer`, `HashComputer` (vs the documented
   `column-pseudonymization`), `ImputeWithML`, `JSONExtractor` (vs the doc'd
   `jsonpath`/`object-unnest-json`), `XMLExtractor`, `NestedProcessor`,
   `ProcessorGroup`, `UUIDGenerator`, `ReverseGeocoder` (the doc has only a
   prose section, not a processor name). Recommendation: audit each against
   an exported DSS recipe JSON; remove or label clearly as
   "non-canonical / SDK-only" so the LLM does not emit them by default.

8. **[important] Settings drift in `SortSettings` / null-value placement.**
   The Sort recipe doc
   (`docs/dataiku-reference/recipes/sort.md:15-17`) explicitly enumerates
   null-value placement (asc → nulls first, desc → nulls last; configurable
   per DSS 4.1+). Lib `SortSettings` (`recipe_settings.py:333-336`) carries
   only `sort_columns: list[dict[str, str]]` — there is no `nulls_first` /
   `nulls_last` toggle. Fix: extend the per-column dict shape (or add a
   top-level `null_handling` field).

9. **[important] Settings drift in `JoinSettings` / unmatched-rows outputs.**
   Join recipe doc
   (`docs/dataiku-reference/recipes/join.md:37-41`) describes per-join
   "Send unmatched rows to other output dataset(s)" plus `LEFT_ANTI` /
   `RIGHT_ANTI` join types and per-join "Post-join computed columns"
   (`join.md:51`). Lib `JoinSettings`
   (`recipe_settings.py:162-167`) carries `join_type`, `join_keys`,
   `selected_columns` only. The lib does correctly enumerate
   `LEFT_ANTI`/`RIGHT_ANTI`/`ADVANCED` in `JoinType` (`dataiku_recipe.py:73-83`)
   so the enum side is fine; the settings shape is what is missing
   (no `unmatched_outputs` field, no `post_join_computed_columns`).

10. **[important] Settings drift in `PivotSettings` / modality controls.**
    Pivot recipe doc
    (`docs/dataiku-reference/recipes/pivot.md:48-74`) enumerates several
    real configuration knobs: modality computation mode
    (`most_frequent` / `min_occurrence_count` / `explicit`), modality
    cleaning (`soft_slugification` / `hard_slugification` / `numbering` /
    `truncation`), `recompute_at_each_run`, plus per-row aggregates
    (the "Other columns" section). Lib `PivotSettings`
    (`recipe_settings.py:463-469`) only carries `row_columns`,
    `column_column`, `value_column`, `aggregation`. None of the modality
    controls are modelled.

## By category

### Recipes

- ✓ Match (14): `prepare`, `sync`, `grouping`, `window`, `join`, `fuzzy-join`,
  `geojoin`, `stack`, `split`, `sort`, `distinct`, `topn`, `pivot`, `sampling`.
- ⚠ Settings drift (4 — settings class missing entirely though doc enumerates
  knobs):
    - `SYNC` (`recipes/sync.md:39-62`): doc enumerates engine choice
      (DSS streaming / Spark / SQL / Hive / Impala / fast-paths), schema
      handling, partition handling. Lib `RecipeType.SYNC`
      (`dataiku_recipe.py:21`) has `settings_class: null`.
    - `FUZZY_JOIN` (`recipes/fuzzy-join.md:33-72`): doc enumerates distance
      metric (Damerau-Levenshtein / Hamming / Jaccard / Cosine / Euclidean /
      Geospatial / strict equality), threshold (absolute / relative %), text
      normalization options, output-matching-details + debug-mode toggles.
      No settings class exists.
    - `GEO_JOIN` (`recipes/geojoin.md:64-77`): doc enumerates 8 spatial
      operators (Contains, IsContained, WithinDistance, BeyondDistance,
      Intersects, Touches, Disjoint, StrictEquality) plus the distance unit
      (Meter, Km, Foot, Yard, Mile, NauticalMile). No settings class.
    - `GENERATE_STATISTICS`: no doc snapshot was captured (it isn't
      under the public `other_recipes/` index), but the recipe is referenced
      from `pandas_mappings` indirectly (via `df.describe()` / `df.info()`
      per CLAUDE.md). Lib has no settings class.
- ✗ Missing in lib (recipes with doc page but no enum): **0**.
- ➕ Extra in lib with no doc page (likely intentional code recipes or
  SDK-internal): `PYTHON`, `R`, `SQL`, `HIVE`, `IMPALA`, `SPARKSQL`, `PYSPARK`,
  `SPARK_SCALA`, `SPARKR`, `SHELL`, `DOWNLOAD`, `GENERATE_FEATURES`,
  `GENERATE_STATISTICS`, `PUSH_TO_EDITABLE`, `LIST_FOLDER_CONTENTS`,
  `DYNAMIC_REPEAT`, `EXTRACT_FAILED_ROWS`, `UPSERT`, `LIST_ACCESS`,
  `PREDICTION_SCORING`, `CLUSTERING_SCORING`, `EVALUATION`,
  `AI_ASSISTANT_GENERATE`. All 23 of these are real DSS recipe values
  (verified by `value=` strings looking like DSS internals); not drift.

### Processors

- ✓ Match (~56): every catalog key whose `canonical_name` corresponds to a
  doc slug, including the heavily-used filter/flag family
  (`FilterOnValue` ↔ `filter-on-value`,
  `FilterOnNumericRange` ↔ `filter-on-range`,
  `FilterOnDateRange` ↔ `filter-on-date`,
  `FilterOnFormula` ↔ `filter-on-formula`,
  same flag pairs), `FoldMultipleColumns` ↔ `fold-columns-by-name`,
  `Round`, `Binner`, `ColumnRenamer`, `ColumnsSelector`,
  `Coalesce`, `IfThenElse`, `SwitchCase`, etc.
- ⚠ Param-name drift (≥70 % confidence):
    - `FilterOnValue` (catalog `matchingMode` example value `"EQUALS"` in
      `processor_catalog.py:451-463`) — DSS doc
      `processors/filter-on-value.md:39-50` enumerates the real values:
      `Complete value` / `Substring` / `Regular expression` (and a
      separate `Normalization mode`: `Exact` / `Lowercase` / `Normalize`).
      The likely canonical wire values are `FULL_STRING` / `SUBSTRING` /
      `PATTERN`, **not** `EQUALS`. Inventory example
      `"matchingMode": "EQUALS"` (line 1197) is almost certainly wrong —
      `EQUALS` isn't on the doc-enumerated set. Also the `matchingMode`
      field doesn't capture normalization mode — that's a separate param
      (probably `normalizationMode`) which is missing entirely.
    - `FindReplace` / `MultiColumnFindReplace` (catalog: `matchMode`
      with example `"LITERAL"` at `processor_catalog.py:141-146` and
      inventory line 602; also for `MultiColumnFindReplace` at
      inventory line 659). Doc
      (`processors/find-replace.md:32-49`) enumerates `Matching mode` =
      `Complete value` / `Substring` / `Regular expression` plus a
      separate `Normalization mode`. (a) field name is probably
      `matchingMode` (consistent with the rest of the family), not
      `matchMode`; (b) `LITERAL` is not on the doc's enumerated set.
      Also `FlagOnValue.matchMode` (inventory line 1366) shares the same
      typo pattern. Fix: rename `matchMode` → `matchingMode` and align
      example values with `FULL_STRING`/`SUBSTRING`/`PATTERN`.
    - `Round` (catalog params `column`, `precision`, `mode` at
      `processor_catalog.py:318-325`; inventory line 939-948). Doc
      (`processors/round.md:22-37`) enumerates two distinct numeric
      controls: `significantDigits` and `decimalPlaces` (and a `mode`
      = round/floor/ceil). The lib collapses both to a single
      `precision`. Fix: split into `significantDigits` and `decimalPlaces`
      (or document which one `precision` represents).
    - `Binner` (inventory line 980-985 has params `column`, `mode`,
      `bins`, `labels` with `mode` example `'FIXED_BINS'`). Doc
      (`processors/binner.md:18-31`) enumerates `Fixed size intervals`
      (with `bin width`, `Minimum value`, `Maximum value`) vs `Custom,
      use raw values`. The doc mentions no `labels` field. Likely
      fields the lib is missing: `binWidth`, `minimumValue`,
      `maximumValue`, `outputColumn`. The `labels` field is plausibly
      synthetic.
    - `Tokenizer` (inventory line 562-571 has `column`, `operation`,
      `pattern` with `operation` example `'SPLIT_WHITESPACE'`). Doc
      doesn't directly enumerate this `operation` value (the snapshot
      describes "tokenize a text column into array, one token per row,
      or one token per column with simplification options" — three
      output modes, not splitting strategies). Field name and value-set
      are likely off.
    - `FillEmptyWithComputedValue` (inventory line 510-517 has `column`,
      `mode` with `mode='MEAN'`). Doc
      (`processors/fill-empty-with-computed-value.md:9`) enumerates
      `mean / median / mode`. The wire value is plausibly an enum
      string, but the field could be named `imputationMode` or just
      `method` (consistent with `ColumnPseudoAnonymizer.method` and
      `ImputeWithML.method`). Worth verifying against an exported
      recipe JSON.
- ✗ Missing in lib (top concrete gaps — see #6 above for full list of 39).
- ➕ Extra in lib with no doc page (44 — see #7 above). Subset
  audit-priority: `FilterOnGeoZone`, `FilterOnCustomCondition`,
  `FilterOnNullNumeric`, `DateRangeClassifier`, `TimezoneConverter`,
  `ImputeWithML`, `JSONExtractor`, `XMLExtractor`, `NestedProcessor`,
  `ProcessorGroup`, `HashComputer`, `LemmatizeText`, `StemText`,
  `SentimentAnalyzer`, `LanguageDetector`, `PhoneFormatter`,
  `CountryNormalizer`, `UUIDGenerator`, `ReverseGeocoder`,
  `MultiColumnFindReplace`, `MultiColumnFormula`. Many are likely real
  but should be flagged in the catalog as "no public DSS doc page —
  verify before emitting from LLM".

### Pandas mappings

- ✓ Sane mappings: 19 of 21 entries in `RECIPE_MAPPINGS`
  (`pandas_mappings.py:22-44`) and 16 / 16 in `PROCESSOR_MAPPINGS`
  (`pandas_mappings.py:47-67`) target a recipe / processor that exists in
  the doc set. The non-obvious mappings called out in `CLAUDE.md` (melt
  → PREPARE+FOLD_MULTIPLE_COLUMNS, df.abs() → CREATE_COLUMN_WITH_GREL,
  cumsum/diff/shift → WINDOW, nlargest → TOP_N, fillna → FILL_EMPTY_WITH_VALUE,
  to_datetime → DATE_PARSER) all check out against the snapshot.
- ⚠ Suspect mappings (low-confidence, worth verifying):
    - `"map" → TRANSLATE_VALUES` (`pandas_mappings.py:58`): pandas
      `Series.map(dict)` does map values, but the doc-confirmed
      `TranslateValues` (inventory line 1849-1864) takes a list of
      `{from, to}` pairs. Behaviourally OK for a literal-dict mapping,
      but `df["x"].map(some_function)` cannot be expressed; the lib
      likely silently drops the function case — flag for the rule-based
      handler tests.
    - `"explode" → UNFOLD` (`pandas_mappings.py:59`): pandas
      `df.explode(col)` produces one row per array element. DSS `Unfold`
      (inventory line 1934-1945) per the snapshot
      (`processors/unfold.md`) is the dummification ("transform values
      of a column into binary columns") processor — not at all the
      same operation. The semantically correct target is `ARRAY_UNFOLD`
      (`processors/unfold-array.md` ≈ DSS `ArrayUnfold`, inventory line
      2034-2047) or possibly `ARRAY_FOLD`. This is a real bug.

### Aggregations

- ✓ Match: the 21 canonical members in `AggregationFunction`
  (`dataiku_recipe.py:114-144`) cover all the aggregations a typical
  GROUPING / WINDOW recipe needs (SUM, AVG, COUNT, COUNTD, MIN, MAX,
  FIRST, LAST, STDDEV, VAR, MEDIAN, MODE, percentiles 25/50/75/90/95/99,
  CONCAT, COLLECT_LIST, COLLECT_SET). The 4 phantom aliases
  (MEAN→AVG, NUNIQUE→COUNTD, STD→STDDEV, VARIANCE→VAR) are intentional
  pandas-compat — not drift.
- ⚠ Drift: none with ≥70 % confidence. The grouping recipe doc
  (`recipes/grouping.md`) does not enumerate the aggregation list
  explicitly (it just says "any aggregation"), so no contradictory
  evidence either way.

## Verdict

The library is **broadly accurate** at the recipe level — every public DSS
recipe doc maps cleanly to a `RecipeType` enum member, and most pandas →
recipe routing decisions are sound. The accuracy story degrades on two
axes: (a) **processor catalog completeness and naming** — about 40 % of
public DSS processors aren't in the catalog at all, while ~25 of the
catalog's "extra" entries don't appear in any public doc and may be
invented; (b) **`RecipeSettings` shape coverage** — only 12 / 37 recipe
types have a settings class, and even where one exists (Pivot, Sort,
Join), it doesn't model documented configuration knobs (modality
controls, null-placement, unmatched-row outputs). Filter-family wire
values (`matchingMode: "EQUALS"`) and the `unixtimestamp-parser` /
`email-split` direction errors are likely to produce broken DSS JSON
on a real round-trip and should be the first fix wave.

The highest-impact follow-up is a catalog audit driven by an exported
real-DSS recipe JSON — that would simultaneously fix the param-name
drift (#1, #2, #3 in the top 10), validate the 44 lib-only entries
(#7), and surface the missing 39 doc-only processors (#6).

## Suggested fixes (mapped to specific files)

- `py2dataiku/models/prepare_step.py:96` — split `TIMESTAMP_EXTRACTOR`
  (date→unix) from a new `UNIX_TIMESTAMP_PARSER` enum (unix→date).
  Add catalog entry per `docs/dataiku-reference/processors/unixtimestamp-parser.md:7-15`.
- `py2dataiku/mappings/processor_catalog.py` `ColumnPseudoAnonymizer`
  block — add `algorithm` (req, enum SHA-256/SHA-512/MD5), `pepper`
  (opt str), `saltColumn` (opt str column ref) per
  `docs/dataiku-reference/processors/column-pseudonymization.md:23-31`.
- `py2dataiku/models/prepare_step.py:55` and corresponding catalog —
  rename `EmailDomainExtractor` to `EmailSplitter`; add
  `outputLocalPartColumn` + `outputDomainColumn` outputs per
  `docs/dataiku-reference/processors/email-split.md:9-17`.
- `py2dataiku/mappings/processor_catalog.py:451-463` (`FilterOnValue`)
  — change `matchingMode` example from `"EQUALS"` to `"FULL_STRING"`
  (or canonical DSS value); add a separate `normalizationMode` param
  per `docs/dataiku-reference/processors/filter-on-value.md:39-58`.
- `py2dataiku/mappings/processor_catalog.py:136-146` (`FindReplace`)
  — rename `matchMode` → `matchingMode`; align example value to one of
  `FULL_STRING`/`SUBSTRING`/`PATTERN` per
  `docs/dataiku-reference/processors/find-replace.md:32-49`. Apply same
  rename to `MultiColumnFindReplace` and `FlagOnValue`.
- `py2dataiku/mappings/processor_catalog.py:318-325` (`Round`) — replace
  the single `precision` param with `significantDigits` and
  `decimalPlaces` per
  `docs/dataiku-reference/processors/round.md:22-37`.
- `py2dataiku/models/recipe_settings.py:333` — extend `SortSettings`
  with `null_handling` field (or per-column `nulls` flag) per
  `docs/dataiku-reference/recipes/sort.md:15-17`.
- `py2dataiku/models/recipe_settings.py:162-167` — extend `JoinSettings`
  with `unmatched_outputs: list[str]` and
  `post_join_computed_columns: list[dict]` per
  `docs/dataiku-reference/recipes/join.md:37-51`.
- `py2dataiku/models/recipe_settings.py:463-469` — extend `PivotSettings`
  with `modality_mode`, `modality_limit`, `name_simplification`,
  `recompute_modalities_each_run`, `marginal_aggregates` per
  `docs/dataiku-reference/recipes/pivot.md:48-96`.
- `py2dataiku/models/recipe_settings.py` — add new
  `SyncSettings(engine, schema_resync, partition_dependency)`,
  `FuzzyJoinSettings(distance_metric, threshold, threshold_relative,
  text_normalization, output_meta, debug_mode)`,
  `GeoJoinSettings(spatial_operator, distance_value, distance_unit)`,
  `GenerateStatisticsSettings(...)` per the corresponding
  `docs/dataiku-reference/recipes/{sync,fuzzy-join,geojoin}.md` pages.
- `py2dataiku/mappings/pandas_mappings.py:59` — `"explode" →
  ARRAY_UNFOLD` (not `UNFOLD`) per
  `docs/dataiku-reference/processors/unfold-array.md` vs
  `docs/dataiku-reference/processors/unfold.md`. Pandas explode is
  array → rows, which matches DSS `ArrayFold` more than either
  `Unfold`/`ArrayUnfold` — verify against an exported recipe.
- `py2dataiku/mappings/processor_catalog.py` (whole-file audit) — for
  each of the 44 lib-only entries listed in finding #7, either remove
  if invented or annotate `description="… (no public DSS doc page)"`
  so the LLM prompt and tests can deprioritize them.
- `py2dataiku/mappings/processor_catalog.py` — add catalog entries for
  the 15-ish high-priority doc-only processors per finding #6
  (`CurrencyConverter`, `CurrencySplitter`, `NumbersExtractor`,
  `CountMatches`, `Negator`, `LineByLineMean`, `MoveColumns`,
  `PivotProcessor`, `NumericalFormatConverter`, `NumericalCombinations`,
  `QueryStringSplitter`, `Grok`, `UnixTimestampParser`, `VisitorIdGenerator`,
  `ZipArrays`, `TriggeredUnfold`, `SplitAndFold`, `SplitAndUnfold`,
  `TextSplitter`, `FoldMultipleColumnsByPattern`, `FoldObject`,
  `ObjectNest`, `ChangeCRS`, `GeoPointBuffer`, `GeoPointExtract`,
  `GeoInfoExtractor`, `FilterOnBadMeaning`, `FlagOnBadMeaning`,
  `MeaningTranslate`, `InvalidValuesSplitter`, `LongTailFilter`).
