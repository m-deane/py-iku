import type { Meta, StoryObj } from "@storybook/react";
import { ReactFlowProvider } from "reactflow";
import { RecipeNode } from "../src/nodes/RecipeNode";
import type { RecipeNodeData, RecipeType } from "../src/types";

const meta: Meta<typeof RecipeNode> = {
  title: "Categories/ML recipes",
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

export const PredictionScoring: Story = { args: makeProps("PREDICTION_SCORING", "Score") };
export const ClusteringScoring: Story = { args: makeProps("CLUSTERING_SCORING", "Cluster score") };
export const Evaluation: Story = { args: makeProps("EVALUATION", "Evaluate") };
export const AiAssistantGenerate: Story = { args: makeProps("AI_ASSISTANT_GENERATE", "AI gen") };
