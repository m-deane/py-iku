import { describe, expect, it } from "vitest";
import { toSvg } from "../src/export/exportFlow";

describe("toSvg", () => {
  it("returns an SVG XML string with the configured background", () => {
    const root = document.createElement("div");
    root.innerHTML = `
      <div class="react-flow__viewport"></div>
      <div class="react-flow__nodes">
        <div data-recipe-type="PREPARE">prep</div>
      </div>
      <svg class="react-flow__edges" width="640" height="480"></svg>
    `;
    document.body.appendChild(root);
    const svg = toSvg(root, { background: "#ffeedd", theme: "light" });
    expect(svg).toContain("<svg");
    expect(svg).toContain("#ffeedd");
    expect(svg).toContain("foreignObject");
    expect(svg).toContain("PREPARE");
    document.body.removeChild(root);
  });

  it("uses the dark theme default background when no background is provided", () => {
    const root = document.createElement("div");
    root.innerHTML = `
      <div class="react-flow__viewport"></div>
      <div class="react-flow__nodes"></div>
      <svg class="react-flow__edges" width="200" height="200"></svg>
    `;
    document.body.appendChild(root);
    const svg = toSvg(root, { theme: "dark" });
    expect(svg).toContain("#1E1E1E");
    document.body.removeChild(root);
  });
});
