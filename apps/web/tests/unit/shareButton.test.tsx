import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ConvertPage } from "../../src/features/conversion/ConvertPage";
import type { ConvertResponse } from "../../src/api/client";
import { useFlowStore } from "../../src/state/flowStore";

const FLOW: ConvertResponse = {
  flow: {
    flow_name: "shared",
    total_recipes: 0,
    total_datasets: 0,
    datasets: [],
    recipes: [],
  },
  score: {
    complexity: 4.2,
    recipe_count: 0,
    dataset_count: 0,
  },
  warnings: [],
};

function makeShareClient() {
  return {
    saveFlow: vi.fn(async () => ({ id: "saved-1", created_at: "now" })),
    shareFlow: vi.fn(async () => ({
      token: "tkn",
      url: "http://testserver/share/tkn",
      expires_at: "later",
    })),
    score: vi.fn(async () => ({
      recipe_count: 0,
      processor_count: 0,
      max_depth: 0,
      fan_out_max: 0,
      complexity: 4.2,
    })),
  };
}

describe("Share-this-flow button on ConvertPage", () => {
  it("saves the flow when needed and then shares it", async () => {
    useFlowStore.setState({ currentCode: "import pandas as pd\n" });
    const convert = vi.fn(async () => FLOW);
    const shareClient = makeShareClient();
    render(
      <MemoryRouter>
        <ConvertPage
          convertImpl={convert}
          useRestOnly
          useFallbackEditor
          shareClientImpl={shareClient as never}
        />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("convert-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("share-flow-button")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("share-flow-button"));
    await waitFor(() => {
      expect(shareClient.saveFlow).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(shareClient.shareFlow).toHaveBeenCalledWith(
        "saved-1",
        expect.objectContaining({ scopes: ["read"] }),
      );
    });
  });

  it("renders a complexity score badge after conversion", async () => {
    useFlowStore.setState({ currentCode: "import pandas as pd\n" });
    const convert = vi.fn(async () => FLOW);
    const shareClient = makeShareClient();
    render(
      <MemoryRouter>
        <ConvertPage
          convertImpl={convert}
          useRestOnly
          useFallbackEditor
          shareClientImpl={shareClient as never}
        />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("convert-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("score-badge")).toHaveTextContent(/complexity/i);
    });
  });
});
