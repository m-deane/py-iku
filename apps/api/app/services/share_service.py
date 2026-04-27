"""Share-with-fixtures helper.

Wraps :mod:`fixture_synthesizer` so the share routes can ask for a single
combined payload — flow body + per-input-dataset rows — without each
caller needing to know about the synthesizer's schema-discovery details.

Sprint 4D follow-up: the recipient-facing share payload now embeds fixtures
inline (gzip+base64) so a recipient can replay the flow against the
original rows without a separate downloadable bundle. Compression keeps
the embedded payload small even for the 100-row cap times every input
dataset.
"""

from __future__ import annotations

import base64
import gzip
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
    """Base64-encode the bundle for embedding in URL-safe / share payloads.

    Plain base64 — no compression. Suitable for small previews. For the
    inline-share-token payload prefer :func:`encode_bundle_gzip_b64`.
    """
    raw = json.dumps(bundle, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def encode_bundle_gzip_b64(bundle: FixtureBundle) -> str:
    """Compress with gzip then base64-encode — preferred for share payloads.

    Round-trip: ``decode_bundle_gzip_b64(encode_bundle_gzip_b64(bundle)) == bundle``.
    """
    raw = json.dumps(bundle, separators=(",", ":"), sort_keys=False).encode("utf-8")
    compressed = gzip.compress(raw, compresslevel=6)
    return base64.b64encode(compressed).decode("ascii")


def decode_bundle_gzip_b64(payload: str) -> FixtureBundle:
    """Inverse of :func:`encode_bundle_gzip_b64`. Raises ``ValueError`` on garbage."""
    try:
        compressed = base64.b64decode(payload.encode("ascii"), validate=True)
        raw = gzip.decompress(compressed)
        bundle = json.loads(raw.decode("utf-8"))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not decode fixture payload: {exc}") from exc
    if not isinstance(bundle, dict) or "datasets" not in bundle or "n_rows" not in bundle:
        raise ValueError("decoded payload is not a FixtureBundle")
    return FixtureBundle(
        n_rows=int(bundle.get("n_rows", 0) or 0),
        datasets=dict(bundle.get("datasets") or {}),
    )


def summarise_bundle(bundle: FixtureBundle) -> dict[str, Any]:
    """Return ``{n_datasets, total_rows}`` for the share-recipient indicator.

    The SharePage's "Includes fixture data" pill renders both numbers so the
    recipient knows what they're getting before clicking "Run with embedded
    fixtures".
    """
    datasets = bundle.get("datasets") or {}
    total_rows = 0
    for rows in datasets.values():
        if isinstance(rows, list):
            total_rows += len(rows)
    return {"n_datasets": len(datasets), "total_rows": total_rows}


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
