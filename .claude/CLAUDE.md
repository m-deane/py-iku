# Workflow Directives

These directives supplement the root `CLAUDE.md`.

## Core Rules

- Never use mock data, results or workarounds
- Implement tests after every checkpoint and verify all tests pass
- Update progress and project plans in `.claude_plans/`
- Write all tests to `tests/test_py2dataiku/`

## File Boundaries

**SAFE TO MODIFY**: `py2dataiku/`, `tests/`, `.claude_plans/`

**NEVER MODIFY**: `.git/`, `dist/`, `build/`
