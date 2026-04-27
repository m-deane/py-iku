---
title: Commit Conventions
sidebar_position: 3
description: Commit message format, milestone naming, and branch conventions for py-iku Studio.
---

# Commit Conventions

## Commit message format

Commit messages follow a `<scope> <description>` pattern with an optional body:

```
M5 streaming: add WebSocket event envelopes with seq + ts fields

- WsEventEnvelope schema in apps/api/app/schemas/events.py
- Streaming service emits seq-numbered frames
- Web app ws.ts consumes and renders incremental recipe nodes

https://claude.ai/code/session_...
```

The first line should be ≤ 72 characters. The body (separated by a blank line) lists key changes. The footer contains the session URL for agent-authored commits.

## Milestone naming

Prefix commits with the milestone they belong to:

| Pattern | Meaning |
|---------|---------|
| `M<n>:` | Main deliverable for milestone n |
| `M<n>a:`, `M<n>b:` | Sub-task or followup within milestone n |
| `M<n> <scope>:` | Milestone n, specific scope |

Examples:
- `M1 api: add POST /convert with Pydantic v2 schemas`
- `M3 flow-viz: add GROUPING and JOIN node components`
- `M8 e2e: add Playwright smoke test for /share/:token`
- `M9 docs: Docusaurus site + DSS write-back design`

## Branch naming

| Pattern | Use |
|---------|-----|
| `main` | Stable, deployed |
| `claude/<feature>-<id>` | Agent branches |
| `feat/<description>` | Human feature branches |
| `fix/<description>` | Bug fix branches |
| `docs/<description>` | Documentation-only changes |

## PR titles

PR titles should mirror the commit prefix pattern: `M<n> <scope>: <description>`.

## What NOT to do

- Do not amend published commits (use a new commit instead).
- Do not force-push to `main`.
- Do not skip pre-commit hooks (`--no-verify`) without explicit approval.
- Do not commit `.env` files, API keys, or secrets.
