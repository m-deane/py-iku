import type { Meta, StoryObj } from "@storybook/react";
import { FlowCanvas } from "../src/FlowCanvas";
import type { MinimalFlow } from "../src/types";

const fixture: MinimalFlow = {
  nodes: [
    {
      id: "ds_in",
      type: "dataset",
      data: { datasetType: "INPUT", connectionType: "SQL_POSTGRESQL", name: "orders_raw" },
    },
    {
      id: "rec_prep",
      type: "recipe",
      data: { type: "PREPARE", name: "Clean orders", inputs: 1, outputs: 1 },
    },
    {
      id: "rec_group",
      type: "recipe",
      data: { type: "GROUPING", name: "Sales by region", inputs: 1, outputs: 1 },
    },
    {
      id: "rec_split",
      type: "recipe",
      data: { type: "SPLIT", name: "Train/test", inputs: 1, outputs: 2 },
    },
    {
      id: "ds_out",
      type: "dataset",
      data: { datasetType: "OUTPUT", connectionType: "SQL_BIGQUERY", name: "metrics_daily" },
    },
  ],
  edges: [
    { id: "e1", source: "ds_in", target: "rec_prep" },
    { id: "e2", source: "rec_prep", target: "rec_group" },
    { id: "e3", source: "rec_group", target: "rec_split" },
    { id: "e4", source: "rec_split", target: "ds_out" },
  ],
};

const meta: Meta<typeof FlowCanvas> = {
  title: "Canvas/FlowCanvas",
  component: FlowCanvas,
  parameters: { layout: "fullscreen" },
};
export default meta;

type Story = StoryObj<typeof FlowCanvas>;

export const FivePipelineLight: Story = {
  name: "5-node pipeline (light)",
  render: () => (
    <div style={{ width: "100vw", height: "80vh" }}>
      <FlowCanvas flow={fixture} theme="light" />
    </div>
  ),
};

export const FivePipelineDark: Story = {
  name: "5-node pipeline (dark)",
  render: () => (
    <div style={{ width: "100vw", height: "80vh", background: "#1E1E1E" }}>
      <FlowCanvas flow={fixture} theme="dark" />
    </div>
  ),
};
