import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { SchemaDriftBanner } from "../../src/features/conversion/SchemaDriftBanner";
import { SchemaDriftPanel } from "../../src/features/conversion/SchemaDriftPanel";
import {
  hashSource,
  useSchemaSnapshots,
} from "../../src/store/schemaSnapshots";
import type { Client, SchemaDriftResponse } from "../../src/api/client";

const SOURCE = "import pandas as pd\ndf = pd.read_csv('x.csv')\n";

const FLOW = {
  flow_name: "f",
  datasets: [
    {
      name: "df",
      type: "input",
      connection_type: "Filesystem",
      schema: [
        { name: "a", type: "int" },
        { name: "b", type: "string" },
      ],
    },
  ],
  recipes: [],
};

function stubClient(drift: SchemaDriftResponse): Client {
  return {
    schemaDrift: vi.fn(async () => drift),
  } as unknown as Client;
}

beforeEach(() => {
  // Reset the persisted store between tests.
  useSchemaSnapshots.getState().clear();
});

describe("<SchemaDriftBanner />", () => {
  it("captures a snapshot on first conversion and renders nothing", async () => {
    const drift: SchemaDriftResponse = {
      summary: {
        datasets_added: 0,
        datasets_removed: 0,
        columns_added: 0,
        columns_removed: 0,
        columns_renamed: 0,
        columns_type_changed: 0,
        has_drift: false,
      },
      headline: "No schema drift detected.",
      datasets_added: [],
      datasets_removed: [],
      per_dataset: [],
    };
    render(
      <SchemaDriftBanner
        source={SOURCE}
        flow={FLOW}
        clientImpl={stubClient(drift)}
      />,
    );
    // No banner — first run.
    await waitFor(() => {
      expect(useSchemaSnapshots.getState().get(hashSource(SOURCE))).not.toBeNull();
    });
    expect(screen.queryByTestId("schema-drift-banner")).toBeNull();
  });

  it("renders the banner on a re-conversion when drift is reported", async () => {
    // Pre-load a snapshot (simulating a prior run).
    useSchemaSnapshots.getState().put(hashSource(SOURCE), {
      flow: { datasets: [], recipes: [] },
      capturedAt: new Date().toISOString(),
    });
    const drift: SchemaDriftResponse = {
      summary: {
        datasets_added: 1,
        datasets_removed: 0,
        columns_added: 2,
        columns_removed: 0,
        columns_renamed: 1,
        columns_type_changed: 0,
        has_drift: true,
      },
      headline: "2 added, 1 renamed since last run.",
      datasets_added: ["df"],
      datasets_removed: [],
      per_dataset: [],
    };
    render(
      <SchemaDriftBanner
        source={SOURCE}
        flow={FLOW}
        clientImpl={stubClient(drift)}
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("schema-drift-banner")).toBeInTheDocument();
    });
    expect(screen.getByTestId("schema-drift-headline")).toHaveTextContent(
      "2 added, 1 renamed since last run.",
    );
  });

  it("Review → invokes onReview with the drift payload", async () => {
    useSchemaSnapshots.getState().put(hashSource(SOURCE), {
      flow: { datasets: [], recipes: [] },
      capturedAt: new Date().toISOString(),
    });
    const drift: SchemaDriftResponse = {
      summary: {
        datasets_added: 0,
        datasets_removed: 0,
        columns_added: 1,
        columns_removed: 0,
        columns_renamed: 0,
        columns_type_changed: 0,
        has_drift: true,
      },
      headline: "1 added since last run.",
      datasets_added: [],
      datasets_removed: [],
      per_dataset: [],
    };
    const onReview = vi.fn();
    render(
      <SchemaDriftBanner
        source={SOURCE}
        flow={FLOW}
        clientImpl={stubClient(drift)}
        onReview={onReview}
      />,
    );
    await waitFor(() => screen.getByTestId("schema-drift-banner"));
    fireEvent.click(screen.getByTestId("schema-drift-review"));
    expect(onReview).toHaveBeenCalledWith(drift);
  });

  it("dismiss button hides the banner", async () => {
    useSchemaSnapshots.getState().put(hashSource(SOURCE), {
      flow: { datasets: [], recipes: [] },
      capturedAt: new Date().toISOString(),
    });
    const drift: SchemaDriftResponse = {
      summary: {
        datasets_added: 0,
        datasets_removed: 0,
        columns_added: 1,
        columns_removed: 0,
        columns_renamed: 0,
        columns_type_changed: 0,
        has_drift: true,
      },
      headline: "1 added since last run.",
      datasets_added: [],
      datasets_removed: [],
      per_dataset: [],
    };
    render(
      <SchemaDriftBanner
        source={SOURCE}
        flow={FLOW}
        clientImpl={stubClient(drift)}
      />,
    );
    await waitFor(() => screen.getByTestId("schema-drift-banner"));
    fireEvent.click(screen.getByTestId("schema-drift-dismiss"));
    expect(screen.queryByTestId("schema-drift-banner")).toBeNull();
  });
});

describe("<SchemaDriftPanel />", () => {
  it("renders nothing when closed", () => {
    render(<SchemaDriftPanel drift={null} open={false} onClose={() => {}} />);
    expect(screen.queryByTestId("schema-drift-panel")).toBeNull();
  });

  it("renders renamed and type-changed rows", () => {
    const drift: SchemaDriftResponse = {
      summary: {
        datasets_added: 0,
        datasets_removed: 0,
        columns_added: 0,
        columns_removed: 0,
        columns_renamed: 1,
        columns_type_changed: 1,
        has_drift: true,
      },
      headline: "drift",
      datasets_added: [],
      datasets_removed: [],
      per_dataset: [
        {
          dataset: "trades",
          added: [],
          removed: [],
          renamed: [{ from: "price", to: "px", type: "double" }],
          type_changed: [{ name: "qty", from_type: "int", to_type: "string" }],
        },
      ],
    };
    render(<SchemaDriftPanel drift={drift} open={true} onClose={() => {}} />);
    expect(screen.getByTestId("schema-drift-panel")).toBeInTheDocument();
    expect(screen.getByTestId("drift-renamed-price-px")).toHaveTextContent("price");
    expect(screen.getByTestId("drift-type-changed-qty")).toHaveTextContent("qty");
  });
});
