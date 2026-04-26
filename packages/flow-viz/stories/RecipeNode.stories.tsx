import type { Meta, StoryObj } from "@storybook/react";
import { ReactFlowProvider } from "reactflow";
import { RecipeNode } from "../src/nodes/RecipeNode";
import type { RecipeNodeData, RecipeType } from "../src/types";

const meta: Meta<typeof RecipeNode> = {
  title: "Nodes/RecipeNode",
  component: RecipeNode,
  decorators: [
    (Story) => (
      <ReactFlowProvider>
        <Story />
      </ReactFlowProvider>
    ),
  ],
};
export default meta;

type Story = StoryObj<typeof RecipeNode>;

function makeNodeProps(type: RecipeType, name: string, status?: RecipeNodeData["status"]) {
  return {
    id: `${type}-1`,
    type: "recipe",
    selected: false,
    zIndex: 0,
    isConnectable: false,
    xPos: 0,
    yPos: 0,
    dragging: false,
    data: { type, name, inputs: 1, outputs: 1, status } as RecipeNodeData,
  } as const;
}

export const PrepareDefault: Story = {
  args: makeNodeProps("PREPARE", "Clean orders"),
};
export const PrepareSelected: Story = {
  args: { ...makeNodeProps("PREPARE", "Clean orders"), selected: true },
};
export const PrepareError: Story = {
  args: makeNodeProps("PREPARE", "Clean orders", "error"),
};

export const Grouping: Story = {
  args: makeNodeProps("GROUPING", "Sales by region"),
};
export const Join: Story = {
  args: makeNodeProps("JOIN", "Orders + customers"),
};
export const Split: Story = {
  args: makeNodeProps("SPLIT", "Train / test split"),
};
export const Window: Story = {
  args: makeNodeProps("WINDOW", "Rolling 7d avg"),
};
