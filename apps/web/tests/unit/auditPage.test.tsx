import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AuditPage } from "../../src/features/audit/AuditPage";
import type { AuditEvent, AuditListResponse } from "../../src/api/client";

const PAGE_1: AuditListResponse = {
  events: [
    {
      ts: "2026-04-26T10:00:00Z",
      actor: "alice",
      action: "flow.create",
      resource_type: "flow",
      resource_id: "f1",
      details: { name: "x" },
    },
    {
      ts: "2026-04-26T10:01:00Z",
      actor: "bob",
      action: "flow.share",
      resource_type: "flow",
      resource_id: "f1",
      details: { ttl_seconds: 600 },
    },
  ],
  next_cursor: "1",
};

const PAGE_2: AuditListResponse = {
  events: [
    {
      ts: "2026-04-26T10:02:00Z",
      actor: "alice",
      action: "flow.update",
      resource_type: "flow",
      resource_id: "f1",
      details: { name: "y" },
    } satisfies AuditEvent,
  ],
  next_cursor: null,
};

describe("<AuditPage />", () => {
  it("renders rows from the first page", async () => {
    const stub = { listAuditEvents: vi.fn(async () => PAGE_1) };
    render(<AuditPage clientImpl={stub} />);
    await waitFor(() => {
      expect(screen.getByTestId("audit-row-0")).toBeInTheDocument();
    });
    expect(screen.getByTestId("audit-row-0")).toHaveTextContent("alice");
    expect(screen.getByTestId("audit-row-1")).toHaveTextContent("bob");
  });

  it("loads the next page when 'Load more' is clicked", async () => {
    const stub = {
      listAuditEvents: vi
        .fn()
        .mockResolvedValueOnce(PAGE_1)
        .mockResolvedValueOnce(PAGE_2),
    };
    render(<AuditPage clientImpl={stub} />);
    await waitFor(() => {
      expect(screen.getByTestId("audit-row-1")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("audit-load-more"));
    await waitFor(() => {
      expect(screen.getByTestId("audit-row-2")).toBeInTheDocument();
    });
    expect(stub.listAuditEvents).toHaveBeenCalledTimes(2);
    const calls = stub.listAuditEvents.mock.calls as unknown as Array<unknown[]>;
    const lastCallArgs = calls[1]?.[0];
    expect(lastCallArgs).toEqual(
      expect.objectContaining({ cursor: "1" }),
    );
  });

  it("re-fetches with filters when Apply is clicked", async () => {
    const stub = {
      listAuditEvents: vi.fn(async () => PAGE_1),
    };
    render(<AuditPage clientImpl={stub} />);
    await waitFor(() => expect(stub.listAuditEvents).toHaveBeenCalledTimes(1));
    fireEvent.change(screen.getByTestId("audit-filter-actor"), {
      target: { value: "alice" },
    });
    fireEvent.click(screen.getByTestId("audit-apply-filters"));
    await waitFor(() => expect(stub.listAuditEvents).toHaveBeenCalledTimes(2));
    const calls = stub.listAuditEvents.mock.calls as unknown as Array<unknown[]>;
    const args = calls[1]?.[0];
    expect(args).toEqual(expect.objectContaining({ actor: "alice" }));
  });

  it("renders an empty state when there are no events", async () => {
    const stub = {
      listAuditEvents: vi.fn(async () => ({ events: [], next_cursor: null })),
    };
    render(<AuditPage clientImpl={stub} />);
    await waitFor(() => {
      expect(screen.getByTestId("audit-empty")).toBeInTheDocument();
    });
  });
});
