import { useParams } from "react-router-dom";

/**
 * Standalone flow-viewer route. The actual graph rendering lives inside
 * `ConvertPage` today; the IA reorg surfaces this as its own URL so flows
 * can be linked to and so the route appears in the Build cluster.
 *
 * Until the rendering is extracted, the route shows the requested id and
 * directs the user to Convert — but it ships as a real chunk so the URL
 * resolves cleanly.
 */
export function FlowViewer(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  return (
    <section
      style={{
        padding: "var(--space-6, 32px)",
        maxWidth: 720,
        margin: "0 auto",
      }}
    >
      <h1 style={{ marginTop: 0 }}>Flow viewer</h1>
      <p style={{ color: "var(--fg-muted, #5b6470)" }}>
        Standalone flow viewer for <code>{id ?? "(no id)"}</code>. Open the
        flow from the Convert page to inspect its recipes and DAG; the
        extracted standalone view lands in a follow-up sprint.
      </p>
    </section>
  );
}
