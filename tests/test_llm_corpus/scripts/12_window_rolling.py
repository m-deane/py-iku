"""12: WINDOW — groupby + rolling mean (rolling 5-day average price)."""
import pandas as pd

prices = pd.read_csv("prices.csv")
prices["trade_date"] = pd.to_datetime(prices["trade_date"])
prices = prices.sort_values(["ticker", "trade_date"])

# Rolling 5-day mean per ticker — should map to WINDOW recipe
prices["rolling_mean_5d"] = (
    prices.groupby("ticker")["close"].rolling(window=5).mean().reset_index(level=0, drop=True)
)

prices.to_csv("prices_with_rolling.csv", index=False)
