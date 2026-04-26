# Storybook Plan for packages/flow-viz

All stories go in `packages/flow-viz/stories/`. One story file per concern. M3 owns implementation.

---

## 1. Recipe Node Stories (37 total, one per RecipeType)

Each story: renders a standalone node at default size (70x70px) in both light and dark themes. Shows all 6 states: default, hover, selected, focus-mode-dimmed, executing, error.

| Story file | RecipeType | Icon key | Color category |
|---|---|---|---|
| PrepareNode.stories.tsx | PREPARE | prepare | orange |
| SyncNode.stories.tsx | SYNC | sync | grey-blue |
| GroupingNode.stories.tsx | GROUPING | grouping | green |
| WindowNode.stories.tsx | WINDOW | window | teal |
| JoinNode.stories.tsx | JOIN | join | blue |
| FuzzyJoinNode.stories.tsx | FUZZY_JOIN | default (TODO:M3) | blue (inherited from join) |
| GeoJoinNode.stories.tsx | GEO_JOIN | default (TODO:M3) | blue (inherited from join) |
| StackNode.stories.tsx | STACK | stack | purple |
| SplitNode.stories.tsx | SPLIT | split | pink |
| SortNode.stories.tsx | SORT | sort | amber |
| DistinctNode.stories.tsx | DISTINCT | distinct | brown |
| TopNNode.stories.tsx | TOP_N | top_n | amber-deep |
| PivotNode.stories.tsx | PIVOT | pivot | light-blue |
| SamplingNode.stories.tsx | SAMPLING | sample | light-green |
| DownloadNode.stories.tsx | DOWNLOAD | default | grey |
| GenerateFeaturesNode.stories.tsx | GENERATE_FEATURES | default | grey |
| GenerateStatisticsNode.stories.tsx | GENERATE_STATISTICS | default | grey |
| PushToEditableNode.stories.tsx | PUSH_TO_EDITABLE | default | grey |
| ListFolderContentsNode.stories.tsx | LIST_FOLDER_CONTENTS | default | grey |
| DynamicRepeatNode.stories.tsx | DYNAMIC_REPEAT | default | grey |
| ExtractFailedRowsNode.stories.tsx | EXTRACT_FAILED_ROWS | filter | red-orange |
| UpsertNode.stories.tsx | UPSERT | default | grey |
| ListAccessNode.stories.tsx | LIST_ACCESS | default | grey |
| PythonNode.stories.tsx | PYTHON | python | indigo |
| RNode.stories.tsx | R | default (TODO:M3) | indigo (inherited) |
| SqlNode.stories.tsx | SQL | default (TODO:M3) | indigo (inherited) |
| HiveNode.stories.tsx | HIVE | default (TODO:M3) | indigo (inherited) |
| ImpalaNode.stories.tsx | IMPALA | default (TODO:M3) | indigo (inherited) |
| SparkSqlNode.stories.tsx | SPARKSQL | default (TODO:M3) | indigo (inherited) |
| PySparkNode.stories.tsx | PYSPARK | python (inherited) | indigo (inherited) |
| SparkScalaNode.stories.tsx | SPARK_SCALA | default (TODO:M3) | indigo (inherited) |
| SparkRNode.stories.tsx | SPARKR | default (TODO:M3) | indigo (inherited) |
| ShellNode.stories.tsx | SHELL | default | grey-blue |
| PredictionScoringNode.stories.tsx | PREDICTION_SCORING | default (TODO:M3) | TODO:designer-decision purple |
| ClusteringScoringNode.stories.tsx | CLUSTERING_SCORING | default (TODO:M3) | TODO:designer-decision purple |
| EvaluationNode.stories.tsx | EVALUATION | default (TODO:M3) | TODO:designer-decision purple |
| AiAssistantGenerateNode.stories.tsx | AI_ASSISTANT_GENERATE | default (TODO:M3) | TODO:designer-decision |

---

## 2. Dataset Node Stories (3 DatasetType x 13 DatasetConnectionType)

One story file per DatasetType; each story shows all 13 connection types as variants.

| Story file | DatasetType | Variants |
|---|---|---|
| InputDataset.stories.tsx | INPUT | 13 connection type variants |
| IntermediateDataset.stories.tsx | INTERMEDIATE | 13 connection type variants |
| OutputDataset.stories.tsx | OUTPUT | 13 connection type variants |

---

## 3. Composite Pipeline Stories

Each story renders a full `FlowCanvas` with a representative DAG. Use the rule-based converter fixtures from `tests/` for reproducibility.

| Story file | Pipeline pattern | RecipeTypes used |
|---|---|---|
| ReadPrepWrite.stories.tsx | Minimal ETL | INPUT → PREPARE → OUTPUT |
| ReadPrepSplitWrite.stories.tsx | Train/test split | INPUT → PREPARE → SPLIT → OUTPUT (x2) |
| ReadPrepGroupWrite.stories.tsx | Aggregation | INPUT → PREPARE → GROUPING → OUTPUT |
| ReadPrepJoinWrite.stories.tsx | Join two sources | INPUT (x2) → PREPARE (x2) → JOIN → OUTPUT |
| ReadPrepWindowWrite.stories.tsx | Window function | INPUT → PREPARE → WINDOW → OUTPUT |
| FullMLPipeline.stories.tsx | Read → Prep → Split → Score → Write | INPUT → PREPARE → SPLIT → PREDICTION_SCORING → OUTPUT (x2) |
| MultiStepETL.stories.tsx | 10-node pipeline | INPUT → PREPARE → GROUPING → JOIN → SORT → TOP_N → OUTPUT |
| PivotAndStack.stories.tsx | Reshape | INPUT → PIVOT → STACK → OUTPUT |
| SamplingAndDistinct.stories.tsx | Data quality | INPUT → SAMPLING → DISTINCT → OUTPUT |
| PythonCodeRecipe.stories.tsx | Code recipe in flow | INPUT → PREPARE → PYTHON → OUTPUT |

---

## 4. Feature Stories

### Focus Mode
`FocusMode.stories.tsx`
- Variant: no focus (all nodes full opacity)
- Variant: click node — selected subgraph (ancestors + descendants) at 100%, rest at 25% opacity
- Variant: click edge — highlight path

### Animated Execution Simulation
`ExecutionSim.stories.tsx`
- Variant: idle state (no animation)
- Variant: running — executing node pulses, upstream edges animate stroke-dashoffset
- Variant: completed — all nodes show success badge
- Variant: partial error — failed node shows error state, downstream nodes show blocked state

### Zone Overlays
`ZoneOverlays.stories.tsx`
- Variant: no zones
- Variant: 4 predefined zones (Input / Prep / ML / Output) — use zone_colors[0..3]
- Variant: all 8 zone colors
- Variant: dark theme zones

### Light/Dark Theme
`ThemeToggle.stories.tsx`
- Variant: light (DATAIKU_LIGHT)
- Variant: dark (DATAIKU_DARK)
- Variant: side-by-side comparison of the same 5-node flow in both themes

### Edge Variants
`EdgeVariants.stories.tsx`
- Variant: default solid edge (primary input)
- Variant: dashed edge (optional input)
- Variant: thin / medium / thick edges (row-count buckets)
- Variant: schema-change amber tint
- Variant: schema-break red tint
- Variant: animated executing edge

### Error States
`ErrorStates.stories.tsx`
- Variant: recipe node in error state
- Variant: dataset node in error state
- Variant: multiple error nodes in a pipeline
- Variant: error state in dark theme

### Minimap
`Minimap.stories.tsx`
- Variant: minimap visible, 100-node fixture
- Variant: minimap hidden

### Export
`Export.stories.tsx`
- Variant: export to SVG (download button)
- Variant: export to PNG
- Variant: export to PDF

---

## 5. Story Count Summary

| Category | Count |
|---|---|
| Recipe node stories | 37 |
| Dataset node stories | 3 |
| Composite pipeline stories | 10 |
| Focus mode | 1 |
| Animated execution sim | 1 |
| Zone overlays | 1 |
| Light/dark theme | 1 |
| Edge variants | 1 |
| Error states | 1 |
| Minimap | 1 |
| Export | 1 |
| **Total** | **58** |

---

## 6. Storybook Configuration Notes for M3

- Use `@storybook/react-vite` builder (matches `apps/web` Vite version).
- `packages/flow-viz/.storybook/preview.tsx` must wrap all stories in a theme provider that reads a `theme` global from the Storybook toolbar.
- Globals: `theme` (light | dark), `animationEnabled` (boolean), `showMinimap` (boolean).
- Visual regression: `@storybook/test-runner` + `jest-image-snapshot`; run only rule-based composite stories in CI (LLM stories gated behind manual job per risk register).
- Accessibility: configure `@storybook/addon-a11y`; all recipe and dataset nodes must pass axe WCAG 2.1 AA at default state.
- Performance budget story: render 100-node fixture, assert `performance.measure` frame time <16ms (one story tagged `@perf`).
