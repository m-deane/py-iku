---
title: Diff
sidebar_position: 4
description: POST /diff — compute the structural difference between two DataikuFlow objects.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Diff

## POST /diff

Compute the structural difference between two `DataikuFlow` objects. Returns lists of added, removed, and changed nodes keyed by node id.

### Request

```json
{
  "a": { ...DataikuFlow.to_dict()... },
  "b": { ...DataikuFlow.to_dict()... }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `a` | object | Yes | First flow (e.g. rule-based result). |
| `b` | object | Yes | Second flow (e.g. LLM result). |

### Response 200

```json
{
  "added": [
    {
      "node_id": "join_sales_summary",
      "type": "recipe",
      "recipe_type": "JOIN"
    }
  ],
  "removed": [
    {
      "node_id": "prepare_input_csv",
      "type": "recipe",
      "recipe_type": "PREPARE"
    }
  ],
  "changed": [
    {
      "node_id": "grouping_by_region",
      "type": "recipe",
      "recipe_type": "GROUPING",
      "diff": {
        "settings.aggregations": {
          "a": [{"column": "amount", "function": "sum"}],
          "b": [{"column": "amount", "function": "sum"}, {"column": "count", "function": "count"}]
        }
      }
    }
  ]
}
```

Nodes are identified by their deterministic id, which is derived from recipe type + input/output dataset names. This makes the diff stable across regenerations of the same logical flow.

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Diff computed (may be empty if flows are identical) |
| 422 | Invalid flow payload |
| 500 | Internal error |

### Example

```bash
curl -X POST http://localhost:8000/diff \
  -H "Content-Type: application/json" \
  -d '{
    "a": <rule-based flow>,
    "b": <llm flow>
  }'
```
