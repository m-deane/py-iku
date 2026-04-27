import { SpeechBubbleIcon } from "./CommentDrawer";

export interface RecipeCommentBubbleProps {
  /** The recipe whose thread the bubble opens. */
  recipeId: string;
  /** Number of comments on this recipe — drives the badge. */
  count: number;
  /** Click handler — typically wired to set the open recipe in parent state. */
  onOpen: (recipeId: string) => void;
}

/**
 * Speech-bubble button rendered in the corner of a recipe card.
 * Shows a count badge when there is at least one comment on the recipe.
 */
export function RecipeCommentBubble(
  props: RecipeCommentBubbleProps,
): JSX.Element {
  const { recipeId, count, onOpen } = props;
  const hasComments = count > 0;
  return (
    <button
      type="button"
      onClick={() => onOpen(recipeId)}
      data-testid={`recipe-comment-bubble-${recipeId}`}
      data-comment-count={count}
      aria-label={
        hasComments
          ? `Open comments on ${recipeId} (${count})`
          : `Add comment on ${recipeId}`
      }
      title={
        hasComments
          ? `${count} comment${count === 1 ? "" : "s"}`
          : "Add comment"
      }
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: 28,
        height: 28,
        borderRadius: "var(--radius-pill)",
        border: "1px solid var(--border)",
        background: hasComments ? "var(--accent-bg-soft)" : "var(--surface-raised)",
        color: hasComments ? "var(--accent-hover)" : "var(--fg-muted)",
        cursor: "pointer",
        padding: 0,
      }}
    >
      <SpeechBubbleIcon size={14} />
      {hasComments ? (
        <span
          aria-hidden="true"
          data-testid={`recipe-comment-badge-${recipeId}`}
          style={{
            position: "absolute",
            top: -4,
            right: -4,
            minWidth: 16,
            height: 16,
            padding: "0 4px",
            borderRadius: "var(--radius-pill)",
            background: "var(--accent)",
            color: "var(--accent-fg)",
            fontSize: 10,
            fontWeight: "var(--font-weight-semibold)",
            lineHeight: "16px",
            textAlign: "center",
          }}
        >
          {count > 99 ? "99+" : count}
        </span>
      ) : null}
    </button>
  );
}
