import type { Meta, StoryObj } from "@storybook/react";
import { ReactFlowProvider } from "reactflow";
import { RecipeNode } from "../src/nodes/RecipeNode";
import type { RecipeNodeData, RecipeType } from "../src/types";

const meta: Meta<typeof RecipeNode> = {
  title: "Categories/Prep recipes",
  component: RecipeNode,
  decorators: [(S) => <ReactFlowProvider><S /></ReactFlowProvider>],
};
export default meta;
type Story = StoryObj<typeof RecipeNode>;

function makeProps(type: RecipeType, name: string) {
  return {
    id: `${type}-1`, type: "recipe", selected: false, zIndex: 0,
    isConnectable: false, xPos: 0, yPos: 0, dragging: false,
    data: { type, name, inputs: 1, outputs: 1 } as RecipeNodeData,
  } as const;
}

export const Sampling: Story = { args: makeProps("SAMPLING", "Sample 10%") };
export const Distinct: Story = { args: makeProps("DISTINCT", "Unique") };
export const Stack: Story = { args: makeProps("STACK", "Concat") };
export const ExtractFailedRows: Story = { args: makeProps("EXTRACT_FAILED_ROWS", "Failed rows") };
export const GenerateFeatures: Story = { args: makeProps("GENERATE_FEATURES", "Gen features") };
export const GenerateStatistics: Story = { args: makeProps("GENERATE_STATISTICS", "Stats") };
export const DynamicRepeat: Story = { args: makeProps("DYNAMIC_REPEAT", "Dyn repeat") };
