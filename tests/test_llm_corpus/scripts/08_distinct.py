"""08: DISTINCT — drop_duplicates on a subset of keys."""
import pandas as pd

events = pd.read_csv("events.csv")

# Dedupe on (counterparty_id, trade_date) keeping the last record
unique_events = events.drop_duplicates(
    subset=["counterparty_id", "trade_date"],
    keep="last",
)

unique_events.to_csv("events_unique.csv", index=False)
