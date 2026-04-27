import type { Meta, StoryObj } from "@storybook/react";
import { FlowCanvas } from "../src/FlowCanvas";
import type { MinimalFlow } from "../src/types";

const fixture: MinimalFlow = {
  nodes: [
    { id: "ds_in", type: "dataset", data: { datasetType: "INPUT", connectionType: "S3", name: "raw" } },
    { id: "rec_prep", type: "recipe", data: { type: "PREPARE", name: "Clean", inputs: 1, outputs: 1 } },
    { id: "rec_grp", type: "recipe", data: { type: "GROUPING", name: "Aggregate", inputs: 1, outputs: 1 } },
    { id: "rec_score", type: "recipe", data: { type: "PREDICTION_SCORING", name: "Predict", inputs: 1, outputs: 1 } },
    { id: "ds_out", type: "dataset", data: { datasetType: "OUTPUT", connectionType: "SQL_BIGQUERY", name: "scored" } },
  ],
  edges: [
    { id: "e1", source: "ds_in", target: "rec_prep" },
    { id: "e2", source: "rec_prep", target: "rec_grp" },
    { id: "e3", source: "rec_grp", target: "rec_score" },
    { id: "e4", source: "rec_score", target: "ds_out" },
  ],
};

const meta: Meta<typeof FlowCanvas> = {
  title: "Features/Zones",
  component: FlowCanvas,
  parameters: { layout: "fullscreen" },
};
export default meta;
type Story = StoryObj<typeof FlowCanvas>;

export const ZonesOff: Story = {
  name: "No zones",
  render: () => (
    <div style={{ width: "100vw", height: "80vh" }}>
      <FlowCanvas flow={fixture} theme="light" showZones={false} />
    </div>
  ),
};

export const ZonesOn: Story = {
  name: "Auto zones (input / prep / ml / output)",
  render: () => (
    <div style={{ width: "100vw", height: "80vh" }}>
      <FlowCanvas flow={fixture} theme="light" showZones={true} />
    </div>
  ),
};

export const ZonesDark: Story = {
  name: "Auto zones (dark theme)",
  render: () => (
    <div style={{ width: "100vw", height: "80vh", background: "#1E1E1E" }}>
      <FlowCanvas flow={fixture} theme="dark" showZones={true} />
    </div>
  ),
};
