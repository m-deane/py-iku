"""23: Deep flow — 12-recipe chain."""
import pandas as pd

t = pd.read_csv("trades.csv")
b = pd.read_csv("books.csv")
c = pd.read_csv("counterparties.csv")

# 1. Drop nulls
t = t.dropna(subset=["trade_id"])
# 2. Rename
t = t.rename(columns={"cp_id": "counterparty_id"})
# 3. Cast
t["notional"] = t["notional"].astype(float)
# 4. Filter
t = t[t["status"] == "CONFIRMED"]
# 5. Join with books
t = t.merge(b, on="book_id", how="left")
# 6. Join with counterparties
t = t.merge(c, on="counterparty_id", how="inner")
# 7. Sort
t = t.sort_values("trade_date")
# 8. Distinct
t = t.drop_duplicates(subset=["trade_id"])
# 9. Group/aggregate
g = t.groupby(["book_id", "trade_date"]).agg(daily_notional=("notional", "sum")).reset_index()
# 10. Window cumsum
g = g.sort_values(["book_id", "trade_date"])
g["cum_notional"] = g.groupby("book_id")["daily_notional"].cumsum()
# 11. Top N
top = g.sort_values("cum_notional", ascending=False).head(20)
# 12. Sample
final = top.sample(frac=0.5, random_state=1)

final.to_csv("trades_deep_pipeline.csv", index=False)
