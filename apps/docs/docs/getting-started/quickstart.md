---
title: Quickstart
sidebar_position: 2
description: Clone the repo, start with Docker Compose, and convert your first Python script in under 5 minutes.
---

# Quickstart

## Prerequisites

- Docker 24+ and Docker Compose v2
- Git

No local Node or Python install required — everything runs in containers.

## 1. Clone

```bash
git clone https://github.com/m-deane/py-iku.git
cd py-iku
```

## 2. Configure API keys (optional but recommended)

LLM-mode conversion requires an API key. Rule-based mode works offline.

```bash
cp .env.example .env          # create from template if present
# edit .env and set one of:
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

If neither key is set, LLM mode will return a `502` error; rule-based mode always works.

## 3. Start

```bash
docker compose up
```

Services:

| Service | Port | URL |
|---------|------|-----|
| `api` | 8000 | http://localhost:8000 |
| `web` | 5173 | http://localhost:5173 |
| `docs` | 3000 | http://localhost:3000 |

## 4. Open the Studio

Navigate to **http://localhost:5173**. You will see the Convert page with a Monaco code editor pre-loaded with a sample pandas snippet.

## 5. Convert your first script

Paste the following into the editor:

```python
import pandas as pd

df = pd.read_csv("sales.csv")
df = df.dropna(subset=["amount"])
df = df.rename(columns={"amt": "amount"})

by_region = df.groupby("region").agg({"amount": "sum"}).reset_index()
merged = pd.merge(df, by_region, on="region", suffixes=("", "_total"))
result = merged.sort_values("amount", ascending=False)
result.to_csv("output.csv", index=False)
```

Click **Convert (Rule-based)** and a flow graph appears in the canvas panel on the right:

- A PREPARE recipe (dropna + rename)
- A GROUPING recipe
- A JOIN recipe
- A SORT recipe
- Input and output dataset nodes connected by edges

## 6. Try LLM mode

If you set an API key, switch to **LLM** mode in the toolbar. The streaming panel on the left shows event-by-event progress (`ast_parsed` → `recipe_created` → `completed`). The result is semantically richer — the LLM understands that `merge` is a JOIN, not a STACK, even in ambiguous cases.

Use the **Diff** tab to compare the two flows side-by-side.

## 7. Export

Click **Export** in the top toolbar. Choose a format:

- **JSON** — machine-readable `DataikuFlow.to_dict()` payload
- **YAML** — human-readable equivalent
- **SVG** — pixel-accurate Dataiku-styled diagram
- **ZIP** — bundle containing JSON + SVG + manifest

## Next steps

- Read the [Architecture](/getting-started/architecture) page to understand how the services fit together.
- Explore the [User Guide](/user-guide/convert-page) for each feature in depth.
- Check the [API Reference](/api-reference/overview) if you want to call the API directly.
