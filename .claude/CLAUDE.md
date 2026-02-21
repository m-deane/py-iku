# PROJECT CONTEXT & CORE DIRECTIVES

## Project Overview

**py-iku** is a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams.

**Technology Stack**: Python
**Architecture**: Library/Package

## WORKFLOW - Core guidelines

- Never use mock data, results or workarounds
- Implement tests after every checkpoint and verify all tests pass
- Update progress and project plans in the ".claude_plans" directory
- Write all tests to the "tests/" folder
- Do not leave files in the root directory - organize into appropriate folder locations

## File Structure & Boundaries

**SAFE TO MODIFY**:
- `/py2dataiku/` - Main library source code
- `/tests/` - Test files
- `/.claude_plans/` - Planning documents

**NEVER MODIFY**:
- `/.git/` - Version control
- `/dist/` or `/build/` - Build outputs

## Code Style Standards

**Python Naming Conventions**:
- Variables: snake_case
- Functions: snake_case with descriptive verbs
- Classes: PascalCase
- Constants: SCREAMING_SNAKE_CASE
- Files: snake_case

## Testing Requirements

- Use pytest framework
- All tests in `tests/test_py2dataiku/`
- Current test count: 1693 tests (all should pass)
- Run with: `python -m pytest tests/ -v`

## Development Guidelines

See main `CLAUDE.md` at repository root for:
- Architecture overview
- Recipe and processor types
- Examples registry
- Adding new features
