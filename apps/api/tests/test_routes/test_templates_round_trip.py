"""Round-trip every template through convert() and assert the recorded shape.

The key contract for the gallery: ``verifiedRecipes`` and ``verifiedDatasets``
in ``templates.json`` are NOT aspirational labels — they are the actual output
captured from a past ``convert(...)`` call. If py-iku's analyzer or optimizer
changes the produced shape, this test will surface it as a regression and the
template entry must be updated (or the analyzer's behaviour rolled back).

Each test:
  1. Fetches GET /templates/{id} (so the test path matches the user path).
  2. Runs ``convert(body['pythonSource'])``.
  3. Asserts the produced recipe-type list and dataset-name set match
     what the template recorded.
"""

from __future__ import annotations

import pytest
from py2dataiku import convert


# All 10 ids in the canonical order they appear in templates.json. Kept inline
# so a failure in /templates discovery doesn't mask a round-trip regression.
TEMPLATE_IDS = [
    "trade-ingestion-validation",
    "trade-dedup-multi-system",
    "book-mtm-eod",
    "pjm-lmp-tick-analytics",
    "forward-curve-scd",
    "mark-validation-vs-broker",
    "counterparty-features",
    "counterparty-exposure-rollup",
    "pjm-hub-locational-analysis",
    "trade-event-aggregation",
]


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
@pytest.mark.asyncio
async def test_template_round_trips_through_convert(client, template_id: str) -> None:  # type: ignore[no-untyped-def]
    """convert(pythonSource) must produce verifiedRecipes / verifiedDatasets.

    If this test fails, either:
      * the analyzer changed and templates.json needs updating, OR
      * the template script broke (in which case fix the script, re-run
        ``/Users/.../apps/api/.venv/bin/python -c ...``, and update the
        recorded shape).
    """
    response = await client.get(f"/templates/{template_id}")
    assert response.status_code == 200, response.text
    body = response.json()

    expected_recipes = body["verifiedRecipes"]
    expected_datasets = set(body["verifiedDatasets"])

    flow = convert(body["pythonSource"])
    actual_recipes = [r.recipe_type.value for r in flow.recipes]
    actual_datasets = {d.name for d in flow.datasets if d.name}

    assert actual_recipes == expected_recipes, (
        f"Template {template_id!r}: recipe shape drift.\n"
        f"  expected: {expected_recipes}\n"
        f"  actual:   {actual_recipes}"
    )
    assert actual_datasets == expected_datasets, (
        f"Template {template_id!r}: dataset name set drift.\n"
        f"  expected: {sorted(expected_datasets)}\n"
        f"  actual:   {sorted(actual_datasets)}"
    )


@pytest.mark.asyncio
async def test_round_trip_covers_all_ten_templates(client) -> None:  # type: ignore[no-untyped-def]
    """Sanity: the parametrised test list above stays aligned with the API."""
    response = await client.get("/templates")
    assert response.status_code == 200
    api_ids = {t["id"] for t in response.json()}
    assert api_ids == set(TEMPLATE_IDS), (
        f"Round-trip parametrisation drift. API: {sorted(api_ids)}, "
        f"test list: {sorted(TEMPLATE_IDS)}"
    )
