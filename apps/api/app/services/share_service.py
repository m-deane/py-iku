"""Share-with-fixtures helper.

Wraps :mod:`fixture_synthesizer` so the share routes can ask for a single
combined payload — flow body + per-input-dataset rows — without each
caller needing to know about the synthesizer's schema-discovery details.
"""

from __future__ import annotations

import base64
import json
from typing import Any, TypedDict

from .fixture_synthesizer import build_fixture_payload, find_input_datasets


class FixtureBundle(TypedDict):
    """Embedded fixture-data snapshot for a shared flow."""

    n_rows: int
    datasets: dict[str, list[dict[str, Any]]]


def build_share_bundle(
    flow: dict[str, Any], *, n_rows: int = 100
) -> FixtureBundle:
    """Return a fixture bundle for *flow* — at most *n_rows* per input dataset."""
    capped = max(0, min(int(n_rows), 100))
    return FixtureBundle(
        n_rows=capped,
        datasets=build_fixture_payload(flow, n_rows=capped),
    )


def encode_bundle_b64(bundle: FixtureBundle) -> str:
    """Base64-encode the bundle for embedding in URL-safe / share payloads."""
    raw = json.dumps(bundle, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def fixture_preview(
    flow: dict[str, Any], *, n_rows: int = 5
) -> dict[str, Any]:
    """Return a small inspectable preview describing each input dataset.

    Used by the Share modal's preview pane: lists each input dataset with
    its column count and a tiny sample of rows, capped tightly at 5 rows.
    """
    capped = max(0, min(int(n_rows), 25))
    datasets = []
    for ds in find_input_datasets(flow):
        cols = []
        schema = ds.get("schema") or []
        if isinstance(schema, list):
            for c in schema:
                if isinstance(c, str):
                    cols.append(c)
                elif isinstance(c, dict) and isinstance(c.get("name"), str):
                    cols.append(str(c["name"]))
        datasets.append({"name": ds.get("name"), "columns": cols})

    rows_by_name = build_fixture_payload(flow, n_rows=capped)
    for d in datasets:
        d["sample_rows"] = rows_by_name.get(d["name"] or "", [])
    return {"n_rows": capped, "datasets": datasets}
