---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/string-transform.html
fetched_at: 2026-04-29
category: processors
---

# Transform string

Perform a variety of encoding, decoding, and string transformations on one or several columns. Transformations are always done in-place. For more advanced transformations, use the [Formula processor](https://doc.dataiku.com/dss/latest/preparation/processors/formula.html).

## Options

**Column**

Apply transformation to the following:

*   A single column
*   An explicit list of columns
*   All columns matching a regex pattern
*   All columns

**Mode**

Select transformation to apply:

*   **Convert to uppercase/lowercase:** convert all text to upper or lower case
*   **Encode/decode URL:** form URL escape (`nice 7%` -> `nice%207%25`) or unescape (`nice%207%25` -> `nice 7%`)
*   **Escape/unescape XML entities:** replace `&lt;`, `&gt;`, and `&amp;` by `<`, `>` and `&` respectively in XML strings
*   **Escape/unescape Unicode values:** replace Unicode characters by their codepoint: `e` -> `é` or the opposite
*   **Remove leading/trailing whitespace**: trim
*   **Capitalize:** put a capital letter at the beginning of each cell
*   **Capitalize every word:** put a capital letter at the beginning of each word in the cell
*   **Normalize:** convert to lowercase, remove accents, and perform Unicode normalization (`Cafe` -> `cafe`)
*   **Truncate:** keep only the first N characters of the cell
