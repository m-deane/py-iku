---
title: Diff View
sidebar_position: 3
description: Compare two flows side-by-side — rule-based vs LLM, or any two saved flows.
---

# Diff View

Route: `/diff`

The Diff View lets you compare two `DataikuFlow` objects side-by-side. The most common use-case is comparing the rule-based and LLM conversion results for the same Python code to evaluate conversion quality.

## Opening the diff

From the Convert page, after converting once, click **Diff** in the toolbar. Studio automatically populates:

- **Left**: the currently displayed flow (e.g. rule-based result).
- **Right**: an empty canvas ready for the second flow.

Convert again with LLM mode; the right canvas populates. Alternatively, load any saved flow by ID.

## What is compared

The diff is computed server-side via `POST /diff`. It returns three lists keyed by node id:

| List | Meaning |
|------|---------|
| `added[]` | Nodes present in B but not A |
| `removed[]` | Nodes present in A but not B |
| `changed[]` | Nodes present in both with different settings |

Nodes are identified by their deterministic id (derived from recipe type + input/output dataset names). Edge differences follow from node differences.

## Visual encoding

In the dual-canvas view:

- **Green border**: node added (only in B).
- **Red border**: node removed (only in A).
- **Orange border**: node changed — settings differ.
- **No border**: node identical in both flows.

Hovering a changed node opens a tooltip showing the differing fields (e.g. a JOIN that changed from `inner` to `left` join type).

## JSON diff panel

Below the dual canvas, a split JSON diff panel shows the raw `DataikuFlow.to_dict()` payloads with a character-level diff. Lines are colour-coded (green = added, red = removed) following standard unified-diff conventions.

## Saving a diff

Click **Save Diff Report** to download a JSON file containing both flows and the `diff` payload. This is useful for code review or for sharing with a team before importing into DSS.
