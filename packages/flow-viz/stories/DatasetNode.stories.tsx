import type { Meta, StoryObj } from "@storybook/react";
import { ReactFlowProvider } from "reactflow";
import { DatasetNode } from "../src/nodes/DatasetNode";
import type { DatasetConnectionType, DatasetNodeData, DatasetType } from "../src/types";

const meta: Meta<typeof DatasetNode> = {
  title: "Nodes/DatasetNode",
  component: DatasetNode,
  decorators: [
    (Story) => (
      <ReactFlowProvider>
        <Story />
      </ReactFlowProvider>
    ),
  ],
};
export default meta;

type Story = StoryObj<typeof DatasetNode>;

function makeProps(
  datasetType: DatasetType,
  connectionType: DatasetConnectionType,
  name: string,
) {
  return {
    id: `${datasetType}-${connectionType}`,
    type: "dataset",
    selected: false,
    zIndex: 0,
    isConnectable: false,
    xPos: 0,
    yPos: 0,
    dragging: false,
    data: { datasetType, connectionType, name } as DatasetNodeData,
  } as const;
}

export const InputCsvCylinder: Story = {
  name: "Input — SQL Postgres (cylinder)",
  args: makeProps("INPUT", "SQL_POSTGRESQL", "orders_raw"),
};

export const InputS3Document: Story = {
  name: "Input — S3 (document)",
  args: makeProps("INPUT", "S3", "events.json"),
};

export const IntermediateFolder: Story = {
  name: "Intermediate — Filesystem (folder)",
  args: makeProps("INTERMEDIATE", "FILESYSTEM", "stage_clean"),
};

export const OutputBigQueryCylinder: Story = {
  name: "Output — BigQuery (cylinder)",
  args: makeProps("OUTPUT", "SQL_BIGQUERY", "metrics_daily"),
};
