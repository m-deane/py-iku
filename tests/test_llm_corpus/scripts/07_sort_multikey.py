"""07: SORT — multi-key descending."""
import pandas as pd

positions = pd.read_csv("positions.csv")

# Multi-key descending sort
sorted_positions = positions.sort_values(
    by=["trade_date", "notional"],
    ascending=[False, False],
)

sorted_positions.to_csv("positions_sorted.csv", index=False)
