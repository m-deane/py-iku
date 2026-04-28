"""21: Self-mutating chain — bug #2 (rebinding `trades` 4x)."""
import pandas as pd

trades = pd.read_csv("trades.csv")

# Rebind 1: drop nulls
trades = trades.dropna(subset=["counterparty_id", "notional"])

# Rebind 2: filter to only confirmed trades
trades = trades[trades["status"] == "CONFIRMED"]

# Rebind 3: add a derived column
trades = trades.assign(gross=trades["notional"] * trades["price"])

# Rebind 4: keep only top columns
trades = trades[["trade_id", "counterparty_id", "notional", "price", "gross"]]

trades.to_csv("trades_clean.csv", index=False)
