"""17: book-mtm-eod — formula-drop case (bug #1, fixed by Fix-A)."""
import pandas as pd

positions = pd.read_csv("positions.csv")
marks = pd.read_csv("eod_marks.csv")

# Join positions with marks
positions = positions.merge(marks, on=["instrument_id", "trade_date"], how="left")

# Compute MTM PnL — this formula step is the one historically dropped
positions["mtm_pnl"] = (positions["mark_price"] - positions["cost_basis"]) * positions["quantity"]

# Roll up to book level
book_pnl = positions.groupby(["book_id", "trade_date"]).agg(
    book_mtm=("mtm_pnl", "sum"),
).reset_index()

book_pnl.to_csv("book_mtm_eod.csv", index=False)
