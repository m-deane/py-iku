---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/tokenizer.html
fetched_at: 2026-04-29
category: processors
---

# Tokenize text

This processor tokenizes (splits in words) a text column.

## Example use case

You want to perform statistics on the words used in a product catalog or query log. "Tokenization allows you to handle words separately."

## Output

The tokenizer offers several output modes:

* **Convert to array**: An array (JSON-formatted) containing the words is generated, either in the input column or in another column. This mode is most useful if you intend to perform some custom processing and need to retain the structure of the original text.

* **One token per row**: in this mode, for each token, a new row is generated. The row contains a copy of all other columns in the original row. This mode is most useful if you intend to group by word afterwards.

* **One token per column**: in this mode, a new column is generated for each token. For example, if a column contains 4 words, and you use 'out_' as prefix, columns 'out_0', 'out_1', 'out_2' and 'out_3' will be generated.

## Simplification

Very often, you'll want to simplify the text to remove some variance in your text corpus. This processor offers several possible simplifications on the text to tokenize.

* **Normalize text**: transforms to lowercase, removes accents and performs Unicode normalization (Cafe -> cafe)

* **Clear stop words**: remove so-called 'stop words' (the, I, a, of, ...). This transformation is language-specific and requires you to enter the language of your column.

* **Stem words**: transforms each word into its 'stem', ie its grammatical root. For example, 'grammatical' is transformed to 'grammat'. This transformation is language-specific and requires you to enter the language of your column.

* **Sort words alphabetically**: sorts all words of the text. For example, 'the small dog' is transformed to 'dog small the'. This allows you to match together strings that are written with the same words in a different order.
