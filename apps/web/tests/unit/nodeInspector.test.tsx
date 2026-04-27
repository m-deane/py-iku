import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { NodeInspector } from "../../src/features/inspector/NodeInspector";
import { useFlowStore } from "../../src/state/flowStore";

const PREPARE_FLOW = {
  flow_name: "f",
  total_recipes: 1,
  total_datasets: 2,
  datasets: [
    {
      name: "input_ds",
      type: "input",
      connection_type: "Filesystem",
      schema: [
        { name: "id", type: "string", nullable: true },
        { name: "value", type: "double", nullable: true },
      ],
      source_variable: "df",
      source_line: 2,
    },
    {
      name: "output_ds",
      type: "output",
      connection_type: "Filesystem",
      schema: [],
    },
  ],
  recipes: [
    {
      name: "prepare_1",
      type: "prepare",
      inputs: ["input_ds"],
      outputs: ["output_ds"],
      step_count: 2,
      steps: [
        { metaType: "PROCESSOR", type: "ColumnRenamer", disabled: false },
      ],
    },
  ],
};

describe("<NodeInspector />", () => {
  beforeEach(() => {
    act(() => {
      useFlowStore.getState().reset();
    });
  });

  it("renders nothing when there is no selection", () => {
    const { container } = render(
      <NodeInspector flow={PREPARE_FLOW as never} selectedNodeId={null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders RecipeSettings fields for a selected PREPARE recipe", () => {
    render(
      <NodeInspector flow={PREPARE_FLOW as never} selectedNodeId="prepare_1" />,
    );
    expect(screen.getByTestId("recipe-inspector")).toBeInTheDocument();
    expect(screen.getByTestId("recipe-type")).toHaveTextContent(/prepare/i);
    // Recipe inputs and outputs render in lists.
    expect(screen.getByText("input_ds")).toBeInTheDocument();
    expect(screen.getByText("output_ds")).toBeInTheDocument();
    // Settings KV list renders fields parsed by RecipeSettingsModelSchema.
    expect(screen.getByTestId("settings-kvlist")).toBeInTheDocument();
  });

  it("renders dataset metadata for a selected dataset", () => {
    render(
      <NodeInspector flow={PREPARE_FLOW as never} selectedNodeId="input_ds" />,
    );
    expect(screen.getByTestId("dataset-inspector")).toBeInTheDocument();
    expect(screen.getByTestId("dataset-type")).toHaveTextContent(/input/i);
    expect(screen.getByTestId("schema-count")).toHaveTextContent(/2 columns/);
  });

  it("close button clears selection in flowStore (default onClose)", () => {
    act(() => {
      useFlowStore.getState().setSelectedNodeId("prepare_1");
      useFlowStore.getState().setFlow(PREPARE_FLOW as never);
    });
    render(<NodeInspector />);
    fireEvent.click(screen.getByTestId("inspector-close"));
    expect(useFlowStore.getState().selectedNodeId).toBeNull();
  });

  it("falls back to JsonView when settings cannot be parsed by the schema", () => {
    const flowWithUnknownKind = {
      ...PREPARE_FLOW,
      recipes: [
        {
          name: "weird_1",
          // Cast through `as never` to bypass the discriminated union type.
          type: "ai_assistant_generate",
          inputs: [],
          outputs: [],
          custom_field: { foo: "bar" },
        },
      ],
    };
    render(
      <NodeInspector
        flow={flowWithUnknownKind as never}
        selectedNodeId="weird_1"
      />,
    );
    expect(screen.getByTestId("settings-fallback")).toBeInTheDocument();
  });

  it("shows a not-found message when the id is unknown", () => {
    render(
      <NodeInspector flow={PREPARE_FLOW as never} selectedNodeId="missing" />,
    );
    expect(screen.getByTestId("inspector-empty")).toHaveTextContent(/not found/i);
  });
});
