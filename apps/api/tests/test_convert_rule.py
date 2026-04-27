"""Tests for POST /convert with mode=rule using real py-iku examples."""

from __future__ import annotations

import pytest

from app.schemas.convert import ConvertResponse
from app.schemas.recipe import RecipeTypeEnum

# ---------------------------------------------------------------------------
# Representative pandas snippets taken from py2dataiku/examples/recipe_examples.py
# ---------------------------------------------------------------------------

SNIPPET_READ_CSV = """
import pandas as pd
df = pd.read_csv('data.csv')
df['name'] = df['name'].str.upper()
df.to_csv('out.csv', index=False)
"""

SNIPPET_GROUPBY = """
import pandas as pd
df = pd.read_csv('transactions.csv')
summary = df.groupby('category').agg({'amount': 'sum', 'quantity': 'mean'}).reset_index()
summary.to_csv('summary.csv', index=False)
"""

SNIPPET_MERGE = """
import pandas as pd
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
merged = pd.merge(customers, orders, on='customer_id', how='left')
merged.to_csv('customer_orders.csv', index=False)
"""

SNIPPET_SORT = """
import pandas as pd
df = pd.read_csv('products.csv')
sorted_df = df.sort_values('price', ascending=False)
sorted_df.to_csv('sorted_products.csv', index=False)
"""

SNIPPET_MELT = """
import pandas as pd
df = pd.read_csv('wide_data.csv')
melted = df.melt(id_vars=['id'], value_vars=['jan', 'feb', 'mar'],
                  var_name='month', value_name='value')
melted.to_csv('melted.csv', index=False)
"""

SNIPPET_SKLEARN = """
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

df = pd.read_csv('features.csv')
X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
"""

VALID_RECIPE_TYPES = {e.value for e in RecipeTypeEnum}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "snippet,label",
    [
        (SNIPPET_READ_CSV, "read_csv+prepare"),
        (SNIPPET_GROUPBY, "groupby_agg"),
        (SNIPPET_MERGE, "merge_left"),
        (SNIPPET_SORT, "sort_values"),
        (SNIPPET_MELT, "melt"),
        (SNIPPET_SKLEARN, "sklearn_pipeline"),
    ],
)
async def test_convert_rule_snippets(client, snippet: str, label: str) -> None:  # type: ignore[no-untyped-def]
    """Each snippet must return 200, parse as ConvertResponse, and have >0 recipes."""
    response = await client.post(
        "/convert",
        json={"code": snippet, "mode": "rule"},
    )
    assert response.status_code == 200, f"[{label}] got {response.status_code}: {response.text}"

    data = response.json()
    conv = ConvertResponse.model_validate(data)

    assert len(conv.flow.recipes) > 0, f"[{label}] expected at least one recipe"
    for recipe in conv.flow.recipes:
        assert recipe.type.value in VALID_RECIPE_TYPES, (
            f"[{label}] unknown recipe type: {recipe.type!r}"
        )


@pytest.mark.asyncio
async def test_convert_rule_returns_score(client) -> None:  # type: ignore[no-untyped-def]
    """Score must contain expected fields with sensible values."""
    response = await client.post(
        "/convert",
        json={"code": SNIPPET_GROUPBY, "mode": "rule"},
    )
    assert response.status_code == 200
    data = response.json()
    score = data["score"]
    assert score["recipe_count"] >= 0
    assert score["processor_count"] >= 0
    # dataset_count powers the DATASETS dashboard tile — must be present
    # and >= the number of datasets actually serialised in the flow.
    assert "dataset_count" in score
    assert score["dataset_count"] >= 0
    assert score["dataset_count"] == len(data["flow"]["datasets"])
    assert score["max_depth"] >= 0
    assert score["fan_out_max"] >= 0
    assert score["complexity"] >= 0.0


@pytest.mark.asyncio
async def test_convert_rule_flow_datasets_present(client) -> None:  # type: ignore[no-untyped-def]
    """All recipe inputs/outputs must be listed in datasets."""
    response = await client.post(
        "/convert",
        json={"code": SNIPPET_MERGE, "mode": "rule"},
    )
    assert response.status_code == 200
    data = response.json()
    dataset_names = {d["name"] for d in data["flow"]["datasets"]}
    for recipe in data["flow"]["recipes"]:
        for ref in recipe.get("inputs", []) + recipe.get("outputs", []):
            assert ref in dataset_names, f"Dataset '{ref}' missing from flow.datasets"
