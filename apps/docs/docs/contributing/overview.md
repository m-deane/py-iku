---
title: Contributing Overview
sidebar_position: 1
description: How to contribute to py-iku Studio — branches, commit conventions, and milestone naming.
---

# Contributing

## Getting started

1. Fork the repo and create a branch from `main` using the pattern `claude/<feature>-<id>` (for agent contributions) or `feat/<description>` (for human contributions).
2. Install dependencies: `pnpm install`.
3. Install Python dependencies: `pip install -e ".[dev]" && pip install -e "apps/api[dev]"`.
4. Start services: `docker compose up` or `pnpm dev:all`.
5. Run tests: `pnpm -r test && python -m pytest tests/ -q`.

## Branch and file scope

The repo has four ownership zones:

| Zone | Contents | Guard |
|------|---------|-------|
| Python library | `py2dataiku/`, `tests/` | `python-pro` role |
| API + web + packages | `apps/api/`, `apps/web/`, `packages/` | `code-reviewer` role |
| Docs | `apps/docs/`, `docs/` | `docusaurus-expert` role |
| Plans | `.claude_plans/` | All roles |

Do not modify files outside your zone without coordination.

## Pre-commit hooks

The repo uses `pre-commit`. After cloning, run:

```bash
pre-commit install
```

Hooks run on commit: `ruff`, `black`, `isort`, `mypy` (Python), `eslint`, `prettier` (Node).

## Testing expectations

- Every new feature in `py2dataiku/` needs a test in `tests/test_py2dataiku/`.
- Every new API route needs a test in `apps/api/tests/test_routes/`.
- Every new `flow-viz` component needs a Storybook story and a Vitest unit test.
- E2E smoke tests in `apps/web/tests/e2e/` for any new user-facing route.

See [CI Matrix](/operations/ci-matrix) for coverage gates.
