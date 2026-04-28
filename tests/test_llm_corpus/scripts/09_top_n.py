"""09: TOP_N — sort_values + head (bug #5)."""
import pandas as pd

trades = pd.read_csv("trades.csv")

# Top 10 trades by notional — should map to TOP_N recipe (not SORT + SAMPLING)
top_trades = trades.sort_values("notional", ascending=False).head(10)

top_trades.to_csv("top_trades.csv", index=False)
