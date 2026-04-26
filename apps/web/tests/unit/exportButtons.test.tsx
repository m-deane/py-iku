import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ExportButtons } from "../../src/features/export/ExportButtons";
import type { ExportFormat, client as ClientType } from "../../src/api/client";

const FORMATS: ExportFormat[] = ["zip", "json", "yaml", "svg", "png", "pdf"];

function stubClient(): typeof ClientType {
  return {
    export: vi.fn(async (format: ExportFormat) => ({
      blob: new Blob([`fake-${format}`], { type: "application/octet-stream" }),
      filename: `flow.${format}`,
      contentType: "application/octet-stream",
    })),
  } as unknown as typeof ClientType;
}

describe("<ExportButtons />", () => {
  it("renders one button per supported format", () => {
    render(<ExportButtons flow={{ flow_name: "x" }} clientImpl={stubClient()} />);
    for (const fmt of FORMATS) {
      expect(screen.getByTestId(`export-${fmt}`)).toBeInTheDocument();
    }
  });

  it("disables all buttons when there is no flow", () => {
    render(<ExportButtons flow={null} clientImpl={stubClient()} />);
    for (const fmt of FORMATS) {
      expect(screen.getByTestId(`export-${fmt}`)).toBeDisabled();
    }
  });

  it.each(FORMATS)("clicking %s triggers client.export with the right format", async (fmt) => {
    const stub = stubClient();
    const onExported = vi.fn();
    render(
      <ExportButtons
        flow={{ flow_name: "demo" }}
        clientImpl={stub}
        onExported={onExported}
      />,
    );
    fireEvent.click(screen.getByTestId(`export-${fmt}`));
    await waitFor(() => {
      expect(stub.export).toHaveBeenCalledWith(fmt, { flow_name: "demo" });
    });
    await waitFor(() => {
      expect(onExported).toHaveBeenCalled();
    });
    const [calledFmt, result] = onExported.mock.calls[0]!;
    expect(calledFmt).toBe(fmt);
    expect(result.filename).toBe(`flow.${fmt}`);
  });

  it("does nothing when clicked with a null flow", () => {
    const stub = stubClient();
    render(<ExportButtons flow={null} clientImpl={stub} />);
    fireEvent.click(screen.getByTestId("export-json"));
    expect(stub.export).not.toHaveBeenCalled();
  });
});
