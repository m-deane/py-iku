/**
 * ELK-backed layout for flow-viz. Wraps `elkjs` in a web worker when one is
 * available (browser, Storybook), and falls back to a synchronous
 * main-thread layout when not (jsdom test environment, SSR).
 *
 * Default algorithm: `layered`, top-down (`elk.direction: DOWN`). Spacing
 * pulled from `tokens.json` via the SPACING constant.
 *
 * Public API:
 *   layoutFlow(nodes, edges, options?) → Promise<{nodes, edges}>
 *
 * Where the returned nodes carry React Flow-friendly `position: {x, y}`.
 */

import ELK, { type LayoutOptions } from "elkjs/lib/elk.bundled.js";
import type { Edge as RFEdge, Node as RFNode } from "reactflow";
import { NODE_SIZES, DSS_LAYOUT_SPACING } from "../theme/tokens";
import type { DatasetNodeData, RecipeNodeData } from "../types";

export interface ElkLayoutOptions {
  /** ELK layout direction. Default: "RIGHT" (left-to-right Sugiyama). */
  direction?: "DOWN" | "RIGHT" | "UP" | "LEFT";
  /** Override node-node spacing. Default 110 to mirror DSS row spacing. */
  nodeSpacing?: number;
  /** Override layer spacing. Default 220 to mirror DSS column spacing. */
  layerSpacing?: number;
}

function buildOptions(overrides: ElkLayoutOptions): LayoutOptions {
  const pad = DSS_LAYOUT_SPACING.padding;
  return {
    "elk.algorithm": "layered",
    "elk.direction": overrides.direction ?? "RIGHT",
    "elk.spacing.nodeNode": String(overrides.nodeSpacing ?? DSS_LAYOUT_SPACING.node),
    "elk.layered.spacing.nodeNodeBetweenLayers": String(
      overrides.layerSpacing ?? DSS_LAYOUT_SPACING.layer,
    ),
    // Sugiyama crossing-min (LAYER_SWEEP) is the ELK default for `layered`.
    "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
    "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
    "elk.padding": `[top=${pad},left=${pad},bottom=${pad},right=${pad}]`,
  };
}

function nodeSize(n: RFNode<RecipeNodeData | DatasetNodeData>): { width: number; height: number } {
  if (n.type === "dataset") return NODE_SIZES.dataset;
  return NODE_SIZES.recipe;
}

const elk = new ELK();

function canUseWorker(): boolean {
  return (
    typeof Worker !== "undefined" &&
    typeof URL !== "undefined" &&
    typeof window !== "undefined"
  );
}

async function layoutInWorker(
  nodes: RFNode[],
  edges: RFEdge[],
  options: LayoutOptions,
): Promise<RFNode[]> {
  return new Promise((resolve, reject) => {
    let worker: Worker;
    try {
      worker = new Worker(new URL("./elk.worker.ts", import.meta.url), { type: "module" });
    } catch (err) {
      reject(err);
      return;
    }
    worker.onmessage = (
      ev: MessageEvent<{ nodes: { id: string; x: number; y: number }[]; __error?: string }>,
    ) => {
      worker.terminate();
      if (ev.data.__error) {
        reject(new Error(`ELK layout worker error: ${ev.data.__error}`));
        return;
      }
      const positions = new Map(ev.data.nodes.map((n) => [n.id, { x: n.x, y: n.y }]));
      const out = nodes.map((n) => ({
        ...n,
        position: positions.get(n.id) ?? n.position ?? { x: 0, y: 0 },
      }));
      resolve(out);
    };
    worker.onerror = (e) => {
      worker.terminate();
      reject(e);
    };
    worker.postMessage({
      nodes: nodes.map((n) => ({ id: n.id, ...nodeSize(n as RFNode<RecipeNodeData | DatasetNodeData>) })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
      options,
    });
  });
}

async function layoutSync(
  nodes: RFNode[],
  edges: RFEdge[],
  options: LayoutOptions,
): Promise<RFNode[]> {
  const graph = {
    id: "root",
    layoutOptions: options,
    children: nodes.map((n) => ({
      id: n.id,
      ...nodeSize(n as RFNode<RecipeNodeData | DatasetNodeData>),
    })),
    edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };
  const result = await elk.layout(graph);
  const positions = new Map(
    (result.children ?? []).map((c) => [c.id, { x: c.x ?? 0, y: c.y ?? 0 }]),
  );
  return nodes.map((n) => ({
    ...n,
    position: positions.get(n.id) ?? n.position ?? { x: 0, y: 0 },
  }));
}

/**
 * Layout an array of React Flow nodes/edges. Returns the same edge array
 * unchanged plus nodes with `position` populated. Uses the web worker when
 * available; falls back to synchronous main-thread ELK in test/SSR envs.
 */
export async function layoutFlow(
  nodes: RFNode[],
  edges: RFEdge[],
  options: ElkLayoutOptions = {},
): Promise<{ nodes: RFNode[]; edges: RFEdge[] }> {
  if (nodes.length === 0) return { nodes, edges };
  const elkOptions = buildOptions(options);
  let positioned: RFNode[];
  if (canUseWorker()) {
    try {
      positioned = await layoutInWorker(nodes, edges, elkOptions);
    } catch {
      positioned = await layoutSync(nodes, edges, elkOptions);
    }
  } else {
    positioned = await layoutSync(nodes, edges, elkOptions);
  }
  return { nodes: positioned, edges };
}
