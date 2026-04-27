import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CommentDrawer } from "../../src/features/comments/CommentDrawer";
import { RecipeCommentBubble } from "../../src/features/comments/RecipeCommentBubble";
import type {
  CollabClient,
  Comment,
  CommentListResponse,
} from "../../src/api/client";

const FLOW_ID = "11111111-2222-3333-4444-555555555555";

function makeClient(seed: Comment[] = []): {
  client: CollabClient;
  posts: Array<{ recipeId: string; body: string }>;
} {
  let store = [...seed];
  const posts: Array<{ recipeId: string; body: string }> = [];
  const cli: Partial<CollabClient> = {
    listComments: vi.fn(async () => ({ comments: store }) as CommentListResponse),
    postComment: vi.fn(async (_flowId, recipeId, body) => {
      const created: Comment = {
        id: `c-${store.length + 1}`,
        flow_id: FLOW_ID,
        recipe_id: recipeId,
        author: body.author ?? "you",
        body: body.body,
        timestamp: new Date().toISOString(),
        edited_at: null,
      };
      store = [...store, created];
      posts.push({ recipeId, body: body.body });
      return created;
    }),
    deleteComment: vi.fn(async (_flowId, commentId) => {
      store = store.filter((c) => c.id !== commentId);
    }),
    previewFixtures: vi.fn(),
    bundleFixtures: vi.fn(),
    githubPublish: vi.fn(),
  };
  return { client: cli as CollabClient, posts };
}

function withQueryClient(node: JSX.Element): JSX.Element {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{node}</QueryClientProvider>;
}

describe("<CommentDrawer />", () => {
  it("renders existing comments when opened on a recipe", async () => {
    const { client } = makeClient([
      {
        id: "c1",
        flow_id: FLOW_ID,
        recipe_id: "prepare_trades",
        author: "matthew",
        body: "Sanity-check the FX join",
        timestamp: "2026-04-26T10:00:00Z",
        edited_at: null,
      },
    ]);
    render(
      withQueryClient(
        <CommentDrawer
          flowId={FLOW_ID}
          recipeId="prepare_trades"
          onClose={() => {}}
          clientImpl={client}
        />,
      ),
    );
    await waitFor(() => {
      expect(screen.getByTestId("comment-c1")).toBeInTheDocument();
    });
    expect(screen.getByText("Sanity-check the FX join")).toBeInTheDocument();
  });

  it("optimistically appends a comment on submit before the server resolves", async () => {
    const { client, posts } = makeClient();
    render(
      withQueryClient(
        <CommentDrawer
          flowId={FLOW_ID}
          recipeId="join_books"
          onClose={() => {}}
          clientImpl={client}
        />,
      ),
    );
    await waitFor(() => {
      expect(screen.getByTestId("comment-empty")).toBeInTheDocument();
    });
    const input = screen.getByTestId("comment-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "watch out for nulls" } });
    fireEvent.click(screen.getByTestId("comment-submit"));

    // Optimistic item lands immediately with a tmp- prefix id.
    await waitFor(() => {
      const items = screen.getAllByText("watch out for nulls");
      expect(items.length).toBeGreaterThan(0);
    });
    await waitFor(() => {
      expect(posts).toHaveLength(1);
      expect(posts[0]).toEqual({
        recipeId: "join_books",
        body: "watch out for nulls",
      });
    });
  });

  it("returns null when no recipe is selected", () => {
    const { client } = makeClient();
    const { container } = render(
      withQueryClient(
        <CommentDrawer
          flowId={FLOW_ID}
          recipeId={null}
          onClose={() => {}}
          clientImpl={client}
        />,
      ),
    );
    expect(container.querySelector('[data-testid="comment-drawer"]')).toBeNull();
  });
});

describe("<RecipeCommentBubble />", () => {
  it("shows a badge when count > 0", () => {
    render(
      <RecipeCommentBubble
        recipeId="prepare_trades"
        count={3}
        onOpen={() => {}}
      />,
    );
    expect(
      screen.getByTestId("recipe-comment-badge-prepare_trades"),
    ).toHaveTextContent("3");
  });

  it("hides the badge when count is 0", () => {
    render(
      <RecipeCommentBubble
        recipeId="prepare_trades"
        count={0}
        onOpen={() => {}}
      />,
    );
    expect(
      screen.queryByTestId("recipe-comment-badge-prepare_trades"),
    ).toBeNull();
  });

  it("invokes onOpen with the recipeId", () => {
    const onOpen = vi.fn();
    render(
      <RecipeCommentBubble
        recipeId="join_books"
        count={1}
        onOpen={onOpen}
      />,
    );
    fireEvent.click(screen.getByTestId("recipe-comment-bubble-join_books"));
    expect(onOpen).toHaveBeenCalledWith("join_books");
  });

  it("clamps the badge at 99+", () => {
    render(
      <RecipeCommentBubble
        recipeId="x"
        count={250}
        onOpen={() => {}}
      />,
    );
    expect(screen.getByTestId("recipe-comment-badge-x")).toHaveTextContent(
      "99+",
    );
  });
});
