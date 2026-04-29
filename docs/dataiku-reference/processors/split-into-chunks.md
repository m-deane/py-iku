---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/split-into-chunks.html
fetched_at: 2026-04-29
category: processors
---

# Split into chunks

This processor splits text into chunks (one row per chunk) using a recursive splitter approach.

## Example use case

You want to perform embedding and semantic search on a corpus of text documents for Retrieval-Augmented Generation (RAG). Splitting the text into smaller chunks ensures that each piece of text can be embedded into a vector store efficiently.

## Output

For each chunk, a new row is generated. The row contains a copy of all other columns in the original row and a new chunk column.

## Options

*   **Maximum Chunk Size**: Define the maximum number of characters each chunk can contain. This helps to keep chunks within manageable sizes for embedding.

*   **Chunk Overlap**: Specify the number of characters that should overlap between consecutive chunks. This is useful for ensuring context continuity across chunks.

*   **Separators**: Specify the separators to consider for splitting the text. By default, the separators are (in the following order) double new lines, new line, space and between any character. The order of separators matters as the processor will apply them sequentially. You can add or remove separators as required.

*   Regular expressions can also be used to specify separators, providing additional flexibility for complex text structures.

*   **Keep Separators**: you can choose whether the separators should be kept in the output chunks or removed.
