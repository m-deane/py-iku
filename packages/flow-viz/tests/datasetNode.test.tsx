/**
 * Sprint-6 — DatasetNode rounded-rect with left stripe.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReactFlow, ReactFlowProvider } from "reactflow";
import "reactflow/dist/style.css";
import { nodeTypes } from "../src/nodes";

describe("<DatasetNode>", () => {
  it("renders the connection family on the data attribute", async () => {
    render(
      <div style={{ width: 600, height: 400 }}>
        <ReactFlowProvider>
          <ReactFlow
            nodes={[
              {
                id: "n1",
                type: "dataset",
                position: { x: 0, y: 0 },
                data: {
                  datasetType: "INPUT",
                  connectionType: "PostgreSQL",
                  name: "orders",
                },
              },
            ]}
            edges={[]}
            nodeTypes={nodeTypes}
            proOptions={{ hideAttribution: true }}
          />
        </ReactFlowProvider>
      </div>,
    );
    const node = await screen.findByTestId("dataset-node-orders");
    expect(node.getAttribute("data-connection-family")).toBe("sql");
    expect(node.getAttribute("data-dataset-type")).toBe("INPUT");
  });

  it("renders an optional column-count badge when columnCount is set", async () => {
    render(
      <div style={{ width: 600, height: 400 }}>
        <ReactFlowProvider>
          <ReactFlow
            nodes={[
              {
                id: "n1",
                type: "dataset",
                position: { x: 0, y: 0 },
                data: {
                  datasetType: "INPUT",
                  connectionType: "Filesystem",
                  name: "orders",
                  columnCount: 12,
                },
              },
            ]}
            edges={[]}
            nodeTypes={nodeTypes}
            proOptions={{ hideAttribution: true }}
          />
        </ReactFlowProvider>
      </div>,
    );
    const badge = await screen.findByTestId("dataset-cols-orders");
    expect(badge.textContent).toMatch(/12 cols/);
  });
});
