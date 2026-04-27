/**
 * ELK web worker. Receives `{nodes, edges, options}` from the main thread,
 * runs `elk.layout()`, and returns `{nodes, edges}` with `position` filled in.
 *
 * Vite picks this file up via `new Worker(new URL("./elk.worker.ts", ...))`
 * with `{ type: "module" }`.
 */

import ELK, { type ElkNode, type LayoutOptions } from "elkjs/lib/elk.bundled.js";

interface WorkerInputNode {
  id: string;
  width: number;
  height: number;
}

interface WorkerInputEdge {
  id: string;
  source: string;
  target: string;
}

interface WorkerInput {
  nodes: WorkerInputNode[];
  edges: WorkerInputEdge[];
  options: LayoutOptions;
}

interface WorkerOutputNode extends WorkerInputNode {
  x: number;
  y: number;
}

interface WorkerOutput {
  nodes: WorkerOutputNode[];
  edges: WorkerInputEdge[];
}

const elk = new ELK();

self.onmessage = async (ev: MessageEvent<WorkerInput>) => {
  const { nodes, edges, options } = ev.data;
  const graph: ElkNode = {
    id: "root",
    layoutOptions: options,
    children: nodes.map((n) => ({ id: n.id, width: n.width, height: n.height })),
    edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };
  try {
    const result = await elk.layout(graph);
    const positioned: WorkerOutputNode[] = (result.children ?? []).map((c) => {
      const orig = nodes.find((n) => n.id === c.id);
      return {
        id: c.id,
        width: orig?.width ?? 0,
        height: orig?.height ?? 0,
        x: c.x ?? 0,
        y: c.y ?? 0,
      };
    });
    const output: WorkerOutput = { nodes: positioned, edges };
    (self as unknown as Worker).postMessage(output);
  } catch (err) {
    // Propagate layout errors back to the main thread via a structured error
    // message. Without this, an async throw inside onmessage is silently
    // swallowed and layoutInWorker's Promise never resolves.
    const message = err instanceof Error ? err.message : String(err);
    (self as unknown as Worker).postMessage({ __error: message, nodes: [], edges });
  }
};
