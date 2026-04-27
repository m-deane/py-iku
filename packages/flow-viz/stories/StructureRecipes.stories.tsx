import type { Meta, StoryObj } from "@storybook/react";
import { ReactFlowProvider } from "reactflow";
import { RecipeNode } from "../src/nodes/RecipeNode";
import type { RecipeNodeData, RecipeType } from "../src/types";

const meta: Meta<typeof RecipeNode> = {
  title: "Categories/Structure recipes",
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

export const FuzzyJoin: Story = { args: makeProps("FUZZY_JOIN", "Fuzzy match") };
export const GeoJoin: Story = { args: makeProps("GEO_JOIN", "Geo lookup") };
export const Sort: Story = { args: makeProps("SORT", "Sort by date") };
export const TopN: Story = { args: makeProps("TOP_N", "Top 100") };
export const Pivot: Story = { args: makeProps("PIVOT", "Pivot wide") };
