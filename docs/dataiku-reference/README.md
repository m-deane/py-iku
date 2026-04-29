# Dataiku DSS Documentation Snapshot

**Snapshot date:** 2026-04-29

**Agent commit SHA:** `c83ed9be8fcd218bc566a1a87377e0d88e668080`

## Source URL list

The four canonical roots crawled (plus inbound links followed one level deep):

1. https://doc.dataiku.com/dss/latest/preparation/index.html (Prepare-recipe / Data Preparation index)
2. https://doc.dataiku.com/dss/latest/preparation/processors/ (individual processor pages)
3. https://doc.dataiku.com/dss/latest/recipes/ (visual-recipes index — returns 404 at `recipes/`; the visual-recipe pages live under `other_recipes/`, which were enumerated from the main DSS docs root and followed)
4. https://doc.dataiku.com/dss/latest/ (main reference root)

## Total page count by category

| Category | Page count |
|----------|-----------|
| recipes | 14 |
| processors | 95 |
| settings | 7 |
| **Total** | **116** |

(Excludes the four `_index.md` / `README.md` files in this folder.)

## Layout

```
docs/dataiku-reference/
├── README.md                     ← this file
├── recipes/
│   ├── _index.md                 ← every recipe page with slug + URL + 1-line summary
│   ├── distinct.md
│   ├── fuzzy-join.md
│   ├── geojoin.md
│   ├── grouping.md
│   ├── join.md
│   ├── pivot.md
│   ├── prepare.md
│   ├── sampling.md
│   ├── sort.md
│   ├── split.md
│   ├── stack.md
│   ├── sync.md
│   ├── topn.md
│   └── window.md
├── processors/
│   ├── _index.md                 ← every processor page with category + URL + 1-line summary
│   └── <95 individual processor pages>.md
└── settings/
    ├── _index.md                 ← every settings page with URL + 1-line summary
    ├── copy-steps.md
    ├── dates.md
    ├── engines.md
    ├── filter-flag.md
    ├── geographic.md
    ├── reshaping.md
    └── sampling.md
```

## Frontmatter

Every page begins with YAML frontmatter of the form:

```yaml
---
source_url: https://doc.dataiku.com/dss/latest/...
fetched_at: 2026-04-29
category: recipes | processors | settings
---
```

The H1 title is pulled from the source page; the body is faithful markdown of the source page contents.

## URLs that failed

None failed terminally. Notes on encountered issues:

* `https://doc.dataiku.com/dss/latest/recipes/` returns 404 — the visual-recipe documentation actually lives under `other_recipes/`. Recipe URLs were obtained by enumerating links from the main DSS docs root (https://doc.dataiku.com/dss/latest/), not the non-existent `recipes/` index.
* The Prepare-recipe processors index (https://doc.dataiku.com/dss/latest/preparation/processors/) initially served URLs prefixed with `data-preparation/processors/...`, which all return 404. The valid path prefix is `preparation/processors/...`. All processor pages were re-fetched on the valid path successfully.
* Some processor reference pages have very brief source content (e.g. `column-copy`, `move-columns`, `negate`, `array-sort`, `fold-object`, `merge-long-tail-values`, `measure-normalize`, `meaning-translate`, `transpose`, `fill-column`); their snapshot files are correspondingly short — this reflects the upstream documentation, not truncation.

No 429 or 503 responses were encountered during the snapshot. All non-success responses were 404s for the two URL-pattern issues above, which were corrected and re-fetched.

## robots.txt compliance

`https://doc.dataiku.com/robots.txt` was checked at start; it disallows `/dss/<old-version>/` paths and `/display/DSS<n>/`. The `dss/latest/` path used here is permitted. No disallowed URLs were fetched.

## License disclaimer

This snapshot is captured for cross-reference review purposes only. Authoritative source: https://doc.dataiku.com/dss/latest/. Each page links back to its origin URL via the `source_url` frontmatter.
