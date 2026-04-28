"""24: Mixed pandas idioms — stress the analyzer (script_08 from llm-schema)."""
import numpy as np
import pandas as pd

trades = pd.read_csv("trades.csv")
positions = pd.read_csv("positions.csv")

# Boolean indexing with isin
trades = trades[trades["product"].isin(["FX_SPOT", "FX_FWD", "FX_SWAP"])]

# .loc assignment
trades.loc[trades["notional"] < 0, "side"] = "SELL"

# np.where
trades["abs_notional"] = np.where(trades["notional"] < 0, -trades["notional"], trades["notional"])

# query()
high_value = trades.query("abs_notional > 1000000")

# pd.merge() functional form
merged = pd.merge(high_value, positions, on="trade_id", how="left")

# groupby with agg-callable
res = merged.groupby("counterparty_id").agg(
    n_trades=("trade_id", "nunique"),
    total_notional=("abs_notional", "sum"),
).reset_index()

res.to_csv("mixed_idioms_out.csv", index=False)
