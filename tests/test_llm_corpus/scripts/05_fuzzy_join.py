"""05: FUZZY_JOIN — fuzzy string matching across counterparty names."""
import pandas as pd
from rapidfuzz import fuzz, process


internal_cps = pd.read_csv("internal_counterparties.csv")
external_cps = pd.read_csv("external_counterparties.csv")


def fuzzy_match(name, choices, threshold=85):
    match = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
    return match[0] if match and match[1] >= threshold else None


# Fuzzy match counterparty names
internal_cps["matched_external"] = internal_cps["legal_name"].apply(
    lambda n: fuzzy_match(n, external_cps["legal_name"].tolist())
)

merged = internal_cps.merge(
    external_cps,
    left_on="matched_external",
    right_on="legal_name",
    how="left",
    suffixes=("_int", "_ext"),
)

merged.to_csv("counterparties_fuzzy_matched.csv", index=False)
