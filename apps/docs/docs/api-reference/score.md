---
title: Score
sidebar_position: 5
description: POST /score — compute complexity and cost estimate for a DataikuFlow.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Score

## POST /score

Compute a complexity and cost estimate for a flow. The score is deterministic — given the same `DataikuFlow.to_dict()` payload, it always returns the same result. It reuses `FlowGraph` metrics (node count, edge count, depth, branching factor).

### Request

```json
{
  "flow": { ...DataikuFlow.to_dict()... }
}
```

### Response 200

```json
{
  "complexity": 3.2,
  "cost_estimate": 0.012,
  "breakdown": [
    {
      "factor": "recipe_count",
      "value": 4,
      "weight": 0.4,
      "contribution": 1.6
    },
    {
      "factor": "prepare_step_count",
      "value": 6,
      "weight": 0.1,
      "contribution": 0.6
    },
    {
      "factor": "join_count",
      "value": 1,
      "weight": 0.5,
      "contribution": 0.5
    },
    {
      "factor": "max_depth",
      "value": 5,
      "weight": 0.1,
      "contribution": 0.5
    }
  ]
}
```

### Complexity score

The `complexity` field is a dimensionless float (typical range 1–20). It is computed from:

- Number of recipes (`recipe_count`)
- Number of PREPARE steps (`prepare_step_count`)
- Number of JOIN/FUZZY_JOIN/GEO_JOIN recipes (`join_count`)
- Maximum DAG depth (`max_depth`)
- Branching factor (number of SPLIT recipes)

### Cost estimate

The `cost_estimate` field is a rough DSS execution cost estimate in abstract "units". It is intended for relative comparison between flows, not as a real cost forecast. The estimate uses `FlowGraph` topology and does not know about actual data volumes or DSS cluster configuration.

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Score computed |
| 422 | Invalid flow payload |
