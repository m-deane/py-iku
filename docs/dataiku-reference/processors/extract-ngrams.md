---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/extract-ngrams.html
fetched_at: 2026-04-29
category: processors
---

# Extract ngrams

This processor extracts sequences of words, called _ngrams_, from a text column.

## What are ngrams ?

For example, for text 'the quick brown fox jumps', the ngrams are:

*   ngrams of size 2 (also called 2-grams) : the quick, quick brown, brown fox, fox jumps

*   ngrams of size 3 (also called 3-grams): the quick brown, quick brown fox, brown fox jumps

## Example use case

You want to perform statistics on the sequence of words used in a query log.

## Output

The NGram extractor offers several output modes:

*   Convert to JSON: A JSON array containing the ngrams is generated, either in the input column or in another column. This mode is most useful if you intend to perform some custom processing and need to retain the structure of the original text.

*   One ngram per row: in this mode, for each ngram, a new row is generated. The row contains a copy of all other columns in the original row. This mode is most useful if you intend to group by ngram afterwards.

*   One ngram per column: in this mode, a new column is generated for each ngram. For example, if a column contains 4 words, you ask for 2-grams, and you use 'out\_' as prefix, columns 'out\_0', 'out\_1' and 'out\_2' will be generated.

## Simplification

Very often, you'll want to simplify the text to remove some variance in your text corpus. This processor offers several possible simplifications on the text before extracting ngrams.

*   Normalize text: transforms to lowercase, removes accents and performs Unicode normalization (Cafe -> cafe)

*   Clear stop words: remove so-called 'stop words' (the, I, a, of, ...). This transformation is language-specific and requires you to enter the language of your column.

*   Stem words: transforms each word into its 'stem', ie its grammatical root. For example, 'grammatical' is transformed to 'grammat'. This transformation is language-specific and requires you to enter the language of your column.

*   Sort words alphabetically: sorts all words of the text. For example, 'the small dog' is transformed to 'dog small the'. This allows you to match together strings that are written with the same words in a different order.

Note: it is strongly advised to clear stop words before extracting ngrams

## Advanced options

*   Split on sentence boundaries: Generally, you don't want to compute cross-sentence ngrams. For example, with text 'The rain falls. The sun shines', you don't want to generate 'falls the' as a ngram.

*   Compute skip-grams : In our sample sentence, the skip-grams would be: the brown, the fox, the jumps, quick fox, quick jumps, ... Enabling skip-grams computation dramatically increases output size and computation requirements.
