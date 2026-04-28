"""10: SAMPLING — df.sample with frac."""
import pandas as pd

trades = pd.read_csv("trades.csv")

# 10% random sample for QA
sampled = trades.sample(frac=0.1, random_state=42)

sampled.to_csv("trades_sample.csv", index=False)
