"""18: counterparty-features — long PREPARE chain."""
import pandas as pd

cps = pd.read_csv("counterparties_raw.csv")

cps = cps.dropna(subset=["counterparty_id"])
cps["legal_name"] = cps["legal_name"].str.upper().str.strip()
cps["lei"] = cps["lei"].fillna("UNKNOWN")
cps["country"] = cps["country"].fillna("XX")
cps = cps.rename(columns={"cp_type": "counterparty_type"})
cps["counterparty_type"] = cps["counterparty_type"].str.lower()
cps["onboarded_date"] = pd.to_datetime(cps["onboarded_date"])
cps["years_active"] = (pd.Timestamp.today() - cps["onboarded_date"]).dt.days / 365.25
cps["is_eu"] = cps["country"].isin(["DE", "FR", "IT", "ES", "NL", "BE", "IE", "AT", "FI", "PT"])
cps["risk_band"] = cps["credit_score"].fillna(0).astype(int)

cps.to_csv("counterparty_features.csv", index=False)
