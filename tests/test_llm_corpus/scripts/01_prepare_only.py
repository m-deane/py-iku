"""01: PREPARE-only — 4-step chain (dropna, fillna, rename, type-cast)."""
import pandas as pd

customers = pd.read_csv("customers.csv")

# Drop rows with all-NaN
customers = customers.dropna(how="all")

# Fill missing email with placeholder
customers["email"] = customers["email"].fillna("unknown@example.com")

# Rename a column
customers = customers.rename(columns={"cust_id": "customer_id"})

# Cast type
customers["customer_id"] = customers["customer_id"].astype(str)

customers.to_csv("customers_clean.csv", index=False)
