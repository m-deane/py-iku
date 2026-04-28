"""06: STACK — vertical concat of three regional trade blotters."""
import pandas as pd

emea = pd.read_csv("trades_emea.csv")
amer = pd.read_csv("trades_amer.csv")
apac = pd.read_csv("trades_apac.csv")

# Vertical concat — should map to STACK recipe
all_trades = pd.concat([emea, amer, apac], ignore_index=True)

all_trades.to_csv("trades_global.csv", index=False)
