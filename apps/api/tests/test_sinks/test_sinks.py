"""Unit tests for the FlowSink hierarchy in apps/api/app/sinks.py."""

from __future__ import annotations

import io
import json
import zipfile

import pytest
import yaml
from py2dataiku.models.dataiku_flow import DataikuFlow

from app.sinks import (
    DSSApiSink,
    JsonSink,
    SinkCapabilities,
    SinkResult,
    YamlSink,
    ZipBundleSink,
)


def _flow() -> DataikuFlow:
    payload = {
        "flow_name": "sinks_demo",
        "total_recipes": 1,
        "total_datasets": 2,
        "datasets": [
            {"name": "raw", "type": "input", "connection_type": "Filesystem", "schema": []},
            {"name": "out", "type": "output", "connection_type": "Filesystem", "schema": []},
        ],
        "recipes": [
            {
                "name": "r1",
                "type": "grouping",
                "inputs": ["raw"],
                "outputs": ["out"],
                "keys": ["x"],
                "aggregations": [],
            },
        ],
    }
    return DataikuFlow.from_dict(payload)


# ---------------------------------------------------------------------------
# JsonSink
# ---------------------------------------------------------------------------


class TestJsonSink:
    def test_write_round_trips_through_from_dict(self) -> None:
        flow = _flow()
        result = JsonSink().write(flow)
        assert isinstance(result, SinkResult)
        assert result.media_type == "application/json"
        assert result.filename.endswith(".json")
        rebuilt = DataikuFlow.from_dict(json.loads(result.content))
        assert rebuilt.name == "sinks_demo"
        assert len(rebuilt.recipes) == 1

    def test_capabilities_supported(self) -> None:
        caps = JsonSink().capabilities()
        assert isinstance(caps, SinkCapabilities)
        assert caps.supported is True
        assert caps.media_type == "application/json"

    def test_dry_run_estimates_size(self) -> None:
        report = JsonSink().dry_run(_flow())
        assert report.media_type == "application/json"
        assert report.estimated_size_bytes is not None
        assert report.estimated_size_bytes > 0


# ---------------------------------------------------------------------------
# YamlSink
# ---------------------------------------------------------------------------


class TestYamlSink:
    def test_write_round_trips(self) -> None:
        flow = _flow()
        result = YamlSink().write(flow)
        assert result.media_type == "application/x-yaml"
        assert result.filename.endswith(".yaml")
        parsed = yaml.safe_load(result.content)
        rebuilt = DataikuFlow.from_dict(parsed)
        assert rebuilt.name == "sinks_demo"

    def test_capabilities(self) -> None:
        caps = YamlSink().capabilities()
        assert caps.supported is True
        assert caps.name == "yaml"


# ---------------------------------------------------------------------------
# ZipBundleSink
# ---------------------------------------------------------------------------


class TestZipBundleSink:
    def test_write_produces_expected_files(self) -> None:
        flow = _flow()
        result = ZipBundleSink().write(flow)
        assert result.media_type == "application/zip"
        assert result.filename.endswith(".zip")

        bundle = zipfile.ZipFile(io.BytesIO(result.content))
        names = set(bundle.namelist())
        assert "flow.json" in names
        assert "manifest.json" in names
        # SVG is best-effort but the demo flow does render cleanly.
        assert "flow.svg" in names

    def test_manifest_has_expected_fields(self) -> None:
        flow = _flow()
        result = ZipBundleSink().write(flow)
        bundle = zipfile.ZipFile(io.BytesIO(result.content))
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["flow_id"] == "sinks_demo"
        assert "py_iku_version" in manifest
        assert "generated_at" in manifest
        assert "format_versions" in manifest
        assert manifest["format_versions"]["flow_json"] == "1"

    def test_inner_flow_json_round_trips(self) -> None:
        flow = _flow()
        result = ZipBundleSink().write(flow)
        bundle = zipfile.ZipFile(io.BytesIO(result.content))
        inner = json.loads(bundle.read("flow.json"))
        rebuilt = DataikuFlow.from_dict(inner)
        assert rebuilt.name == "sinks_demo"
        assert len(rebuilt.recipes) == 1

    def test_capabilities(self) -> None:
        caps = ZipBundleSink().capabilities()
        assert caps.supported is True
        assert caps.media_type == "application/zip"


# ---------------------------------------------------------------------------
# DSSApiSink — stub
# ---------------------------------------------------------------------------


class TestDSSApiSink:
    def test_capabilities_unsupported(self) -> None:
        caps = DSSApiSink().capabilities()
        assert caps.supported is False
        assert caps.name == "dss-api"
        assert caps.next_steps  # non-empty
        assert all(isinstance(step, str) for step in caps.next_steps)

    def test_write_raises_not_implemented(self) -> None:
        flow = _flow()
        with pytest.raises(NotImplementedError) as exc_info:
            DSSApiSink().write(flow)
        # Error message mentions next-step guidance.
        assert "not implemented" in str(exc_info.value).lower()
        assert "feature flag" in str(exc_info.value).lower()

    def test_dry_run_returns_metadata(self) -> None:
        flow = _flow()
        report = DSSApiSink().dry_run(flow)
        assert report.media_type == "application/json"
        assert "DSSApiSink" in " ".join(report.notes)
