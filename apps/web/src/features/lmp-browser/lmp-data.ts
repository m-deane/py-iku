/**
 * ISO/RTO LMP node browser — six US power markets, ~10 nodes each.
 *
 * Single source of truth: ``lmp-nodes.json`` next to this file. Node IDs are
 * lifted from each ISO's published settlement-point or pricing-node feed.
 * The list is a *snapshot for editor convenience* — it is not realtime and
 * not exhaustive. Refresh from each ISO's MIS / OASIS / Data Miner before
 * deploying any pricing logic.
 */
import lmpJson from "./lmp-nodes.json";

export type IsoName = "PJM" | "ERCOT" | "MISO" | "CAISO" | "NYISO" | "ISONE";

export interface LmpNode {
  iso: IsoName;
  zone: string;
  node_id: string;
  node_name: string;
  voltage_kv: number | null;
  region: string;
}

export interface LmpCatalogMetadata {
  snapshot_date: string;
  staleness_warning: string;
  sources: Record<IsoName, string>;
}

interface LmpJson {
  metadata: LmpCatalogMetadata;
  nodes: LmpNode[];
}

const data = lmpJson as unknown as LmpJson;

export const LMP_NODES: readonly LmpNode[] = data.nodes;
export const LMP_METADATA: LmpCatalogMetadata = data.metadata;

export const LMP_ISOS: readonly IsoName[] = [
  "PJM",
  "ERCOT",
  "MISO",
  "CAISO",
  "NYISO",
  "ISONE",
];

export function nodesByIso(iso: IsoName): readonly LmpNode[] {
  return LMP_NODES.filter((n) => n.iso === iso);
}

/**
 * Build the "Copy as snippet" pandas pattern for a given node — `read_csv`
 * + filter on the node_id. Includes a comment header so the trader knows
 * which ISO/zone the snippet is for.
 */
export function buildNodeSnippet(node: LmpNode): string {
  const csvName = `${node.iso.toLowerCase()}_lmps.csv`;
  return [
    `# ${node.iso} ${node.zone} — ${node.node_name}`,
    `# region: ${node.region}` +
      (node.voltage_kv ? ` | voltage: ${node.voltage_kv} kV` : ""),
    `# source: ${LMP_METADATA.sources[node.iso]}`,
    `import pandas as pd`,
    ``,
    `df = pd.read_csv("${csvName}")`,
    `node_df = df[df["node_id"] == "${node.node_id}"].sort_values("timestamp")`,
    ``,
  ].join("\n");
}
