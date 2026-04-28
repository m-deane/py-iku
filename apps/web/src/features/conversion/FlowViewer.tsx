import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { FlowCanvas } from "@flow-viz/index";
import type {
  DatasetConnectionType,
  DatasetType,
  FlowEdge,
  FlowNode,
  MinimalFlow,
  RecipeType,
  ThemeName,
} from "@flow-viz/types";
import type { DataikuFlow } from "@py-iku-studio/types";
import { useSettingsStore } from "../../state/settingsStore";
import { useFlowStore } from "../../state/flowStore";

/**
 * Standalone flow-viewer route. Renders the converted flow stored in
 * `flowStore` using the new DSS-style FlowCanvas. When no flow is loaded
 * the route surfaces a small empty-state pointing the user back to
 * `/convert`. The Sprint-6 toolbar (Fit / Auto-layout / Mini-map) appears
 * inline in the canvas itself.
 *
 * Wave-2 fix: the previous implementation cast the persisted DataikuFlow
 * (with `recipes` + `datasets` array fields) directly to MinimalFlow (with
 * `nodes` + `edges`). That cast lied to TypeScript and produced an empty
 * canvas at runtime because FlowCanvas only iterates `nodes`/`edges`.
 * `dataikuFlowToMinimal()` below performs the structural adaptation:
 *
 *   datasets[]  → nodes (type=dataset)
 *   recipes[]   → nodes (type=recipe)
 *   recipe.inputs[]  → edges {source: input, target: recipe.name}
 *   recipe.outputs[] → edges {source: recipe.name, target: output}
 *
 * This mirrors the convention used by the Wave-1 flow-viz fixtures and
 * by py-iku-studio/types' DataikuFlowModel definition (recipes reference
 * datasets by name).
 */
export function FlowViewer(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const theme = useSettingsStore((s) => s.theme as ThemeName | undefined) ?? "light";
  const flow = useFlowStore((s) => s.currentFlow);

  const minimal = useMemo<MinimalFlow | null>(() => {
    if (!flow) return null;
    return dataikuFlowToMinimal(flow);
  }, [flow]);

  if (!minimal || minimal.nodes.length === 0) {
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
      data-testid="flow-viewer-root"
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

/**
 * Adapt a DataikuFlow (recipes[] + datasets[]) into the MinimalFlow shape
 * (nodes[] + edges[]) that FlowCanvas expects. The conversion is purely
 * structural — we never invent node types, only re-pack the relationship
 * graph. Exported for tests.
 */
export function dataikuFlowToMinimal(flow: DataikuFlow): MinimalFlow {
  const nodes: FlowNode[] = [];
  const edges: FlowEdge[] = [];
  const seenNodeIds = new Set<string>();

  // Datasets first — recipes will reference these by name.
  for (const ds of flow.datasets ?? []) {
    if (!ds || typeof ds.name !== "string") continue;
    if (seenNodeIds.has(ds.name)) continue;
    seenNodeIds.add(ds.name);
    // Pydantic-side `connection_type` snake-cases to TS-side `connection_type`
    // (codegen preserves the API field name). Both are present.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dsAny = ds as any;
    const connectionType = (dsAny.connection_type ??
      dsAny.connectionType ??
      "Filesystem") as DatasetConnectionType;
    const datasetType = (ds.type ?? "intermediate") as DatasetType;
    nodes.push({
      id: ds.name,
      type: "dataset",
      data: {
        name: ds.name,
        datasetType,
        connectionType,
      },
    });
  }

  // Then recipes. Edges are emitted from each input/output relationship.
  for (const r of flow.recipes ?? []) {
    if (!r || typeof r.name !== "string") continue;
    if (seenNodeIds.has(r.name)) continue;
    seenNodeIds.add(r.name);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const rAny = r as any;
    const recipeType = (r.type ?? "prepare") as RecipeType;
    const inputs = Array.isArray(r.inputs) ? r.inputs : [];
    const outputs = Array.isArray(r.outputs) ? r.outputs : [];
    nodes.push({
      id: r.name,
      type: "recipe",
      data: {
        name: r.name,
        type: recipeType,
        inputs: inputs.length,
        outputs: outputs.length,
        confidence:
          typeof rAny.confidence === "number" ? rAny.confidence : null,
        sourceLines:
          Array.isArray(rAny.source_lines) && rAny.source_lines.length === 2
            ? [rAny.source_lines[0], rAny.source_lines[1]]
            : null,
        reasoning:
          typeof rAny.reasoning === "string" ? rAny.reasoning : null,
      },
    });

    for (const inputName of inputs) {
      if (typeof inputName !== "string") continue;
      edges.push({
        id: `e:${inputName}->${r.name}`,
        source: inputName,
        target: r.name,
      });
    }
    for (const outputName of outputs) {
      if (typeof outputName !== "string") continue;
      // If the output dataset isn't in the datasets array (rare, but
      // happens with synthetic intermediates), synthesize a stub node so
      // the edge has a target.
      if (!seenNodeIds.has(outputName)) {
        seenNodeIds.add(outputName);
        nodes.push({
          id: outputName,
          type: "dataset",
          data: {
            name: outputName,
            datasetType: "intermediate" as DatasetType,
            connectionType: "Filesystem" as DatasetConnectionType,
          },
        });
      }
      edges.push({
        id: `e:${r.name}->${outputName}`,
        source: r.name,
        target: outputName,
      });
    }
  }

  return { nodes, edges };
}
