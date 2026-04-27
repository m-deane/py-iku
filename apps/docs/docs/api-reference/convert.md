---
title: Convert
sidebar_position: 2
description: POST /convert and WS /convert/stream — synchronous and streaming code conversion endpoints.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Convert

## POST /convert

Convert Python code to a Dataiku flow synchronously. Maximum wall-clock timeout is 30 seconds.

### Request

```json
{
  "code": "import pandas as pd\ndf = pd.read_csv('data.csv')\n...",
  "mode": "rule",
  "provider": "anthropic",
  "model": null,
  "options": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Python source code. Max 256 KB. |
| `mode` | `"rule"` \| `"llm"` | No | Conversion mode. Default: `"rule"`. |
| `provider` | `"anthropic"` \| `"openai"` | No | LLM provider. Only used when `mode="llm"`. |
| `model` | string \| null | No | Model override (e.g. `"claude-opus-4-5"`). Default uses provider default. |
| `options` | object | No | Reserved for future options. |

### Response 200

```json
{
  "flow": {
    "recipes": [...],
    "datasets": [...],
    "name": "converted_flow",
    "metadata": {}
  },
  "score": {
    "complexity": 3.2,
    "cost_estimate": 0.012,
    "breakdown": []
  },
  "warnings": [
    {
      "level": "warning",
      "message": "Unrecognised pattern at line 12",
      "node_id": null
    }
  ]
}
```

The `flow` field is the `DataikuFlow.to_dict()` serialisation. The `score` field is the same payload as `POST /score`.

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Conversion succeeded |
| 400 | Invalid Python syntax (`InvalidPythonCodeError`) |
| 413 | Code exceeds `max_code_size_bytes` |
| 422 | Conversion failure or Pydantic validation error |
| 500 | Internal server error |
| 502 | LLM provider error |

### Example

```bash
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import pandas as pd\ndf = pd.read_csv(\"data.csv\")\nresult = df.groupby(\"cat\").agg({\"val\": \"sum\"})",
    "mode": "rule"
  }'
```

---

## WS /convert/stream

Convert Python code with real-time progress events over WebSocket.

### Connection

```
ws://localhost:8000/convert/stream
```

### Protocol

**Client → Server (first frame):**

```json
{
  "code": "...",
  "mode": "rule",
  "provider": "anthropic",
  "model": null
}
```

**Server → Client (event frames):**

```json
{
  "event": "started",
  "seq": 0,
  "ts": "2025-01-15T10:30:00.123Z",
  "payload": { "code_size_bytes": 1243 }
}
```

### Event types

| Event | When | Payload |
|-------|------|---------|
| `started` | Connection accepted | `{code_size_bytes}` |
| `ast_parsed` | AST analysis complete | `{statement_count}` |
| `recipe_created` | A new recipe node added | `{recipe_type, recipe_name}` |
| `processor_added` | A processor added to current PREPARE | `{processor_type, step_index}` |
| `optimized` | Flow optimisation complete | `{merged_prepare_count}` |
| `completed` | Full flow ready | Same as `POST /convert` response body |
| `error` | Conversion failed | `{type, message, status}` (RFC 7807) |

**Client → Server (cancellation):**

```json
{ "action": "cancel" }
```

The server closes the WebSocket cleanly on cancel. Partial results are discarded.

### Backpressure

The server buffers up to 10 frames per connection. If the client is slow to consume, the server pauses emission. If the buffer fills (> 30 s), the connection is closed with code 1008 (Policy Violation).
