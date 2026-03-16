# Concept Diagram Style Guide

Reference for creating new concept diagrams that match the 66 existing diagrams in `docs/assets/images/concepts/`.

---

## Quick Start Template

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# --- Color Palette (matches MkDocs teal theme + existing example plots) ---
COLORS = {
    'teal': '#009688',         # Primary brand color
    'coral': '#FF6B6B',        # Warnings, errors, bad examples
    'green': '#2ECC71',        # Success, correct, good examples
    'blue': '#5B8DEF',         # Secondary accent, data points
    'purple': '#9B59B6',       # Tertiary accent, special elements
    'amber': '#F5A623',        # Highlights, callouts
    'gray': '#95A5A6',         # Neutral, arrows, borders
    'dark': '#2C3E50',         # Text, titles, dark backgrounds
    'light_blue': '#B3E5FC',   # Light fill, grids, backgrounds
    'light_red': '#FFCDD2',    # Light error fill
    'light_green': '#C8E6C9',  # Light success fill
    'light_teal': '#B2DFDB',   # Light brand fill
    'light_purple': '#E1BEE7', # Light accent fill
    'light_amber': '#FFE0B2',  # Light highlight fill
    'white': '#FFFFFF',
    'off_white': '#F8F9FA',
}

# --- Save settings ---
SAVEFIG_KWARGS = {
    'dpi': 150,
    'bbox_inches': 'tight',
    'pad_inches': 0.3,
    'facecolor': 'white',
}

# --- Output directory ---
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'docs', 'assets', 'images', 'concepts'
)
os.makedirs(OUT_DIR, exist_ok=True)

# --- Matplotlib rcParams ---
def setup_style():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'savefig.facecolor': 'white',
        'savefig.dpi': 150,
    })
```

---

## Color Palette

### Semantic Usage

| Color | Hex | Use For |
|-------|-----|---------|
| **Teal** | `#009688` | Primary elements, brand identity, correct examples, main flow |
| **Coral** | `#FF6B6B` | Errors, warnings, incorrect examples, "bad" paths |
| **Green** | `#2ECC71` | Success states, checkmarks, correct outcomes |
| **Blue** | `#5B8DEF` | Data points, secondary elements, input/output boxes |
| **Purple** | `#9B59B6` | Special elements, third category, transformations |
| **Amber** | `#F5A623` | Highlights, callouts, attention-drawing elements |
| **Gray** | `#95A5A6` | Arrows, borders, neutral connectors, disabled states |
| **Dark** | `#2C3E50` | Text, titles, dark-background boxes |

### Light Variants (for fills and backgrounds)

Use light variants when you need a filled area that doesn't dominate:

| Color | Hex | Pair With |
|-------|-----|-----------|
| `light_blue` | `#B3E5FC` | `blue` or `dark` text |
| `light_red` | `#FFCDD2` | `coral` border or `dark` text |
| `light_green` | `#C8E6C9` | `green` border or `dark` text |
| `light_teal` | `#B2DFDB` | `teal` border or `dark` text |
| `light_purple` | `#E1BEE7` | `purple` border or `dark` text |
| `light_amber` | `#FFE0B2` | `amber` border or `dark` text |

### Color Pairing Rules

1. **Dark backgrounds** (`teal`, `blue`, `purple`, `dark`, `coral`) use **white text**
2. **Light backgrounds** (`light_*`, `off_white`, `white`) use **dark text** (`#2C3E50`)
3. **Max 4 distinct colors** per diagram (excluding gray/dark for text/arrows)
4. **Consistent meaning** within a diagram: if teal = "correct" in panel 1, keep that throughout

---

## Figure Dimensions

### Standard Sizes

| Diagram Type | figsize | When to Use |
|-------------|---------|-------------|
| **Single panel, flow** | `(10, 5)` to `(12, 6)` | Horizontal flows, pipelines |
| **Single panel, tall** | `(10, 7)` to `(12, 7)` | Vertical flows, tree structures |
| **1x3 subplots** | `(12, 4)` to `(14, 4.5)` | Side-by-side comparisons |
| **2x2 subplots** | `(10, 8)` | Four-panel comparisons |
| **Wide flow** | `(13, 5)` to `(15, 6)` | Complex multi-stage pipelines |

### Size Guidelines

- **Minimum width**: 9 inches (renders well at 800px on site)
- **Maximum width**: 15 inches (avoids overflow)
- **Aspect ratio**: Prefer wider than tall (landscape orientation)
- **Rendered width**: All images render at max `800px` CSS width on the site

---

## Typography

### Font Sizes

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| **Main title** | 14-18pt | Bold | `dark` (#2C3E50) |
| **Section/subtitle** | 12-13pt | Bold | `dark` |
| **Box labels** | 9-11pt | Bold | White (dark bg) or Dark (light bg) |
| **Annotations** | 9-10pt | Normal | `dark` or `gray` |
| **Axis labels** | 11pt (default) | Normal | Default matplotlib |
| **Small labels** | 8pt | Normal/Bold | `gray` or `dark` |

### Text Rules

- **Titles**: Use `ax.set_title()` or `ax.text()` with `fontweight='bold'`
- **Suptitles**: Use `fig.suptitle()` for multi-panel figures, with `y=1.02` to avoid overlap
- **Box text**: Always centered (`ha='center', va='center'`)
- **No emojis** in diagram text
- **Use Unicode**: `\u2192` (arrow), `\u2713` (checkmark), `\u2717` (cross), `\u2022` (bullet)

---

## Shared Helper Functions

### Rounded Box

```python
def add_box(ax, x, y, w, h, text, color, text_color='white', fontsize=10, alpha=1.0):
    """Add a rounded rectangle with centered text. (x,y) is CENTER of box."""
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.1",
        facecolor=color, edgecolor='none', alpha=alpha,
        transform=ax.transData, zorder=2
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, zorder=3)
    return box
```

**Alternative signature** (used in tier3/10to11 scripts — `(x,y)` is TOP-LEFT corner):

```python
def add_rounded_box(ax, xy, width, height, text, color, text_color='white',
                    fontsize=10, fontweight='bold', alpha=1.0, edgecolor=None):
    """Add a rounded box. xy=(x,y) is TOP-LEFT corner."""
    x, y = xy
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.08",
        facecolor=color, edgecolor=edgecolor or color,
        alpha=alpha, linewidth=1.5, zorder=2
    )
    ax.add_patch(box)
    ax.text(x + width/2, y + height/2, text,
            ha='center', va='center', fontsize=fontsize,
            fontweight=fontweight, color=text_color, zorder=3)
    return box
```

### Arrow

```python
def add_arrow(ax, x1, y1, x2, y2, color='#95A5A6', style='->', lw=1.5):
    """Add an arrow between two points."""
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=15,
        color=color, lw=lw, zorder=1
    )
    ax.add_patch(arrow)
    return arrow
```

### Mini Tree (for ensemble diagrams)

```python
def draw_mini_tree(ax, cx, cy, scale=1.0):
    """Draw a small decision tree icon centered at (cx, cy)."""
    s = scale
    # Root node
    ax.plot(cx, cy + 0.15*s, 'o', color=COLORS['dark'], markersize=6*s, zorder=5)
    # Branches
    ax.plot([cx, cx - 0.12*s], [cy + 0.15*s, cy - 0.05*s],
            '-', color=COLORS['dark'], lw=1.5*s, zorder=4)
    ax.plot([cx, cx + 0.12*s], [cy + 0.15*s, cy - 0.05*s],
            '-', color=COLORS['dark'], lw=1.5*s, zorder=4)
    # Leaf nodes
    ax.plot(cx - 0.12*s, cy - 0.05*s, 's', color=COLORS['green'],
            markersize=5*s, zorder=5)
    ax.plot(cx + 0.12*s, cy - 0.05*s, 's', color=COLORS['coral'],
            markersize=5*s, zorder=5)
```

---

## Diagram Patterns

### Pattern 1: Horizontal Flow (Pipeline)

Used for: workflows, data pipelines, transformation chains.

```
[Input] ──→ [Step 1] ──→ [Step 2] ──→ [Output]
```

- Boxes spaced evenly left to right
- Gray arrows connecting them
- Title centered above
- Example: `ch07-workflow-composition.png`, `ch03-mold-forge-pipeline.png`

### Pattern 2: Layered Stack

Used for: architecture diagrams, package layers.

```
┌─────────────────────────┐
│      Top Layer          │
├─────────────────────────┤
│      Middle Layer       │
├─────────────────────────┤
│      Bottom Layer       │
└─────────────────────────┘
```

- Full-width boxes stacked vertically
- Arrows between layers pointing up or down
- Side panel for extensions/notes
- Example: `ch01-ecosystem-architecture.png`

### Pattern 3: Side-by-Side Comparison

Used for: good vs bad, before/after, method comparison.

```
[Method A]          [Method B]
  ✓ Pro               ✓ Pro
  ✗ Con               ✗ Con
```

- 1x2 or 1x3 subplots, or two columns in single axes
- Green checkmarks (✓) vs red crosses (✗)
- Consistent vertical alignment
- Example: `ch06-linear-reg-assumptions.png`, `ch10-resampling-comparison.png`

### Pattern 4: Decision Tree / Flowchart

Used for: choosing between options, diagnostic flows.

```
        [Question?]
       /           \
    [Yes]         [No]
     |              |
  [Action A]    [Action B]
```

- Diamond or rounded boxes for decisions
- Branching arrows with labels
- Color-code paths (teal=recommended, gray=alternative)
- Example: `ch25-search-strategies.png`, `appendix-nan-handling-flow.png`

### Pattern 5: Data-Driven Plot

Used for: statistical concepts, mathematical relationships.

```python
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, data in zip(axes, datasets):
    ax.scatter(x, y, color=COLORS['teal'], s=40, edgecolors='white', linewidth=0.5)
    ax.plot(x_line, y_line, color=COLORS['coral'], linewidth=2.5)
```

- Scatter points in `teal` with white edge
- Fit lines in `coral`
- Clean axes (top/right spines removed)
- RMSE or metric annotations in corner
- Example: `ch12-overfitting-polynomial.png`, `ch09-r-squared-misleading.png`

### Pattern 6: Grid / Matrix

Used for: cross-products, hyperparameter spaces, data structures.

```
┌──┬──┬──┐
│  │  │  │
├──┼──┼──┤
│  │  │  │
└──┴──┴──┘
```

- `FancyBboxPatch` cells with consistent spacing
- Highlight specific cells with different colors
- Labels on rows/columns
- Example: `ch15-workflowset-cross-product.png`, `ch13-grid-search-heatmap.png`

---

## Canvas Setup

For diagram-style figures (not data plots), always:

```python
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis('off')
```

- Use logical coordinate space (0-12 width is common)
- `ax.axis('off')` removes all axes/ticks
- Place elements using the coordinate space
- Leave margins (don't place boxes at x=0 or x=12)

---

## Saving

```python
fig.savefig(os.path.join(OUT_DIR, 'chXX-descriptive-name.png'), **SAVEFIG_KWARGS)
plt.close(fig)
```

### File Naming Convention

```
ch{NN}-{descriptive-kebab-case-name}.png
appendix-{descriptive-kebab-case-name}.png
```

Examples:
- `ch12-overfitting-polynomial.png`
- `ch07-workflow-composition.png`
- `appendix-nan-handling-flow.png`

### Save Parameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| `dpi` | 150 | Good quality without excessive file size |
| `bbox_inches` | `'tight'` | Crop whitespace |
| `pad_inches` | 0.3 | Small consistent margin |
| `facecolor` | `'white'` | White background (not transparent) |

---

## Embedding in Chapter Markdown

```markdown
![Descriptive Alt Text](../assets/images/concepts/chXX-name.png)

*Figure X.Y: Caption describing what the diagram shows and why it matters.*
```

- Alt text should describe the concept, not the visual layout
- Caption in italics below the image
- Use relative path from the chapter file

---

## Complete Example: Simple Flow Diagram

```python
def ch99_example_flow():
    """Example: 3-step data pipeline."""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis('off')
    ax.set_title('Data Processing Pipeline', fontsize=14,
                 fontweight='bold', color=COLORS['dark'], pad=15)

    # Three boxes
    steps = [
        (2, 2, 'Raw Data', COLORS['light_blue'], COLORS['dark']),
        (6, 2, 'Transform', COLORS['teal'], 'white'),
        (10, 2, 'Clean Data', COLORS['green'], 'white'),
    ]
    box_w, box_h = 2.5, 1.2

    for x, y, label, bg, fg in steps:
        add_box(ax, x, y, box_w, box_h, label, bg, text_color=fg, fontsize=12)

    # Arrows between boxes
    add_arrow(ax, 2 + box_w/2 + 0.1, 2, 6 - box_w/2 - 0.1, 2)
    add_arrow(ax, 6 + box_w/2 + 0.1, 2, 10 - box_w/2 - 0.1, 2)

    # Annotation below
    ax.text(6, 0.5, 'step_normalize() + step_dummy() + step_naomit()',
            ha='center', va='center', fontsize=9, style='italic',
            color=COLORS['gray'])

    fig.savefig(os.path.join(OUT_DIR, 'ch99-example-flow.png'), **SAVEFIG_KWARGS)
    plt.close(fig)
```

---

## Checklist for New Diagrams

- [ ] Uses the standard `COLORS` palette (no ad-hoc hex codes)
- [ ] Uses `setup_style()` or equivalent rcParams
- [ ] White background (`facecolor='white'`)
- [ ] 150 DPI, `bbox_inches='tight'`, `pad_inches=0.3`
- [ ] File named `ch{NN}-descriptive-name.png`
- [ ] Saved to `docs/assets/images/concepts/`
- [ ] Title is bold, 14-18pt, in `dark` color
- [ ] Text on dark boxes is white; text on light boxes is dark
- [ ] Max 4 accent colors per diagram
- [ ] `plt.close(fig)` after saving (prevents memory leaks)
- [ ] Renders clearly at 800px width on the site

---

## Existing Diagram Inventory (66 diagrams)

### By Chapter

| Chapter | Count | Diagrams |
|---------|:-----:|----------|
| Ch1 | 4 | ecosystem-architecture, three-model-types, engine-abstraction, pit-of-success |
| Ch2 | 3 | method-chaining, reshape-wide-long, groupby-split-apply-combine |
| Ch3 | 4 | mold-forge-pipeline, three-dataframe-output, dual-path-architecture, unified-interface |
| Ch5 | 3 | data-budget, data-leakage, split-strategies |
| Ch6 | 1 | linear-reg-assumptions |
| Ch7 | 3 | workflow-composition, workflow-container, fit-predict-lifecycle |
| Ch8 | 3 | prep-bake-pipeline, selector-context, step-categories |
| Ch9 | 1 | r-squared-misleading |
| Ch10 | 3 | kfold-cross-validation, resampling-comparison, time-series-cv |
| Ch11 | 2 | model-comparison-funnel, one-standard-error-rule |
| Ch12 | 1 | overfitting-polynomial |
| Ch13 | 3 | grid-search-heatmap, regular-vs-random-grid, tune-finalize-flow |
| Ch14 | 2 | bayesian-opt-concept, exploration-exploitation |
| Ch15 | 2 | screening-pipeline, workflowset-cross-product |
| Ch16 | 2 | pca-overview, curse-of-dimensionality |
| Ch17 | 1 | encoding-strategies |
| Ch18 | 1 | model-interpretability |
| Ch19 | 1 | conformal-prediction |
| Ch20 | 2 | bagging-overview, boosting-overview |
| Ch21 | 3 | dual-path-architecture, forecast-horizon, model-taxonomy |
| Ch22 | 3 | bayesian-workflow, mcmc-sampling, prior-sensitivity |
| Ch23 | 2 | hierarchy-tree, reconciliation-methods |
| Ch24 | 2 | nested-vs-global, panel-data-structure |
| Ch25 | 2 | feature-selection-taxonomy, search-strategies |
| Ch26 | 2 | causal-vs-predictive, treatment-effect |
| Ch27 | 2 | storytelling-pipeline, causal-vs-predictive |
| Ch28 | 1 | vintage-backtesting |
| Ch29 | 1 | mlflow-lifecycle |
| Ch31 | 1 | financial-indicators |
| Ch32 | 2 | production-pipeline, leakage-prevention |
| Appendix | 3 | recipe-step-ordering, nan-handling-flow, column-name-reference |

### Generation Scripts

| Script | Diagrams | Chapters |
|--------|:--------:|----------|
| `generate_tier1_diagrams.py` | 17 | Ch1-3, Appendix |
| `generate_diagrams_1to4.py` | 4 | Ch6, 9, 12, 18 (DDODS replacements) |
| `generate_diagrams_5to7.py` | 3 | Ch14, 16, 19 (DDODS replacements) |
| `generate_diagrams_8to9.py` | 2 | Ch14, 16 (DDODS replacements) |
| `generate_diagrams_10to11.py` | 2 | Ch20 (DDODS replacements) |
| `generate_tier3_diagrams.py` | 8 | Ch17, 27, 28, 29, 31, 32 |
| *(remaining 30 generated by embedding agents)* | 30 | Ch5, 7-8, 10-11, 13, 15, 21-26 |
