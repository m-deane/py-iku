/**
 * SchemaDriftPanel — side panel that surfaces a column-by-column diff for
 * each dataset that drifted. Driven by the `SchemaDriftResponse` payload
 * coming back from the banner.
 */
import type { SchemaDriftResponse } from "../../api/client";

export interface SchemaDriftPanelProps {
  drift: SchemaDriftResponse | null;
  open: boolean;
  onClose: () => void;
}

export function SchemaDriftPanel(props: SchemaDriftPanelProps): JSX.Element | null {
  if (!props.open || !props.drift) return null;
  const { drift } = props;
  return (
    <aside
      role="complementary"
      aria-label="Schema drift detail"
      data-testid="schema-drift-panel"
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: "min(440px, 100vw)",
        height: "100vh",
        background: "var(--surface, #fff)",
        borderLeft: "1px solid var(--border, #eaecf0)",
        boxShadow: "var(--shadow-lg, 0 24px 64px rgba(15,23,42,0.12))",
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
        padding: "1rem 1.1rem",
        zIndex: 50,
        overflow: "auto",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "var(--text-md, 16px)" }}>Schema drift</h2>
        <button
          type="button"
          data-testid="schema-drift-panel-close"
          onClick={props.onClose}
          aria-label="Close schema drift panel"
          style={{
            border: "1px solid var(--border-strong, #d0d5dd)",
            background: "transparent",
            color: "inherit",
            padding: "0.2rem 0.6rem",
            borderRadius: "var(--radius-sm, 4px)",
            cursor: "pointer",
          }}
        >
          ×
        </button>
      </header>

      <div data-testid="schema-drift-headline" style={{ fontSize: "var(--text-sm, 13px)" }}>
        {drift.headline}
      </div>

      {drift.datasets_added.length > 0 ? (
        <DriftSection title="New datasets">
          <ul>{drift.datasets_added.map((d) => <li key={d}><code>{d}</code></li>)}</ul>
        </DriftSection>
      ) : null}
      {drift.datasets_removed.length > 0 ? (
        <DriftSection title="Removed datasets">
          <ul>{drift.datasets_removed.map((d) => <li key={d}><code>{d}</code></li>)}</ul>
        </DriftSection>
      ) : null}

      {drift.per_dataset.map((d) => (
        <DriftSection key={d.dataset} title={`Dataset: ${d.dataset}`}>
          {d.added.length > 0 ? (
            <SubGroup label="Added" tone="add">
              {d.added.map((c) => (
                <Row key={c.name} name={c.name} type={c.type} />
              ))}
            </SubGroup>
          ) : null}
          {d.removed.length > 0 ? (
            <SubGroup label="Removed" tone="remove">
              {d.removed.map((c) => (
                <Row key={c.name} name={c.name} type={c.type} />
              ))}
            </SubGroup>
          ) : null}
          {d.renamed.length > 0 ? (
            <SubGroup label="Renamed" tone="renamed">
              {d.renamed.map((r) => (
                <div
                  key={`${r.from}-${r.to}`}
                  data-testid={`drift-renamed-${r.from}-${r.to}`}
                  style={{ fontSize: "var(--text-xs, 12px)" }}
                >
                  <code>{r.from}</code> → <code>{r.to}</code>{" "}
                  <span style={{ color: "var(--fg-muted, #5b6470)" }}>({r.type})</span>
                </div>
              ))}
            </SubGroup>
          ) : null}
          {d.type_changed.length > 0 ? (
            <SubGroup label="Type changed" tone="warn">
              {d.type_changed.map((t) => (
                <div
                  key={t.name}
                  data-testid={`drift-type-changed-${t.name}`}
                  style={{ fontSize: "var(--text-xs, 12px)" }}
                >
                  <code>{t.name}</code>:{" "}
                  <span style={{ color: "var(--fg-muted, #5b6470)" }}>{t.from_type}</span>
                  {" → "}
                  <span>{t.to_type}</span>
                </div>
              ))}
            </SubGroup>
          ) : null}
        </DriftSection>
      ))}
    </aside>
  );
}

function DriftSection(props: { title: string; children: React.ReactNode }): JSX.Element {
  return (
    <section
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.4rem",
        padding: "0.5rem 0.6rem",
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-md, 6px)",
        background: "var(--surface-raised, #f7f8fa)",
      }}
    >
      <strong style={{ fontSize: "var(--text-sm, 13px)" }}>{props.title}</strong>
      {props.children}
    </section>
  );
}

function SubGroup(props: {
  label: string;
  tone: "add" | "remove" | "renamed" | "warn";
  children: React.ReactNode;
}): JSX.Element {
  const colors: Record<string, string> = {
    add: "var(--accent-hover, #0f766e)",
    remove: "#b71c1c",
    renamed: "var(--fg-muted, #5b6470)",
    warn: "#b54708",
  };
  return (
    <div
      data-testid={`drift-subgroup-${props.tone}`}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.15rem",
        paddingLeft: "0.4rem",
        borderLeft: `3px solid ${colors[props.tone]}`,
      }}
    >
      <span style={{ fontSize: "var(--text-xs, 12px)", color: colors[props.tone] }}>
        {props.label}
      </span>
      {props.children}
    </div>
  );
}

function Row(props: { name: string; type: string }): JSX.Element {
  return (
    <div
      style={{
        display: "flex",
        gap: "0.5rem",
        fontSize: "var(--text-xs, 12px)",
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      }}
    >
      <code>{props.name}</code>
      <span style={{ color: "var(--fg-muted, #5b6470)" }}>{props.type}</span>
    </div>
  );
}
