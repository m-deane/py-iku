"""04: JOIN — left, right, inner, outer mixed across multiple merges."""
import pandas as pd

trades = pd.read_csv("trades.csv")
counterparties = pd.read_csv("counterparties.csv")
books = pd.read_csv("books.csv")
desks = pd.read_csv("desks.csv")

# Inner join trades with counterparties
enriched = trades.merge(counterparties, on="counterparty_id", how="inner")

# Left join with books
enriched = enriched.merge(books, on="book_id", how="left")

# Outer join with desks (preserve everything)
enriched = enriched.merge(desks, on="desk_id", how="outer")

enriched.to_csv("trades_enriched.csv", index=False)
