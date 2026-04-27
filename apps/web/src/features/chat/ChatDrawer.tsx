import { useEffect, useMemo, useRef, useState } from "react";
import { useChatStore, flowIdFromCode } from "./chatStore";
import { ChatMessage } from "./ChatMessage";
import { useChatStream, type UseChatStreamOptions } from "./useChatStream";
import { useFlowStore } from "../../state/flowStore";
import { useSettingsStore } from "../../state/settingsStore";
import type { ChatTurn } from "./chatStore";

export interface ChatDrawerProps {
  /** Test seam — swap in stub fetch / client. */
  streamOptions?: UseChatStreamOptions;
  /** Force-open the drawer (used by tests). */
  open?: boolean;
}

/**
 * Right-side chat-with-flow drawer. Open with the gear-bar button or
 * Cmd+I. Width defaults to 30 vw and is bounded between 25 vw and 50 vw via
 * the chat store.
 *
 * History is per-flow (keyed by the active flow's id) so switching between
 * Convert tabs surfaces the right thread.
 */
export function ChatDrawer({ streamOptions, open: openProp }: ChatDrawerProps): JSX.Element | null {
  const drawerOpen = useChatStore((s) => s.drawerOpen);
  const setOpen = useChatStore((s) => s.setOpen);
  const drawerWidth = useChatStore((s) => s.drawerWidth);
  const historyByFlow = useChatStore((s) => s.historyByFlow);
  const appendTurn = useChatStore((s) => s.appendTurn);
  const patchAssistantTurn = useChatStore((s) => s.patchAssistantTurn);
  const clearHistory = useChatStore((s) => s.clearHistory);

  const flow = useFlowStore((s) => s.currentFlow);
  const code = useFlowStore((s) => s.currentCode);
  const provider = useSettingsStore((s) => s.llmProvider);
  const model = useSettingsStore((s) => s.llmModel);

  const stream = useChatStream(streamOptions);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [draft, setDraft] = useState("");

  const flowId = useMemo(() => flowIdFromCode(code || "(empty)"), [code]);
  const history: ChatTurn[] = historyByFlow[flowId] ?? [];

  // Cmd+I shortcut — toggle drawer.
  useEffect(() => {
    function onKey(e: KeyboardEvent): void {
      const meta = e.metaKey || e.ctrlKey;
      if (meta && (e.key === "i" || e.key === "I")) {
        e.preventDefault();
        useChatStore.getState().toggleOpen();
      }
      if (e.key === "Escape" && useChatStore.getState().drawerOpen) {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setOpen]);

  // Auto-scroll to bottom on new turn / streaming update.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [history.length, stream.partial]);

  // While streaming, mirror partial text into the in-flight assistant turn.
  const inFlightAssistantId = useRef<string | null>(null);
  useEffect(() => {
    if (stream.status === "streaming" && inFlightAssistantId.current) {
      patchAssistantTurn(flowId, inFlightAssistantId.current, {
        content: stream.partial,
        pending: true,
      });
    }
  }, [stream.status, stream.partial, flowId, patchAssistantTurn]);

  useEffect(() => {
    if (stream.status === "done" && stream.final && inFlightAssistantId.current) {
      patchAssistantTurn(flowId, inFlightAssistantId.current, {
        content: stream.final.answer,
        citations: stream.final.citations,
        pending: false,
      });
      inFlightAssistantId.current = null;
    }
    if (stream.status === "error" && stream.error && inFlightAssistantId.current) {
      patchAssistantTurn(flowId, inFlightAssistantId.current, {
        content: `Error: ${stream.error.detail ?? stream.error.title}`,
        pending: false,
      });
      inFlightAssistantId.current = null;
    }
  }, [stream.status, stream.final, stream.error, flowId, patchAssistantTurn]);

  const isOpen = openProp ?? drawerOpen;

  const send = (): void => {
    const q = draft.trim();
    if (!q) return;
    if (!flow) {
      appendTurn(flowId, {
        id: `t-${Date.now()}-sys`,
        role: "system",
        content: "Convert a Python script first — the chat needs a flow.",
        ts: Date.now(),
      });
      setDraft("");
      return;
    }
    const userTurn: ChatTurn = {
      id: `t-${Date.now()}-u`,
      role: "user",
      content: q,
      ts: Date.now(),
    };
    appendTurn(flowId, userTurn);
    const assistantTurn: ChatTurn = {
      id: `t-${Date.now()}-a`,
      role: "assistant",
      content: "",
      pending: true,
      ts: Date.now(),
    };
    appendTurn(flowId, assistantTurn);
    inFlightAssistantId.current = assistantTurn.id;
    setDraft("");
    void stream.start({
      flow_json: flow as Record<string, unknown>,
      question: q,
      pandas_source: code,
      flow_id: flowId,
      history: history.map((t) => ({ role: t.role, content: t.content })),
      provider,
      model,
      stream: true,
    });
  };

  if (!isOpen) return null;

  const widthVw = `${Math.round(drawerWidth * 100)}vw`;

  return (
    <aside
      data-testid="chat-drawer"
      role="dialog"
      aria-label="Chat with flow"
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        bottom: 0,
        width: widthVw,
        minWidth: 340,
        maxWidth: "50vw",
        background: "var(--surface, #ffffff)",
        borderLeft: "1px solid var(--border, #eaecf0)",
        boxShadow: "var(--shadow-lg, 0 24px 48px rgba(15, 23, 42, 0.12))",
        display: "flex",
        flexDirection: "column",
        zIndex: 60,
      }}
    >
      <header
        style={{
          padding: "var(--space-3, 12px) var(--space-4, 16px)",
          borderBottom: "1px solid var(--border, #eaecf0)",
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2, 8px)",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "var(--text-md, 16px)" }}>
          Chat with flow
        </h2>
        <span
          style={{
            fontSize: "var(--text-xs, 12px)",
            color: "var(--fg-muted, #5b6470)",
          }}
        >
          {flow ? `${(flow as { flow_name?: string }).flow_name ?? flowId}` : "no flow yet"}
        </span>
        <span style={{ marginLeft: "auto", display: "inline-flex", gap: 8 }}>
          <button
            type="button"
            data-testid="chat-clear"
            onClick={() => clearHistory(flowId)}
            style={iconBtn}
            aria-label="Clear chat history"
          >
            ⌫
          </button>
          <button
            type="button"
            data-testid="chat-close"
            onClick={() => setOpen(false)}
            style={iconBtn}
            aria-label="Close chat drawer"
          >
            ✕
          </button>
        </span>
      </header>

      <div
        ref={scrollRef}
        data-testid="chat-history"
        style={{
          flex: 1,
          overflow: "auto",
          padding: "var(--space-2, 8px) 0",
        }}
      >
        {history.length === 0 ? (
          <EmptyState />
        ) : (
          history.map((turn) => <ChatMessage key={turn.id} turn={turn} />)
        )}
      </div>

      <footer
        style={{
          padding: "var(--space-3, 12px) var(--space-4, 16px)",
          borderTop: "1px solid var(--border, #eaecf0)",
        }}
      >
        <textarea
          ref={inputRef}
          data-testid="chat-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder={
            flow
              ? "Ask about the flow… e.g. 'why is recipe 4 medium-confidence?'"
              : "Convert a script first to enable chat."
          }
          rows={2}
          style={{
            width: "100%",
            resize: "none",
            border: "1px solid var(--border, #eaecf0)",
            borderRadius: "var(--radius-md, 8px)",
            padding: "var(--space-2, 8px) var(--space-3, 12px)",
            fontSize: "var(--text-sm, 14px)",
            background: "var(--surface, #ffffff)",
            color: "var(--fg, #101828)",
            fontFamily: "inherit",
          }}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "var(--space-2, 8px)",
          }}
        >
          <span
            style={{
              fontSize: "var(--text-xs, 12px)",
              color: "var(--fg-muted, #5b6470)",
            }}
          >
            {stream.status === "streaming"
              ? "streaming…"
              : stream.status === "connecting"
                ? "connecting…"
                : stream.status === "error"
                  ? `error: ${stream.error?.detail ?? stream.error?.title ?? ""}`
                  : "Enter ↩ to send · Shift+↩ for newline"}
          </span>
          <button
            type="button"
            data-testid="chat-send"
            onClick={send}
            disabled={!draft.trim() || stream.status === "streaming"}
            style={{
              padding: "var(--space-2, 6px) var(--space-3, 14px)",
              border: 0,
              borderRadius: "var(--radius-md, 8px)",
              background: "var(--accent, #0d9488)",
              color: "var(--accent-fg, #ffffff)",
              fontWeight: 600,
              cursor: !draft.trim() ? "not-allowed" : "pointer",
              opacity: !draft.trim() ? 0.6 : 1,
            }}
          >
            Send
          </button>
        </div>
      </footer>
    </aside>
  );
}

const iconBtn: React.CSSProperties = {
  width: 28,
  height: 28,
  border: "1px solid var(--border, #eaecf0)",
  borderRadius: "var(--radius-md, 6px)",
  background: "transparent",
  color: "var(--fg, #101828)",
  cursor: "pointer",
};

function EmptyState(): JSX.Element {
  return (
    <div
      style={{
        padding: "var(--space-5, 24px)",
        color: "var(--fg-muted, #5b6470)",
        fontSize: "var(--text-sm, 14px)",
        lineHeight: 1.5,
      }}
    >
      <p style={{ margin: "0 0 var(--space-3, 12px)" }}>
        Ask anything about this flow. The assistant will cite the specific
        recipes it references — click a chip to highlight that node on the
        canvas.
      </p>
      <p style={{ margin: 0, fontWeight: 600 }}>Examples</p>
      <ul style={{ margin: "var(--space-1, 4px) 0 0", paddingLeft: 18 }}>
        <li>What does the WINDOW recipe do?</li>
        <li>Why is recipe 4 medium-confidence?</li>
        <li>Rewrite the GROUPING step in plain SQL.</li>
      </ul>
    </div>
  );
}
