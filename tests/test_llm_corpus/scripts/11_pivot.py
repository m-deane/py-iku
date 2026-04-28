"""11: PIVOT — pivot_table with sums across products and venues."""
import pandas as pd

trades = pd.read_csv("trades.csv")

# Pivot trades to a venue x product matrix of total notional
pivoted = trades.pivot_table(
    index="venue",
    columns="product",
    values="notional",
    aggfunc="sum",
    fill_value=0,
)

pivoted.reset_index().to_csv("trades_pivot.csv", index=False)
