---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/simplify-text.html
fetched_at: 2026-04-29
category: processors
---

# Simplify text

Perform various simplifications on a text column.

## Options

- **Normalize text**: Transform to lowercase, remove punctuation and accents and perform Unicode NFD normalization (`Cafe` -> `cafe`).

- **Stem words:** Transform each word into its "stem", i.e. its grammatical root. For example, `grammatical` is transformed to `grammat`. This transformation is language-specific.

- **Clear stop words**: Remove so-called "stop words" (`the`, `I`, `a`, `of`, ...). This transformation is language-specific.

- **Sort words alphabetically:** Sorts all words of the text. For example, `the small dog` is transformed to `dog small the`, allowing strings containing the same words in different order to be matched.

## Note

Other processors with text operation -- tokenization, n-gram extraction, fuzzy join -- benefit from built-in text simplification options. You do not need to perform text simplification separately prior to using them.
