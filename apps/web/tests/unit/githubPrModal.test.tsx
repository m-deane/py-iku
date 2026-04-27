import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { GithubPrModal } from "../../src/features/github/GithubPrModal";
import type { Client, CollabClient } from "../../src/api/client";

const FLOW = {
  flow_name: "demo-flow",
  total_recipes: 0,
  total_datasets: 0,
  datasets: [],
  recipes: [],
};

function makeClient(): Client {
  return {
    export: vi.fn(async () => ({
      blob: new Blob(["<svg/>"], { type: "image/svg+xml" }),
      filename: "flow.svg",
      contentType: "image/svg+xml",
    })),
  } as unknown as Client;
}

function makeCollab(
  publish: CollabClient["githubPublish"],
): CollabClient {
  return {
    listComments: vi.fn(),
    postComment: vi.fn(),
    deleteComment: vi.fn(),
    previewFixtures: vi.fn(),
    bundleFixtures: vi.fn(),
    githubPublish: publish,
  } as unknown as CollabClient;
}

describe("<GithubPrModal />", () => {
  it("renders nothing when flow is null", () => {
    const { container } = render(
      <GithubPrModal
        flow={null}
        onClose={() => {}}
        clientImpl={makeClient()}
        collabImpl={makeCollab(vi.fn())}
      />,
    );
    expect(container.querySelector('[data-testid="github-pr-modal"]')).toBeNull();
  });

  it("disables submit until the form is filled", () => {
    render(
      <GithubPrModal
        flow={FLOW}
        onClose={() => {}}
        clientImpl={makeClient()}
        collabImpl={makeCollab(vi.fn())}
      />,
    );
    // PAT + repo are blank by default, so submit is disabled.
    expect(screen.getByTestId("github-pr-submit")).toBeDisabled();
  });

  it("invokes githubPublish on submit and shows the success view", async () => {
    const publish = vi.fn(async () => ({
      pr_url: "https://github.com/owner/repo/pull/42",
      pr_number: 42,
      branch: "studio/demo-x",
      commit_sha: "abc",
    }));
    render(
      <GithubPrModal
        flow={FLOW}
        onClose={() => {}}
        clientImpl={makeClient()}
        collabImpl={makeCollab(publish)}
      />,
    );
    fireEvent.change(screen.getByTestId("github-pat-input"), {
      target: { value: "ghp_xxx" },
    });
    fireEvent.change(screen.getByTestId("github-repo-input"), {
      target: { value: "owner/demo-flows" },
    });
    fireEvent.click(screen.getByTestId("github-pr-submit"));
    await waitFor(() => {
      expect(publish).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByTestId("github-pr-success")).toBeInTheDocument();
    });
    expect(screen.getByTestId("github-pr-link")).toHaveAttribute(
      "href",
      "https://github.com/owner/repo/pull/42",
    );
  });

  it("surfaces a friendly message for the BAD_PAT error code", async () => {
    const publish = vi.fn(async () => {
      const err = new Error("BAD_PAT") as Error & {
        detail?: { code: string; message: string };
      };
      err.detail = { code: "BAD_PAT", message: "Bad credentials" };
      throw err;
    });
    render(
      <GithubPrModal
        flow={FLOW}
        onClose={() => {}}
        clientImpl={makeClient()}
        collabImpl={makeCollab(publish)}
      />,
    );
    fireEvent.change(screen.getByTestId("github-pat-input"), {
      target: { value: "ghp_invalid" },
    });
    fireEvent.change(screen.getByTestId("github-repo-input"), {
      target: { value: "owner/repo" },
    });
    fireEvent.click(screen.getByTestId("github-pr-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("github-pr-error")).toBeInTheDocument();
    });
    const errBox = screen.getByTestId("github-pr-error");
    expect(errBox).toHaveAttribute("data-error-code", "BAD_PAT");
    expect(errBox).toHaveTextContent(/PAT/i);
  });

  it("surfaces a friendly message for BRANCH_EXISTS", async () => {
    const publish = vi.fn(async () => {
      const err = new Error("BRANCH_EXISTS") as Error & {
        detail?: { code: string; message: string };
      };
      err.detail = { code: "BRANCH_EXISTS", message: "branch already exists" };
      throw err;
    });
    render(
      <GithubPrModal
        flow={FLOW}
        onClose={() => {}}
        clientImpl={makeClient()}
        collabImpl={makeCollab(publish)}
      />,
    );
    fireEvent.change(screen.getByTestId("github-pat-input"), {
      target: { value: "ghp_x" },
    });
    fireEvent.change(screen.getByTestId("github-repo-input"), {
      target: { value: "owner/repo" },
    });
    fireEvent.click(screen.getByTestId("github-pr-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("github-pr-error")).toHaveAttribute(
        "data-error-code",
        "BRANCH_EXISTS",
      );
    });
  });
});
