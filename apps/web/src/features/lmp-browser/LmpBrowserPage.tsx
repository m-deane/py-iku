import { useMemo, useState } from "react";
import {
  buildNodeSnippet,
  LMP_ISOS,
  LMP_METADATA,
  LMP_NODES,
  type IsoName,
  type LmpNode,
} from "./lmp-data";
import styles from "./LmpBrowserPage.module.css";

type IsoFilter = "all" | IsoName;

export interface LmpBrowserPageProps {
  /** Test seam — overrides the clipboard write so tests can assert intent. */
  copyImpl?: (text: string) => Promise<void> | void;
}

/**
 * ISO/RTO LMP node browser — six US power markets, ~10 nodes per ISO.
 *
 * Renders a sortable hierarchical table: ISO → Zone → Node, with a search
 * box and ISO filter chips. The "Copy snippet" button generates the canonical
 * pandas read_csv + filter pattern for that node.
 *
 * Node IDs come from each ISO's published settlement-point feed. The list
 * is a snapshot for editor convenience — see ``LMP_METADATA.staleness_warning``
 * for the honest provenance disclosure.
 */
export function LmpBrowserPage(
  props: LmpBrowserPageProps = {},
): JSX.Element {
  const [query, setQuery] = useState("");
  const [iso, setIso] = useState<IsoFilter>("all");
  const [copiedFor, setCopiedFor] = useState<string | null>(null);

  const filtered: LmpNode[] = useMemo(() => {
    const q = query.trim().toLowerCase();
    let pool = [...LMP_NODES];
    if (iso !== "all") pool = pool.filter((n) => n.iso === iso);
    if (q.length > 0) {
      pool = pool.filter(
        (n) =>
          n.node_id.toLowerCase().includes(q) ||
          n.node_name.toLowerCase().includes(q) ||
          n.zone.toLowerCase().includes(q) ||
          n.region.toLowerCase().includes(q) ||
          n.iso.toLowerCase().includes(q),
      );
    }
    // Stable sort: ISO order then zone then node_id.
    pool.sort((a, b) => {
      const isoOrder =
        LMP_ISOS.indexOf(a.iso) - LMP_ISOS.indexOf(b.iso);
      if (isoOrder !== 0) return isoOrder;
      const zoneCmp = a.zone.localeCompare(b.zone);
      if (zoneCmp !== 0) return zoneCmp;
      return a.node_id.localeCompare(b.node_id);
    });
    return pool;
  }, [query, iso]);

  const handleCopy = async (node: LmpNode): Promise<void> => {
    const snippet = buildNodeSnippet(node);
    const writer =
      props.copyImpl ??
      (async (text: string) => {
        if (typeof navigator !== "undefined" && navigator.clipboard) {
          await navigator.clipboard.writeText(text);
        }
      });
    try {
      await writer(snippet);
      setCopiedFor(node.node_id);
      window.setTimeout(() => setCopiedFor(null), 1800);
    } catch {
      // Clipboard write can fail in tests / locked-down browsers; non-fatal.
    }
  };

  return (
    <section className={styles.page} data-testid="lmp-browser-page" data-route="lmp">
      <header className={styles.header}>
        <h1 className={styles.title}>LMP Node Browser</h1>
        <span className={styles.count} data-testid="lmp-count">
          {filtered.length} of {LMP_NODES.length} nodes
        </span>
      </header>

      <p className={styles.subtitle}>
        Hierarchical lookup for ISO/RTO Locational Marginal Pricing —
        {" "}PJM, ERCOT, MISO, CAISO, NYISO, ISO-NE. Six markets, 10 nodes
        each, drawn from each ISO's published settlement-point feed.
        Click a row's "Copy snippet" to grab a {" "}
        <code>pd.read_csv(...)</code> +{" "}
        <code>df["node_id"] == ...</code> pattern wired to that exact node.
      </p>

      <div
        className={styles.staleBanner}
        role="status"
        data-testid="lmp-stale-banner"
      >
        Snapshot {LMP_METADATA.snapshot_date}.{" "}
        {LMP_METADATA.staleness_warning}
      </div>

      <div className={styles.controls}>
        <input
          type="search"
          className={styles.search}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by node id, name, zone, or region…"
          aria-label="Search LMP nodes"
          data-testid="lmp-search"
        />
        <div
          role="tablist"
          aria-label="Filter by ISO"
          className={styles.chips}
        >
          <IsoChip
            active={iso === "all"}
            onClick={() => setIso("all")}
            value="all"
          >
            All
          </IsoChip>
          {LMP_ISOS.map((name) => (
            <IsoChip
              key={name}
              active={iso === name}
              onClick={() => setIso(name)}
              value={name}
            >
              {name}
            </IsoChip>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className={styles.empty} data-testid="lmp-empty">
          No nodes match this filter.
        </div>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table} data-testid="lmp-table">
            <thead>
              <tr>
                <th scope="col">ISO</th>
                <th scope="col">Zone</th>
                <th scope="col">Node ID</th>
                <th scope="col">Node Name</th>
                <th scope="col">Voltage (kV)</th>
                <th scope="col">Region</th>
                <th scope="col" aria-label="Actions"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((n) => (
                <tr
                  key={`${n.iso}-${n.node_id}`}
                  className={styles.row}
                  data-testid={`lmp-row-${n.iso}-${n.node_id}`}
                >
                  <td className={styles.isoCell}>{n.iso}</td>
                  <td>{n.zone}</td>
                  <td className={styles.nodeIdCell}>{n.node_id}</td>
                  <td>{n.node_name}</td>
                  <td className={styles.numericCell}>
                    {n.voltage_kv ?? "—"}
                  </td>
                  <td>{n.region}</td>
                  <td>
                    <button
                      type="button"
                      className={styles.copyBtn}
                      data-testid={`lmp-copy-${n.iso}-${n.node_id}`}
                      onClick={() => void handleCopy(n)}
                      aria-label={`Copy snippet for ${n.node_name}`}
                    >
                      Copy snippet
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {copiedFor ? (
        <div
          className={styles.copiedToast}
          role="status"
          data-testid="lmp-copied-toast"
        >
          Snippet copied for {copiedFor}
        </div>
      ) : null}
    </section>
  );
}

interface IsoChipProps {
  active: boolean;
  onClick: () => void;
  value: string;
  children: React.ReactNode;
}

function IsoChip(props: IsoChipProps): JSX.Element {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={props.active}
      data-testid={`lmp-filter-${props.value}`}
      onClick={props.onClick}
      className={`${styles.chip} ${props.active ? styles.chipActive : ""}`}
    >
      {props.children}
    </button>
  );
}
