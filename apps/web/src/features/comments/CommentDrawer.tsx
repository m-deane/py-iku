import { useEffect, useRef, useState } from "react";
import type { Comment, CollabClient } from "../../api/client";
import { useComments } from "./useComments";

export interface CommentDrawerProps {
  /** UUID of the saved flow that owns these comments. */
  flowId: string;
  /** The recipe whose thread is open — null hides the drawer. */
  recipeId: string | null;
  /** Close handler — controlled component. */
  onClose: () => void;
  /** Test seam — swap in a stub client. */
  clientImpl?: CollabClient;
}

/**
 * Inline comment thread for a single recipe.
 *
 * Single-user mode for v1 — every author defaults to "you" or
 * ``STUDIO_AUTHOR``.  Multi-user real-time collab is a Wave 5+ extension.
 */
export function CommentDrawer(props: CommentDrawerProps): JSX.Element | null {
  const { flowId, recipeId, onClose } = props;
  const open = recipeId !== null;
  const { comments, post, remove } = useComments(flowId, {
    clientImpl: props.clientImpl,
    enabled: open,
  });
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (open) {
      // Defer focus so the drawer transition doesn't fight us.
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  if (!open || !recipeId) return null;

  const recipeComments: Comment[] = comments.filter(
    (c) => c.recipe_id === recipeId,
  );

  const submit = (): void => {
    const trimmed = draft.trim();
    if (!trimmed) return;
    post.mutate({ recipeId, body: trimmed });
    setDraft("");
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      submit();
    }
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  };

  return (
    <aside
      data-testid="comment-drawer"
      role="dialog"
      aria-label={`Comments on ${recipeId}`}
      style={{
        position: "fixed",
        right: 0,
        top: 0,
        bottom: 0,
        width: "min(420px, 100vw)",
        background: "var(--surface)",
        borderLeft: "1px solid var(--border)",
        boxShadow: "var(--shadow-lg)",
        zIndex: 50,
        display: "flex",
        flexDirection: "column",
        fontFamily: "var(--font-sans)",
      }}
    >
      <header
        style={{
          padding: "var(--space-4) var(--space-5)",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
        }}
      >
        <SpeechBubbleIcon size={18} />
        <h2
          style={{
            margin: 0,
            fontSize: "var(--text-md)",
            fontWeight: "var(--font-weight-semibold)",
            color: "var(--fg)",
            flex: 1,
          }}
        >
          {recipeId}
        </h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close comments"
          data-testid="comment-drawer-close"
          style={{
            border: 0,
            background: "transparent",
            cursor: "pointer",
            color: "var(--fg-muted)",
            fontSize: "1.2rem",
            lineHeight: 1,
            padding: "var(--space-1)",
          }}
        >
          ×
        </button>
      </header>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "var(--space-4) var(--space-5)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-3)",
        }}
        data-testid="comment-list"
      >
        {recipeComments.length === 0 ? (
          <p
            data-testid="comment-empty"
            style={{
              color: "var(--fg-muted)",
              fontSize: "var(--text-sm)",
              margin: 0,
            }}
          >
            No comments yet. Add the first note for this recipe.
          </p>
        ) : (
          recipeComments.map((c) => (
            <CommentItem
              key={c.id}
              comment={c}
              onDelete={() => remove.mutate({ commentId: c.id })}
            />
          ))
        )}
      </div>

      <footer
        style={{
          borderTop: "1px solid var(--border)",
          padding: "var(--space-3) var(--space-5) var(--space-4)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-2)",
        }}
      >
        <textarea
          ref={inputRef}
          data-testid="comment-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Leave a note for the next reviewer…"
          rows={3}
          style={{
            width: "100%",
            resize: "vertical",
            padding: "var(--space-2) var(--space-3)",
            border: "1px solid var(--border-strong)",
            borderRadius: "var(--radius-md)",
            background: "var(--surface)",
            color: "var(--fg)",
            fontFamily: "inherit",
            fontSize: "var(--text-sm)",
            lineHeight: "var(--lh-snug)",
          }}
        />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "var(--space-2)",
          }}
        >
          <span
            style={{
              fontSize: "var(--text-xs)",
              color: "var(--fg-subtle)",
            }}
          >
            ⌘+Enter to send · Esc to close
          </span>
          <button
            type="button"
            onClick={submit}
            disabled={!draft.trim() || post.isPending}
            data-testid="comment-submit"
            style={{
              padding: "var(--space-2) var(--space-4)",
              borderRadius: "var(--radius-md)",
              border: 0,
              background: "var(--accent)",
              color: "var(--accent-fg)",
              fontWeight: "var(--font-weight-semibold)",
              fontSize: "var(--text-sm)",
              cursor:
                !draft.trim() || post.isPending ? "not-allowed" : "pointer",
              opacity: !draft.trim() || post.isPending ? 0.5 : 1,
            }}
          >
            {post.isPending ? "Sending…" : "Comment"}
          </button>
        </div>
      </footer>
    </aside>
  );
}

function CommentItem(props: {
  comment: Comment;
  onDelete: () => void;
}): JSX.Element {
  const { comment, onDelete } = props;
  const isOptimistic = comment.id.startsWith("tmp-");
  return (
    <article
      data-testid={`comment-${comment.id}`}
      data-optimistic={isOptimistic ? "true" : undefined}
      style={{
        padding: "var(--space-3)",
        borderRadius: "var(--radius-md)",
        background: "var(--surface-raised)",
        border: "1px solid var(--border)",
        opacity: isOptimistic ? 0.7 : 1,
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2)",
          marginBottom: "var(--space-1)",
        }}
      >
        <strong
          style={{
            fontSize: "var(--text-sm)",
            color: "var(--fg)",
          }}
        >
          {comment.author}
        </strong>
        <time
          dateTime={comment.timestamp}
          style={{
            fontSize: "var(--text-xs)",
            color: "var(--fg-muted)",
          }}
        >
          {formatTimestamp(comment.timestamp)}
        </time>
        <button
          type="button"
          onClick={onDelete}
          aria-label="Delete comment"
          disabled={isOptimistic}
          style={{
            marginLeft: "auto",
            border: 0,
            background: "transparent",
            color: "var(--fg-muted)",
            cursor: isOptimistic ? "not-allowed" : "pointer",
            fontSize: "var(--text-xs)",
          }}
        >
          delete
        </button>
      </header>
      <p
        style={{
          margin: 0,
          fontSize: "var(--text-sm)",
          color: "var(--fg)",
          lineHeight: "var(--lh-base)",
          whiteSpace: "pre-wrap",
        }}
      >
        {comment.body}
      </p>
    </article>
  );
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts;
    return d.toLocaleString();
  } catch {
    return ts;
  }
}

/** Speech-bubble icon, also used by the recipe-card overlay button. */
export function SpeechBubbleIcon(props: { size?: number }): JSX.Element {
  const size = props.size ?? 14;
  return (
    <svg
      role="img"
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2 4.5C2 3.67 2.67 3 3.5 3h9c.83 0 1.5.67 1.5 1.5v6c0 .83-.67 1.5-1.5 1.5H6.5l-3 2.5v-2.5h-.5C2.67 12 2 11.33 2 10.5v-6Z" />
    </svg>
  );
}
