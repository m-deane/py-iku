---
title: Validation Panel
sidebar_position: 5
description: Understanding and resolving flow validation warnings shown in the validation panel.
---

# Validation Panel

The Validation Panel is a collapsible drawer at the bottom of the canvas. It surfaces the `warnings[]` array from the `ConvertResponse` and any structural issues detected in the `FlowGraph`.

## Warning sources

Warnings come from two places:

1. **Conversion warnings** — returned by the API in `ConvertResponse.warnings[]`. These are raised by `py2dataiku` during conversion (e.g. an unrecognised pandas pattern, a missing column reference, a truncated LLM response).

2. **Graph warnings** — computed client-side by `packages/flow-viz` after rendering. These include:
   - Disconnected nodes (no path from any source).
   - Cycles detected in the DAG (would cause infinite loops in DSS).
   - Recipes with zero inputs or zero outputs.
   - Dataset names that clash (two nodes with the same name).

## Severity levels

| Level | Colour | Meaning |
|-------|--------|---------|
| `error` | Red | Structural problem that will prevent DSS import |
| `warning` | Orange | Possible issue — review before import |
| `info` | Blue | Informational; no action required |

## Warning cards

Each warning card shows:

- Severity icon.
- Warning message.
- Affected node id (click to highlight that node on the canvas).
- Source tag (`conversion` or `graph`).

## Common warnings and resolutions

| Warning | Cause | Resolution |
|---------|-------|-----------|
| `Unrecognised pandas pattern at line N` | AST analyser could not classify a statement | Switch to LLM mode for semantic understanding |
| `Missing column reference: 'col'` | A column used in an operation was not defined in scope | Check the source dataset schema |
| `Cycle detected: A → B → A` | Circular dependency in the generated flow | This is a conversion bug — open an issue |
| `Disconnected node: recipe_X` | No path from any source dataset to this recipe | The code may have conditional branches that the rule-based analyser missed |
| `LLM response truncated` | The LLM hit its output token limit | Reduce input code size, or increase `max_tokens` in settings |

## Suppressing warnings

Warnings persist in the panel until the next conversion. There is no per-warning suppression UI in M8; this is planned for M10.
