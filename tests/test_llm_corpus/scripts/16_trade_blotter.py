"""16: trade-blotter — full ingestion + validation."""
import pandas as pd

raw = pd.read_csv("trade_blotter_raw.csv")

# Drop trades without a counterparty
raw = raw.dropna(subset=["counterparty_id"])

# Coerce numeric columns
raw["notional"] = pd.to_numeric(raw["notional"], errors="coerce")
raw["price"] = pd.to_numeric(raw["price"], errors="coerce")

# Drop coercion failures
raw = raw.dropna(subset=["notional", "price"])

# Normalize side
raw["side"] = raw["side"].str.upper().str.strip()

# Drop unrecognised sides
raw = raw[raw["side"].isin(["BUY", "SELL"])]

# Cast trade_date
raw["trade_date"] = pd.to_datetime(raw["trade_date"]).dt.date

# Compute gross
raw["gross"] = raw["notional"] * raw["price"]

raw.to_csv("trade_blotter_clean.csv", index=False)
