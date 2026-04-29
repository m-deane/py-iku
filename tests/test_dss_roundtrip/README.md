# DSS round-trip acceptance harness

This harness asserts that py-iku's recipe / processor serialization
preserves the documented Dataiku DSS wire shapes.

## Why

Agent C's cross-check at `docs/dataiku-reference/_findings.md` found ~40%
of documented processors missing from the lib catalog plus ~25 invented
catalog entries that DSS can't consume. This harness encodes those
findings as parametrized pytest cases so a fix-wave commit can be
validated end-to-end: as fixes land, `xfail` markers flip to `xpass` and
new `pass` rows appear.

## How it works

1. **Fixtures** at `fixtures/_seeds/{recipes,processors}/*.json` are
   hand-authored canonical DSS shapes derived from the public-doc
   snapshots at `docs/dataiku-reference/`. Each fixture has the envelope:

   ```json
   {
     "_meta": {
       "kind": "recipe" | "processor",
       "source_md": "docs/dataiku-reference/.../foo.md",
       "source_url": "https://doc.dataiku.com/dss/.../foo.html",
       "expected_xfail": "reason citing finding number, optional"
     },
     "payload": { ... the DSS wire shape ... }
   }
   ```

2. **Tests** at `test_recipe_roundtrip.py` and `test_processor_roundtrip.py`
   parametrize over every fixture of the matching kind (via
   `discover_fixtures()` in `conftest.py`).

3. **Auto-extractor** at `extract_fixtures.py` can pull additional fixtures
   from JSON code blocks inside the `docs/dataiku-reference/*.md`
   snapshots; auto-extracted fixtures land under
   `fixtures/{recipes,processors}/`. The seam handles both auto and seed
   directories transparently.

## Running

```bash
pytest tests/test_dss_roundtrip/ -v
```

Or just one category:

```bash
pytest tests/test_dss_roundtrip/test_processor_roundtrip.py -v
```

## Baseline (2026-04-29 – post FX wave)

| Outcome | Count | Meaning |
|---|---|---|
| **passed** | 57 | Round-trip clean — type resolves, in catalog, params line up |
| **xfailed** | 34 | Known drift documented in `_findings.md` (e.g. EmailSplitter, UnixTimestampParser) |
| **failed** | 0 | Catalog is in lockstep with the doc-canonical wire-name set |

History:
- **Initial baseline**: 44 / 34 / 13 — the 13 fails were a systemic
  empty-`ProcessorInfo.params` gap masking real drift.
- **FX-1 (auto-derive)**: 50 / 34 / 7 — `params` defaulted to
  `required+optional` post-init; surfaced 7 real wire-name mismatches
  (ColumnsSelector / DateParser / FilterOnFormula / FilterOnNumericRange /
  FoldMultipleColumns / IfThenElse / TranslateValues).
- **FX-1 follow-up (this wave)**: 57 / 34 / 0 — added each missing
  doc-canonical name to the catalog's `optional_params`. The lib-historical
  spellings remain accepted; the params dict round-trips opaquely so both
  shapes work.

## Fix-wave linkage

When a fix lands:

1. **Catalog drift fix** (e.g. rename `mode` → `matching_mode` in
   `processor_catalog.py`) — the matching xfail flips to xpass.
   Remove the `expected_xfail` field from the fixture meta.
2. **Settings-class addition** (e.g. add `SyncSettings`) — the
   matching recipe round-trip starts asserting the new fields and
   the xfail flips.
3. **Catalog `params` population** — all 13 currently-failing
   "missing params" tests turn green at once.

## Extending

Drop a new fixture under `fixtures/_seeds/{recipes,processors}/`:

```json
{
  "_meta": {
    "kind": "processor",
    "source_md": "docs/dataiku-reference/processors/<slug>.md",
    "source_url": "https://doc.dataiku.com/...",
    "notes": "what this fixture exercises"
  },
  "payload": { "type": "...", "params": { ... } }
}
```

Both test modules will pick it up on the next run.

## Failure interpretation

| Failure mode | Meaning | Where to fix |
|---|---|---|
| `test_processor_type_resolves` | Lib doesn't know the processor type | `py2dataiku/models/prepare_step.py` (add enum member) |
| `test_processor_in_catalog` | Type known but not registered | `py2dataiku/mappings/processor_catalog.py` |
| `test_processor_param_names_present` | Catalog has the processor but its `params` list is missing or has drifted names | `py2dataiku/mappings/processor_catalog.py` |
| `test_recipe_type_resolves` | Lib doesn't know the recipe type | `py2dataiku/models/dataiku_recipe.py` |
| `test_recipe_round_trip_preserves_canonical_fields` | Type / inputs / outputs renamed during serialization | `py2dataiku/models/dataiku_flow.py` or per-recipe `to_dict()` |

## CI integration

This harness runs on every PR via `.github/workflows/cross-format.yml`.
A new failure (not an existing xfail) means a regression — either the
catalog drifted or the docs caught up faster than the lib.
