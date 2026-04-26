import type { Meta, StoryObj } from "@storybook/react";
import { ReactFlowProvider } from "reactflow";
import { RecipeNode } from "../src/nodes/RecipeNode";
import type { RecipeNodeData, RecipeType } from "../src/types";

const meta: Meta<typeof RecipeNode> = {
  title: "Categories/Code recipes",
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

function makeProps(type: RecipeType, name: string) {
  return {
    id: `${type}-1`,
    type: "recipe",
    selected: false,
    zIndex: 0,
    isConnectable: false,
    xPos: 0,
    yPos: 0,
    dragging: false,
    data: { type, name, inputs: 1, outputs: 1 } as RecipeNodeData,
  } as const;
}

export const Python: Story = { args: makeProps("PYTHON", "Train model") };
export const R: Story = { args: makeProps("R", "Stat tests") };
export const SQL: Story = { args: makeProps("SQL", "Daily metrics") };
export const Hive: Story = { args: makeProps("HIVE", "Hive query") };
export const Impala: Story = { args: makeProps("IMPALA", "Impala query") };
export const SparkSQL: Story = { args: makeProps("SPARKSQL", "Spark SQL") };
export const PySpark: Story = { args: makeProps("PYSPARK", "PySpark job") };
export const SparkScala: Story = { args: makeProps("SPARK_SCALA", "Scala job") };
export const SparkR: Story = { args: makeProps("SPARKR", "SparkR job") };
export const Shell: Story = { args: makeProps("SHELL", "Bash script") };
