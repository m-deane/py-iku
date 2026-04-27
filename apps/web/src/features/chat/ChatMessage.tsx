import { useMemo } from "react";
import type { ChatTurn } from "./chatStore";
import { useChatStore } from "./chatStore";
import { useFlowStore } from "../../state/flowStore";

export interface ChatMessageProps {
  turn: ChatTurn;
}

/**
 * Renders one chat turn. Citation markers `[recipe:NAME]` in assistant
 * answers become clickable chips that highlight the matching recipe on the
 * canvas (via flowStore.setSelectedNodeId) and on the chat-store hover state.
 */
export function ChatMessage({ turn }: ChatMessageProps): JSX.Element {
  const setHighlight = useChatStore((s) => s.setHighlight);
  const setSelectedNodeId = useFlowStore((s) => s.setSelectedNodeId);

  const segments = useMemo(() => splitWithCitations(turn.content), [turn.content]);

  const isUser = turn.role === "user";
  const wrapStyle: React.CSSProperties = {
    display: "flex",
    justifyContent: isUser ? "flex-end" : "flex-start",
    padding: "var(--space-2, 8px) var(--space-3, 12px)",
  };
  const bubbleStyle: React.CSSProperties = {
    maxWidth: "85%",
    background: isUser
      ? "var(--accent, #0d9488)"
      : "var(--surface-raised, #f7f8fa)",
    color: isUser ? "var(--accent-fg, #ffffff)" : "var(--fg, #101828)",
    border: isUser ? "none" : "1px solid var(--border, #eaecf0)",
    padding: "var(--space-2, 8px) var(--space-3, 12px)",
    borderRadius: "var(--radius-md, 8px)",
    fontSize: "var(--text-sm, 14px)",
    whiteSpace: "pre-wrap",
    lineHeight: 1.45,
  };

  return (
    <div style={wrapStyle} data-testid={`chat-turn-${turn.role}`}>
      <div style={bubbleStyle}>
        {segments.map((seg, idx) =>
          seg.kind === "text" ? (
            <span key={idx}>{seg.text}</span>
          ) : (
            <button
              type="button"
              key={idx}
              data-testid={`chat-citation-${seg.recipeId}`}
              onMouseEnter={() => setHighlight(seg.recipeId)}
              onMouseLeave={() => setHighlight(null)}
              onClick={() => setSelectedNodeId(seg.recipeId)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                margin: "0 2px",
                padding: "0 6px",
                borderRadius: "var(--radius-pill, 9999px)",
                border: "1px solid var(--border-strong, #d0d5dd)",
                background: "var(--surface, #ffffff)",
                color: "var(--accent, #0d9488)",
                fontSize: "var(--text-xs, 12px)",
                fontWeight: 600,
                cursor: "pointer",
              }}
              aria-label={`Highlight recipe ${seg.recipeId}`}
            >
              ▣ {seg.recipeId}
            </button>
          ),
        )}
        {turn.pending ? (
          <span
            data-testid="chat-streaming-cursor"
            style={{ marginLeft: 4, opacity: 0.7 }}
          >
            ▍
          </span>
        ) : null}
      </div>
    </div>
  );
}

interface CitationSeg {
  kind: "citation";
  recipeId: string;
}
interface TextSeg {
  kind: "text";
  text: string;
}
type Segment = CitationSeg | TextSeg;

const RE = /\[recipe:([A-Za-z0-9_\-]+)\]/g;

export function splitWithCitations(content: string): Segment[] {
  const out: Segment[] = [];
  let lastIdx = 0;
  let m: RegExpExecArray | null;
  RE.lastIndex = 0;
  while ((m = RE.exec(content)) !== null) {
    if (m.index > lastIdx) {
      out.push({ kind: "text", text: content.slice(lastIdx, m.index) });
    }
    out.push({ kind: "citation", recipeId: m[1] });
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < content.length) {
    out.push({ kind: "text", text: content.slice(lastIdx) });
  }
  return out;
}
