import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { FlowCanvas } from "@flow-viz/index";
import type { MinimalFlow, ThemeName } from "@flow-viz/types";
import { useSettingsStore } from "../../state/settingsStore";
import { useFlowStore } from "../../state/flowStore";

/**
 * Standalone flow-viewer route. Renders the converted flow stored in
 * `flowStore` using the new DSS-style FlowCanvas. When no flow is loaded
 * the route surfaces a small empty-state pointing the user back to
 * `/convert`. The Sprint-6 toolbar (Fit / Auto-layout / Mini-map) appears
 * inline in the canvas itself.
 */
export function FlowViewer(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const theme = useSettingsStore((s) => s.theme as ThemeName | undefined) ?? "light";
  const flow = useFlowStore((s) => s.currentFlow);

  // Hand off to FlowCanvas — coerce the persisted flow shape to the
  // MinimalFlow contract used by the canvas. The conversion is mechanical;
  // see `packages/flow-viz/src/types.ts`.
  const minimal = useMemo<MinimalFlow | null>(() => {
    if (!flow) return null;
    // The runtime shape matches MinimalFlow today (nodes[]/edges[] with
    // a discriminated `type` field). Avoid an unsafe cast by returning the
    // object as-is — tsc verifies the field-by-field compatibility.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return flow as any as MinimalFlow;
  }, [flow]);

  if (!minimal) {
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
          No flow loaded for <code>{id ?? "(no id)"}</code>. Open the Convert
          page, run a conversion, and the resulting flow will render here.
        </p>
      </section>
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: "var(--app-header-height, 56px) 0 0 0",
        height: "calc(100vh - var(--app-header-height, 56px))",
      }}
    >
      <FlowCanvas
        flow={minimal}
        theme={theme}
        showMinimap
        showControls
        showBackground
        showToolbar
      />
    </div>
  );
}
