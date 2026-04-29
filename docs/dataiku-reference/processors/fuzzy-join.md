---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/fuzzy-join.html
fetched_at: 2026-04-29
category: processors
---

# Fuzzy join with other dataset (memory-based)

> Warning: **Deprecated**: Memory-based fuzzy join processor is deprecated. Use a dedicated fuzzy join recipe instead.

## Overview

This processor executes a fuzzy left join operation with another (small) dataset. "Fuzzy" indicates the join can match strings that are similar but not identical. Since processing occurs in memory, dataset size represents the primary limitation. For larger datasets, Dataiku recommends using the dedicated fuzzy join recipe.

## Example use case

Consider a dataset containing search queries with product name variations and typos. When you also have a product reference dataset, fuzzy join can identify the correct product despite imperfect spelling matches, enabling you to enrich queries with corresponding product details.

### Behaviour details

The processor performs a deduplicated left join with these characteristics:

- Unmatched rows in the 'other' dataset result in empty joined columns
- Multiple matches trigger selection of the closest match based on edit distance

## Requirements and limitations

The 'other' dataset must fit entirely in RAM, with a practical limit around 500,000 rows. Larger datasets require recipe-based approaches using Hive, Python, or SQL. Both datasets must contain a column designated as the join key.

## Fuzziness and simplification

The processor calculates string distance--essentially the differing character count. To improve match recall, text simplification is recommended. Available options include:

- **Normalize text**: Converts to lowercase, removes accents, performs Unicode normalization (Cafe -> cafe)
- **Clear stop words**: Removes common words like "the," "a," "of" (requires language specification)
- **Stem words**: Reduces words to grammatical roots (e.g., "grammatical" -> "grammat") (requires language specification)
- **Sort words alphabetically**: Reorders words to match different orderings (e.g., "the small dog" -> "dog small the")

## Parameters

Required configuration includes:

- Join key column in the current dataset
- Target dataset name (must reside in the same project)
- Join key column in the target dataset
- Columns from the target dataset to copy for matched rows
- Simplification options
- Maximum Damerau-Levenshtein distance threshold for match consideration

## Output

The processor outputs selected columns from the joined dataset. Each row receives data from the matching row in the joined dataset. Unmatched rows leave output columns empty.
