import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { TemplatePreview } from "../../src/features/templates/TemplatePreview";
import {
  applyTemplateParameters,
  defaultParameterValues,
  isoToday,
  type FlowTemplate,
} from "../../src/features/templates/templates-data";

const PARAMETRIC_TEMPLATE: FlowTemplate = {
  id: "demo-parametric",
  name: "Demo Parametric Template",
  category: "trade-capture",
  summary: "demo",
  personas: ["data-eng"],
  tags: ["demo"],
  pythonSource: 'today = "${TODAY}"\nbook = "${BOOK_NAME}"\n',
  verifiedRecipes: [],
  verifiedDatasets: [],
  estimatedSavingMinutes: 0,
  parameters: [
    {
      name: "TODAY",
      label: "As-of date",
      type: "date",
      defaultValue: "2026-04-26",
    },
    {
      name: "BOOK_NAME",
      label: "Book",
      type: "text",
      defaultValue: "BOOK_A",
    },
  ],
};

describe("applyTemplateParameters", () => {
  it("replaces every ${PLACEHOLDER} occurrence with its value", () => {
    const out = applyTemplateParameters(
      'a = "${X}"; b = "${X}"; c = "${Y}"',
      { X: "foo", Y: "bar" },
    );
    expect(out).toBe('a = "foo"; b = "foo"; c = "bar"');
  });

  it("does not eval values — preserves regex metacharacters verbatim", () => {
    const out = applyTemplateParameters("v = ${A}", { A: "$1.50 ($)" });
    expect(out).toBe("v = $1.50 ($)");
  });

  it("leaves unknown placeholders untouched (defensive)", () => {
    const out = applyTemplateParameters("${KNOWN} ${UNKNOWN}", { KNOWN: "ok" });
    expect(out).toBe("ok ${UNKNOWN}");
  });
});

describe("defaultParameterValues", () => {
  it("seeds the values dict from the parameter spec", () => {
    const v = defaultParameterValues(PARAMETRIC_TEMPLATE);
    expect(v).toEqual({ TODAY: "2026-04-26", BOOK_NAME: "BOOK_A" });
  });

  it("falls back to today's ISO date for ${TODAY} with empty default", () => {
    const v = defaultParameterValues({
      parameters: [
        { name: "TODAY", label: "Today", type: "date", defaultValue: "" },
      ],
    });
    expect(v.TODAY).toBe(isoToday());
  });
});

describe("<TemplatePreview /> — parametric render", () => {
  it("shows the parameters form when the template has parameters", () => {
    render(
      <TemplatePreview
        template={PARAMETRIC_TEMPLATE}
        onClose={() => {}}
        onOpenInEditor={() => {}}
        fallbackTextarea
      />,
    );
    expect(screen.getByTestId("template-preview-parameters")).toBeInTheDocument();
    expect(screen.getByTestId("param-input-TODAY")).toBeInTheDocument();
    expect(screen.getByTestId("param-input-BOOK_NAME")).toBeInTheDocument();
  });

  it("Open in Editor passes the substituted source to the parent", () => {
    const onOpen = vi.fn();
    render(
      <TemplatePreview
        template={PARAMETRIC_TEMPLATE}
        onClose={() => {}}
        onOpenInEditor={onOpen}
        fallbackTextarea
      />,
    );
    // change BOOK_NAME to NG_DESK
    fireEvent.change(screen.getByTestId("param-input-BOOK_NAME"), {
      target: { value: "NG_DESK" },
    });
    fireEvent.click(screen.getByTestId("template-preview-open"));
    expect(onOpen).toHaveBeenCalledTimes(1);
    const [tmpl, rendered] = onOpen.mock.calls[0];
    expect(tmpl.id).toBe("demo-parametric");
    expect(rendered).toContain('book = "NG_DESK"');
    expect(rendered).toContain('today = "2026-04-26"');
  });

  it("does not render the parameters section for a non-parametric template", () => {
    const plain: FlowTemplate = {
      ...PARAMETRIC_TEMPLATE,
      pythonSource: "x = 1\n",
      parameters: undefined,
    };
    render(
      <TemplatePreview
        template={plain}
        onClose={() => {}}
        onOpenInEditor={() => {}}
        fallbackTextarea
      />,
    );
    expect(screen.queryByTestId("template-preview-parameters")).toBeNull();
  });
});
