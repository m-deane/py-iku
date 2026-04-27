import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  collabClient as defaultClient,
  type Comment,
  type CommentListResponse,
  type CollabClient,
} from "../../api/client";

export interface UseCommentsOptions {
  /** Test seam — swap in a stub client. */
  clientImpl?: CollabClient;
  /** Disable when no flow is loaded. */
  enabled?: boolean;
}

export function commentsQueryKey(flowId: string): [string, string] {
  return ["comments", flowId];
}

/**
 * TanStack Query-backed hook for the comments feature.
 *
 * Posts use optimistic updates so the new comment appears in the drawer the
 * moment the user hits Send — backend round-trip then either confirms or
 * rolls the temp item back on failure.
 */
export function useComments(flowId: string | null, options?: UseCommentsOptions) {
  const cli = options?.clientImpl ?? defaultClient;
  const qc = useQueryClient();

  const enabled = Boolean(flowId) && options?.enabled !== false;

  const list = useQuery<CommentListResponse, Error>({
    queryKey: commentsQueryKey(flowId ?? "__none__"),
    queryFn: () => cli.listComments(flowId as string),
    enabled,
    staleTime: 10_000,
  });

  const post = useMutation<
    Comment,
    Error,
    { recipeId: string; body: string; author?: string },
    { previous?: CommentListResponse }
  >({
    mutationFn: ({ recipeId, body, author }) => {
      if (!flowId) {
        return Promise.reject(new Error("flowId is required"));
      }
      return cli.postComment(flowId, recipeId, { body, author });
    },
    onMutate: async ({ recipeId, body, author }) => {
      if (!flowId) return {};
      await qc.cancelQueries({ queryKey: commentsQueryKey(flowId) });
      const previous = qc.getQueryData<CommentListResponse>(
        commentsQueryKey(flowId),
      );
      const tempId = `tmp-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
      const optimistic: Comment = {
        id: tempId,
        flow_id: flowId,
        recipe_id: recipeId,
        author: author ?? "you",
        body,
        timestamp: new Date().toISOString(),
        edited_at: null,
      };
      qc.setQueryData<CommentListResponse>(commentsQueryKey(flowId), {
        comments: [...(previous?.comments ?? []), optimistic],
      });
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      if (!flowId) return;
      if (ctx?.previous) {
        qc.setQueryData(commentsQueryKey(flowId), ctx.previous);
      }
    },
    onSettled: () => {
      if (flowId) {
        void qc.invalidateQueries({ queryKey: commentsQueryKey(flowId) });
      }
    },
  });

  const remove = useMutation<void, Error, { commentId: string }, { previous?: CommentListResponse }>({
    mutationFn: ({ commentId }) => {
      if (!flowId) return Promise.reject(new Error("flowId is required"));
      return cli.deleteComment(flowId, commentId);
    },
    onMutate: async ({ commentId }) => {
      if (!flowId) return {};
      await qc.cancelQueries({ queryKey: commentsQueryKey(flowId) });
      const previous = qc.getQueryData<CommentListResponse>(commentsQueryKey(flowId));
      qc.setQueryData<CommentListResponse>(commentsQueryKey(flowId), {
        comments: (previous?.comments ?? []).filter((c) => c.id !== commentId),
      });
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      if (!flowId || !ctx?.previous) return;
      qc.setQueryData(commentsQueryKey(flowId), ctx.previous);
    },
    onSettled: () => {
      if (flowId) {
        void qc.invalidateQueries({ queryKey: commentsQueryKey(flowId) });
      }
    },
  });

  const comments = list.data?.comments ?? [];

  /** Map of recipe_id → comment count for the speech-bubble badge. */
  const countByRecipe: Record<string, number> = {};
  for (const c of comments) {
    countByRecipe[c.recipe_id] = (countByRecipe[c.recipe_id] ?? 0) + 1;
  }

  return {
    comments,
    countByRecipe,
    isLoading: list.isLoading,
    error: list.error,
    post,
    remove,
    refetch: list.refetch,
  };
}
