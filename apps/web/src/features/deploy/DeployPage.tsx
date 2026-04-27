/**
 * Deploy is the final lifecycle step — push the validated flow into a target
 * DSS project. Direct DSS write-back is on the roadmap but not yet wired
 * (see `docs/future-dss-writeback.md` for the planned design); for now this
 * page lays out the surface and disables the action.
 *
 * The IA review explicitly called out that `features/deploy/` was empty —
 * this file is the first occupant.
 */
export function DeployPage(): JSX.Element {
  return (
    <section
      style={{
        padding: "var(--space-6, 32px)",
        maxWidth: 720,
        margin: "0 auto",
      }}
    >
      <h1 style={{ marginTop: 0 }}>Deploy</h1>
      <p style={{ color: "var(--fg-muted, #5b6470)", marginTop: 0 }}>
        Push a converted flow into a Dataiku DSS project. Direct write-back is
        on the roadmap; for now, export the flow as JSON or ZIP from the
        Export page and import it from inside DSS.
      </p>
      <button
        type="button"
        disabled
        aria-disabled="true"
        style={{
          marginTop: "var(--space-4, 16px)",
          padding: "var(--space-2, 8px) var(--space-4, 16px)",
          borderRadius: "var(--radius-md, 8px)",
          border: "1px solid var(--border, #eaecf0)",
          background: "var(--surface-sunken, #f2f4f7)",
          color: "var(--fg-muted, #5b6470)",
          cursor: "not-allowed",
        }}
      >
        Deploy to DSS — not yet available
      </button>
    </section>
  );
}
