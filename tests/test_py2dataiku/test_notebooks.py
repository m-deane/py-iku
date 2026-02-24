"""Tests for example notebooks - ensures all code cells execute without errors."""
import json
import os
import pytest


NOTEBOOKS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "notebooks"
)

# Patterns that indicate Jupyter-only features that should be skipped
SKIP_PATTERNS = [
    "from IPython.display",
    "IPython.display",
    "display(SVG",
    "display(HTML",
]


def extract_code_cells(notebook_path):
    """Extract code cells from a notebook file."""
    with open(notebook_path, "r") as f:
        nb = json.load(f)
    cells = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            cells.append((i, source))
    return cells


def should_skip_cell(source):
    """Check if a cell should be skipped due to Jupyter-only features."""
    for pattern in SKIP_PATTERNS:
        if pattern in source:
            return True
    return False


def run_notebook(notebook_name):
    """Execute all code cells in a notebook and raise on first failure."""
    notebook_path = os.path.join(NOTEBOOKS_DIR, notebook_name)
    assert os.path.exists(notebook_path), f"Notebook not found: {notebook_path}"

    cells = extract_code_cells(notebook_path)
    namespace = {}
    skipped = 0

    for cell_idx, (nb_cell_num, source) in enumerate(cells):
        if should_skip_cell(source):
            skipped += 1
            continue
        try:
            exec(source, namespace)
        except Exception as e:
            pytest.fail(
                f"{notebook_name} cell {cell_idx} (nb#{nb_cell_num}) failed: "
                f"{type(e).__name__}: {e}\n\nCode:\n{source[:500]}"
            )

    return len(cells), skipped


def test_01_beginner():
    """Test that all code cells in 01_beginner.ipynb execute without errors."""
    total, skipped = run_notebook("01_beginner.ipynb")
    assert total > 0, "No code cells found"


def test_02_intermediate():
    """Test that all code cells in 02_intermediate.ipynb execute without errors."""
    total, skipped = run_notebook("02_intermediate.ipynb")
    assert total > 0, "No code cells found"


def test_03_advanced():
    """Test that all code cells in 03_advanced.ipynb execute without errors."""
    total, skipped = run_notebook("03_advanced.ipynb")
    assert total > 0, "No code cells found"


def test_04_expert():
    """Test that all code cells in 04_expert.ipynb execute without errors."""
    total, skipped = run_notebook("04_expert.ipynb")
    assert total > 0, "No code cells found"


def test_05_master():
    """Test that all code cells in 05_master.ipynb execute without errors."""
    total, skipped = run_notebook("05_master.ipynb")
    assert total > 0, "No code cells found"
