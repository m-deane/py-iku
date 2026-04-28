"""15: SPLIT consolidation — bug #3 (~cond pattern → one SPLIT, not two filters)."""
import pandas as pd

trades = pd.read_csv("trades.csv")

# Complementary filter: in-the-money vs out-of-the-money
itm_mask = trades["pnl"] > 0
itm = trades[itm_mask]
otm = trades[~itm_mask]

itm.to_csv("trades_itm.csv", index=False)
otm.to_csv("trades_otm.csv", index=False)
