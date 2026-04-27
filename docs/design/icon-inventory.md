# Icon Inventory

Source file: `py2dataiku/visualizers/icons.py`

All icons live in the `RecipeIcons` class. The file has four dictionaries: `UNICODE` (line 11), `LABELS` (line 29), `SVG_PATHS` (line 48), `ASCII` (line 57). Icons are keyed by lowercase recipe type string, not by `RecipeType` enum member name.

---

## Unicode Icons

`icons.py:11-27`

| Key | Codepoint | Glyph | RecipeType member(s) | Notes |
|---|---|---|---|---|
| prepare | U+2699 | ⚙ | PREPARE | Gear |
| join | U+22C8 | ⋈ | JOIN | Bowtie — join symbol |
| stack | U+2630 | ☰ | STACK | Trigram / stacked lines |
| grouping | U+03A3 | Σ | GROUPING | Sigma — aggregate |
| window | U+25A6 | ▦ | WINDOW | Square with grid |
| split | U+2442 | ⑂ | SPLIT | Fork |
| sort | U+21C5 | ⇅ | SORT | Up-down arrows |
| distinct | U+25CE | ◎ | DISTINCT | Bullseye |
| filter | U+25BC | ▼ | FILTER (PREPARE processor context only) | Down triangle / funnel |
| python | U+03BB | λ | PYTHON, R, SQL, HIVE, IMPALA, SPARKSQL, PYSPARK, SPARK_SCALA, SPARKR (shared) | Lambda |
| sync | U+21C4 | ⇄ | SYNC | Left-right arrows |
| sample | U+25D4 | ◔ | SAMPLING | Circle with quarter |
| pivot | U+229E | ⊞ | PIVOT | Squared plus |
| top_n | U+2191 | ↑ | TOP_N | Up arrow |
| default | U+25A0 | ■ | DOWNLOAD, GENERATE_FEATURES, GENERATE_STATISTICS, PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, UPSERT, LIST_ACCESS, SHELL, PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION, AI_ASSISTANT_GENERATE, SPARK_SCALA, SPARKR, SHELL, R, SQL, HIVE, IMPALA, SPARKSQL | Solid square fallback |

---

## SVG Paths

`icons.py:48-55` — Only 5 entries; all others fall back to `default`.

| Key | Line | RecipeType member | Path |
|---|---|---|---|
| prepare | 50 | PREPARE | Circle with info path |
| join | 51 | JOIN | Hexagonal join shape |
| grouping | 52 | GROUPING | 2x2 grid squares |
| split | 53 | SPLIT | Fork branches |
| default | 54 | (all unmapped) | Simple rectangle |

---

## ASCII Representations

`icons.py:57-74`

| Key | ASCII | RecipeType member(s) |
|---|---|---|
| prepare | [*] | PREPARE |
| join | [><] | JOIN |
| stack | [=] | STACK |
| grouping | [E] | GROUPING |
| window | [#] | WINDOW |
| split | [Y] | SPLIT |
| sort | [\|] | SORT |
| distinct | [O] | DISTINCT |
| filter | [V] | FILTER context |
| python | [Py] | PYTHON + code variants |
| sync | [<>] | SYNC |
| sample | [%] | SAMPLING |
| pivot | [+] | PIVOT |
| top_n | [^] | TOP_N |
| default | [?] | all unmapped |

---

## RecipeType Coverage Gap Analysis

All 37 `RecipeType` members listed. `icons.py` keys are lowercase strings; the mapping shows which key each member resolves to via `get_unicode()` / `get_label()`.

| RecipeType member | Resolved key | Has dedicated Unicode | Has dedicated SVG path | Has dedicated ASCII | Status |
|---|---|---|---|---|---|
| PREPARE | prepare | Yes | Yes | Yes | Full coverage |
| SYNC | sync | Yes | No | Yes | Missing SVG — TODO:M3 |
| GROUPING | grouping | Yes | Yes | Yes | Full coverage |
| WINDOW | window | Yes | No | Yes | Missing SVG — TODO:M3 |
| JOIN | join | Yes | Yes | Yes | Full coverage |
| FUZZY_JOIN | default | No (falls back) | No | No | All missing — TODO:M3 |
| GEO_JOIN | default | No (falls back) | No | No | All missing — TODO:M3 |
| STACK | stack | Yes | No | Yes | Missing SVG — TODO:M3 |
| SPLIT | split | Yes | Yes | Yes | Full coverage |
| SORT | sort | Yes | No | Yes | Missing SVG — TODO:M3 |
| DISTINCT | distinct | Yes | No | Yes | Missing SVG — TODO:M3 |
| TOP_N | top_n | Yes | No | Yes | Missing SVG — TODO:M3 |
| PIVOT | pivot | Yes | No | Yes | Missing SVG — TODO:M3 |
| SAMPLING | sample | Yes | No | Yes | Missing SVG — TODO:M3 |
| DOWNLOAD | default | No (falls back) | No | No | All missing — TODO:M3 |
| GENERATE_FEATURES | default | No (falls back) | No | No | All missing — TODO:M3 |
| GENERATE_STATISTICS | default | No (falls back) | No | No | All missing — TODO:M3 |
| PUSH_TO_EDITABLE | default | No (falls back) | No | No | All missing — TODO:M3 |
| LIST_FOLDER_CONTENTS | default | No (falls back) | No | No | All missing — TODO:M3 |
| DYNAMIC_REPEAT | default | No (falls back) | No | No | All missing — TODO:M3 |
| EXTRACT_FAILED_ROWS | default | No (falls back) | No | No | All missing — TODO:M3 |
| UPSERT | default | No (falls back) | No | No | All missing — TODO:M3 |
| LIST_ACCESS | default | No (falls back) | No | No | All missing — TODO:M3 |
| PYTHON | python | Yes | No | Yes | Missing SVG — TODO:M3 |
| R | default | No (falls back) | No | No | All missing — TODO:M3 |
| SQL | default | No (falls back) | No | No | All missing — TODO:M3 |
| HIVE | default | No (falls back) | No | No | All missing — TODO:M3 |
| IMPALA | default | No (falls back) | No | No | All missing — TODO:M3 |
| SPARKSQL | default | No (falls back) | No | No | All missing — TODO:M3 |
| PYSPARK | default | No (falls back) | No | No | All missing — TODO:M3 |
| SPARK_SCALA | default | No (falls back) | No | No | All missing — TODO:M3 |
| SPARKR | default | No (falls back) | No | No | All missing — TODO:M3 |
| SHELL | default | No (falls back) | No | No | All missing — TODO:M3 |
| PREDICTION_SCORING | default | No (falls back) | No | No | All missing — TODO:M3 |
| CLUSTERING_SCORING | default | No (falls back) | No | No | All missing — TODO:M3 |
| EVALUATION | default | No (falls back) | No | No | All missing — TODO:M3 |
| AI_ASSISTANT_GENERATE | default | No (falls back) | No | No | All missing — TODO:M3 |

### Summary

- Full coverage (Unicode + SVG + ASCII): 4 types (PREPARE, JOIN, GROUPING, SPLIT)
- Unicode + ASCII only, missing SVG: 10 types
- Fully missing (all fallback to default): 23 types

M3 must add at minimum: SVG path icons for the 10 partially covered types and purpose-built icons (or confirmed shared glyphs) for the 23 fully missing types.

---

## Dataset Type Icons

`icons.py` does not define dataset icons. The SVGVisualizer and HTMLVisualizer render datasets as plain rectangles using dataset color tokens. M3 must implement connection-type icons as described in `node-spec.md` section 2. These are all TODO:M3.

| DatasetConnectionType | Shape needed | Icon needed |
|---|---|---|
| FILESYSTEM | Rounded rect | Folder open — TODO:M3 |
| MANAGED_FOLDER | Rounded rect | Folder solid — TODO:M3 |
| SQL_POSTGRESQL | Rounded rect | Cylinder — TODO:M3 |
| SQL_MYSQL | Rounded rect | Cylinder — TODO:M3 |
| SQL_BIGQUERY | Rounded rect | Cylinder + cloud — TODO:M3 |
| SQL_SNOWFLAKE | Rounded rect | Cylinder + snowflake — TODO:M3 |
| SQL_REDSHIFT | Rounded rect | Cylinder + cloud — TODO:M3 |
| S3 | Rounded rect | Cloud bucket — TODO:M3 |
| GCS | Rounded rect | Cloud bucket — TODO:M3 |
| AZURE_BLOB | Rounded rect | Cloud container — TODO:M3 |
| HDFS | Rounded rect | Cylinder + bars — TODO:M3 |
| MONGODB | Rounded rect | Document stack — TODO:M3 |
| ELASTICSEARCH | Rounded rect | Magnifier + doc — TODO:M3 |
