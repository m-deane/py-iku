import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ExportButtons } from "../../src/features/export/ExportButtons";
import type { Client } from "../../src/api/client";

function stubClient(): Client {
  return {
    export: vi.fn(),
    scaffoldTest: vi.fn(async () => ({
      blob: new Blob(["# generated test"], { type: "text/x-python" }),
      filename: "test_v5_integration.py",
      contentType: "text/x-python",
    })),
  } as unknown as Client;
}

describe("ExportButtons → Export as integration test", () => {
  it("disables the integration-test button when no source is provided", () => {
    render(
      <ExportButtons
        flow={{ flow_name: "x" }}
        clientImpl={stubClient()}
      />,
    );
    expect(screen.getByTestId("export-integration-test")).toBeDisabled();
  });

  it("calls scaffoldTest with flow + source + tracked columns", async () => {
    const stub = stubClient();
    const sourceCode = "import pandas as pd";
    render(
      <ExportButtons
        flow={{ flow_name: "v5" }}
        sourceCode={sourceCode}
        trackColumns={["px"]}
        clientImpl={stub}
      />,
    );
    fireEvent.click(screen.getByTestId("export-integration-test"));
    await waitFor(() => {
      expect(stub.scaffoldTest).toHaveBeenCalled();
    });
    const call = (stub.scaffoldTest as unknown as { mock: { calls: unknown[][] } }).mock
      .calls[0];
    expect(call?.[0]).toEqual({
      flow: { flow_name: "v5" },
      source: sourceCode,
      flow_name: "v5",
      track_columns: ["px"],
    });
  });
});
