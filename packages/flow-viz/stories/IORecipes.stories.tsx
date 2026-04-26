import type { Meta, StoryObj } from "@storybook/react";
import { ReactFlowProvider } from "reactflow";
import { RecipeNode } from "../src/nodes/RecipeNode";
import type { RecipeNodeData, RecipeType } from "../src/types";

const meta: Meta<typeof RecipeNode> = {
  title: "Categories/IO recipes",
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

export const Sync: Story = { args: makeProps("SYNC", "Sync data") };
export const Download: Story = { args: makeProps("DOWNLOAD", "Download") };
export const PushToEditable: Story = { args: makeProps("PUSH_TO_EDITABLE", "Push") };
export const Upsert: Story = { args: makeProps("UPSERT", "Upsert") };
export const ListFolderContents: Story = { args: makeProps("LIST_FOLDER_CONTENTS", "List folder") };
export const ListAccess: Story = { args: makeProps("LIST_ACCESS", "List access") };
