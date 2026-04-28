"""25: Unicode + tricky column names."""
import pandas as pd

prices = pd.read_csv("prices_intl.csv")

# Rename to ASCII-friendly names
prices = prices.rename(columns={
    "price ($)": "price_usd",
    "日付": "trade_date",
    "société": "counterparty",
    "qté": "quantity",
})

# Drop nulls
prices = prices.dropna(subset=["price_usd", "trade_date"])

# Filter on a tricky-named original column reference no longer exists post-rename
prices = prices[prices["price_usd"] > 0]

prices.to_csv("prices_intl_clean.csv", index=False)
