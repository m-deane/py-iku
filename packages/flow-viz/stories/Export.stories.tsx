import { useRef, useState } from "react";
import type { Meta, StoryObj } from "@storybook/react";
import { FlowCanvas } from "../src/FlowCanvas";
import { toPdf, toPng, toSvg } from "../src/export/exportFlow";
import type { MinimalFlow } from "../src/types";

const fixture: MinimalFlow = {
  nodes: [
    { id: "ds_in", type: "dataset", data: { datasetType: "INPUT", connectionType: "S3", name: "raw" } },
    { id: "rec_prep", type: "recipe", data: { type: "PREPARE", name: "Clean", inputs: 1, outputs: 1 } },
    { id: "rec_grp", type: "recipe", data: { type: "GROUPING", name: "Aggregate", inputs: 1, outputs: 1 } },
    { id: "ds_out", type: "dataset", data: { datasetType: "OUTPUT", connectionType: "SQL_POSTGRESQL", name: "out" } },
  ],
  edges: [
    { id: "e1", source: "ds_in", target: "rec_prep" },
    { id: "e2", source: "rec_prep", target: "rec_grp" },
    { id: "e3", source: "rec_grp", target: "ds_out" },
  ],
};

function ExportPanel(): JSX.Element {
  const ref = useRef<HTMLDivElement | null>(null);
  const [status, setStatus] = useState<string>("");

  function download(blob: Blob | string, name: string): void {
    const url = typeof blob === "string"
      ? URL.createObjectURL(new Blob([blob], { type: "image/svg+xml" }))
      : URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "80vh" }}>
      <div style={{ display: "flex", gap: 8, padding: 8 }}>
        <button onClick={() => { if (ref.current) download(toSvg(ref.current, { theme: "light" }), "flow.svg"); setStatus("SVG"); }}>Export SVG</button>
        <button onClick={async () => { if (ref.current) download(await toPng(ref.current, { theme: "light" }), "flow.png"); setStatus("PNG"); }}>Export PNG</button>
        <button onClick={async () => {
          if (!ref.current) return;
          const nodes = fixture.nodes.map(n => ({ id: n.id, type: n.type, name: ("name" in n.data ? n.data.name : n.id) }));
          download(await toPdf(ref.current, { theme: "light", title: "Demo Flow", nodes }), "flow.pdf");
          setStatus("PDF");
        }}>Export PDF</button>
        <span>{status && `Last export: ${status}`}</span>
      </div>
      <div ref={ref} style={{ flex: 1 }}>
        <FlowCanvas flow={fixture} theme="light" />
      </div>
    </div>
  );
}

const meta: Meta = {
  title: "Features/Export",
  parameters: { layout: "fullscreen" },
};
export default meta;
type Story = StoryObj;

export const ExportButtons: Story = {
  name: "SVG / PNG / PDF download",
  render: () => <ExportPanel />,
};
