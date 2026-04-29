---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/enrich-with-build-context.html
fetched_at: 2026-04-29
category: processors
---

# Enrich with build context

This processor adds columns containing information about the current build context, when available.

The following information can be added:

* Build date: date when the job started
* Job ID: ID of the job that ran the Prepare recipe

Additionally, this processor will not output any valid data when designing the preparation. The data will only be filled when actually running the recipe.
