---
title: Convert Page
sidebar_position: 1
description: How to use the Convert page — editor, mode selection, streaming, and toolbar actions.
---

# Convert Page

Route: `/convert`

The Convert page is the primary entry point. It is split into two panels: the **editor panel** (left) containing the Monaco code editor and conversion controls, and the **canvas panel** (right) showing the rendered flow graph.

## Editor panel

### Monaco code editor

The editor provides Python syntax highlighting, IntelliSense for pandas and numpy, and bracket matching. It is sized to fill the panel with a minimum height of 400px.

**Snippet gallery**: Click the **Snippets** button in the editor toolbar to open a drawer with pre-built pandas patterns (groupby, merge, pivot, rolling window, etc.). Selecting a snippet replaces the current editor content.

### Conversion mode

Two modes are available via a toggle in the editor toolbar:

| Mode | Engine | Network | Speed |
|------|--------|---------|-------|
| Rule-based | AST (`CodeAnalyzer`) | Offline | Fast (< 1 s) |
| LLM | `LLMCodeAnalyzer` via Anthropic / OpenAI | Requires API key | Up to 30 s |

The default mode is **rule-based**. The server enforces a 256 KB code size limit regardless of mode.

### Streaming progress

When using LLM mode or clicking **Stream**, the left panel switches to a streaming log showing real-time WebSocket events:

```
[0ms]  started      — code received, size 1.2 KB
[12ms] ast_parsed   — 8 statements identified
[340ms] recipe_created — PREPARE (dropna, rename)
[510ms] recipe_created — GROUPING (region → amount_sum)
[680ms] recipe_created — JOIN (inner, on=region)
[820ms] recipe_created — SORT (amount DESC)
[840ms] optimized    — merged 1 PREPARE step
[841ms] completed    — 4 recipes, 5 datasets
```

The canvas panel updates incrementally as each `recipe_created` event arrives — you see nodes appear one by one.

### Toolbar actions

| Button | Action |
|--------|--------|
| Convert | Sends `POST /convert`, replaces canvas |
| Stream | Sends WS `/convert/stream`, animates canvas |
| Clear | Resets editor and canvas |
| Diff | Opens diff view comparing current canvas to previous (or rule vs LLM) |
| Export | Opens export modal |
| Share | Generates a share link (requires flow to be saved first) |
| Save | Persists flow via `POST /flows` |

## Canvas panel

The canvas uses `packages/flow-viz` `FlowCanvas`. Interaction:

- **Pan**: drag the background.
- **Zoom**: scroll wheel or pinch gesture (trackpad).
- **Select node**: click — opens the **Inspector panel** as a right-side drawer.
- **Multi-select**: shift-click or drag a selection box.
- **Minimap**: toggle via the minimap button (bottom right).
- **Focus mode**: click the Focus button (top right) to collapse non-selected paths.

Node colours match the design tokens in `docs/design/tokens.json`. Each recipe type has a distinct colour family; dataset nodes are colour-coded by role (input, intermediate, output).

## Validation panel

A collapsible panel at the bottom of the canvas shows validation warnings from the `ConvertResponse.warnings[]` array. Each warning links to the relevant node. See [Validation Panel](/user-guide/validation-panel) for full details.
