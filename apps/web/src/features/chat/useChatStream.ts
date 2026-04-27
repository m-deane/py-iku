import { useCallback, useRef, useState } from "react";
import {
  client as defaultClient,
  type ChatCitation,
  type ChatRequest,
  type ChatResponse,
} from "../../api/client";
import { useSettingsStore } from "../../state/settingsStore";

export type ChatStreamStatus =
  | "idle"
  | "connecting"
  | "streaming"
  | "done"
  | "error";

export interface UseChatStreamOptions {
  /** Test seam — swap in a stub fetch for SSE. */
  fetchImpl?: typeof fetch;
  /** Test seam — swap in a stub `client.chat` for non-stream fallback. */
  clientImpl?: { chat: typeof defaultClient.chat };
}

export interface UseChatStreamResult {
  status: ChatStreamStatus;
  /** Live partial text while streaming. Empty after `done`. */
  partial: string;
  /** Final response (citations, usage, cost) once stream completes. */
  final: ChatResponse | null;
  error: { title: string; detail?: string } | null;
  start: (req: ChatRequest) => Promise<void>;
  cancel: () => void;
}

interface SsePayload {
  event: string;
  data: unknown;
}

/**
 * Parse a Server-Sent Events stream chunk into structured events.
 *
 * Real SSE parsers handle multi-line `data:` and event reset on blank line —
 * we implement just the subset our backend emits: `event: NAME\ndata: JSON\n\n`.
 */
function* parseSse(buffer: string): Generator<SsePayload> {
  const events = buffer.split("\n\n");
  for (const block of events) {
    if (!block.trim()) continue;
    let event = "message";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event: ")) event = line.slice(7).trim();
      else if (line.startsWith("data: ")) data = line.slice(6).trim();
    }
    if (!data) continue;
    let parsed: unknown = null;
    try {
      parsed = JSON.parse(data);
    } catch {
      parsed = data;
    }
    yield { event, data: parsed };
  }
}

/**
 * Streaming chat hook. Uses ``fetch`` with ``ReadableStream`` to consume the
 * SSE response from POST /chat. We deliberately use plain fetch instead of
 * EventSource because EventSource only supports GET — chat needs to POST a
 * payload that includes the flow JSON.
 *
 * Cancellation routes through an AbortController so closing the drawer
 * mid-stream cleanly aborts the in-flight request.
 */
export function useChatStream(
  options: UseChatStreamOptions = {},
): UseChatStreamResult {
  const [status, setStatus] = useState<ChatStreamStatus>("idle");
  const [partial, setPartial] = useState("");
  const [final, setFinal] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<{ title: string; detail?: string } | null>(
    null,
  );
  const abortRef = useRef<AbortController | null>(null);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const start = useCallback(
    async (req: ChatRequest): Promise<void> => {
      cancel();
      const ac = new AbortController();
      abortRef.current = ac;
      setStatus("connecting");
      setPartial("");
      setFinal(null);
      setError(null);

      const fetchImpl = options.fetchImpl ?? fetch;
      const baseUrl = useSettingsStore
        .getState()
        .apiBaseUrl.replace(/\/$/, "");
      const url = `${baseUrl}/chat`;
      const body = JSON.stringify({ ...req, stream: true });

      try {
        const response = await fetchImpl(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body,
          signal: ac.signal,
        });

        if (!response.ok) {
          let detail = response.statusText;
          try {
            const data = await response.json();
            detail = data.detail?.reason || data.detail || data.title || detail;
          } catch {
            /* ignore */
          }
          setStatus("error");
          setError({ title: `HTTP ${response.status}`, detail });
          return;
        }

        if (!response.body) {
          // Older browsers / mocked fetch — try the JSON sync fallback.
          const cli = options.clientImpl ?? defaultClient;
          const result = await cli.chat({ ...req, stream: false });
          setPartial(result.answer);
          setFinal(result);
          setStatus("done");
          return;
        }

        setStatus("streaming");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let assembled = "";
        let citations: ChatCitation[] = [];

        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          // Drain whole-event blocks (terminated by \n\n). Keep the trailing
          // partial chunk in the buffer for the next iteration.
          const lastBlankIdx = buffer.lastIndexOf("\n\n");
          if (lastBlankIdx === -1) continue;
          const drainable = buffer.slice(0, lastBlankIdx + 2);
          buffer = buffer.slice(lastBlankIdx + 2);

          for (const evt of parseSse(drainable)) {
            if (evt.event === "delta") {
              const text = (evt.data as { text?: string })?.text ?? "";
              assembled += text;
              setPartial(assembled);
            } else if (evt.event === "final") {
              const f = evt.data as ChatResponse;
              citations = f.citations ?? [];
              setFinal({ ...f, answer: assembled || f.answer });
              setStatus("done");
              return;
            } else if (evt.event === "error") {
              const e = evt.data as { title?: string; detail?: string };
              setError({
                title: e.title ?? "Stream error",
                detail: e.detail,
              });
              setStatus("error");
              return;
            }
          }
        }

        // EOF without a final event — still surface what we have.
        setStatus("done");
        if (!final) {
          setFinal({
            answer: assembled,
            citations,
            model: "(unknown)",
            usage: {},
            cost_usd: 0,
          });
        }
      } catch (err) {
        if ((err as { name?: string })?.name === "AbortError") {
          setStatus("idle");
          return;
        }
        setStatus("error");
        setError({
          title: "Network error",
          detail: err instanceof Error ? err.message : String(err),
        });
      } finally {
        abortRef.current = null;
      }
    },
    [cancel, options, final],
  );

  return { status, partial, final, error, start, cancel };
}
