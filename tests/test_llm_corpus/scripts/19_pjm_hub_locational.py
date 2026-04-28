"""19: pjm-hub-locational — geographic JOIN + GROUPING (PJM LMPs)."""
import pandas as pd

lmps = pd.read_csv("pjm_lmps.csv")
nodes = pd.read_csv("pjm_nodes.csv")

# Join LMPs with node metadata to get hub/zone
enriched = lmps.merge(nodes, on="pnode_id", how="inner")

# Filter to hub nodes only
hubs = enriched[enriched["node_type"] == "HUB"]

# Average LMP per hub per hour
hub_avg = hubs.groupby(["hub_name", "datetime_beginning_ept"]).agg(
    avg_lmp=("total_lmp", "mean"),
    avg_congestion=("congestion_price", "mean"),
).reset_index()

hub_avg.to_csv("pjm_hub_hourly.csv", index=False)
