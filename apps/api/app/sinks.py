"""FlowSink abstraction and built-in sinks.

A ``FlowSink`` is the seam between a ``DataikuFlow`` and an output medium.  The
in-process sinks (``JsonSink``, ``YamlSink``, ``ZipBundleSink``) produce
self-contained byte payloads that the export route streams back to the client.
``DSSApiSink`` is a forward-looking stub that signals (via ``capabilities()``)
that DSS write-back is not yet implemented; it raises ``NotImplementedError``
with a structured ``next_steps`` list when ``write()`` is invoked.

This file is referenced from:
  * ``apps/api/app/services/export_service.py`` (uses ``JsonSink``,
    ``YamlSink``, ``ZipBundleSink``)
  * ``apps/api/tests/test_sinks/test_sinks.py`` (covers all sinks including
    ``DSSApiSink``)
"""

from __future__ import annotations

import io
import json
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from py2dataiku.models.dataiku_flow import DataikuFlow

try:  # py-iku exposes the package version via importlib.metadata.
    from py2dataiku import __version__ as PY_IKU_VERSION
except Exception:  # pragma: no cover — fallback never normally reached
    PY_IKU_VERSION = "unknown"


# ---------------------------------------------------------------------------
# Result / capability dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SinkResult:
    """Output of a successful ``FlowSink.write`` invocation."""

    content: bytes
    media_type: str
    filename: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DryRunReport:
    """Metadata describing what a ``write()`` would produce."""

    media_type: str
    filename: str
    estimated_size_bytes: int | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SinkCapabilities:
    """Static capabilities advertised by a sink."""

    name: str
    supported: bool
    media_type: str
    description: str = ""
    next_steps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class FlowSink(ABC):
    """Abstract sink: writes a ``DataikuFlow`` to bytes (or remote system)."""

    @abstractmethod
    def write(self, flow: DataikuFlow, opts: dict[str, Any] | None = None) -> SinkResult:
        """Materialise the flow as a binary payload."""

    @abstractmethod
    def dry_run(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> DryRunReport:
        """Return metadata about what ``write()`` would produce, without doing it."""

    @abstractmethod
    def capabilities(self) -> SinkCapabilities:
        """Static info about what this sink supports."""


# ---------------------------------------------------------------------------
# JsonSink — DataikuFlow.to_json() bytes
# ---------------------------------------------------------------------------


class JsonSink(FlowSink):
    """Serialise the flow as JSON bytes."""

    media_type = "application/json"

    def write(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> SinkResult:
        indent = (opts or {}).get("indent", 2)
        content = flow.to_json(indent=indent).encode("utf-8")
        return SinkResult(
            content=content,
            media_type=self.media_type,
            filename=f"{flow.name}.json",
        )

    def dry_run(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> DryRunReport:
        # Approximate: serialise without indent for a tighter estimate
        return DryRunReport(
            media_type=self.media_type,
            filename=f"{flow.name}.json",
            estimated_size_bytes=len(flow.to_json(indent=0).encode("utf-8")),
        )

    def capabilities(self) -> SinkCapabilities:
        return SinkCapabilities(
            name="json",
            supported=True,
            media_type=self.media_type,
            description="Serialise the flow as JSON (round-trippable via from_dict).",
        )


# ---------------------------------------------------------------------------
# YamlSink — DataikuFlow.to_yaml() bytes
# ---------------------------------------------------------------------------


class YamlSink(FlowSink):
    """Serialise the flow as YAML bytes."""

    media_type = "application/x-yaml"

    def write(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> SinkResult:
        content = flow.to_yaml().encode("utf-8")
        return SinkResult(
            content=content,
            media_type=self.media_type,
            filename=f"{flow.name}.yaml",
        )

    def dry_run(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> DryRunReport:
        return DryRunReport(
            media_type=self.media_type,
            filename=f"{flow.name}.yaml",
            estimated_size_bytes=len(flow.to_yaml().encode("utf-8")),
        )

    def capabilities(self) -> SinkCapabilities:
        return SinkCapabilities(
            name="yaml",
            supported=True,
            media_type=self.media_type,
            description="Serialise the flow as YAML.",
        )


# ---------------------------------------------------------------------------
# ZipBundleSink — flow.json + flow.svg + manifest.json zipped
# ---------------------------------------------------------------------------


class ZipBundleSink(FlowSink):
    """Bundle the flow JSON, SVG, and a manifest into a zip archive."""

    media_type = "application/zip"

    def _build(self, flow: DataikuFlow, opts: dict[str, Any] | None) -> bytes:
        flow_json = flow.to_json(indent=2)
        # SVG is best-effort: if visualisation fails we still ship the JSON.
        try:
            svg_content: str | None = flow.visualize(format="svg")
        except Exception:
            svg_content = None

        manifest = {
            "flow_id": flow.name,
            "py_iku_version": PY_IKU_VERSION,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "format_versions": {
                "flow_json": "1",
                "flow_svg": "1" if svg_content is not None else None,
                "manifest": "1",
            },
            "files": [
                "flow.json",
                *(["flow.svg"] if svg_content is not None else []),
                "manifest.json",
            ],
        }

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("flow.json", flow_json)
            if svg_content is not None:
                zf.writestr("flow.svg", svg_content)
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        return buffer.getvalue()

    def write(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> SinkResult:
        content = self._build(flow, opts)
        return SinkResult(
            content=content,
            media_type=self.media_type,
            filename=f"{flow.name}.zip",
        )

    def dry_run(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> DryRunReport:
        return DryRunReport(
            media_type=self.media_type,
            filename=f"{flow.name}.zip",
            estimated_size_bytes=None,
            notes=["Bundles flow.json, flow.svg (if renderable), manifest.json"],
        )

    def capabilities(self) -> SinkCapabilities:
        return SinkCapabilities(
            name="zip",
            supported=True,
            media_type=self.media_type,
            description="Zipped bundle: flow.json + flow.svg + manifest.json.",
        )


# ---------------------------------------------------------------------------
# DSSApiSink — forward-looking stub, advertises supported=False
# ---------------------------------------------------------------------------


class DSSApiSink(FlowSink):
    """Stub sink for direct DSS REST API write-back.

    Not implemented — calling ``write()`` raises ``NotImplementedError`` with a
    structured ``next_steps`` list.  ``capabilities()`` advertises
    ``supported=False`` so feature flags can hide UI affordances.
    """

    media_type = "application/json"

    _NEXT_STEPS = [
        "Wire the dataikuapi client behind a feature flag.",
        "Provide a connection profile via /settings/connections.",
        "Implement project + recipe upsert with idempotency keys.",
        "Add a dry-run mode that diffs against the remote project.",
    ]

    def write(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> SinkResult:
        raise NotImplementedError(
            "DSSApiSink.write is not implemented. "
            f"Next steps: {self._NEXT_STEPS}"
        )

    def dry_run(
        self, flow: DataikuFlow, opts: dict[str, Any] | None = None
    ) -> DryRunReport:
        return DryRunReport(
            media_type=self.media_type,
            filename=f"{flow.name}.dss-stub",
            notes=["DSSApiSink is a placeholder; no remote call performed."],
        )

    def capabilities(self) -> SinkCapabilities:
        return SinkCapabilities(
            name="dss-api",
            supported=False,
            media_type=self.media_type,
            description="Direct DSS REST API write-back — future capability.",
            next_steps=list(self._NEXT_STEPS),
        )
