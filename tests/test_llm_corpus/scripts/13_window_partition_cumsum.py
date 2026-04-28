"""13: WINDOW — groupby + cumsum partition (running notional per book)."""
import pandas as pd

trades = pd.read_csv("trades.csv")
trades["trade_date"] = pd.to_datetime(trades["trade_date"])
trades = trades.sort_values(["book_id", "trade_date"])

# Running notional per book — partitioned WINDOW recipe with CUMULATIVE_SUM
trades["running_notional"] = trades.groupby("book_id")["notional"].cumsum()

trades.to_csv("trades_running.csv", index=False)
