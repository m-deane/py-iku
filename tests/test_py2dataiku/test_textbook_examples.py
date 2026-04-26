"""Verify that textbook code examples are syntactically valid and that every
public symbol referenced in chapter imports actually exists in py-iku.

The textbook lives at ``docs/textbook/01-*.md`` through ``12-*.md``. Each
chapter contains a sequence of fenced ``python`` blocks. Some blocks are
self-contained (``convert(source_string)``); others depend on variables defined
earlier in the chapter (``flow = convert(...); print(len(flow.recipes))``).

This verifier does three things:

1. **Compile every block** — every fenced ``python`` block must parse as valid
   Python. This catches typos, mismatched brackets, and broken indentation.
2. **Resolve every ``from py2dataiku...`` import** — every name imported from
   ``py2dataiku`` (or one of its submodules) in a textbook block must resolve
   to a real attribute. This catches doc rot caused by renames.
3. **Run a known-good rule-based example end-to-end** — at least one chapter
   block from the V1 → V5 running-example progression is executed against the
   real ``convert`` to prove the documented shape still holds.

The verifier deliberately does NOT run every block. Many blocks reference
fictional CSVs, mid-chapter variables, or LLM calls that need an API key.
Running those would either require synthetic-data scaffolding or produce false
failures unrelated to documentation accuracy. Compile + import-resolution +
spot-execution is the right level of rigor for this corpus.
"""

from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import pytest

TEXTBOOK_DIR = Path(__file__).resolve().parents[2] / "docs" / "textbook"

CHAPTER_FILES = sorted(TEXTBOOK_DIR.glob("[0-9][0-9]-*.md"))
EXAMPLE_FILES = sorted(TEXTBOOK_DIR.glob("examples-*.md"))
APPENDIX_FILES = sorted(TEXTBOOK_DIR.glob("appendix-*.md"))
INDEX_FILE = TEXTBOOK_DIR / "index.md"

CODE_BLOCK_RE = re.compile(r"```python\n(.*?)\n```", re.DOTALL)


def _extract_blocks(path: Path) -> list[str]:
    return CODE_BLOCK_RE.findall(path.read_text())


def _all_textbook_files() -> list[Path]:
    return [INDEX_FILE, *CHAPTER_FILES, *EXAMPLE_FILES, *APPENDIX_FILES]


# ----------------------------------------------------------------------------
# Test 1: every block parses
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path", _all_textbook_files(), ids=lambda p: p.name
)
def test_every_python_block_parses(path: Path) -> None:
    """Every fenced python block in every textbook file must be valid Python."""
    blocks = _extract_blocks(path)
    if not blocks:
        pytest.skip(f"{path.name}: no python blocks")

    failures: list[tuple[int, str]] = []
    for i, block in enumerate(blocks, 1):
        try:
            ast.parse(block)
        except SyntaxError as e:
            failures.append((i, f"block {i}: {e}"))

    assert not failures, (
        f"{path.name}: {len(failures)} block(s) failed to parse:\n"
        + "\n".join(msg for _, msg in failures)
    )


# ----------------------------------------------------------------------------
# Test 2: every py2dataiku import in textbook blocks resolves
# ----------------------------------------------------------------------------


def _collect_py2dataiku_imports() -> dict[Path, list[tuple[str, str]]]:
    """Return ``{file: [(module, name), ...]}`` for every py2dataiku import.

    Includes both ``from py2dataiku import X`` and ``from py2dataiku.sub import Y``.
    """
    out: dict[Path, list[tuple[str, str]]] = {}
    for path in _all_textbook_files():
        for block in _extract_blocks(path):
            try:
                tree = ast.parse(block)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if not node.module or not node.module.startswith("py2dataiku"):
                    continue
                for alias in node.names:
                    out.setdefault(path, []).append((node.module, alias.name))
    return out


_IMPORTS = _collect_py2dataiku_imports()
_IMPORT_PARAMS = [
    (path.name, module, name)
    for path, items in _IMPORTS.items()
    for module, name in items
]


@pytest.mark.parametrize(
    ("file_name", "module", "name"),
    _IMPORT_PARAMS,
    ids=[f"{f}::{m}.{n}" for f, m, n in _IMPORT_PARAMS],
)
def test_textbook_imports_resolve(file_name: str, module: str, name: str) -> None:
    """Every ``from py2dataiku...`` import in the textbook must resolve."""
    mod = importlib.import_module(module)
    assert hasattr(mod, name), (
        f"{file_name}: `from {module} import {name}` — "
        f"{module} has no attribute {name!r}"
    )


# ----------------------------------------------------------------------------
# Test 3: documented running-example V1 round-trips through convert()
# ----------------------------------------------------------------------------


def test_running_example_v1_executes() -> None:
    """Chapter 2's V1 example must convert into a single PREPARE recipe.

    Asserts only the structurally stable facts the chapter rests on. The
    rule-based AST analyzer's output-dataset naming is heuristic; the LLM path
    (Chapter 7) recovers the documented ``orders_clean`` name.
    """
    from py2dataiku import RecipeType, convert

    source = """
import pandas as pd

orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
"""
    flow = convert(source)

    assert len(flow.recipes) == 1
    assert flow.recipes[0].recipe_type == RecipeType.PREPARE

    assert "orders" in {d.name for d in flow.datasets}
    assert flow.input_datasets and flow.input_datasets[0].name == "orders"

    step_types = [s.processor_type.value for s in flow.recipes[0].steps]
    assert "FillEmptyWithValue" in step_types
    assert "ColumnRenamer" in step_types


# ----------------------------------------------------------------------------
# Test 4: every chapter has at least one Python block
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path", CHAPTER_FILES, ids=lambda p: p.name
)
def test_every_chapter_has_python_blocks(path: Path) -> None:
    """Every numbered chapter must demonstrate code, not just prose."""
    assert _extract_blocks(path), f"{path.name}: no python blocks found"


# ----------------------------------------------------------------------------
# Test 5: textbook is wired into mkdocs nav
# ----------------------------------------------------------------------------


def test_mkdocs_nav_lists_every_chapter() -> None:
    """All 12 chapters + 3 appendices + foreword must appear in mkdocs.yml nav."""
    mkdocs = (TEXTBOOK_DIR.parent.parent / "mkdocs.yml").read_text()
    expected = [p.name for p in _all_textbook_files()]
    missing = [name for name in expected if name not in mkdocs]
    assert not missing, f"mkdocs.yml is missing nav entries for: {missing}"
