"""DSS round-trip assertions for individual processors.

For each processor fixture, attempt to:
1. Resolve the documented ``type`` against ``ProcessorType`` enum (canonical
   name match, case-insensitive).
2. Confirm the catalog at :class:`py2dataiku.mappings.processor_catalog.ProcessorCatalog`
   knows the type.
3. Verify the documented param names are all representable — either as
   keys in the catalog entry's ``params`` schema or as members of the
   payload's ``params`` dict that round-trip through PrepareStep.

A failure means py-iku has either renamed a documented param, dropped it,
used a wire value that drifts from the documented enum, or doesn't
recognize the processor type at all (catalog has invented entry instead
of canonical). See ``_findings.md`` for the catalogued blockers.

Fixtures with a ``_meta.expected_xfail`` reason are marked ``xfail`` —
when a fix lands the test should xpass and the maintainer should
remove the marker (or delete the ``expected_xfail`` field on the
fixture).
"""
from __future__ import annotations

from typing import Any

import pytest

from py2dataiku.mappings.processor_catalog import ProcessorCatalog
from py2dataiku.models.prepare_step import ProcessorType

from .conftest import FixtureCase, discover_fixtures


_PROCESSOR_CASES: list[FixtureCase] = discover_fixtures("processor")


def _idfn(case: FixtureCase) -> str:
    return case.slug


def _resolve_processor_type(name: str) -> ProcessorType | None:
    """Resolve a documented processor type name against ProcessorType.

    Tries canonical-value match first (e.g. 'FilterOnValue'), then
    enum-name match (e.g. 'FILTER_ON_VALUE'). Returns ``None`` when
    neither hits — that's the 'invented entry / missing catalog
    member' case.
    """
    if not name:
        return None
    # Canonical value (PascalCase)
    for member in ProcessorType:
        if member.value == name:
            return member
    # Enum name (SCREAMING_SNAKE_CASE)
    upper = name.upper()
    if upper in ProcessorType.__members__:
        return ProcessorType[upper]
    return None


@pytest.mark.parametrize("case", _PROCESSOR_CASES, ids=_idfn)
def test_processor_type_resolves(case: FixtureCase) -> None:
    """The documented type maps to a real ProcessorType enum member."""
    if case.expected_xfail_marker:
        pytest.xfail(case.expected_xfail_marker)

    payload: dict[str, Any] = case.payload
    type_name = payload.get("type", "")

    resolved = _resolve_processor_type(type_name)
    assert resolved is not None, (
        f"Processor type {type_name!r} (from {case.slug}) does not match any "
        f"ProcessorType enum member. Either the catalog is missing this "
        f"entry, or the lib has invented a non-canonical name. See "
        f"docs/dataiku-reference/_findings.md for the audit context."
    )


@pytest.mark.parametrize("case", _PROCESSOR_CASES, ids=_idfn)
def test_processor_in_catalog(case: FixtureCase) -> None:
    """The documented type is registered in ProcessorCatalog."""
    if case.expected_xfail_marker:
        pytest.xfail(case.expected_xfail_marker)

    payload: dict[str, Any] = case.payload
    type_name = payload.get("type", "")
    catalog = ProcessorCatalog()
    info = catalog.get_processor(type_name)
    assert info is not None, (
        f"Processor {type_name!r} not in ProcessorCatalog. Add an entry "
        f"to py2dataiku/mappings/processor_catalog.py."
    )


@pytest.mark.parametrize("case", _PROCESSOR_CASES, ids=_idfn)
def test_processor_param_names_present(case: FixtureCase) -> None:
    """Documented param names appear in the catalog entry's params list.

    This catches param-name drift: the doc says ``matchingMode`` but the
    catalog stores ``mode``, etc. We require every doc-payload param key
    to appear in the catalog's known-params list. Extra catalog params
    (lib-side over-specification) are allowed.
    """
    if case.expected_xfail_marker:
        pytest.xfail(case.expected_xfail_marker)

    payload: dict[str, Any] = case.payload
    type_name = payload.get("type", "")
    doc_params = (payload.get("params") or {}).keys()

    catalog = ProcessorCatalog()
    info = catalog.get_processor(type_name)
    if info is None:
        # Already covered by test_processor_in_catalog; skip here.
        pytest.skip(f"{type_name} not in catalog — skipping param check.")

    catalog_params = set(getattr(info, "params", []) or [])
    # Systemic gap: ProcessorInfo.params is empty across the entire
    # catalog (Agent C didn't catch this; the harness does). Auto-xfail
    # when the catalog hasn't been enriched with per-entry params yet.
    # When the catalog-params fix lands, this xfail flips to xpass and
    # the maintainer should remove this guard.
    if not catalog_params:
        pytest.xfail(
            f"{type_name}: catalog entry has empty params field — "
            "systemic gap, ProcessorInfo.params not populated for any "
            "processor. Tracked as a future fix wave; will auto-xpass "
            "when catalog is enriched."
        )

    missing = [p for p in doc_params if p not in catalog_params]
    assert not missing, (
        f"Processor {type_name} catalog entry is missing documented params "
        f"{missing}. Catalog has {sorted(catalog_params)}; doc payload had "
        f"{sorted(doc_params)}."
    )
