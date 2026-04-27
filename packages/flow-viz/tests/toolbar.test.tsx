/**
 * Sprint-6 — DSS-style toolbar (Fit / Auto-layout / Mini-map toggle).
 */
import { describe, expect, it } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FlowCanvas } from "../src/FlowCanvas";
import type { MinimalFlow } from "../src/types";

const fixture: MinimalFlow = {
  nodes: [
    {
      id: "ds_in",
      type: "dataset",
      data: { datasetType: "INPUT", connectionType: "Filesystem", name: "src" },
    },
    {
      id: "rec_prep",
      type: "recipe",
      data: { type: "PREPARE", name: "Prep", inputs: 1, outputs: 1 },
    },
    {
      id: "ds_out",
      type: "dataset",
      data: { datasetType: "OUTPUT", connectionType: "PostgreSQL", name: "dst" },
    },
  ],
  edges: [
    { id: "e1", source: "ds_in", target: "rec_prep" },
    { id: "e2", source: "rec_prep", target: "ds_out" },
  ],
};

describe("FlowCanvas toolbar", () => {
  it("renders Fit / Layout / Map buttons by default", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={fixture} theme="light" />
      </div>,
    );
    expect(await screen.findByTestId("flow-toolbar-fit")).toBeTruthy();
    expect(screen.getByTestId("flow-toolbar-layout")).toBeTruthy();
    expect(screen.getByTestId("flow-toolbar-minimap")).toBeTruthy();
  });

  it("hides the toolbar when showToolbar is false", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={fixture} theme="light" showToolbar={false} />
      </div>,
    );
    await screen.findByTestId("flow-canvas");
    expect(screen.queryByTestId("flow-toolbar-fit")).toBeNull();
  });

  it("toggles the mini-map button aria-pressed state", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={fixture} theme="light" showMinimap />
      </div>,
    );
    const btn = await screen.findByTestId("flow-toolbar-minimap");
    expect(btn.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(btn);
    await waitFor(() => {
      expect(btn.getAttribute("aria-pressed")).toBe("false");
    });
  });
});
