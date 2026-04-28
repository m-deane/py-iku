"""20: forward-curve-scd — ~cond SPLIT (bug #3) for current vs historical curves."""
import pandas as pd

curves = pd.read_csv("forward_curves.csv")
curves["as_of_date"] = pd.to_datetime(curves["as_of_date"])

# Current vs historical split (complementary mask)
latest = curves["as_of_date"].max()
is_current = curves["as_of_date"] == latest

current_curve = curves[is_current]
historical_curves = curves[~is_current]

current_curve.to_csv("forward_curve_current.csv", index=False)
historical_curves.to_csv("forward_curve_historical.csv", index=False)
