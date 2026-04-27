"""Tests for POST /export/{format}."""

from __future__ import annotations

import io
import json
import zipfile

import pytest
import yaml
from py2dataiku.models.dataiku_flow import DataikuFlow


def _ds(name: str, dtype: str = "intermediate") -> dict:
    return {
        "name": name,
        "type": dtype,
        "connection_type": "Filesystem",
        "schema": [],
    }


def _flow_dict() -> dict:
    """A small but valid flow with one grouping recipe."""
    return {
        "flow_name": "demo_flow",
        "total_recipes": 1,
        "total_datasets": 2,
        "datasets": [_ds("raw", "input"), _ds("agg", "output")],
        "recipes": [
            {
                "name": "groupby_1",
                "type": "grouping",
                "inputs": ["raw"],
                "outputs": ["agg"],
                "keys": ["x"],
                "aggregations": [],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Happy-path tests — one per format
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_json(client) -> None:  # type: ignore[no-untyped-def]
    payload = {"flow": _flow_dict()}
    response = await client.post("/export/json", json=payload)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".json" in cd
    # Round-trip through DataikuFlow.from_dict to prove the body is well-formed.
    parsed = json.loads(response.content)
    rebuilt = DataikuFlow.from_dict(parsed)
    assert rebuilt.name == "demo_flow"
    assert len(rebuilt.recipes) == 1


@pytest.mark.asyncio
async def test_export_yaml(client) -> None:  # type: ignore[no-untyped-def]
    payload = {"flow": _flow_dict()}
    response = await client.post("/export/yaml", json=payload)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/x-yaml")
    cd = response.headers.get("content-disposition", "")
    assert ".yaml" in cd
    parsed = yaml.safe_load(response.content)
    assert parsed["flow_name"] == "demo_flow"
    rebuilt = DataikuFlow.from_dict(parsed)
    assert rebuilt.name == "demo_flow"


@pytest.mark.asyncio
async def test_export_svg(client) -> None:  # type: ignore[no-untyped-def]
    payload = {"flow": _flow_dict()}
    response = await client.post("/export/svg", json=payload)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("image/svg+xml")
    body = response.content.decode("utf-8")
    assert body.lstrip().startswith("<")
    assert "<svg" in body or "<?xml" in body


@pytest.mark.asyncio
async def test_export_zip_bundle(client) -> None:  # type: ignore[no-untyped-def]
    payload = {"flow": _flow_dict()}
    response = await client.post("/export/zip", json=payload)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/zip")

    # Zip must contain flow.json + flow.svg + manifest.json.
    bundle = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(bundle.namelist())
    assert "flow.json" in names
    assert "manifest.json" in names
    # SVG is best-effort; the demo flow renders cleanly so it should be present.
    assert "flow.svg" in names

    manifest = json.loads(bundle.read("manifest.json"))
    assert manifest["flow_id"] == "demo_flow"
    assert "py_iku_version" in manifest
    assert "generated_at" in manifest
    assert "format_versions" in manifest

    # Inner flow.json must round-trip.
    inner = json.loads(bundle.read("flow.json"))
    rebuilt = DataikuFlow.from_dict(inner)
    assert rebuilt.name == "demo_flow"


@pytest.mark.asyncio
async def test_export_png(client) -> None:  # type: ignore[no-untyped-def]
    """PNG export uses py-iku's matplotlib visualizer."""
    pytest.importorskip("matplotlib")
    payload = {"flow": _flow_dict()}
    response = await client.post("/export/png", json=payload)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("image/png")
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".png" in cd
    # PNG magic bytes
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_export_png_with_dpi_opt(client) -> None:  # type: ignore[no-untyped-def]
    """PNG export should accept a custom DPI option."""
    pytest.importorskip("matplotlib")
    payload = {"flow": _flow_dict(), "opts": {"dpi": 100}}
    response = await client.post("/export/png", json=payload)
    assert response.status_code == 200, response.text
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_export_pdf(client) -> None:  # type: ignore[no-untyped-def]
    """PDF export wraps the SVG in HTML and renders via WeasyPrint."""
    pytest.importorskip("weasyprint")
    payload = {"flow": _flow_dict()}
    response = await client.post("/export/pdf", json=payload)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".pdf" in cd
    assert response.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_export_pdf_empty_flow(client) -> None:  # type: ignore[no-untyped-def]
    """PDF export should still produce a valid PDF for an empty flow."""
    pytest.importorskip("weasyprint")
    payload = {"flow": {"flow_name": "empty", "datasets": [], "recipes": []}}
    response = await client.post("/export/pdf", json=payload)
    assert response.status_code == 200, response.text
    assert response.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_export_png_empty_flow(client) -> None:  # type: ignore[no-untyped-def]
    """PNG export should still produce a valid PNG for an empty flow."""
    pytest.importorskip("matplotlib")
    payload = {"flow": {"flow_name": "empty", "datasets": [], "recipes": []}}
    response = await client.post("/export/png", json=payload)
    assert response.status_code == 200, response.text
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# Validation paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_invalid_format_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    payload = {"flow": _flow_dict()}
    response = await client.post("/export/docx", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_export_malformed_flow_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """A non-dict ``flow`` should produce a 422, not a 500."""
    response = await client.post("/export/json", json={"flow": "not a flow"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_export_missing_flow_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.post("/export/json", json={})
    assert response.status_code == 422
