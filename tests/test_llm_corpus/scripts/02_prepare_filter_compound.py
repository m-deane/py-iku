"""02: PREPARE + compound filter — bug #8 (df[(a > 5) & (b < 10)])."""
import pandas as pd

trades = pd.read_csv("trades.csv")

# Compound numeric filter — should map to FilterOnFormula with GREL
filtered = trades[(trades["quantity"] > 5) & (trades["price"] < 10)]

filtered.to_csv("trades_filtered.csv", index=False)
