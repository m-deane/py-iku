import type { Meta, StoryObj } from "@storybook/react";
import { FlowCanvas } from "../src/FlowCanvas";
import type { MinimalFlow } from "../src/types";

const fixture: MinimalFlow = {
  nodes: [
    { id: "ds_in", type: "dataset", data: { datasetType: "INPUT", connectionType: "S3", name: "raw" } },
    { id: "rec_prep", type: "recipe", data: { type: "PREPARE", name: "Clean", inputs: 1, outputs: 1 } },
    { id: "rec_split", type: "recipe", data: { type: "SPLIT", name: "Split", inputs: 1, outputs: 2 } },
    { id: "rec_grp", type: "recipe", data: { type: "GROUPING", name: "Aggregate", inputs: 1, outputs: 1 } },
    { id: "ds_out", type: "dataset", data: { datasetType: "OUTPUT", connectionType: "SQL_POSTGRESQL", name: "out" } },
  ],
  edges: [
    { id: "e1", source: "ds_in", target: "rec_prep" },
    { id: "e2", source: "rec_prep", target: "rec_split" },
    { id: "e3", source: "rec_split", target: "rec_grp" },
    { id: "e4", source: "rec_grp", target: "ds_out" },
  ],
};

const meta: Meta<typeof FlowCanvas> = {
  title: "Features/Focus mode",
  component: FlowCanvas,
  parameters: { layout: "fullscreen" },
};
export default meta;
type Story = StoryObj<typeof FlowCanvas>;

export const FocusInactive: Story = {
  name: "No focus (no selection)",
  render: () => (
    <div style={{ width: "100vw", height: "80vh" }}>
      <FlowCanvas flow={fixture} theme="light" focusOnSelect={true} />
    </div>
  ),
};

export const FocusOnSplit: Story = {
  name: "Focus on a node — click to dim peers",
  render: () => (
    <div style={{ width: "100vw", height: "80vh" }}>
      <FlowCanvas flow={fixture} theme="light" focusOnSelect={true} />
    </div>
  ),
};
