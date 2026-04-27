# Dataiku-Faithful Node and Edge Specification

Source of truth: `py2dataiku/visualizers/themes.py` and `py2dataiku/visualizers/icons.py`.
All hex values are exact copies from those files. Values marked `TODO:designer-decision` are absent from `themes.py`.

---

## 1. Recipe Node Anatomy

A recipe node is a square tile with rounded corners (`radius: 10px`). Default size: `70 x 70px`.

```
+------------------------------------------+
|  [category stripe — 4px left border]     |
|                                           |
|   [ ICON  ]   20px unicode / SVG glyph   |
|                                           |
|   [  Label  ]  11px, centered             |
|                                           |
|  [IO badge row]  input-count / output-count|
|                                           |
|  [status badge]  top-right corner slot   |
+------------------------------------------+
```

| Layer | Description |
|---|---|
| Background fill | `recipe_colors[type].bg` from theme |
| Left border stripe | `recipe_colors[type].border`, 4px solid |
| Icon | Unicode glyph from `RecipeIcons.UNICODE` or SVG path from `RecipeIcons.SVG_PATHS`, 20px, color `recipe_colors[type].text` |
| Name label | Recipe name, 11px, `font_family`, color `recipe_colors[type].text`, centered below icon |
| IO badge row | Two small pills: inputs (blue tint) / outputs (green tint), 9px text, bottom edge |
| Status badge slot | 16x16px circle, top-right corner; renders `not_deployed` (hollow) by default; states: deploying (spinner), deployed (check), error (X) |

---

## 2. Dataset Node Anatomy

Datasets are rectangular tiles: `160 x 50px`, `radius: 6px`.

```
+---------------------------------------------+
| [shape icon]  [dataset name — 13px]          |
|               [connection type tag — 9px]    |
+---------------------------------------------+
```

### Shape mapping by DatasetType and DatasetConnectionType

| DatasetType | DatasetConnectionType | Shape | Rationale |
|---|---|---|---|
| INPUT | any | Rounded rect + left-pointing arrow badge | Entry point |
| OUTPUT | any | Rounded rect + right-pointing arrow badge | Exit point |
| INTERMEDIATE | any | Rounded rect, no badge | Internal buffer |

### Shape mapping by DatasetConnectionType (secondary icon)

| DatasetConnectionType | Node Icon | Rationale |
|---|---|---|
| FILESYSTEM | Folder (open) | Local or network filesystem |
| MANAGED_FOLDER | Folder (solid) | DSS-managed folder |
| SQL_POSTGRESQL | Cylinder | Relational tabular |
| SQL_MYSQL | Cylinder | Relational tabular |
| SQL_BIGQUERY | Cylinder + cloud tag | Cloud warehouse |
| SQL_SNOWFLAKE | Cylinder + snowflake tag | Cloud warehouse |
| SQL_REDSHIFT | Cylinder + cloud tag | Cloud warehouse |
| S3 | Cloud + bucket | Object store |
| GCS | Cloud + bucket | Object store |
| AZURE_BLOB | Cloud + container | Object store |
| HDFS | Cylinder + cluster bars | Distributed FS |
| MONGODB | Document stack | Document store |
| ELASTICSEARCH | Magnifier + doc | Search index / unstructured |

---

## 3. Edge Styles

All edges are directed (source → target). Rendered as smooth-step or bezier curves in React Flow.

| Property | Encoding | Values |
|---|---|---|
| Line style | Input type | Solid = primary input; Dashed = optional / secondary input |
| Stroke width | Row-count estimate bucket | Thin (1.5px) = <10k rows; Medium (2.5px) = 10k–1M rows; Thick (4px) = >1M rows |
| Color tint | Schema-change indicator | `connection_color` (#90A4AE light / #546E7A dark) = no change; amber tint (#FFB300) = schema modified; red tint (#E53935) = schema break |
| Arrow head | Always present | Solid filled triangle, `arrow_size: 8px` from themes.py |
| Animated | Executing state | Stroke-dashoffset animation at 20px/s along path |

---

## 4. Zone Overlay Spec

Zones group related node clusters behind a translucent colored rectangle. The `zone_colors` list (8 entries) and `zone_border_colors` list (8 entries) are defined in `themes.py:80-87`.

```
+================================================+  <-- dashed border, zone_border_colors[i]
|  [Zone Label — 11px, bold, zone_border_colors[i]]  top-left
|                                               |
|   [  node  ]    [  node  ]    [  node  ]      |
|                                               |
+================================================+
```

| Property | Value |
|---|---|
| Fill | `zone_colors[i]` at 60% opacity |
| Border | `zone_border_colors[i]`, 1.5px dashed |
| Border radius | 12px (TODO:designer-decision — not in themes.py) |
| Label | 11px (`zone_label_size`), bold, `font_family`, `zone_border_colors[i]` |
| Padding | 20px (`zone_padding`) on all sides |
| z-index | Below all nodes |

### Predefined zone roles (suggested mapping to zone_colors index)

| Zone | Index | Light fill | Light border |
|---|---|---|---|
| Input zone | 0 | #E3F2FD | #90CAF9 |
| Prep zone | 1 | #F3E5F5 | #CE93D8 |
| ML zone | 2 | #E8F5E9 | #A5D6A7 |
| Output zone | 3 | #FFF3E0 | #FFCC80 |

Indices 4-7 are available for user-defined zones.

---

## 5. Light/Dark Parity Table

Every token used in both themes. Source: `themes.py:98-139`.

| Token | Light | Dark |
|---|---|---|
| background | #FAFAFA | #1E1E1E |
| grid | #E0E0E0 | #333333 |
| connection_color | #90A4AE | #546E7A |
| connection_hover | #1976D2 | TODO:designer-decision |
| dataset.input.bg | #E3F2FD | #1E3A5F |
| dataset.input.border | #4A90D9 | #4A90D9 |
| dataset.input.text | #1565C0 | #90CAF9 |
| dataset.output.bg | #E8F5E9 | #1B3D1B |
| dataset.output.border | #43A047 | #43A047 |
| dataset.output.text | #2E7D32 | #A5D6A7 |
| dataset.intermediate.bg | #ECEFF1 | #2D2D2D |
| dataset.intermediate.border | #78909C | #78909C |
| dataset.intermediate.text | #455A64 | #B0BEC5 |
| dataset.error.bg | #FFEBEE | TODO:designer-decision |
| dataset.error.border | #E53935 | TODO:designer-decision |
| dataset.error.text | #C62828 | TODO:designer-decision |
| recipe.prepare.bg | #FFF3E0 | #3E2723 |
| recipe.prepare.border | #FF9800 | #FF9800 |
| recipe.prepare.text | #E65100 | #FFB74D |
| recipe.join.bg | #E3F2FD | #1A237E |
| recipe.join.border | #2196F3 | #2196F3 |
| recipe.join.text | #1565C0 | #64B5F6 |
| recipe.grouping.bg | #E8F5E9 | #1B5E20 |
| recipe.grouping.border | #4CAF50 | #4CAF50 |
| recipe.grouping.text | #2E7D32 | #81C784 |
| recipe.window.bg | #E0F7FA | #006064 |
| recipe.window.border | #00BCD4 | #00BCD4 |
| recipe.window.text | #00838F | #4DD0E1 |
| recipe.split.bg | #FCE4EC | #880E4F |
| recipe.split.border | #E91E63 | #E91E63 |
| recipe.split.text | #AD1457 | #F48FB1 |
| recipe.sort.bg | #FFFDE7 | #F57F17 |
| recipe.sort.border | #FFC107 | #FFC107 |
| recipe.sort.text | #FF8F00 | #FFD54F |
| recipe.distinct.bg | #EFEBE9 | #3E2723 |
| recipe.distinct.border | #795548 | #795548 |
| recipe.distinct.text | #4E342E | #A1887F |
| recipe.filter.bg | #FBE9E7 | #BF360C |
| recipe.filter.border | #FF5722 | #FF5722 |
| recipe.filter.text | #D84315 | #FF8A65 |
| recipe.python.bg | #E8EAF6 | #1A237E |
| recipe.python.border | #3F51B5 | #3F51B5 |
| recipe.python.text | #283593 | #7986CB |
| recipe.sync.bg | #ECEFF1 | #263238 |
| recipe.sync.border | #607D8B | #607D8B |
| recipe.sync.text | #37474F | #90A4AE |
| recipe.sample.bg | #F1F8E9 | #33691E |
| recipe.sample.border | #8BC34A | #8BC34A |
| recipe.sample.text | #558B2F | #AED581 |
| recipe.pivot.bg | #E1F5FE | #01579B |
| recipe.pivot.border | #03A9F4 | #03A9F4 |
| recipe.pivot.text | #0277BD | #4FC3F7 |
| recipe.top_n.bg | #FFF8E1 | #E65100 |
| recipe.top_n.border | #FFB300 | #FFB300 |
| recipe.top_n.text | #FF6F00 | #FFD54F |
| recipe.default.bg | #F5F5F5 | #424242 |
| recipe.default.border | #9E9E9E | #9E9E9E |
| recipe.default.text | #616161 | #BDBDBD |

---

## 6. Node States

| State | Visual Treatment |
|---|---|
| default | Theme bg/border per type, no shadow |
| hover | Border brightens by 20% luminance; drop shadow `0 2px 8px rgba(0,0,0,0.15)`; cursor pointer — TODO:designer-decision (shadow not in themes.py) |
| selected | 2px outer ring using `connection_hover` color (#1976D2 light); border weight increases to 3px |
| focus-mode-dimmed | All non-selected nodes at 25% opacity; selected subgraph stays at 100% |
| executing | Animated pulsing border (keyframe: border-color oscillates bg ↔ border at 1.2s ease-in-out); IO edges animate stroke-dashoffset |
| error | Border switches to `error_border` (#E53935); bg switches to `error_bg` (#FFEBEE light / TODO:designer-decision dark); status badge shows X icon in error red |

---

## 7. Gaps Where themes.py Was Missing Tokens

The following tokens are needed by M3 but were not defined in `themes.py`. All are marked `TODO:designer-decision` in `tokens.json`.

| Missing token | Needed for | Suggested default |
|---|---|---|
| `connectionHover` (dark theme) | Edge hover highlight in dark mode | #64B5F6 (blue-300) |
| `error.*` (dark theme) | Error state dataset/recipe in dark mode | Derive from light: darken bg, keep border/text |
| `shadow.*` (both themes) | Hover and selected state depth cues | Standard elevation scale: 0 2px 4px / 0 4px 16px |
| `radius.zone` (both themes) | Zone overlay corner rounding | 12px |
| `typography.fontWeight.*` | Bold labels, zone labels | 400 / 500 / 700 |
| ML recipe colors (PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION) | 3 ML RecipeType nodes | DSS uses purple (#9C27B0 family) — confirm with designer |
| `AI_ASSISTANT_GENERATE` colors | AI recipe node | No precedent in themes.py |
| Code recipe colors for R, SQL, HIVE, IMPALA, SPARKSQL, SPARK_SCALA, SPARKR, SHELL | 8 code RecipeType nodes | themes.py maps "python" to #3F51B5 indigo; same palette may apply to all code recipes |
