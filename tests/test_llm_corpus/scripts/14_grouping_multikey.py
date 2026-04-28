"""14: GROUPING — multi-key groupby + 3 aggregations."""
import pandas as pd

trades = pd.read_csv("trades.csv")

# Group by (book_id, product) with 3 aggregations
agg = trades.groupby(["book_id", "product"]).agg(
    total_notional=("notional", "sum"),
    avg_price=("price", "mean"),
    trade_count=("trade_id", "count"),
).reset_index()

agg.to_csv("trades_grouped.csv", index=False)
