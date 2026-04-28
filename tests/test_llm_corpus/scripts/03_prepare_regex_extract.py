"""03: PREPARE + regex extract — bug #4 (str.extract pattern)."""
import pandas as pd

logs = pd.read_csv("logs.csv")

# Extract digits from a string column — should map to EXTRACT_REGEX processor
logs["digits"] = logs["message"].str.extract(r"(\d+)")

logs.to_csv("logs_extracted.csv", index=False)
